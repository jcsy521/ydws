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
from utils.public import (record_add_action, delete_terminal, add_user, add_terminal)
from utils.misc import (get_terminal_sessionID_key, get_terminal_address_key,
     get_terminal_info_key, get_lq_sms_key, get_lq_interval_key, get_del_data_key,
     get_tid_from_mobile_ydwq)
from constants import UWEB, GATEWAY
from helpers.gfsenderhelper import GFSenderHelper
from helpers.smshelper import SMSHelper
from helpers.queryhelper import QueryHelper
from helpers.confhelper import ConfHelper

from utils.checker import check_phone, check_zs_phone
from codes.errorcode import ErrorCode
from codes.smscode import SMSCode

from base import BaseHandler, authenticated
from mixin.base import BaseMixin

class BatchImportHandler(BaseHandler):
    """Batch."""

    @authenticated
    @tornado.web.removeslash
    def get(self):
        """Render to fileUpload.html 
        """
        self.render('fileUpload.html',
                    status=None)

    @authenticated
    @tornado.web.removeslash
    def post(self):
        """Read excel.
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
                #NOTE: first line is title, and is ignored
                for j in range(1,sheet.nrows): 
                    row = sheet.row_values(j)
                    tmobile = unicode(row[0])
                    tmobile = tmobile[0:11]
                    umobile = ''
                    if len(row) > 1:
                        umobile = unicode(row[1])
                        umobile = umobile[0:11]
                    biz_type = UWEB.BIZ_TYPE.YDWS 
                    if len(row) > 2:
                        biz_type = unicode(row[2])
                        biz_type = biz_type[0:1]
                        biz_type = biz_type if biz_type else UWEB.BIZ_TYPE.YDWS 

                    r = DotDict(tmobile=tmobile,
                                umobile=umobile,
                                biz_type=int(biz_type),
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

                    existed_terminal = self.db.get("SELECT id, tid, service_status FROM T_TERMINAL_INFO"
                                                   "  WHERE mobile = %s", tmobile)
                    if existed_terminal:
                        if existed_terminal.service_status == UWEB.SERVICE_STATUS.TO_BE_UNBIND:
                            delete_terminal(existed_terminal.tid, self.db, self.redis)
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
            status = ErrorCode.ILLEGAL_FILE
            self.render("fileUpload.html",
                        status=status,
                        message=ErrorCode.ERROR_MESSAGE[status])


class BatchDeleteHandler(BaseHandler, BaseMixin):
    """Batch delete."""

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
                                       "    AND (service_status = %s"
                                       "    OR service_status = %s)",
                                       tid, UWEB.SERVICE_STATUS.ON, UWEB.SERVICE_STATUS.TO_BE_ACTIVATED)
                if not terminal:
                    r.status = ErrorCode.SUCCESS
                    res.append(r)
                    logging.error("The terminal with tid: %s does not exist!", tid)
                    continue 

                key = get_del_data_key(tid)
                self.redis.set(key, flag)
                biz_type = QueryHelper.get_biz_type_by_tmobile(terminal.mobile, self.db) 
                if int(biz_type) == UWEB.BIZ_TYPE.YDWQ:
                    delete_terminal(tid, self.db, self.redis)
                    res.append(r)
                    continue 
                elif int(biz_type) == UWEB.BIZ_TYPE.YDWS:
                    if terminal.login != GATEWAY.TERMINAL_LOGIN.ONLINE:
                        if terminal.mobile == tid:
                            delete_terminal(tid, self.db, self.redis)
                        else:
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
                    biz_type = QueryHelper.get_biz_type_by_tmobile(terminal.mobile, self.db)
                    if biz_type != UWEB.BIZ_TYPE.YDWS:
                        ret = DotDict(status=ErrorCode.SUCCESS)
                    else:
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
            status = ErrorCode.ILLEGAL_FILE
            self.write_ret(status)

class BatchJHHandler(BaseHandler):
    """Batch jh."""

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
                if item['umobile']: 
                    umobile = item['umobile'] 
                else:
                    corp = self.db.get("SELECT cid, mobile FROM T_CORP WHERE cid = %s", self.current_user.cid) 
                    umobile = corp.mobile

                biz_type = item['biz_type']
                r = DotDict(tmobile=tmobile,
                            status=ErrorCode.SUCCESS)
                # 1. add terminal

                terminal = self.db.get("SELECT id, tid, service_status FROM T_TERMINAL_INFO WHERE mobile = %s",
                                       tmobile)
                if terminal:
                    if terminal.service_status == UWEB.SERVICE_STATUS.TO_BE_UNBIND:
                        delete_terminal(terminal.tid, self.db, self.redis)
                    else:
                        logging.error("[UWEB] mobile: %s already existed.", tmobile)
                        r['status'] = ErrorCode.TERMINAL_ORDERED
                        continue 

                terminal_info = dict(tid=tmobile,
                                     group_id=gid,
                                     tmobile=tmobile,
                                     owner_mobile=umobile,
                                     mannual_status=UWEB.DEFEND_STATUS.YES,
                                     begintime=begintime,
                                     endtime=4733481600,
                                     offline_time=begintime,
                                     login_permit=0,
                                     biz_type=biz_type,
                                     service_status=UWEB.SERVICE_STATUS.ON)

                if int(biz_type) == UWEB.BIZ_TYPE.YDWS:
                    register_sms = SMSCode.SMS_REGISTER % (umobile, tmobile) 
                    ret = SMSHelper.send_to_terminal(tmobile, register_sms)
                else:
                    activation_code = QueryHelper.get_activation_code(self.db)
                    tid = get_tid_from_mobile_ydwq(tmobile)
                    terminal_info['tid'] = tid
                    terminal_info['activation_code'] = activation_code 
                    terminal_info['service_status'] = UWEB.SERVICE_STATUS.TO_BE_ACTIVATED 

                    register_sms = SMSCode.SMS_REGISTER_YDWQ % (ConfHelper.UWEB_CONF.url_out, activation_code)
                    ret = SMSHelper.send(tmobile, register_sms)

                add_terminal(terminal_info, self.db, self.redis)
                # record the add action, enterprise
                bind_info = dict(tid=terminal_info['tid'], 
                                 tmobile=tmobile,
                                 umobile=umobile,
                                 group_id=gid,
                                 cid=self.current_user.cid,
                                 add_time=int(time.time()))
                record_add_action(bind_info, self.db)

                ret = DotDict(json_decode(ret))
                if ret.status == ErrorCode.SUCCESS:
                    self.db.execute("UPDATE T_TERMINAL_INFO"
                                    "  SET msgid = %s"
                                    "  WHERE tid = %s",
                                    ret['msgid'], terminal_info['tid'])
                else:
                    r['status'] = ErrorCode.FAILED 
                    
                # 2. add user
                existed_user = self.db.get("SELECT id FROM T_USER"
                                           " WHERE mobile = %s", umobile)
                if existed_user:
                    pass
                else:
                    user_info = dict(umobile=umobile,
                                     password='111111',
                                     uname=umobile)
                    add_user(user_info, self.db, self.redis)
                res.append(r)
            self.write_ret(status, 
                           dict_=DotDict(res=res))
        except Exception as e:
            logging.exception("[UWEB] cid: %s batch jh failed. Exception: %s",
                              self.current_user.cid, e.args)
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)

class BatchSpeedlimitHandler(BaseHandler):
    """Batch set speedlimit."""

    @authenticated
    @tornado.web.removeslash
    def put(self):
        
        try:
            data = DotDict(json_decode(self.request.body))
            tids = data.tids
            speed_limit = data.speed_limit
            logging.info("[UWEB] Batch speed_limit request: %s, corp_id: %s", 
                         data, self.current_user.cid)
        except Exception as e:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            logging.exception("[UWEB] Invalid data format. Exception: %s",
                              e.args)
            self.write_ret(status)
            return

        try:
            status = ErrorCode.SUCCESS
            self.db.executemany("UPDATE T_TERMINAL_INFO SET speed_limit = %s"
                                "  WHERE tid = %s", 
                               [(speed_limit, tid) for tid in tids])
            self.write_ret(status)
        except Exception as e:
            logging.exception("[UWEB] Batch speed_limit failed. Exception: %s, cid: %s",
                               e.args, self.current_user.cid)
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)
