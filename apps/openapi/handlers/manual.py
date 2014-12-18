# -*- coding: utf-8 -*-

"""This module is designed for manual_status of Open API.
"""

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
from utils.public import update_mannual_status

from base import BaseHandler

class ManualHandler(BaseHandler):

    @tornado.web.removeslash
    def post(self):
        """Get last infomation of a terminal.
        """
        status = ErrorCode.SUCCESS
        try:
            data = DotDict(json_decode(self.request.body))
            mobile = str(data.mobile)
            manual_status = data.manual_status
            token = data.token
            logging.info("[MANUAL] Request, data:%s", data)
        except Exception as e:
            status = ErrorCode.DATA_FORMAT_INVALID
            logging.exception("[REBOO] Invalid data format, body: %s, mobile: %s.",
                              self.request.body, mobile)
            self.write_ret(status)
            return

        try:
            status = self.basic_check(token, mobile)                             
            if status != ErrorCode.SUCCESS:
                self.write_ret(status)
                return
    
            terminal = QueryHelper.get_terminal_by_tmobile(mobile, self.db)
            tid = terminal.tid                    
            update_mannual_status(self.db, self.redis, tid, manual_status)

            self.write_ret(status)

        except Exception as e:
            logging.exception("[MANUAL] mobile: %s. Exception: %s",
                              mobile, e.args)
            status = ErrorCode.FAILED
            self.write_ret(status)
