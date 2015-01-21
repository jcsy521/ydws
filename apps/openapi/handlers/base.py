# -*- coding: utf-8 -*-

import logging

import tornado.web
from tornado.escape import json_encode

from utils.dotdict import DotDict
from codes.openapi_errorcode import ErrorCode
from helpers.queryhelper import QueryHelper 
from helpers.openapihelper import OpenapiHelper 

class _DBDescriptor(object):
    def __get__(self, obj, type=None):
        return obj.application.db

class BaseHandler(tornado.web.RequestHandler):

    SUPPORTED_METHODS = ("GET", "POST" )

    JSON_HEADER = ("Content-Type", "application/json; charset=utf-8")

    def __init__(self, application, request):
        tornado.web.RequestHandler.__init__(self, application, request)


    # NOTE: use descriptor for db in order to override it in thread callbacks.
    db = _DBDescriptor()

    @property
    def redis(self):
        return self.application.redis

    def finish(self, chunk=None):
        if self.request.connection.stream.closed():
            return
        super(BaseHandler, self).finish(chunk)

    def write_ret(self, status, message=None, dict_=None):
        """
        write back ret message: dict(status=status,
                                     message=ErrorCode.ERROR_MESSAGE[status],
                                     ...)
        """
        ret = DotDict(status=status)
        if message is None:
            ret.message = ErrorCode.ERROR_MESSAGE[status]

        if isinstance(dict_, dict):
            ret.update(dict_)
        self.set_header(*self.JSON_HEADER)
        self.write(json_encode(ret))

    def basic_check(self, token, mobile):
        """Check the request whether valid.
        """
        status = ErrorCode.SUCCESS
        # check token
        sp = OpenapiHelper.check_token(self.redis, token)         
        if (not sp) or (not sp.get('cid','')): 
            status = ErrorCode.TOKEN_EXPIRED
            logging.info("[OPENAPI] Check token failed. token: %s, message: %s.",
                         token, ErrorCode.ERROR_MESSAGE[status])
            return status

        # check mobile
        terminals = QueryHelper.get_all_terminals_by_cid(sp.cid, self.db)
        mobiles = [str(t.mobile) for t in terminals]
        if mobile not in mobiles:                   
            status = ErrorCode.MOBILE_NOT_EXISTED
            logging.info("[OPENAPI] Check mobile failed. mobile: %s, message: %s.",
                         mobile, ErrorCode.ERROR_MESSAGE[status])
            return status

        return status
