# -*- coding: utf-8 -*-

"""This module is designed for other handlers.
"""

import functools
import urlparse
import urllib
import re
import logging
import random
from time import strftime, time

import tornado.web
from tornado.escape import json_encode

from utils.dotdict import DotDict
from utils.misc import safe_utf8, get_client_id
from helpers.queryhelper import QueryHelper
from helpers.confhelper import ConfHelper
from codes.errorcode import ErrorCode

from constants.UWEB import EXPIRES_MINUTES


class _DBDescriptor(object):
    def __get__(self, obj, type=None):
        return obj.application.db


def authenticated(method):
    """Decorate methods with this to require that the user be logged in."""
    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        if not self.current_user:
            url = self.get_login_url()
            if self.request.method == "POST":
                raise tornado.web.HTTPError(403)
            elif self.request.method in ("GET", "HEAD"):
                if "?" not in url:                
                    if urlparse.urlsplit(url).scheme:
                        # if login url is absolute, make next absolute too
                        next_url = self.request.full_url()
                    else:
                        #next_url = self.request.uri
                        next_url = "/index" 
                    url += "?" + urllib.urlencode(dict(next=next_url))
         
            self.redirect(url)
            return
        return method(self, *args, **kwargs)
    return wrapper 


class BaseHandler(tornado.web.RequestHandler):

    SUPPORTED_METHODS = ("GET", "POST", "DELETE", "PUT")

    COOKIE_PATTERN = re.compile(r"C=(?P<cid>.*):O=(?P<oid>.*):U=(?P<uid>.*):T=(?P<tid>.*):TT=(?P<sim>.*)")
    COOKIE_FORMAT = "C=%(cid)s:O=%(oid)s:U=%(uid)s:T=%(tid)s:TT=%(sim)s"
 
    JSON_HEADER = ("Content-Type", "application/json; charset=utf-8")

    def __init__(self, application, request):
        tornado.web.RequestHandler.__init__(self, application, request)

    @property
    def queue(self):
        return self.application.queue

    # NOTE: use descriptor for db in order to override it in thread callbacks.
    db = _DBDescriptor()

    @property
    def redis(self):
        return self.application.redis

    @property
    def app_name(self):
        return self.application.settings.get('app_name')

   
    def bookkeep(self, data_dict):
        """Set cookie for current_user. 
        """
        self.set_secure_cookie(self.app_name,
                               self.COOKIE_FORMAT % data_dict,
                               expires_days=float(EXPIRES_MINUTES)/(24 * 60),
                               httponly=True)

    def get_current_user(self):
        """Override the method in tornado.web. 
        Detect a logined user through cookie.
        """
        app_data = self.get_secure_cookie(self.app_name)
        if app_data:
            res = self.COOKIE_PATTERN.match(app_data)
            if res and all(res.groupdict().itervalues()):
                self.bookkeep(res.groupdict())
                return DotDict(res.groupdict())
        return None

    def write_ret(self, status, message=None, dict_=None):
        """
        write back ret message: dict(status=status,
                                     message=ErrorCode.ERROR_MESSAGE[status],
                                     ...)
        """
        ret = DotDict(status=status)
        if message is None:
            ret.message = ErrorCode.ERROR_MESSAGE[status]
        else:
            ret.message = message

        try:
            ret['message'] = ret['message'].encode('utf8')
        except:
            pass

        if isinstance(dict_, dict):
            ret.update(dict_)
        self.set_header(*self.JSON_HEADER)
        t = json_encode(ret)
        self.write(t)
