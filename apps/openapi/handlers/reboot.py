# -*- coding: utf-8 -*-

"""This module is designed for reboot of Open API.
"""

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
        """Reboot a terminal.
        """
        status = ErrorCode.SUCCESS        
        try:
            data = DotDict(json_decode(self.request.body))
            mobile = str(data.mobile)
            token = data.token
            logging.info("[REBOOT] Request, data:%s", data)
        except Exception as e:
            logging.exception("[REBOOT] Invalid data format, body: %s, mobile: %s.",
                              self.request.body, mobile)
            status = ErrorCode.DATA_FORMAT_INVALID
            self.write_ret(status)
            return

        try:
            status = self.basic_check(token, mobile)                             
            if status != ErrorCode.SUCCESS:
                self.write_ret(status)
                return

            terminal = QueryHelper.get_terminal_by_tmobile(mobile, self.db)         
            tid = terminal.tid
            restart_terminal(self.db, self.redis, tid, mobile) 
            logging.info("[REBOOT] Restart a terminal. tid: %s, mobile: %s", tid, mobile)               

            self.write_ret(status)
        except Exception as e:
            logging.exception("[REBOOT] Reboot failed. mobile: %s. Exception: %s",
                              mobile, e.args)
            status = ErrorCode.FAILED
            self.write_ret(status)
