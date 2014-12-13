# -*- coding: utf-8 -*-

import time
import os
import logging

import tornado.web
from tornado.escape import json_encode, json_decode

from utils.dotdict import DotDict
from codes.openapi_errorcode import ErrorCode
from constants import UWEB, OPENAPI
from helpers.queryhelper import QueryHelper 
from helpers.openapihelper import OpenapiHelper 
from utils.public import restart_terminal


from base import BaseHandler

class RebootHandler(BaseHandler):

    @tornado.web.removeslash
    def post(self):
        """Get last infomation of a terminal.
        """
        status = ErrorCode.SUCCESS        
        try:
            data = DotDict(json_decode(self.request.body))
            mobile = data.mobile
            timestamp = data.timestamp
            token = data.token
            logging.info("[REBOOT] Request, data:%s", data)
        except Exception as e:
            logging.exception("[REBOOT] Invalid data format, body: %s, mobile: %s.",
                              self.request.body, mobile)
            status = ErrorCode.DATA_FORMAT_INVALID
            self.write_ret(status)
            return

        try:
            if (not token) or not OpenapiHelper.check_token(token, self.redis):
                status = ErrorCode.TOKEN_EXPIRED
                logging.info("[REBOOT] Failed. Message: %s.",
                             ErrorCode.ERROR_MESSAGE[status])
                self.write_ret(status)
                return
            else:
                terminal = self.db.get("SELECT tid FROM T_TERMINAL_INFO"
                                       "  WHERE mobile = %s"
                                       "  AND service_status = %s",
                                       mobile, UWEB.SERVICE_STATUS.ON)
                if not terminal:
                    status = ErrorCode.MOBILE_NOT_EXISTED
                    logging.info("[REBOOT] Failed. Message: %s.",
                                 ErrorCode.ERROR_MESSAGE[status])
                    self.write_ret(status)
                else: 
                    tid = terminal.tid
                    restart_terminal(self.db, self.redis, tid, mobile) 
                    logging.info("[REBOOT] Restart a terminal. tid: %s, mobile: %s", tid, mobile)               

            self.write_ret(status)
        except Exception as e:
            logging.exception("[REBOOT] Reboot failed. mobile: %s. Exception: %s",
                              mobile, e.args)
            status = ErrorCode.FAILED
            self.write_ret(status)
