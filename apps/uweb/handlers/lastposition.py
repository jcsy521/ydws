# -*- coding: utf-8 -*-

import logging
import time

import tornado.web
from tornado.escape import json_encode, json_decode

from utils.dotdict import DotDict
from utils.ordereddict import OrderedDict
from utils.misc import get_terminal_info_key, get_location_key,\
     get_lastposition_key, get_lastposition_time_key, get_track_key
from utils.public import get_group_info_by_tid
from helpers.lbmphelper import get_clocation_from_ge, get_locations_with_clatlon
from codes.errorcode import ErrorCode
from helpers.queryhelper import QueryHelper
from constants import UWEB, EVENTER, GATEWAY, LOCATION
from constants.MEMCACHED import ALIVED
from base import BaseHandler, authenticated

       
class LastPositionHandler(BaseHandler):
    """Get the newest info of terminal from database.
    NOTE:It just retrieves data from db, not get info from terminal. 
    """
    @authenticated
    @tornado.web.removeslash
    def post(self):
        try:
            data = DotDict(json_decode(self.request.body))
        except Exception as e:
            self.write_ret(ErrorCode.ILLEGAL_DATA_FORMAT) 
            return

        try:
            res = OrderedDict() 
            usable = 1
            status = ErrorCode.SUCCESS
            terminals = self.db.query("SELECT tid FROM T_TERMINAL_INFO"
                                      "  WHERE service_status = %s"
                                      "    AND owner_mobile = %s"
                                      "    AND login_permit = 1"
                                      "    ORDER BY login DESC",
                                      UWEB.SERVICE_STATUS.ON, self.current_user.uid)
            tids = [terminal.tid for terminal in terminals]
            for tid in tids:
                res[tid] = {'car_info':{},
                            'track_info':[]}

                # 0: get group info
                group_info = get_group_info_by_tid(self.db, tid)

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
                    if location.clatitude and location.clongitude:
                        self.redis.setvalue(location_key, location, EVENTER.LOCATION_EXPIRY)

                if location and location['name'] is None:
                    location['name'] = location['name'] if location['name'] else ''

                car_info=dict(defend_status=terminal['defend_status'] if terminal.get('defend_status', None) is not None else 1,
                              mannual_status=terminal['mannual_status'] if terminal.get('mannual_status', None) is not None else 1,
                              fob_status=terminal['fob_status'] if terminal.get('fob_status', None) is not None else 0,
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
                              owner_mobile = terminal['owner_mobile'],
                              alias=terminal['alias'] if terminal['alias'] else terminal['iccid'],
                              #keys_num=terminal['keys_num'] if terminal['keys_num'] is not None else 0,
                              keys_num=0,
                              group_id=group_info['group_id'],
                              group_name=group_info['group_name'],
                              icon_type=terminal['icon_type'],
                              fob_list=terminal['fob_list'] if terminal['fob_list'] else [])

                res[tid]['car_info'] = car_info
            
            lastposition_key = get_lastposition_key(self.current_user.uid)
            lastposition = self.redis.get(lastposition_key)

            lastposition_time_key = get_lastposition_time_key(self.current_user.uid)
            lastposition_time = self.redis.getvalue(lastposition_time_key)

            if lastposition == str(res):  
                pass
            else:
                lastposition_time = int(time.time())
                self.redis.setvalue(lastposition_key, res) 
                self.redis.setvalue(lastposition_time_key, lastposition_time)

            query_time = data.get('lastposition_time', None)
            # 2 check whether provide usable data   
            if int(data.get('cache', 0)) == 1:  # use cache
                if int(query_time) == lastposition_time:
                    usable = 0 
                    res = {} 
                else: 
                    usable = 1
                    for item in data.track_list:
                        track_tid = item['track_tid']
                        if track_tid not in tids:
                            logging.error("The terminal with tid: %s does not exist", track_tid)
                        else:
                            track_time = item['track_time']
                            track_key = get_track_key(track_tid)
                            self.redis.setvalue(track_key, 1, UWEB.TRACK_INTERVAL)
                            car_info = res[track_tid]['car_info']
                            endtime = int(car_info['timestamp'])-1 if car_info['timestamp'] else int(lastposition_time)-1 
                            track_info = self.get_track_info(track_tid, int(track_time)+1, endtime)
                            res[track_tid]['track_info'] = track_info
            else: 
                usable = 1
                for item in data.track_list:
                    track_tid = item['track_tid']
                    if track_tid not in tids:
                        logging.error("The terminal with tid: %s does not exist", track_tid)
                    else:
                        track_time = item['track_time']
                        track_key = get_track_key(track_tid)
                        self.redis.setvalue(track_key, 1, UWEB.TRACK_INTERVAL)
                        car_info = res[track_tid]['car_info']
                        endtime = int(car_info['timestamp'])-1 if car_info['timestamp'] else int(time.time())-1
                        track_info = self.get_track_info(track_tid, int(track_time)+1, endtime) 
                        res[track_tid]['track_info'] = track_info
            
            self.write_ret(status, 
                           dict_=DotDict(res=res,
                                         usable=usable,
                                         lastposition_time=lastposition_time))

        except Exception as e:
            logging.exception("[UWEB] uid: %s get lastposition failed. Exception: %s", 
                              self.current_user.uid, e.args) 
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)

    def get_track_info(self, tid, begintime, endtime):
        track_info = []
        track = self.db.query("SELECT id, latitude, longitude, clatitude, clongitude, type, timestamp"
                              "  FROM T_LOCATION"
                              "  WHERE tid = %s"
                              "    AND NOT (latitude = 0 OR longitude = 0)"
                              "    AND (timestamp BETWEEN %s AND %s)"
                              "    AND type = 0"
                              "    ORDER BY timestamp",
                              tid, begintime, endtime)
        track = get_locations_with_clatlon(track, self.db)
        for t in track: 
            if t['clatitude'] and t['clongitude']:
                point = dict(latitude=t['latitude'],
                             longitude=t['longitude'],
                             clatitude=t['clatitude'],
                             clongitude=t['clongitude'],
                             type=t['type'],
                             timestamp=t['timestamp'])
                track_info.append(point)

        return track_info
