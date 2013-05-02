# -*- coding: utf-8 -*-

import logging
import xlrd
import time
import datetime
from dateutil.relativedelta import relativedelta
import os
import random
import string

from tornado.escape import json_decode, json_encode
import tornado.web

from utils.dotdict import DotDict
from utils.misc import get_terminal_sessionID_key, get_terminal_address_key,\
    get_terminal_info_key, get_lq_sms_key, get_lq_interval_key, get_del_data_key
from constants import UWEB, GATEWAY
from helpers.gfsenderhelper import GFSenderHelper
from helpers.smshelper import SMSHelper
from utils.checker import check_phone, check_zs_phone
from codes.errorcode import ErrorCode
from codes.smscode import SMSCode

from base import BaseHandler, authenticated
from mixin.base import BaseMixin

class BatchImportHandler(BaseHandler):
    """batch."""

    @authenticated
    @tornado.web.removeslash
    def get(self):
        """ render to fileUpload.html 
        """
        self.render('fileUpload.html',
                    status=None)

    @authenticated
    @tornado.web.removeslash
    def post(self):
        """ read excel
        """
        try:
            upload_file = self.request.files['upload_file'][0]
            logging.info("[UWEB] batch import, corp_id: %s", 
                         self.current_user.cid)
        except Exception as e:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            self.write_ret(status)
            return

        try:
            status = ErrorCode.SUCCESS
            original_fname = upload_file['filename']
            extension = os.path.splitext(original_fname)[1]
            if extension not in ['.xlsx', '.xls']:
                status = ErrorCode.ILLEGAL_EXCEL_FILE
                self.write_ret(status)
                return

            # write into tmp file
            fname = ''.join(random.choice(string.ascii_lowercase + string.digits) for x in range(6))
            final_filename= fname + extension
            file_path = final_filename
            output_file = open(file_path, 'w')
            output_file.write(upload_file['body'])
            output_file.close()

            res = []
            # read from tmp file
            wb = xlrd.open_workbook(file_path)
            for sheet in wb.sheets():
                for j in range(sheet.nrows):
                    row = sheet.row_values(j)
                    tmobile = unicode(row[0])
                    tmobile = tmobile[:tmobile.find('.')]
                    umobile = ''
                    if len(row) > 1:
                        umobile = unicode(row[1])
                        umobile = umobile[:umobile.find('.')]
                    r = DotDict(tmobile=tmobile,
                                umobile=umobile,
                                status=UWEB.TERMINAL_STATUS.UNJH)   

                    if not check_phone(tmobile) or (umobile and not check_phone(umobile)):
                        r.status = UWEB.TERMINAL_STATUS.INVALID 
                        res.append(r)
                        continue 

                    # check tmobile is whitelist or not
                    white_list = check_zs_phone(tmobile, self.db)
                    if not white_list:
                        logging.error("[UWEB] mobile: %s is not whitelist.", tmobile)
                        r['status'] = UWEB.TERMINAL_STATUS.MOBILE_NOT_ORDERED 
                        res.append(r)
                        continue 

                    existed_terminal = self.db.get("SELECT id, service_status FROM T_TERMINAL_INFO"
                                                   "  WHERE mobile = %s", tmobile)
                    if existed_terminal:
                        if existed_terminal.service_status == UWEB.SERVICE_STATUS.TO_BE_UNBIND:
                            self.db.execute("DELETE FROM T_TERMINAL_INFO WHERE id = %s",
                                            existed_terminal.id)
                            res.append(r)
                        else:
                            r.status = UWEB.TERMINAL_STATUS.EXISTED 
                            res.append(r)
                    else:
                        res.append(r)
            # remove tmp file
            os.remove(file_path)
            self.render("fileUpload.html",
                        status=ErrorCode.SUCCESS,
                        res=res)
                  
        except Exception as e:
            logging.exception("[UWEB] cid: %s batch import failed. Exception: %s",
                              self.current_user.cid, e.args)
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)


