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
    def get(self):
        """Get the latest usagle.
        """
        try: 
            tid = self.get_argument('tid',None) 
            # check tid whether exist in request and update current_user
            self.check_tid(tid)
            
            terminal = self.db.get("SELECT id FROM T_TERMINAL_INFO"
                                   "  WHERE tid = %s"
                                   "    AND service_status = %s",
                                   self.current_user.tid,
                                   UWEB.SERVICE_STATUS.ON)
            if not terminal:
                status = ErrorCode.LOGIN_AGAIN
                logging.error("The terminal with tid: %s is noexist, redirect to login.html", self.current_user.tid)
                self.write_ret(status)
                self.finish()
                return

            ret = self.get_realtime(self.current_user.uid, 
                                    self.current_user.sim)
            self.set_header(*self.JSON_HEADER)
            self.write(json_encode(ret))
        except Exception as e:
            logging.exception("Failed to get location: %s, Sim: %s", 
                               e.args, self.current_user.sim) 
            status = ErrorCode.SERVER_BUSY  
            self.write_ret(status)

    @authenticated
    @tornado.web.removeslash
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
        try:
            data = DotDict(json_decode(self.request.body))
            tid = data.get('tid',None) 
            # check tid whether exist in request and update current_user
            self.check_tid(tid, finish=True)
            logging.info("[UWEB] realtime request: %s, uid: %s, tid: %s", 
                         data, self.current_user.uid, self.current_user.tid)
        except Exception as e:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            self.write_ret(status)
            self.finish()
            return 

        current_query = DotDict() 
        current_query.timestamp = int(time())

        terminal = self.db.get("SELECT id FROM T_TERMINAL_INFO"
                               "  WHERE tid = %s"
                               "    AND service_status = %s",
                               self.current_user.tid,
                               UWEB.SERVICE_STATUS.ON)
        if not terminal:
            status = ErrorCode.LOGIN_AGAIN
            logging.error("The terminal with tid: %s does not exist, redirect to login.html", self.current_user.tid)
            self.write_ret(status)
            self.finish()
            return

        current_query.locate_flag = data.locate_flag
        
        def _on_finish(realtime):
            realtime['cellid_status'] = 1 
            self.set_header(*self.JSON_HEADER)
            self.write(json_encode(realtime))
            self.finish()

        def __callback(db):
            self.db = db
            self.request_realtime(current_query,
                                  callback=_on_finish)
            self.keep_waking(self.current_user.sim, self.current_user.tid)

        self.queue.put((10, __callback))

