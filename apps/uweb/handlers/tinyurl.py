# -*- coding: utf-8 -*-

"""This module is designed for tiny-URL.
"""

import logging

import tornado.web

from helpers.confhelper import ConfHelper
from codes.errorcode import ErrorCode
from base import BaseHandler

class TinyURLHandler(BaseHandler):
    """Transfer tinyurl to full-url.

    :url /tl/{url}
    
    """

    @tornado.web.removeslash
    def get(self, tinyid):
        url = self.redis.get(tinyid)
        if not url:
            logging.info("[UWEB] Do not find tinyid. tinyid: %s", tinyid)
            message = ErrorCode.ERROR_MESSAGE[ErrorCode.TINYURL_EXPIRED]
            self.render("error.html",
                        message=message,
                        home_url=ConfHelper.UWEB_CONF.url_out)
        else:
            logging.info("[UWEB] Redirect to url according tinyid. tinyid: %s, url: %s", 
                         tinyid, url)
            self.redirect(url)

