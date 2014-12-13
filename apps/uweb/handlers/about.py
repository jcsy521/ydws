# -*- coding: utf-8 -*-

"""This module is designed for about-information.
"""

import os.path
import pysvn

import tornado.web

from base import BaseHandler

class AboutHandler(BaseHandler):

    @tornado.web.removeslash
    def get(self):
        client = pysvn.Client()
        #NOTE: svn_path = /path/to/trunk
        svn_path = os.path.abspath(os.path.join(self.application.settings['server_path'], '../../'))
        entry = client.info(svn_path)
        self.render('about.html',
                    version = entry.commit_revision.number)
