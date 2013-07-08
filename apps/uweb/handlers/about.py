# -*- coding: utf-8 -*-

import pysvn
import os.path

import tornado.web

from base import BaseHandler

class AboutHandler(BaseHandler):

    @tornado.web.removeslash
    def get(self):
        client = pysvn.Client()
        svn_path = os.path.split(os.path.split(os.getcwd())[0])[0]
        #entry = client.info('/home/w_lhs/acb/trunk')
        entry = client.info(svn_path)
        self.render('about.html',
                    version = entry.commit_revision.number)