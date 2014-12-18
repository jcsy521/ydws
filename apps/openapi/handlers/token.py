# -*- coding: utf-8 -*-

"""This module is designed for token of Open API.
"""

import logging

import tornado.web
from tornado.escape import json_decode

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
        try:
            data = DotDict(json_decode(self.request.body))
            sid = data.sid
            timestamp = str(data.timestamp)
            sign = data.sign
            logging.info("[TOKEN] Request, data: %s", data)
        except Exception as e:
            status = ErrorCode.DATA_FORMAT_INVALID
            logging.exception("[TOKEN] Invalid data format, body: %s.",
                              self.request.body)
            self.write_ret(status)
            return

        try:
            sp = self.db.get("SELECT sid, password, cid, mobile FROM T_SP"
                             " WHERE sid = %s ",
                             sid)
            if (not sp) or (not sp.get('cid','')): 
                status = ErrorCode.SID_NOT_EXISTED
                logging.info("[TOKEN] Get token failed. sid: %s, Message: %s.",
                             sid, ErrorCode.ERROR_MESSAGE[status])
                self.write_ret(status)
                return

            password = sp.password                
            if (not sign) or not OpenapiHelper.check_sign(sign, password, timestamp):
                is_valid = False
            else:
                is_valid = True

            if is_valid:
                token = OpenapiHelper.get_token(self.redis, sp)
            else:                                       
                status = ErrorCode.SIGN_ILLEGAL
                logging.info("[TOKEN] Get token failed. Message: %s.",
                             ErrorCode.ERROR_MESSAGE[status])                   
                                                
            self.write_ret(status,
                           dict_=dict(token=token))

        except Exception as e:
            logging.exception("[TOKEN] Get token failed. sid: %s. Exception: %s",
                              sid, e.args)
            status = ErrorCode.FAILED
            self.write_ret(status)
