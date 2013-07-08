# -*- coding: utf-8 -*-

import os.path
import pysvn

import tornado.web

from base import BaseHandler

class AboutHandler(BaseHandler):

    @tornado.web.removeslash
    def get(self):
        client = pysvn.Client()
        svn_path = os.path.abspath(os.path.join(self.application.settings['server_path'], '../../'))
        #entry = client.info('/home/w_lhs/acb/trunk')
        entry = client.info(svn_path)
        self.render('about.html',
                    version = entry.commit_revision.number)
