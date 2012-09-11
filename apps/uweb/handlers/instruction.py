# -*- coding: utf-8 -*-

import logging
import time

import tornado.web
from tornado.escape import json_encode, json_decode

from utils.dotdict import DotDict
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
        self.render('android.html')

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
