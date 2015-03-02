# -*- coding: utf-8 -*-

"""This module is designed for friendlink .
"""

import tornado.web

from base import BaseHandler


class FriendLinkHandler(BaseHandler):

    @tornado.web.removeslash
    def get(self):
        """Jump to friendlink.html."""
        self.render('friendlink.html')
