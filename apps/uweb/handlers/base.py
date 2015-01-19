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
    """Decorate methods with this to require that the user be logged in.
    
    workflow:
    if not current_user:
        if method is get or head:
            redirect url 
        else: # post, put, delete and so on.
            raise 403            
    else:
        wrapper and return method
    """
    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):

        if not self.current_user:
            url = self.get_login_url()

            if self.request.method in ("GET", "HEAD"):
                if "?" not in url:                
                    if urlparse.urlsplit(url).scheme:
                        # if login url is absolute, make next absolute too
                        next_url = self.request.full_url()
                    else:
                        #next_url = self.request.uri
                        next_url = "/index" 
                    url += "?" + urllib.urlencode(dict(next=next_url))

                self.redirect(url)
            else: # POST and others
                raise tornado.web.HTTPError(403)            
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
    def memcached(self):
        return self.application.memcached

    @property
    def redis(self):
        return self.application.redis

    @property
    def app_name(self):
        return self.application.settings.get('app_name')

    def set_client_id(self, username):
        """Set a value for client_id in cookie when login is invoked, then get
        the client_id in following request.
        """
        client_id = get_client_id(username)
        return self.set_cookie('client_id', client_id,
                               expires_days=float(EXPIRES_MINUTES)/(24 * 60),
                               httponly=True)

    @property
    def client_id(self):
        """Return the virtual client_id of the current HTTP request.

        Set a value for client_id in cookie when login is invoked, then get
        the client_id in following request.
        """
        return self.get_cookie('client_id')

    def finish(self, chunk=None):
        if self.request.connection.stream.closed():
            return
        super(BaseHandler, self).finish(chunk)

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

    def check_tid(self, tid, finish=False):
        """Check tid whether exists in request and modify the current_user.

        workflow:
        if tid is provided:
            update the current_user

        """
        if tid:
            terminal = QueryHelper.get_terminal_by_tid(tid, self.db)  
            self.current_user.tid=terminal.tid if terminal else tid
            self.current_user.sim=terminal.mobile if terminal else ''

    def check_privilege(self, uid, tid=None):
        """Check the user whether is test only.

        The features needs to be checked contains:
        * getting captcha for retrieve-password.
        * modifying password.
        * retrieving-password.

        workflow:
        if uid is test_uid:
            deny it

        """
        status = ErrorCode.SUCCESS     
        if uid == ConfHelper.UWEB_CONF.test_uid:
            status = ErrorCode.TEST_NOT_PERMITED
        return status
    
    def generate_file_name(self, file_name):
        # NOTE: special handlings for IE.
        if "MSIE" in self.request.headers['User-Agent']:
            file_name = urllib.quote(safe_utf8(file_name))
        return '-'.join((file_name, strftime("%Y%m%d")))
