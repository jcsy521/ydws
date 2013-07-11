# -*- coding: utf-8 -*-

import logging
import time

import tornado.web
from tornado.escape import json_encode, json_decode

from utils.dotdict import DotDict
from utils.ordereddict import OrderedDict
from utils.misc import get_terminal_info_key, get_alarm_info_key, get_location_key,\
     get_lastinfo_key, get_lastinfo_time_key, DUMMY_IDS
from codes.errorcode import ErrorCode
from helpers.queryhelper import QueryHelper
from helpers.lbmphelper import get_clocation_from_ge, get_locations_with_clatlon
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
            logging.info("[UWEB] lastfinfo failed, message: %s, request: \n%s", 
                         ErrorCode.ERROR_MESSAGE[status], self.request.body)
            self.write_ret(status)
            return 

        try:
            cars_info = OrderedDict() 
            usable = 0 # nothing is modified, the cars_info is no use, use the data last time
            status = ErrorCode.SUCCESS
            
            terminals = self.db.query("SELECT tid FROM T_TERMINAL_INFO"
                                      "  WHERE service_status = %s"
                                      "    AND owner_mobile = %s"
                                      "    AND group_id = -1"
                                      "    ORDER BY LOGIN DESC",
                                      UWEB.SERVICE_STATUS.ON, self.current_user.uid)
            tids = [terminal.tid for terminal in terminals]

            # 1 inquery data     
            for tid in tids:
                # 1: get terminal info 
                terminal = QueryHelper.get_terminal_info(tid, self.db, self.redis) 
                if terminal['login'] == GATEWAY.TERMINAL_LOGIN.SLEEP:
                    terminal['login'] = GATEWAY.TERMINAL_LOGIN.ONLINE

                # 2: get location 
                location = QueryHelper.get_location_info(tid, self.db, self.redis)
                if location and not (location.clatitude or location.clongitude):
                    location_key = get_location_key(str(tid))
                    locations = [location,] 
                    locations = get_locations_with_clatlon(locations, self.db) 
                    location = locations[0]
                    self.redis.setvalue(location_key, location, EVENTER.LOCATION_EXPIRY)

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

            # BIG NOTE: here, compare lastinfo and cars_info as str
            lastinfo = self.redis.get(lastinfo_key)

            lastinfo_time_key = get_lastinfo_time_key(self.current_user.uid)
            lastinfo_time = self.redis.getvalue(lastinfo_time_key)

            if lastinfo == str(cars_info):  
                pass
            else:
                lastinfo_time = int(time.time())
                self.redis.setvalue(lastinfo_key, cars_info) 
                self.redis.setvalue(lastinfo_time_key, lastinfo_time)

            track_tid = data.get('track_tid', None)  # use cache
            track_info = []
            query_time = data.get('time', None) 
            track_time = data.get('track_time', query_time) 
            
            # 2 check whether provide usable data   
            if data.get('cache', None):  # use cache
                if query_time is not None: # use time
                    if int(query_time) < lastinfo_time:
                        usable = 1
                        if track_tid:
                            if int(query_time) == -1:
                                pass
                            elif lastinfo_time - query_time > 1: # every 30 second, ternimal generate a location 
                                endtime = int(car_info['timestamp'])-1 if location else int(lastinfo_time)-1 
                                track  = self.db.query("SELECT id, latitude, longitude," 
                                                       "    clatitude, clongitude"
                                                       "  FROM T_LOCATION"
                                                       "  WHERE tid = %s"
                                                       "    AND NOT (latitude = 0 OR longitude = 0)"
                                                       "    AND (timestamp BETWEEN %s AND %s)"
                                                       "    AND type = 0"
                                                       "    ORDER BY timestamp",
                                                       track_tid, int(track_time)+1, endtime)
                                track = get_locations_with_clatlon(track, self.db)
                                for item in track:
                                    if item['clatitude'] and item['clongitude']:
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
            data = DotDict(json_decode(self.request.body))
            track_lst = data.get('track_list', None)
            current_time = int(time.time()) 
            lastinfo_time = data.get('lastinfo_time') 
            #NOTE: first time, lastinfo_time = -1, set the lsstinfo_time as current_time 
            if lastinfo_time == -1:
                lastinfo_time = current_time 
        except Exception as e:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            logging.info("[UWEB] lastfinfo for corp failed, message: %s, Exception: %s, request: \n%s", 
                         ErrorCode.ERROR_MESSAGE[status], e.args, self.request.body)
            self.write_ret(status)
            return 

        try:
            status = ErrorCode.SUCCESS
            corp = self.db.get("SELECT cid, name, mobile FROM T_CORP WHERE cid = %s", self.current_user.cid)
            if self.current_user.oid == UWEB.DUMMY_OID:
                groups = self.db.query("SELECT id gid, name FROM T_GROUP WHERE corp_id = %s", self.current_user.cid)
            else:
                groups = self.db.query("SELECT group_id FROM T_GROUP_OPERATOR WHERE oper_id = %s", self.current_user.oid)
                gids = [g.group_id for g in groups]
                groups = self.db.query("SELECT id gid, name FROM T_GROUP WHERE id IN %s", tuple(DUMMY_IDS + gids))
 
            track_tids = []
            if track_lst:
                track_tids = [track['track_tid'] for track in track_lst]

            res = DotDict(name=corp.name if corp else '',
                          cid=corp.cid if corp else '',
                          online=0,
                          offline=0,
                          groups=[],
                          lastinfo_time=current_time)
            for group in groups:
                group['trackers'] = {} 
                terminals = self.db.query("SELECT tid FROM T_TERMINAL_INFO"
                                          "  WHERE group_id = %s"
                                          "    AND service_status = %s",
                                          group.gid, UWEB.SERVICE_STATUS.ON)
                tids = [str(terminal.tid) for terminal in terminals]

                for tid in tids:
                    group['trackers'][tid] = {} 
                    # 1: get terminal info 
                    terminal = QueryHelper.get_terminal_info(tid, self.db, self.redis) 
                    if terminal['login'] == GATEWAY.TERMINAL_LOGIN.SLEEP:
                        terminal['login'] = GATEWAY.TERMINAL_LOGIN.ONLINE

                    if terminal['login'] == GATEWAY.TERMINAL_LOGIN.ONLINE:
                        res['online'] +=1
                    else:
                        res['offline'] +=1

                    # 2: get location 
                    location = QueryHelper.get_location_info(tid, self.db, self.redis)
                    if location and not (location.clatitude or location.clongitude):
                        location_key = get_location_key(str(tid))
                        locations = [location,] 
                        locations = get_locations_with_clatlon(locations, self.db) 
                        location = locations[0]
                        self.redis.setvalue(location_key, location, EVENTER.LOCATION_EXPIRY)

                    if location and location['name'] is None:
                        location['name'] = ''

                    #1: build the basic_info
                    basic_info=dict(defend_status=terminal['defend_status'] if terminal['defend_status'] is not None else 1,
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
                                    icon_type=terminal['icon_type'] if terminal.get('icon_type', None) is not None else 0,
                                    fob_list=terminal['fob_list'] if terminal['fob_list'] else [])

                    #2: build track_info
                    track_info = []
                    if tid in track_tids:
                        endtime = int(basic_info['timestamp'])-1 if location else int(current_time)-1
                        points_track = self.db.query("SELECT id, latitude, longitude," 
                                                     "   clatitude, clongitude, type, timestamp"
                                                     "  FROM T_LOCATION"
                                                     "  WHERE tid = %s"
                                                     "    AND NOT (latitude = 0 OR longitude = 0)"
                                                     "    AND (timestamp BETWEEN %s AND %s)"
                                                     "    AND type = 0"
                                                     "    ORDER BY timestamp",
                                                     tid,
                                                     int(track_lst[tid]['track_time'])+1, endtime)

                        points_track = get_locations_with_clatlon(points_track, self.db)
                        for point in points_track: 
                            if point['clatitude'] and point['clongitude']:
                                t = dict(latitude=point['latitude'],
                                         longitude=point['longitude'],
                                         clatitude=point['clatitude'],
                                         clongitude=point['clongitude'],
                                         type=point['type'],
                                         timestamp=point['timestamp'])
                                track_info.append(t)

                    #3: build trace_info
                    trace_info = []
                    points_trace = self.db.query("SELECT distinct id, latitude, longitude," 
                                                 "    clatitude, clongitude"
                                                 "  FROM T_LOCATION"
                                                 "  WHERE tid = %s"
                                                 "    AND NOT (latitude = 0 OR longitude = 0)"
                                                 "    AND (timestamp  between %s and %s)"
                                                 "    AND type = 0"
                                                 "    ORDER BY timestamp",
                                                 tid, int(current_time)-60*5, int(current_time))

                    points_trace = get_locations_with_clatlon(points_trace, self.db)
                    len_trace = 0
                    if points_trace:
                        for point in points_trace:
                            if len_trace >= 5:
                                break
                            if point['clatitude'] and point['clongitude']:
                                trace_info.append(point['clatitude'])
                                trace_info.append(point['clongitude'])
                                len_trace += 1
                            else:
                                continue

                    #4: build alert_info
                    alarm_info_key = get_alarm_info_key(tid)
                    alarm_info_all = self.redis.getvalue(alarm_info_key)
                    alarm_info_all  = alarm_info_all if alarm_info_all else []
                    alarm_info = []
                    
                    if alarm_info_all:
                        for alarm in alarm_info_all:
                            #NOTE: here, check alarm's keeptime when kept in reids, not timestamp alarm occurs
                            if alarm.get('keeptime', None) is None: 
                                alarm['keeptime'] = alarm['timestamp']
                            if alarm['keeptime'] >= lastinfo_time:
                               alarm_info.append(alarm)
                        
                    if alarm_info:
                        # NOTE: here, do not remove alarm_info, it will automagically disappear after 1 day 
                        #self.redis.delete(alarm_info_key)
                        logging.info("[UWEB] alarm_info_key: %s, alarm_info: %s", alarm_info_key, alarm_info)

                    for alarm in alarm_info:
                        alarm['alias'] = terminal['alias']

                    group['trackers'][tid]['basic_info'] = basic_info
                    group['trackers'][tid]['track_info'] = track_info 
                    group['trackers'][tid]['trace_info'] = trace_info
                    group['trackers'][tid]['alarm_info'] = alarm_info
                res.groups.append(group)
            self.write_ret(status, 
                           dict_=DotDict(res=res))
        except Exception as e:
            logging.exception("[UWEB] cid: %s get corp lastinfo failed. Exception: %s", 
                              self.current_user.cid, e.args) 
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)
