# -*- coding: utf-8 -*-

import logging

import tornado.web

from base import BaseHandler

class ChargeHandler(BaseHandler):

    @tornado.web.removeslash
    def get(self):
        """Jump to the coresponding charge.html."""
        self.render('charge.html')

