# -*- coding: utf-8 -*-

import logging
import time

import tornado.web
from tornado.escape import json_encode, json_decode

from utils.dotdict import DotDict
from helpers.downloadhelper import get_version_info,\
     get_download_count, update_download_count
from helpers.queryhelper import QueryHelper
from constants import DOWNLOAD, UWEB
from codes.errorcode import ErrorCode
from base import BaseHandler

class WebInsHandler(BaseHandler):

    @tornado.web.removeslash
    def get(self):
        """Jump to web.html."""
        self.render('web.html')

class AndroidInsHandler(BaseHandler):

    @tornado.web.removeslash
    def get(self):
        """Jump to android.html."""
        category = self.get_argument('category', '2')
        #version_info = get_version_info('android')
        version_info = QueryHelper.get_version_info_by_category(UWEB.APK_TYPE.YDWS, self.db)
        download_info = get_download_count(category, self.db)

        self.render('android.html',
                    versioncode=version_info.versioncode,
                    versionname=version_info.versionname,
                    versioninfo=version_info.versioninfo,
                    updatetime=version_info.updatetime,
                    filesize=version_info.filesize,
                    count=download_info.count if download_info else 0)

class IOSInsHandler(BaseHandler):

    @tornado.web.removeslash
    def get(self):
        """Jump to ios.html."""
        self.render('ios.html')

class SMSInsHandler(BaseHandler):

    @tornado.web.removeslash
    def get(self):
        """Jump to sms.html."""
        self.render('sms.html')

class ManualInsHandler(BaseHandler):

    @tornado.web.removeslash
    def get(self):
        """Jump to manual.html."""
        self.render('manual.html')
