# -*- coding: utf-8 -*-

"""This module is designed for servicesTerms's show.
"""

import tornado.web
from base import BaseHandler

class ServicesTermsHandler(BaseHandler):
    
    @tornado.web.removeslash
    def get(self):
        self.render('servicesTerms.html')
