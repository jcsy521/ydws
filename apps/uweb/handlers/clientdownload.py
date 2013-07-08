# -*- coding: utf-8 -*-

import logging

import tornado.web

from base import BaseHandler
from helpers.downloadhelper import get_version_info

class ClientDownloadHandler(BaseHandler):

    @tornado.web.removeslash
    def get(self):
        """Jump to the clientDownload.html."""
        version_info = get_version_info('android')
        versionname = version_info.versionname
        self.render('clientDownload.html', versionname=versionname)