class BatchDeleteHandler(BaseHandler, BaseMixin):
    """batch delete."""

    @authenticated
    @tornado.web.removeslash
    def post(self):

        status = ErrorCode.SUCCESS
        try:
            data = DotDict(json_decode(self.request.body))
            logging.info("[UWEB] batch delete request: %s, corp_id: %s", 
                         data, self.current_user.cid)
        except Exception as e:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            self.write_ret(status)
            return

        try:
            status = ErrorCode.SUCCESS
            tids = list(data.tids)
            flag = data.flag
            res = []
            for tid in tids:
                r = DotDict(tid=tid,
                            status=ErrorCode.SUCCESS)
                terminal = self.db.get("SELECT id, mobile, owner_mobile, login FROM T_TERMINAL_INFO"
                                       "  WHERE tid = %s"
                                       "    AND service_status = %s",
                                       tid, 
                                       UWEB.SERVICE_STATUS.ON)
                if not terminal:
                    r.status = ErrorCode.SUCCESS
                    res.append(r)
                    logging.error("The terminal with tid: %s does not exist!", tid)
                    continue 

                key = get_del_data_key(tid)
                self.redis.set(key, flag)
                if terminal.login != GATEWAY.TERMINAL_LOGIN.ONLINE:
                    r.status = self.send_jb_sms(terminal.mobile, terminal.owner_mobile, tid)
                    res.append(r)
                    continue 

                seq = str(int(time.time()*1000))[-4:]
                args = DotDict(seq=seq,
                               tid=tid)
                response = GFSenderHelper.forward(GFSenderHelper.URLS.UNBIND, args)
                response = json_decode(response)
                if response['success'] == ErrorCode.SUCCESS:
                    logging.info("[UWEB] uid:%s, tid: %s, tmobile:%s GPRS unbind successfully", 
                                 self.current_user.uid, tid, terminal.mobile)
                    res.append(r)
                else:
                    # unbind failed. clear sessionID for relogin, then unbind it again
                    sessionID_key = get_terminal_sessionID_key(tid)
                    self.redis.delete(sessionID_key)
                    logging.error('[UWEB] uid:%s, tid: %s, tmobile:%s GPRS unbind failed, message: %s, send JB sms...', 
                                  self.current_user.uid, tid, terminal.mobile, ErrorCode.ERROR_MESSAGE[response['success']])
                    unbind_sms = SMSCode.SMS_UNBIND  
                    ret = SMSHelper.send_to_terminal(terminal.mobile, unbind_sms)
                    ret = DotDict(json_decode(ret))
                    if ret.status == ErrorCode.SUCCESS:
                        res.append(r)
                        self.db.execute("UPDATE T_TERMINAL_INFO"
                                        "  SET service_status = %s"
                                        "  WHERE id = %s",
                                        UWEB.SERVICE_STATUS.TO_BE_UNBIND,
                                        terminal.id)
                        logging.info("[UWEB] uid: %s, tid: %s, tmobile: %s SMS unbind successfully.",
                                     self.current_user.uid, tid, terminal.mobile)
                    else:
                        r.status = ErrorCode.FAILED
                        res.append(r)
                        logging.error("[UWEB] uid: %s, tid: %s, tmobile: %s SMS unbind failed. Message: %s",
                                      self.current_user.uid, tid, terminal.mobile, ErrorCode.ERROR_MESSAGE[status])

            self.write_ret(status, dict_=DotDict(res=res))
        except Exception as e:
            logging.exception("[UWEB] cid: %s batch delete failed. Exception: %s",
                              self.current_user.cid, e.args)
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)

