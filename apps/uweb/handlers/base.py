# -*- coding: utf-8 -*-

import functools
import urlparse
import urllib
import re

import tornado.web
from tornado.escape import json_encode

from utils.dotdict import DotDict
from codes.errorcode import ErrorCode

# cookie expire periods, in minutes, JXQ cookie time out is 4 hours.
EXPIRES_MINUTES = 36500 * 24 * 60 


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
                        next_url = self.request.uri
                    url += "?" + urllib.urlencode(dict(next=next_url))
            self.redirect(url)
            return
        return method(self, *args, **kwargs)
    return wrapper 


class BaseHandler(tornado.web.RequestHandler):

    SUPPORTED_METHODS = ("GET", "POST", "DELETE", "PUT")

    COOKIE_PATTERN = re.compile(r"U=(?P<uid>.*):T=(?P<tid>.*):TT=(?P<sim>.*)")
    COOKIE_FORMAT = "U=%(uid)s:T=%(tid)s:TT=%(sim)s"
 
    JSON_HEADER = ("Content-Type", "application/json; charset=utf-8")

    def __init__(self, application, request):
        tornado.web.RequestHandler.__init__(self, application, request)

    @property
    def queue(self):
        return self.application.queue

    # NOTE: use descriptor for db in order to override it in thread callbacks.
    db = _DBDescriptor()

    @property
    def memcached(self):
        return self.application.memcached

    @property
    def app_name(self):
        return self.application.settings.get('app_name')

    def finish(self, chunk=None):
        if self.request.connection.stream.closed():
            return
        super(BaseHandler, self).finish(chunk)

    def bookkeep(self, data_dict):
        self.set_secure_cookie(self.app_name,
                               self.COOKIE_FORMAT % data_dict,
                               expires_days=float(EXPIRES_MINUTES)/(24 * 60))

    def get_current_user(self):
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
        if isinstance(dict_, dict):
            ret.update(dict_)
        self.set_header(*self.JSON_HEADER)
        print 'test base', json_encode(ret)
        self.write(json_encode(ret))
