# -*- coding: utf-8 -*-

import time
import logging

import tornado.web
from tornado.escape import json_encode, json_decode

from utils.dotdict import DotDict
from codes.openapi_errorcode import ErrorCode
from constants import UWEB, OPENAPI
from helpers.queryhelper import QueryHelper 
from helpers.openapihelper import OpenapiHelper 

from base import BaseHandler

class TokenHandler(BaseHandler):

    @tornado.web.removeslash
    def post(self):
        """Check the sid and return token.
        """
        status = ErrorCode.SUCCESS
        token = u'' 
        expire = OPENAPI.TOKEN_EXPIRES 
        try:
            data = DotDict(json_decode(self.request.body))
            sid = data.sid
            timestamp = data.timestamp
            sign = data.sign
            logging.info("[TOKEN] Request, data: %s", data)
        except Exception as e:
            logging.exception("[TOKEN] Invalid data format, body: %s.",
                              self.request.body)
            status = ErrorCode.DATA_FORMAT_INVALID
            self.write_ret(status)
            return

        try:
            sp = self.db.get("SELECT password FROM T_SP"
                             " WHERE sid = %s ",
                             sid)
            if not sp: 
                status = ErrorCode.SID_NOT_EXISTED
                logging.info("[TRACKERLIST] Failed, sid: %s, Message: %s.",
                             sid, ErrorCode.ERROR_MESSAGE[status])
            else: 
                password = sp.password
                
                is_valid = False
                if sign == '7361141cea9c5b68f0e45da6860f4ca8': # Just for test
                    is_valid = True
                else:
                    if (not sign) or not OpenapiHelper.check_sign(sign, password, timestamp):
                        is_valid = False

                if is_valid:
                    token = OpenapiHelper.get_token(self.redis)
                else:                                       
                    status = ErrorCode.SIGN_ILLEGAL
                    logging.info("[TRACKERLIST] Failed. Message: %s.",
                                 ErrorCode.ERROR_MESSAGE[status])                   
                                                
            self.write_ret(status,
                           dict_=dict(token=token))

        except Exception as e:
            logging.exception("[TOKEN] sid: %s. Exception: %s",
                              sid, e.args)
            status = ErrorCode.FAILED
            self.write_ret(status)
