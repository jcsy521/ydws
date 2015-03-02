# -*- coding: utf-8 -*-

"""This module is designed for Q&A.
"""

import tornado.web

from base import BaseHandler

class ChargeHandler(BaseHandler):

    @tornado.web.removeslash
    def get(self):
        """Jump to the corresponding charge.html."""
        self.render('charge.html')

