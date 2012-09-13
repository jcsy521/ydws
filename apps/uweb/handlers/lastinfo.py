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
    NOTE:It just retrieves data from db, not get info from terminal. 
    """
    @authenticated
    @tornado.web.removeslash
    def post(self):
        try:
            data = DotDict(json_decode(self.request.body))
        except:
            self.write_ret(ErrorCode.ILLEGAL_DATA_FORMAT) 
            return

        try:
            cars_info = DotDict() 
            status = ErrorCode.SUCCESS
            for tid in data.tids:
                # NOTE: monitor and location must not be null. lastinfo is invoked after switchcar
                terminal = self.db.get("SELECT ti.tid, ti.mobile as sim, ti.login,"
                                       "  ti.defend_status, ti.pbat, ti.gps, ti.gsm, ti.alias, ti.keys_num "
                                       "  FROM T_TERMINAL_INFO as ti "
                                       "  WHERE ti.tid = %s"
                                       "  LIMIT 1",
                                       tid)
                if not terminal:
                    status = ErrorCode.LOGIN_AGAIN
                    logging.error("The terminal with tid: %s is noexist, redirect to login.html", tid)
                    self.write_ret(status)
                    return
                location = self.db.get("SELECT speed, timestamp, category, name,"
                                       "  degree, type, latitude, longitude, clatitude, clongitude"
                                       "  FROM T_LOCATION"
                                       "  WHERE tid = %s"
                                       "    AND NOT (clatitude = 0 AND clongitude = 0)"
                                       "    ORDER BY timestamp DESC"
                                       "    LIMIT 1",
                                       tid)
                # NOTE: if there is no records in T_LOCATION, when the car
                # has never got location, just return None
                #event_status = self.get_event_status(tid)
                car_dct = {}
                car_info=DotDict(defend_status=terminal.defend_status,
                                 timestamp=location.timestamp if location else 0,
                                 speed=location.speed if location else 0,
                                 # NOTE: degree's type is Decimal, str() it before json_encode
                                 degree=float(location.degree) if location else 0.00,
                                 name='',
                                 #name=location.name if location else '',
                                 type=location.type if location else 1,
                                 latitude=location.latitude if location else 0,
                                 longitude=location.longitude if location else 0, 
                                 clatitude=location.clatitude if location else 0,
                                 clongitude=location.clongitude if location else 0, 
                                 login=terminal.login,
                                 gps=terminal.gps,
                                 gsm=terminal.gsm,
                                 pbat=terminal.pbat,
                                 mobile=terminal.sim,
                                 alias=terminal.alias if terminal.alias else terminal.sim,
                                 keys_num=terminal.keys_num)

                car_dct[tid]=car_info
                cars_info.update(car_dct)

            self.write_ret(status, 
                           dict_=DotDict(cars_info=cars_info))

        except Exception as e:
            logging.exception("[UWEB] get lastinfo failed. Exception: %s", e.args) 
            status = ErrorCode.SERVER_ERROR        
            self.write_ret(status)

    #def get_event_status(self, tid):
    #    alarm_key = get_alarm_status_key(tid)
    #    event_status = self.redis.getvalue(alarm_key)
    #    is_alived = self.redis.getvalue("is_alived")
    #    if is_alived != ALIVED:
    #        location = self.db.get("SELECT category"
    #                               "  FROM T_LOCATION"
    #                               "  WHERE tid = %s"
    #                               "    ORDER BY timestamp DESC"
    #                               "    LIMIT 1",
    #                               tid)
    #        event_status = location.category if location else 0

    #    return event_status
