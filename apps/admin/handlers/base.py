# -*- coding: utf-8 -*-

import functools
import urlparse
import urllib
import re

import tornado.web

from utils.dotdict import DotDict

# expires period for cookie, it's 30 minutes now.
EXPIRES_MINUTES = 30


def authenticated(method):
    """Decorate methods with this to require that the user be logged in."""
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
                        next_url = self.request.uri
                    url += "?" + urllib.urlencode(dict(next=next_url))
            self.redirect(url)
            return
        return method(self, *args, **kwargs)
    return wrapper


class BaseHandler(tornado.web.RequestHandler):

    SUPPORTED_METHODS = ("GET", "POST")
    
    COOKIE_PATTERN = re.compile(r"ID=(?P<id>.+):SID=(?P<session_id>.+)")
    COOKIE_FORMAT = "ID=%(id)s:SID=%(session_id)s"

    JSON_HEADER = ("Content-Type", "application/json; charset=utf-8")

    def __init__(self, application, request):
        tornado.web.RequestHandler.__init__(self, application, request)

    @property
    def db(self):
        return self.application.db

    @property
    def memcached(self):
        return self.application.memcached

    #@property
    #def mongodb(self):
    #    return self.application.mongodb

    @property
    def app_name(self):
        return self.application.settings.get('app_name')

    def bookkeep(self, data_dict, username=None):
        self.set_secure_cookie(self.app_name,
                               self.COOKIE_FORMAT % data_dict,
                               expires_days=float(EXPIRES_MINUTES)/(24 * 60))
        # This is really ticky!
        self.set_cookie("%s_N" % (self.app_name,),
                        username,
                        expires_days=float(EXPIRES_MINUTES)/(24 * 60))

    def get_current_user(self):
        app_data = self.get_secure_cookie(self.app_name)
        if app_data:
            res = self.COOKIE_PATTERN.match(app_data)
            if res and all(res.groupdict().itervalues()):
                username = self.get_cookie("%s_N" % (self.app_name,))
                self.bookkeep(res.groupdict(), username)
                return DotDict(res.groupdict())
        return None
