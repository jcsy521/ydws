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

class MainHandler(BaseHandler):

    # BIG NOTE: never add removeslash decorator here!
    @authenticated
    def get(self):
        self.write("It works!")
        