# -*- coding: utf-8 -*-

"""This module is designed for ZNBC.

#NOTE：deprecated.
"""

import logging

import tornado.web

from utils.dotdict import DotDict
from utils.misc import get_terminal_info_key, get_location_key
from codes.errorcode import ErrorCode
from helpers.queryhelper import QueryHelper
from constants import EVENTER, GATEWAY
from base import BaseHandler

      
class MAPHandler(BaseHandler):
    """Get the newest information of the line's terminal from redis or database.
    NOTE:It just retrieves data from db, not issue a location and get info from terminals of the line. 
    """

    @tornado.web.removeslash
    def post(self):
        try:
            line_id = int(self.get_argument('line_id'))
            logging.info("[CLIENT] map request line_id : %s", 
                         line_id)
        except Exception as e:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            self.write_ret(status)
            return 

        try:
            cars_info = []
            status = ErrorCode.SUCCESS
            
            terminals = self.db.query("SELECT tid "
                                     "  FROM T_CAR_LINE, T_LINE_PASSENGER"
                                     "  WHERE T_CAR_LINE.line_id = T_LINE_PASSENGER.line_id"
                                     "  AND T_CAR_LINE.line_id = %s",
                                     line_id)
            tids = [terminal.tid for terminal in terminals]

            # 1 inquery data     
            for tid in tids:
                # 1: get terminal info 
                terminal_info_key = get_terminal_info_key(tid)
                terminal = self.redis.getvalue(terminal_info_key)
                if not terminal:
                    terminal = self.db.get("SELECT mannual_status, defend_status,"
                                           "  fob_status, mobile, login, gps, gsm,"
                                           "  pbat, keys_num"
                                           "  FROM T_TERMINAL_INFO"
                                           "  WHERE tid = %s",
                                           tid)

                    terminal = DotDict(terminal)
                    terminal['alias'] = QueryHelper.get_alias_by_tid(tid, self.redis, self.db)
                    fobs = self.db.query("SELECT fobid FROM T_FOB"
                                         "  WHERE tid = %s", tid)
                    terminal['fob_list'] = [fob.fobid for fob in fobs]

                    self.redis.setvalue(terminal_info_key, DotDict(terminal))

                if terminal['login'] == GATEWAY.TERMINAL_LOGIN.SLEEP:
                    terminal['login'] = GATEWAY.TERMINAL_LOGIN.ONLINE

                # 2: get location 
                location_key = get_location_key(str(tid))
                location = self.redis.getvalue(location_key)
                if not location:
                    location = self.db.get("SELECT id, speed, timestamp, category, name,"
                                           "  degree, type, latitude, longitude, clatitude, clongitude, timestamp"
                                           "  FROM T_LOCATION"
                                           "  WHERE tid = %s"
                                           "    AND NOT (clatitude = 0 AND clongitude = 0)"
                                           "    ORDER BY timestamp DESC"
                                           "    LIMIT 1",
                                           tid)
                    if location:
                        mem_location = DotDict({'id':location.id,
                                                'latitude':location.latitude,
                                                'longitude':location.longitude,
                                                'type':location.type,
                                                'clatitude':location.clatitude,
                                                'clongitude':location.clongitude,
                                                'timestamp':location.timestamp,
                                                'name':location.name,
                                                'degree':float(location.degree),
                                                'speed':float(location.speed)})

                        self.redis.setvalue(location_key, mem_location, EVENTER.LOCATION_EXPIRY)

                if location and location['name'] is None:
                    location['name'] = ''

                car_info=dict(defend_status=terminal['defend_status'] if terminal['defend_status'] is not None else 1,
                              mannual_status=terminal['mannual_status'] if terminal['mannual_status'] is not None else 1,
                              fob_status=terminal['fob_status'] if terminal['fob_status'] is not None else 0,
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
                              #keys_num=terminal['keys_num'] if terminal['keys_num'] is not None else 0,
                              keys_num=0,
                              fob_list=terminal['fob_list'] if terminal['fob_list'] else [])

                cars_info.append(car_info)
                
            self.write_ret(status, 
                           dict_=DotDict(cars_info=cars_info))
        except Exception as e:
            logging.exception("[CLIENT] map show tids lastinfo failed, line_id : %s. Exception: %s", 
                              line_id, e.args) 
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)
