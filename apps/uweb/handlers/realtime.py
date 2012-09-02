# -*- coding: utf-8 -*-

import logging
from time import time

import tornado.web
from tornado.escape import json_encode, json_decode

from utils.dotdict import DotDict
from codes.errorcode import ErrorCode
from base import BaseHandler, authenticated
from mixin.realtime import RealtimeMixin


class RealtimeHandler(BaseHandler, RealtimeMixin):
    """Play with realtime location query."""

    @authenticated
    @tornado.web.removeslash
    @tornado.web.asynchronous
    def post(self):
        try: 
            current_query = DotDict(json_decode(self.request.body)) 
        except:
            self.write_ret(ErrorCode.ILLEGAL_DATA_FORMAT) 
            self.finish()
            return

        current_query.timestamp = int(time())
        terminal = self.db.get("SELECT cellid_status FROM T_TERMINAL_INFO WHERE tid = %s", self.current_user.tid)

        if not terminal:
            status = ErrorCode.LOGIN_AGAIN
            logging.error("The terminal with tid: %s is noexist, redirect to login.html", self.current_user.tid)
            self.clear_cookie(self.app_name)
            self.write_ret(status)
            self.finish()
            return
        current_query.cellid_status = terminal.cellid_status 

        logging.debug("Realtime query: %s", current_query)
        
        def _on_finish(realtime):
            self.set_header(*self.JSON_HEADER)
            self.write(json_encode(realtime))
            self.finish()
            
        self.request_realtime(current_query,
                              callback=_on_finish)
