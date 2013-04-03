# -*- coding: utf-8 -*-

import logging
import time

import tornado.web
from tornado.escape import json_encode, json_decode

from utils.dotdict import DotDict
from utils.misc import get_terminal_info_key, get_location_key, get_lastinfo_key, get_lastinfo_time_key, DUMMY_IDS
from codes.errorcode import ErrorCode
from helpers.queryhelper import QueryHelper
from constants import UWEB, EVENTER, GATEWAY
from constants.MEMCACHED import ALIVED
from base import BaseHandler, authenticated

       
class LastInfoHandler(BaseHandler):
    """Get the newest information of terminal from redis or database.
    NOTE:It just retrieves data from db, not issue a locate and get info from terminal. 
    """

    @authenticated
    @tornado.web.removeslash
    def post(self):
        try:
            data = DotDict(json_decode(self.request.body))
        except Exception as e:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            self.write_ret(status)
            return 

        try:
            cars_info = {} 
            usable = 0 # nothing is modified, the cars_info is no use, use the data last time
            status = ErrorCode.SUCCESS
            
            terminals = self.db.query("SELECT tid FROM T_TERMINAL_INFO"
                                      "  WHERE service_status = %s"
                                      "    AND owner_mobile = %s"
                                      "    AND group_id = -1",
                                      UWEB.SERVICE_STATUS.ON, self.current_user.uid)
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

                car_dct = {}
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

                car_dct[tid]=car_info
                cars_info.update(car_dct)
            
            lastinfo_key = get_lastinfo_key(self.current_user.uid)
            lastinfo = self.redis.getvalue(lastinfo_key)

            lastinfo_time_key = get_lastinfo_time_key(self.current_user.uid)
            lastinfo_time = self.redis.getvalue(lastinfo_time_key)

            if lastinfo == cars_info:  
                pass
            else:
                lastinfo_time = int(time.time())
                self.redis.setvalue(lastinfo_key, cars_info) 
                self.redis.setvalue(lastinfo_time_key, lastinfo_time)

            track_tid = data.get('track_tid', None)  # use cache
            track_info = []
            query_time = data.get('time', None) 
            
            # 2 check whether provide usable data   
            if data.get('cache', None):  # use cache
                if query_time is not None: # use time
                    if int(query_time) < lastinfo_time:
                        usable = 1
                        if track_tid:
                            if int(query_time) == -1:
                                pass
                            elif lastinfo_time - query_time > 1: # every 30 second, ternimal generate a location 
                                track  = self.db.query("SELECT clatitude, clongitude"
                                                       "  FROM T_LOCATION"
                                                       "  WHERE tid = %s"
                                                       "    AND NOT (latitude = 0 OR longitude = 0)"
                                                       "    AND (timestamp BETWEEN %s AND %s)"
                                                       #"    AND type = 0"
                                                       "    ORDER BY timestamp",
                                                       track_tid, int(query_time)+1, int(lastinfo_time)+1)
                                for item in track:
                                    track_info.append(item['clatitude'])
                                    track_info.append(item['clongitude'])
                    else: 
                        cars_info = {}
                        usable = 0
                else: # no time
                    if lastinfo == cars_info: 
                        cars_info = {}
                        usable = 0
                    else: 
                        usable = 1
            else: 
                usable = 1
            self.write_ret(status, 
                           dict_=DotDict(cars_info=cars_info,
                                         track_info=track_info,
                                         usable=usable,
                                         lastinfo_time=lastinfo_time)) 
        except Exception as e:
            logging.exception("[UWEB] uid: %s, data: %s get lastinfo failed. Exception: %s", 
                              self.current_user.uid, data, e.args) 
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)

class LastInfoCorpHandler(BaseHandler):
    """Get the newest info of terminal from database.
    NOTE:It just retrieves data from db, not get info from terminal. 
    """
    @authenticated
    @tornado.web.removeslash
    def post(self):
        try:
            status = ErrorCode.SUCCESS
            corp = self.db.get("SELECT cid, name, mobile FROM T_CORP WHERE cid = %s", self.current_user.cid)
            if self.current_user.oid == UWEB.DUMMY_OID:
                groups = self.db.query("SELECT id gid, name FROM T_GROUP WHERE corp_id = %s", self.current_user.cid)
            else:
                groups = self.db.query("SELECT group_id FROM T_GROUP_OPERATOR WHERE oper_id = %s", self.current_user.oid)
                gids = [g.group_id for g in groups]
                groups = self.db.query("SELECT id gid, name FROM T_GROUP WHERE id IN %s", tuple(DUMMY_IDS + gids))
            res = DotDict(name=corp.name if corp else '',
                          cid=corp.cid if corp else '',
                          online=0,
                          offline=0,
                          groups=[])
            for group in groups:
                group['cars'] = []
                terminals = self.db.query("SELECT tid FROM T_TERMINAL_INFO"
                                          "  WHERE group_id = %s"
                                          "    AND service_status = %s",
                                          group.gid, UWEB.SERVICE_STATUS.ON)
                tids = [str(terminal.tid) for terminal in terminals]

                for tid in tids:
                    # 1: get terminal info 
                    terminal_info_key = get_terminal_info_key(tid)
                    terminal = self.redis.getvalue(terminal_info_key)
                    if not terminal:
                        terminal = self.db.get("SELECT mannual_status, defend_status,"
                                               "  fob_status, mobile, login, gps, gsm,"
                                               "  pbat, keys_num"
                                               "  FROM T_TERMINAL_INFO"
                                               "  WHERE tid = %s", tid)

                        if not terminal:
                            status = ErrorCode.LOGIN_AGAIN
                            logging.error("The terminal with tid: %s does not exist, redirect to login.html", tid)
                            self.write_ret(status)
                            return

                        car = self.db.get("SELECT cnum FROM T_CAR"
                                          "  WHERE tid = %s", tid)

                        fobs = self.db.query("SELECT fobid FROM T_FOB"
                                             "  WHERE tid = %s", tid)
                        terminal = DotDict(terminal)
                        terminal['alias'] = car.cnum if car.cnum else terminal.mobile
                        terminal['fob_list'] = [fob.fobid for fob in fobs]

                        self.redis.setvalue(terminal_info_key, DotDict(terminal))
                    if terminal['login'] == GATEWAY.TERMINAL_LOGIN.SLEEP:
                        terminal['login'] = GATEWAY.TERMINAL_LOGIN.ONLINE

                    if terminal['login'] == GATEWAY.TERMINAL_LOGIN.ONLINE:
                        res['online'] +=1
                    else:
                        res['offline'] +=1

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

                    car_info=DotDict(tid=tid,
                                     defend_status=terminal['defend_status'] if terminal['defend_status'] is not None else 1,
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
                    group['cars'].append(car_info)
                res.groups.append(group)
            self.write_ret(status, 
                           dict_=DotDict(res=res))
        except Exception as e:
            logging.exception("[UWEB] cid: %s get corp lastinfo failed. Exception: %s", 
                              self.current_user.cid, e.args) 
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)
