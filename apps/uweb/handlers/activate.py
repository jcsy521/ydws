# -*- coding: utf-8 -*-

import logging

from tornado.escape import json_decode, json_encode
import tornado.web
import time

from utils.dotdict import DotDict
from codes.errorcode import ErrorCode
from constants import UWEB 

from base import BaseHandler, authenticated

class ActivateHandler(BaseHandler):

    @tornado.web.removeslash
    def post(self):
        """Activate a YDWQ terminal.
        """
        status = ErrorCode.SUCCESS
        try:
            data = DotDict(json_decode(self.request.body))
            activation_code = data.activation_code 
            sn = data.sn 
            logging.info("[UWEB] activate request: %s", 
                         data)
        except Exception as e:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            logging.exception("[UWEB] Invalid data format. Exception: %s",
                              e.args)
            self.write_ret(status)
            return

        try:
            terminal = self.db.get("SELECT id, service_status, mobile"
                                   "  FROM T_TERMINAL_INFO"
                                   "  WHERE activation_code = %s"
                                   "  AND sn = %s"
                                   "  AND biz_type = %s LIMIT 1",
                                   activation_code, sn,
                                   UWEB.BIZ_TYPE.YDWQ)
            if terminal: # normal login
                logging.info("[UWEB] normal login. activation_code: %s, sn: %s.", 
                             activation_code, sn)
                self.write_ret(status,
                               dict_=DotDict(mobile=terminal.mobile))
                return
 
            terminal = self.db.get("SELECT id, service_status, mobile"
                                   "  FROM T_TERMINAL_INFO"
                                   "  WHERE activation_code = %s"
                                   "  AND biz_type = %s LIMIT 1",
                                   activation_code, UWEB.BIZ_TYPE.YDWQ)
            if not terminal: # no code, get activate_code first
                status = ErrorCode.TERMINAL_NOT_EXISTED
                logging.error("[UWEB] activation_code: %s can not be found.",
                             activation_code)
                self.write_ret(status)
            else: # has code 
                terminal = self.db.get("SELECT id, service_status, mobile"
                                       "  FROM T_TERMINAL_INFO"
                                       "  WHERE sn = %s LIMIT 1",
                                       sn)
                if terminal: # has code, has sn(but sn exist)
                    status = ErrorCode.TERMINAL_EXIST
                    logging.info("[UWEB] sn: %s has exist.", sn)
                    self.write_ret(status,
                                   dict_=DotDict(mobile=terminal.mobile))
                    return
                # has code, sn not exist: a new activate
                self.db.execute("UPDATE T_TERMINAL_INFO"
                                "  SET sn = %s"
                                "  WHERE activation_code = %s",
                                sn, activation_code)
                if terminal['service_status'] != UWEB.SERVICE_STATUS.ON:
                    self.db.execute("UPDATE T_TERMINAL_INFO"
                                    "  SET service_status = %s"
                                    "  WHERE activation_code = %s",
                                    UWEB.SERVICE_STATUS.ON, activation_code)
                    logging.info("[UWEB] activation_code: %s, mobile: %s is authorized.",
                                 activation_code, terminal['mobile'])
                self.write_ret(status,
                               dict_=DotDict(mobile=terminal.mobile))
        except Exception as e:
            logging.exception("[UWEB] activate YDWQ termianl failed. Exception: %s",
                              e.args)
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)

class ActivationcodeHandler(BaseHandler):

    @tornado.web.removeslash
    def get(self):
        """Get activation_code according to tid or mobile.
        """
        status = ErrorCode.SUCCESS
        try:
            tid = self.get_argument('tid','')
            mobile = self.get_argument('mobile','')
            logging.info("[ACTIVATIONCODE] Activation_code query, tid: %s, mobile: %s.",
                         tid, mobile)
        except Exception as e:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            logging.exception("[ACTIVATIONCODE] Illegal format, body: %s.",
                              self.request.body)
            self.write_ret(status)
            return 

        try:
            terminal = None
            if tid:
                terminal = self.db.get("SELECT activation_code, mobile, tid, biz_type FROM T_TERMINAL_INFO"
                                       "  WHERE tid = %s", 
                                       tid)
            if not terminal:
                if mobile:
                    terminal = self.db.get("SELECT activation_code, mobile, tid, biz_type FROM T_TERMINAL_INFO"
                                           "  WHERE mobile = %s", 
                                           mobile)


            activation_code = terminal.get('activation_code', '') if terminal else ''
            tid = terminal.get('tid', '') if terminal else ''
            mobile = terminal.get('mobile', '') if terminal else ''
            biz_type = terminal.get('biz_type', UWEB.BIZ_TYPE.YDWS) if terminal else UWEB.BIZ_TYPE.YDWS

            self.write_ret(status,
                           dict_=DotDict(activation_code=activation_code,
                                         tid=tid,
                                         mobile=mobile,
                                         biz_type=biz_type))
        except Exception as e:
            status = ErrorCode.SERVER_BUSY
            logging.exception("[ACTIVATIONCODE] get activation_code failed, body: %s. Exception: %s", 
                              self.request.body, e.args)
            self.write_ret(status)

