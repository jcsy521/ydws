# -*- coding: utf-8 -*-

import logging
from time import time

import tornado.web
from tornado.escape import json_encode, json_decode

from utils.dotdict import DotDict
from codes.errorcode import ErrorCode
from constants import UWEB

from base import BaseHandler, authenticated

class RealtimeHandler(BaseHandler):
    """Play with realtime location query."""

    @tornado.web.asynchronous
    def post(self):
        """Get a GPS location or cellid location.
        workflow:
        if gps:
            try to get a gps location
        elif cellid:
            get a latest cellid and get a cellid location
        """
        status = ErrorCode.SUCCESS
        self.write(status,
                   dict_=DotDict(res={}))

