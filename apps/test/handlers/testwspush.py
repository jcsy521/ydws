# -*- coding: utf-8 -*-

"""This module is designed for main page.
"""

import time
import logging

from tornado.escape import json_encode

from base import BaseHandler, authenticated
from helpers.queryhelper import QueryHelper
from helpers.confhelper import ConfHelper
from helpers.wspushhelper import WSPushHelper
from constants import UWEB, GATEWAY
from codes.errorcode import ErrorCode
from utils.dotdict import DotDict
from utils.public import get_push_key

class TestWSpushHandler(BaseHandler):


    def get(self):
        logging.info("[TEST] Test wspush.")
        ## tmeplate_file
        self.render("test_wspush.html")
