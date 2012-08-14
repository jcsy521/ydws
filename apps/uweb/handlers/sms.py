# -*- coding: utf-8 -*-

import logging

import tornado.web
from tornado.escape import json_encode

from helpers.smshelper import SMSHelper
from constants import UWEB

from utils.dotdict import DotDict
from base import BaseHandler
from codes.errorcode import ErrorCode
#from smscallback import process


class SMSHandler(BaseHandler):
    """Handle parent's sms instructions.

    We accept the following instructions:
    o SSDW cmobile
    o DSDW HHMM cmobile
    o YCHB cmobile
    o YCKJ cmobile
    o YCGJ cmobile

    ps: `cmobile` means `child mobile`.
    """

    @tornado.web.removeslash
    def post(self):
        pmobile = self.get_argument("mobile") # parent's mobile
        packet = self.get_argument("content") # sms content
        def _on_finish(db):
            pass
            #self.db = db
            #response = process(pmobile, packet, self.db, self.redis)
            #if response:
            #    SMSHelper.send(pmobile, response)

        self.queue.put((UWEB.PRIORITY.SMS, _on_finish))
        self.set_header("Content-type", "text/plain")
        self.write(str(ErrorCode.SUCCESS))
