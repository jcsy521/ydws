# -*- coding: utf-8 -*-

import functools
import urlparse
import urllib
import re

import tornado.web
from tornado.escape import json_encode

from utils.dotdict import DotDict
from helpers.queryhelper import QueryHelper
from codes.errorcode import ErrorCode

# cookie expire periods, in minutes. one week.
EXPIRES_MINUTES = 7 * 24 * 60 


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

    COOKIE_PATTERN = re.compile(r"C=(?P<cid>.*):U=(?P<uid>.*):T=(?P<tid>.*):TT=(?P<sim>.*)")
    COOKIE_FORMAT = "C=%(cid)s:U=%(uid)s:T=%(tid)s:TT=%(sim)s"
 
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
    def redis(self):
        return self.application.redis

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
        self.write(json_encode(ret))

    def check_tid(self, tid, finish=False):
        """
        check tid whether exists in request and modify the current_user.
        """
        if tid:
            terminal = QueryHelper.get_terminal_by_tid(tid, self.db)
            if not terminal:
                status = ErrorCode.LOGIN_AGAIN
                logging.error("The terminal with uid: %s, tid: %s does not exist, login again", self.current_user.uid, tid)
                self.write_ret(status)
                if finish:
                    self.finish()
                return
  
            self.current_user.tid=terminal.tid
            self.current_user.sim=terminal.mobile
