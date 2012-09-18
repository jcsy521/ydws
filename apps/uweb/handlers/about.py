# -*- coding: utf-8 -*-

import tornado.web

from base import BaseHandler

class AboutHandler(BaseHandler):
    """Show some info for ACB.
    """

    @tornado.web.removeslash
    def get(self):
        """Jump to about.html."""
        self.render('about.html')

