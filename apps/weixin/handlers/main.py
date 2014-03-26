# -*- coding: utf-8 -*-

import time
import logging

from tornado.escape import json_encode

from base import BaseHandler

class MainHandler(BaseHandler):

    def get(self):
        self.write('It works!')
