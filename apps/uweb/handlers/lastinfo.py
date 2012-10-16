# -*- coding: utf-8 -*-

import logging

import tornado.web
from tornado.escape import json_encode, json_decode

from utils.dotdict import DotDict
from utils.misc import get_terminal_info_key, get_location_key
from codes.errorcode import ErrorCode
from helpers.queryhelper import QueryHelper
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
                # 1: get terminal info 
                terminal_info_key = get_terminal_info_key(tid)
                terminal = self.redis.getvalue(terminal_info_key)
                #self.redis.delete(terminal_info_key)
                if not terminal:
                    terminal = self.db.get("SELECT ti.login, ti.mobile, ti.defend_status, ti.pbat,"
                                           "    ti.gps, ti.gsm, ti.alias, ti.keys_num "
                                           "  FROM T_TERMINAL_INFO as ti "
                                           "  WHERE ti.tid = %s"
                                           "  LIMIT 1",
                                           tid)
                    if not terminal:
                        status = ErrorCode.LOGIN_AGAIN
                        logging.error("The terminal with tid: %s does not exist, redirect to login.html", tid)
                        self.write_ret(status)
                        return

                    foblist = QueryHelper.get_fob_list_by_tid(tid, self.db)
                    terminal['fob_list'] = [fob['fobid'] for fob in foblist] 
                    self.redis.setvalue(terminal_info_key, DotDict(terminal))

                if not terminal['alias']:
                   terminal['alias'] = QueryHelper.get_alias_by_tid(tid, self.redis, self.db) 

                if not terminal['mobile']:
                   terminal['mobile'] = QueryHelper.get_tmobile_by_tid(tid, self.redis, self.db) 


                # 2: get location 
                location_key = get_location_key(str(tid))
                location = self.redis.getvalue(location_key)
                if not location:
                    location = self.db.get("SELECT speed, timestamp, category, name,"
                                           "  degree, type, latitude, longitude, clatitude, clongitude"
                                           "  FROM T_LOCATION"
                                           "  WHERE tid = %s"
                                           "    AND NOT (clatitude = 0 AND clongitude = 0)"
                                           "    ORDER BY timestamp DESC"
                                           "    LIMIT 1",
                                           tid)
                if location and location['name'] is None:
                    location['name'] = ''

                car_dct = {}
                car_info=DotDict(defend_status=terminal['defend_status'] if terminal['defend_status'] is not None else 0,
                                 timestamp=location['timestamp'] if location else 0,
                                 speed=location.speed if location else 0,
                                 # NOTE: degree's type is Decimal, float() it before json_encode
                                 degree=float(location.degree) if location else 0.00,
                                 name=location.name if location else '',
                                 type=location.type if location else 1,
                                 latitude=location['latitude'] if location else 0,
                                 longitude=location['longitude'] if location else 0, 
                                 clatitude=location['clatitude'] if location else 0,
                                 clongitude=location['clongitude'] if location else 0, 
                                 login=terminal['login'] if terminal['login'] is not None else 0,
                                 gps=terminal['gps'] if terminal['gps'] is not None else 0,
                                 gsm=terminal['gsm'] if terminal['gsm'] is not None else 0,
                                 pbat=terminal['pbat'] if terminal['pbat'] is not None else 0,
                                 mobile=terminal['mobile'],
                                 alias=terminal['alias'],
                                 keys_num=terminal['keys_num'] if terminal['keys_num'] is not None else 0,
                                 fob_list=terminal['fob_list'])

                car_dct[tid]=car_info
                cars_info.update(car_dct)
            self.write_ret(status, 
                           dict_=DotDict(cars_info=cars_info))

        except Exception as e:
            logging.exception("[UWEB] uid:%s, tid:%s get lastinfo failed. Exception: %s", e.args) 
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)
