# -*- coding: utf-8 -*-

import logging

import tornado.web
from tornado.escape import json_encode, json_decode

from utils.misc import DUMMY_IDS
from utils.dotdict import DotDict
from codes.errorcode import ErrorCode
from constants import UWEB, SMS
from base import BaseHandler, authenticated

       
class SwitchCarHandler(BaseHandler):
    """Switch current car for the current user.
    """
    @authenticated
    @tornado.web.removeslash
    def get(self, tid):
        try:
            monitor = self.db.get("SELECT ti.tid, ti.mobile as sim,"
                                  "  ti.login, ti.defend_status "
                                  "  FROM T_TERMINAL_INFO as ti "
                                  "  WHERE ti.tid = %s"
                                  "  LIMIT 1",
                                  tid)
            if monitor: 
#                location = self.db.get("SELECT speed, timestamp, category, name"
#                                       "  FROM T_LOCATION"
#                                       "  WHERE tid = %s"
#                                       "    ORDER BY timestamp DESC"
#                                       "    LIMIT 1",
#                                       monitor.tid)
                self.bookkeep(dict(uid=self.current_user.uid,
                                   tid=tid,
                                   sim=monitor.sim))
                status = ErrorCode.SUCCESS
                # NOTE: if there is no records in T_LOCATION, when the car
                # has never got location, just return None
                self.write_ret(status) 
#                self.write_ret(status, 
#                    dict_=DotDict(car_info=DotDict(tid=monitor.tid,
#                                                   defend_status=monitor.defend_status,
#                                                   timestamp=location.timestamp if location else None,
#                                                   speed=location.speed if location else 0,
#                                                   event_status=location.category if location else 0,
#                                                   address=location.name if location else None,
#                                                   login=monitor.login,
#                                                   lock_status=monitor.lock_status)))
            else:
                status = ErrorCode.NO_TERMINAL
                self.write_ret(status) 
        except Exception as e:
            logging.exception("Switchcar failded. Exception: %s", e.args) 
            status = ErrorCode.SERVER_ERROR        
            self.write_ret(status)
