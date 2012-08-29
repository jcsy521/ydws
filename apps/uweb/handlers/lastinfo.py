# -*- coding: utf-8 -*-

import logging

import tornado.web
from tornado.escape import json_encode, json_decode

from utils.dotdict import DotDict
from utils.misc import get_alarm_status_key
from codes.errorcode import ErrorCode
from constants import UWEB
from constants.MEMCACHED import ALIVED
from base import BaseHandler, authenticated

       
class LastInfoHandler(BaseHandler):
    """Get the newest info of terminal, from database.
    """

    # maybe, get method is unused.
    @authenticated
    @tornado.web.removeslash
    def get(self, tid):
        try:
            status = ErrorCode.SUCCESS
            # NOTE: monitor and location must not be null. lastinfo is invoked after switchcar
            terminal = self.db.get("SELECT ti.tid, ti.mobile as sim, ti.login,"
                                   "  ti.defend_status, ti.pbat, ti.gps, ti.gsm, ti.alias "
                                   "  FROM T_TERMINAL_INFO as ti "
                                   "  WHERE ti.tid = %s"
                                   "  LIMIT 1",
                                   tid)

            location = self.db.get("SELECT speed, timestamp, category, name,"
                                   "  degree, type, clatitude, clongitude"
                                   "  FROM T_LOCATION"
                                   "  WHERE tid = %s"
                                   "    AND NOT (clatitude = 0 AND clongitude = 0)"
                                   "    ORDER BY timestamp DESC"
                                   "    LIMIT 1",
                                   tid)
            # NOTE: if there is no records in T_LOCATION, when the car
            # has never got location, just return None
            event_status = self.get_event_status(tid)
            self.write_ret(status, 
                 dict_=DotDict(car_info=DotDict(tid=terminal.tid,
                                                defend_status=terminal.defend_status,
                                                timestamp=location.timestamp if location else -1,
                                                speed=location.speed if location else 0,
                                                # NOTE: degree's type is Decimal, str() it before json_encode
                                                #degree=int(round(location.degree/36)) if location else 0,
                                                degree=float(location.degree) if location else 0.00,
                                                event_status=event_status if event_status else 0,
                                                name=location.name if location else '',
                                                type=location.type if location else 1,
                                                clatitude=location.clatitude if location else 0,
                                                clongitude=location.clongitude if location else 0, 
                                                pbat=terminal.pbat,
                                                gps=terminal.gps,
                                                gsm=terminal.gsm,
                                                alias=terminal.alias if terminal.alias else terminal.sim,
                                                login=terminal.login)))
        except Exception as e:
            logging.exception("[UWEB] get lastinfo failed. Exception: %s", e.args) 
            status = ErrorCode.SERVER_ERROR        
            self.write_ret(status)

    @authenticated
    @tornado.web.removeslash
    def post(self):
        data = DotDict(json_decode(self.request.body))
        tids = data.tids
        cars_info = []
        try:
            status = ErrorCode.SUCCESS
            for tid in tids:
                # NOTE: monitor and location must not be null. lastinfo is invoked after switchcar
                terminal = self.db.get("SELECT ti.tid, ti.mobile as sim, ti.login,"
                                       "  ti.defend_status, ti.pbat, ti.gps, ti.gsm, ti.alias "
                                       "  FROM T_TERMINAL_INFO as ti "
                                       "  WHERE ti.tid = %s"
                                       "  LIMIT 1",
                                       tid)

                if not terminal:
                    logging.error("The terminal with tid: %s is noexist, redirect to login.html", tid)
                    self.clear_cookie(self.app_name)
                    self.redirect(self.get_argument("next", "/"))
                    return

                location = self.db.get("SELECT speed, timestamp, category, name,"
                                       "  degree, type, clatitude, clongitude"
                                       "  FROM T_LOCATION"
                                       "  WHERE tid = %s"
                                       "    AND NOT (clatitude = 0 AND clongitude = 0)"
                                       "    ORDER BY timestamp DESC"
                                       "    LIMIT 1",
                                       tid)
                # NOTE: if there is no records in T_LOCATION, when the car
                # has never got location, just return None
                event_status = self.get_event_status(tid)
                car_info=DotDict(tid=terminal.tid,
                                 defend_status=terminal.defend_status,
                                 timestamp=location.timestamp if location else None,
                                 speed=location.speed if location else 0,
                                 # NOTE: degree's type is Decimal, str() it before json_encode
                                 #degree=int(round(location.degree/36)) if location else 0,
                                 degree=float(location.degree) if location else 0.00,
                                 event_status=event_status if event_status else 0,
                                 name=location.name if location else None,
                                 type=location.type if location else 1,
                                 clatitude=location.clatitude if location else 0,
                                 clongitude=location.clongitude if location else 0, 
                                 pbat=terminal.pbat,
                                 gps=terminal.gps,
                                 gsm=terminal.gsm,
                                 alias=terminal.alias if terminal.alias else terminal.sim,
                                 login=terminal.login)

                cars_info.append(car_info)

            self.write_ret(status, 
                           dict_=DotDict(cars_info=cars_info))

        except Exception as e:
            logging.exception("[UWEB] get lastinfo failed. Exception: %s", e.args) 
            status = ErrorCode.SERVER_ERROR        
            self.write_ret(status)

    def get_event_status(self, tid):
        alarm_key = get_alarm_status_key(tid)
        event_status = self.redis.getvalue(alarm_key)
        is_alived = self.redis.getvalue("is_alived")
        if is_alived != ALIVED:
            location = self.db.get("SELECT category"
                                   "  FROM T_LOCATION"
                                   "  WHERE tid = %s"
                                   "    ORDER BY timestamp DESC"
                                   "    LIMIT 1",
                                   tid)
            event_status = location.category if location else 0

        return event_status
