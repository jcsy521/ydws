# -*- coding: utf-8 -*-

import logging

from tornado.escape import json_decode, json_encode
import tornado.web

from utils.dotdict import DotDict
from codes.errorcode import ErrorCode
from constants import UWEB 

from base import BaseHandler, authenticated

class AuthorizeHandler(BaseHandler):

    @tornado.web.removeslash
    def post(self):
        """Authorize a YDWQ terminal.
        """
        status = ErrorCode.SUCCESS
        try:
            data = DotDict(json_decode(self.request.body))
            activation_code = data.activation_code 
            logging.info("[UWEB] authorize request: %s", 
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
                                   "  AND biz_type = %s LIMIT 1",
                                   activation_code, UWEB.BIZ_TYPE.YDWQ)
            if not terminal:
                status = ErrorCode.TERMINAL_NOT_EXISTED
                logging.info("[UWEB] activation_code: %s can not be found.",
                             activation_code)
                self.write_ret(status)
            else:
                self.db.execute("UPDATE T_TERMINAL_INFO"
                                "  SET service_status = %s"
                                "  WHERE activation_code = %s",
                                UWEB.SERVICE_STATUS.ON, activation_code)
                logging.info("[UWEB] activation_code: %s, mobile: %s is authorized.",
                             activation_code, terminal['mobile'])
                self.write_ret(status,
                               dict_=DotDict(mobile=terminal.mobile))
        except Exception as e:
            status = ErrorCode.SERVER_BUSY
            logging.exception("[UWEB] authorize YDWQ termianl failed. Exception: %s",
                              e.args)
            self.write_ret(status)

