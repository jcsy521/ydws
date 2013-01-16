# -*- coding: utf-8 -*-

import logging

import tornado.web

from base import BaseHandler

class FriendLinkHandler(BaseHandler):

    @tornado.web.removeslash
    def get(self):
        """Jump to friendlink.html."""
        self.render('friendlink.html')

