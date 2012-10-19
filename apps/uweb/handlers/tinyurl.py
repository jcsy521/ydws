# -*- coding: utf-8 -*-

import logging

import tornado.web

from helpers.confhelper import ConfHelper
from codes.errorcode import ErrorCode
from base import BaseHandler

class TinyURLHandler(BaseHandler):
    """tinyurl to url."""

    @tornado.web.removeslash
    def get(self, tinyid):
        url = self.redis.get(tinyid)
        if not url:
            message = ErrorCode.ERROR_MESSAGE[ErrorCode.TINYURL_EXPIRED]
            self.render("error.html",
                        message=message,
                        home_url=ConfHelper.UWEB_CONF.url_out)
        else:
            self.redirect(url)

