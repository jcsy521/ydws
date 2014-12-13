# -*- coding: utf-8 -*-

"""It provide some useful utils for the server.

* SignHandler: provide sign;

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

from base import BaseHandler


class SignHandler(BaseHandler):

    @tornado.web.removeslash
    def post(self):
        """Get last infomation of a terminal.
        """
        status = ErrorCode.SUCCESS
        sign = ''
        try: 
            data = DotDict(json_decode(self.request.body))
            password = data.password
            timestamp = data.timestamp
            logging.info("[TEST] Request, data:%s", data)
        except Exception as e:
            logging.exception("[TEST] Invalid data format, body: %s.",
                              self.request.body)
            status = ErrorCode.DATA_FORMAT_INVALID
            self.write_ret(status)
            return

        try:
            # TODO：basic check locals()
            
            sign = OpenapiHelper.get_sign(password, timestamp)
            self.write_ret(status,
                           dict_=dict(sign=sign))

        except Exception as e:
            logging.exception("[TEST] password: %s, timestamp:%s, Exception: %s",
                              password, timestamp, e.args)
            status = ErrorCode.FAILED
            self.write_ret(status)
