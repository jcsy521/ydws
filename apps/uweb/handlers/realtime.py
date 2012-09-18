# -*- coding: utf-8 -*-

import logging
from time import time

import tornado.web
from tornado.escape import json_encode, json_decode

from utils.dotdict import DotDict
from codes.errorcode import ErrorCode
from constants import UWEB
from base import BaseHandler, authenticated
from mixin.realtime import RealtimeMixin


class RealtimeHandler(BaseHandler, RealtimeMixin):
    """Play with realtime location query."""

    @authenticated
    @tornado.web.removeslash
    @tornado.web.asynchronous
    def get(self):

        current_query = DotDict() 
        current_query.timestamp = int(time())
        terminal = self.db.get("SELECT cellid_status FROM T_TERMINAL_INFO WHERE tid = %s", self.current_user.tid)

        if not terminal:
            status = ErrorCode.LOGIN_AGAIN
            logging.error("The terminal with tid: %s is noexist, redirect to login.html", self.current_user.tid)
            self.write_ret(status)
            self.finish()
            return

        if terminal.cellid_status == UWEB.CELLID_STATUS.ON:
            current_query.cellid_status = True 
        else: 
            current_query.cellid_status = False 

        logging.debug("Realtime query: %s", current_query)
        
        def _on_finish(realtime):
            self.set_header(*self.JSON_HEADER)
            self.write(json_encode(realtime))
            self.finish()
            
        self.request_realtime(current_query,
                              callback=_on_finish)
