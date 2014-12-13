# -*- coding: utf-8 -*-

import functools
import logging
import urlparse
import urllib
import re
from time import strftime

import tornado.web
from tornado.escape import json_encode

from utils.dotdict import DotDict
from utils.misc import safe_utf8
from helpers.queryhelper import QueryHelper
from constants import UWEB
from codes.openapi_errorcode import ErrorCode


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
            message = ErrorCode.ERROR_MESSAGE[status]

        # use tornado local to translate the message. 
        ret.message = self.locale.translate(message)

        if isinstance(dict_, dict):
            ret.update(dict_)
        self.set_header(*self.JSON_HEADER)
        self.write(json_encode(ret))