class BatchJHHandler(BaseHandler):
    """batch jh."""

    @authenticated
    @tornado.web.removeslash
    def post(self):
        
        try:
            data = DotDict(json_decode(self.request.body))
            gid = data.gid
            mobiles = list(data.mobiles)
            logging.info("[UWEB] batch jh: %s, corp_id: %s", 
                         data, self.current_user.cid)
        except Exception as e:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            self.write_ret(status)
            return

        try:
            status = ErrorCode.SUCCESS
            begintime = int(time.time())
            now_ = datetime.datetime.now()
            endtime = now_ + relativedelta(years=1)
            endtime = int(time.mktime(endtime.timetuple()))
            res = []
            for item in mobiles:
                tmobile = item['tmobile']
                umobile = item['umobile'] if item['umobile'] else self.current_user.cid
                r = DotDict(tmobile=tmobile,
                            status=ErrorCode.SUCCESS)
                # 1. add terminal
                umobile = umobile if umobile else self.current_user.cid
                terminal = self.db.get("SELECT id, tid, service_status FROM T_TERMINAL_INFO WHERE mobile = %s",
                                       tmobile)
                if terminal:
                    if terminal.service_status == UWEB.SERVICE_STATUS.TO_BE_UNBIND:
                        # clear db
                        self.db.execute("DELETE FROM T_TERMINAL_INFO WHERE id = %s",
                                        terminal.id)
                        tid = terminal.tid
                        user = QueryHelper.get_user_by_tid(tid, self.db)
                        if user:
                            terminals = self.db.query("SELECT id FROM T_TERMINAL_INFO"
                                                      "  WHERE owner_mobile = %s",
                                                      user.owner_mobile)
                            if len(terminals) == 0:
                                self.db.execute("DELETE FROM T_USER"
                                                "  WHERE mobile = %s",
                                                user.owner_mobile)

                                lastinfo_key = get_lastinfo_key(user.owner_mobile)
                                self.redis.delete(lastinfo_key)
                        else:
                            logging.info("[GW] User of %s already not exist.", tid)
                        # clear redis
                        for item in [tid, tmobile]:
                            sessionID_key = get_terminal_sessionID_key(item)
                            address_key = get_terminal_address_key(item)
                            info_key = get_terminal_info_key(item)
                            lq_sms_key = get_lq_sms_key(item)
                            lq_interval_key = get_lq_interval_key(item)
                            keys = [sessionID_key, address_key, info_key, lq_sms_key, lq_interval_key]
                            self.redis.delete(*keys)
                    else:
                        logging.error("[UWEB] mobile: %s already existed.", tmobile)
                        r['status'] = ErrorCode.TERMINAL_ORDERED
                        continue 

                tid = self.db.execute("INSERT INTO T_TERMINAL_INFO(id, tid, mobile, group_id,"
                                      "  owner_mobile, defend_status, mannual_status, begintime, endtime)"
                                      "  VALUES (NULL, %s, %s, %s, %s, %s, %s, %s, %s)",
                                      tmobile, tmobile, gid, umobile, 
                                      UWEB.DEFEND_STATUS.NO, UWEB.DEFEND_STATUS.NO, 
                                      begintime, endtime)
                self.db.execute("INSERT INTO T_CAR(tid)"
                                "  VALUES(%s)",
                                tmobile)
                # 2. add user
                existed_user = self.db.get("SELECT id FROM T_USER"
                                           " WHERE mobile = %s", umobile)
                if existed_user:
                    pass
                else:
                    self.db.execute("INSERT INTO T_USER(id, uid, password, name, mobile)"
                                    "  VALUES (NULL, %s, password(%s), %s, %s)",
                                    umobile, '111111', umobile, umobile)
                    self.db.execute("INSERT INTO T_SMS_OPTION(uid)"
                                    "  VALUES(%s)",
                                    umobile)
                # 3: send JH message to terminal
                register_sms = SMSCode.SMS_REGISTER % (umobile, tmobile) 
                ret = SMSHelper.send_to_terminal(tmobile, register_sms)
                ret = DotDict(json_decode(ret))
                if ret.status == ErrorCode.SUCCESS:
                    self.db.execute("UPDATE T_TERMINAL_INFO"
                                    "  SET msgid = %s"
                                    "  WHERE id = %s",
                                    ret['msgid'], tid)
                else:
                    r['status'] = ErrorCode.FAILED 
                res.append(r)
            self.write_ret(status, dict_=DotDict(res=res))
        except Exception as e:
            logging.exception("[UWEB] cid: %s batch jh failed. Exception: %s",
                              self.current_user.cid, e.args)
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)
