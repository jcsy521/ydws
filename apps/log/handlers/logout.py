# -*- coding:utf-8 -*-

from base import BaseHandler, authenticated

import tornado.web


class LogoutHandler(BaseHandler):

    @authenticated
    @tornado.web.removeslash
    def get(self):
        self.clear_cookie(self.app_name)
        self.clear_cookie("%s_N" % (self.app_name,))
        self.redirect("/")
