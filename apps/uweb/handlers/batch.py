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
from constants import UWEB, GATEWAY
from helpers.gfsenderhelper import GFSenderHelper
from helpers.smshelper import SMSHelper
from utils.checker import check_phone
from codes.errorcode import ErrorCode
from codes.smscode import SMSCode
from base import BaseHandler, authenticated

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
            file_path = "uploads/" + final_filename
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


class BatchDeleteHandler(BaseHandler):
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
            res = []
            for tid in tids:
                r = DotDict(tid=tid,
                            status=ErrorCode.SUCCESS)
                terminal = self.db.get("SELECT id, mobile, login FROM T_TERMINAL_INFO"
                                       "  WHERE tid = %s"
                                       "    AND service_status = %s",
                                       tid, 
                                       UWEB.SERVICE_STATUS.ON)
                if not terminal:
                    r.status = ErrorCode.SUCCESS
                    res.append(r)
                    logging.error("The terminal with tid: %s does not exist!", tid)
                    continue 
                elif terminal.login == GATEWAY.TERMINAL_LOGIN.OFFLINE:
                    self.db.execute("DELETE FROM T_TERMINAL_INFO WHERE id = %s", terminal.id)
                    logging.error("The terminal with tmobile:%s is offline and delete it!", terminal.mobile)

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
                    #status = response['success']
                    logging.error('[UWEB] uid:%s, tid: %s, tmobile:%s GPRS unbind failed, message: %s, send JB sms...', 
                                  self.current_user.uid, tid, terminal.mobile, ErrorCode.ERROR_MESSAGE[status])
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
                umobile = item['umobile']
                r = DotDict(tmobile=tmobile,
                            status=ErrorCode.SUCCESS)
                # 1. add user
                if umobile:
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
                # 2. add terminal
                umobile = umobile if umobile else self.current_user.cid
                tid = self.db.execute("INSERT INTO T_TERMINAL_INFO(id, tid, mobile, group_id, owner_mobile, begintime, endtime)"
                                      "  VALUES (NULL, %s, %s, %s, %s, %s, %s)",
                                      tmobile, tmobile, gid, umobile, begintime, endtime)
                self.db.execute("INSERT INTO T_CAR(tid)"
                                "  VALUES(%s)",
                                tmobile)
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
