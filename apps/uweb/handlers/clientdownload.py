# -*- coding: utf-8 -*-

import logging

import tornado.web

from base import BaseHandler
from helpers.downloadhelper import get_version_info

class ClientDownloadHandler(BaseHandler):

    @tornado.web.removeslash
    def get(self):
        """Jump to the clientDownload html."""
        category = int(self.get_argument('category', 1))
        if category == 1:  # ydws
            self.render('download_ydws.html')
        elif category == 2: # ydwq
            self.render('download_ydwq.html')
        elif category == 3: # ydws-anjietong 
            self.render('download_anjietong.html')
