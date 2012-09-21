# -*- coding: utf-8 -*-

import logging

import tornado.web

from base import BaseHandler

class HelperHandler(BaseHandler):

    @tornado.web.removeslash
    def get(self):
        """Jump to help.html."""
        self.render('helper.html')

