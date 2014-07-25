# -*- coding: utf-8 -*-

import logging
import time

import tornado.web
from tornado.escape import json_encode, json_decode

from utils.dotdict import DotDict
from utils.ordereddict import OrderedDict
from utils.misc import get_terminal_info_key, get_location_key,\
     get_lastposition_key, get_lastposition_time_key, get_track_key, DUMMY_IDS
from utils.public import get_group_info_by_tid
from helpers.lbmphelper import get_clocation_from_ge, get_locations_with_clatlon
from codes.errorcode import ErrorCode
from helpers.queryhelper import QueryHelper
from constants import UWEB, EVENTER, GATEWAY, LOCATION
from constants.MEMCACHED import ALIVED
from base import BaseHandler, authenticated
from mixin.avatar import AvatarMixin
       
class LastPositionHandler(BaseHandler, AvatarMixin):
    """Get the newest info of terminal from database.
    NOTE:It just retrieves data from db, not get info from terminal. 
    """
    @authenticated
    @tornado.web.removeslash
    @tornado.web.asynchronous
    def post(self):
        _start_time = time.time()
        def _on_finish(db):
            self.db = db
            try:
                data = DotDict(json_decode(self.request.body))
                biz_type = data.get("biz_type", UWEB.BIZ_TYPE.YDWS)
                version_type = int(data.get("version_type", 0))
                logging.info("[UWEB] Lastposition request: %s", 
                             data)
            except Exception as e:
                self.write_ret(ErrorCode.ILLEGAL_DATA_FORMAT) 
                self.finish()
                return

            try:
                res = OrderedDict() 
                usable = 1
                status = ErrorCode.SUCCESS
                if data.get('tids', None):
                    terminals = []
                    for tid in data.tids:
                        terminal = QueryHelper.get_terminal_info(tid, self.db, self.redis) 
                        if terminal:
                            terminals.append(DotDict(tid=tid))
                        else:
                            logging.exception("[UWEB] tid: %s can not be found.", 
                                              tid)
                else:
                    if self.current_user.oid != UWEB.DUMMY_OID: # operator,Note: operator also has cid, so we check oid firstly.
                        groups = self.db.query("SELECT group_id FROM T_GROUP_OPERATOR WHERE oper_id = %s", self.current_user.oid)
                        gids = [g.group_id for g in groups]
                        terminals = self.db.query("SELECT tid FROM T_TERMINAL_INFO"
                                                  "  WHERE (service_status = %s"
                                                  "         OR service_status = %s)"
                                                  "    AND biz_type = %s"
                                                  "    AND group_id IN %s"
                                                  "    ORDER BY LOGIN DESC",
                                                  UWEB.SERVICE_STATUS.ON, UWEB.SERVICE_STATUS.TO_BE_ACTIVATED, 
                                                  biz_type,
                                                  tuple(DUMMY_IDS + gids))
                    elif self.current_user.cid != UWEB.DUMMY_CID: # Corp 
                        groups = self.db.query("SELECT id gid, name FROM T_GROUP WHERE corp_id = %s", self.current_user.cid)
                        gids = [g.gid for g in groups]
                        terminals = self.db.query("SELECT tid FROM T_TERMINAL_INFO"
                                                  "  WHERE (service_status = %s"
                                                  "         OR service_status = %s)"
                                                  "    AND biz_type = %s"
                                                  "    AND group_id IN %s"
                                                  "    ORDER BY LOGIN DESC",
                                                  UWEB.SERVICE_STATUS.ON, UWEB.SERVICE_STATUS.TO_BE_ACTIVATED, 
                                                  biz_type,
                                                  tuple(DUMMY_IDS + gids))
                    else : # individual user
                        terminals = self.db.query("SELECT tid FROM T_TERMINAL_INFO"
                                                  "  WHERE (service_status = %s"
                                                  "         OR service_status = %s)"
                                                  "    AND biz_type = %s"
                                                  "    AND owner_mobile = %s"
                                                  "    AND login_permit = 1"
                                                  "    ORDER BY login DESC",
                                                  UWEB.SERVICE_STATUS.ON, UWEB.SERVICE_STATUS.TO_BE_ACTIVATED, 
                                                  biz_type,
                                                  self.current_user.uid)
                _now_time = time.time()
                if (_now_time - _start_time) > 5:
                    logging.info("[UWEB] Lastinfo step1 used time: %s > 5s",
                                _now_time - _start_time)

                tids = [terminal.tid for terminal in terminals]
                for tid in tids:
                    _now_time = time.time()
                    if (_now_time - _start_time) > 5:
                        logging.info("[UWEB] Lastinfo step2 used time: %s > 5s",
                                    _now_time - _start_time)

                    res[tid] = {'car_info':{},
                                'track_info':[]}

                    # 0: get group info
                    group_info = get_group_info_by_tid(self.db, tid)

                    # 1: get terminal info 
                    terminal = QueryHelper.get_terminal_info(tid, self.db, self.redis) 
                    mobile = terminal['mobile']
                    if terminal['login'] == GATEWAY.TERMINAL_LOGIN.SLEEP:
                        terminal['login'] = GATEWAY.TERMINAL_LOGIN.ONLINE

                    # 2: get location 
                    location = QueryHelper.get_location_info(tid, self.db, self.redis)
                    if location and not (location.clatitude or location.clongitude):
                        location_key = get_location_key(str(tid))
                        locations = [location,] 
                        #locations = get_locations_with_clatlon(locations, self.db) 
                        location = locations[0]
                        if location.clatitude and location.clongitude:
                            self.redis.setvalue(location_key, location, EVENTER.LOCATION_EXPIRY)

                    if location and location['name'] is None:
                        location['name'] = location['name'] if location['name'] else ''


                    if location and location['type'] == 1: # cellid
                        location['locate_error'] = 500  # mile

                    avatar_full_path, avatar_path, avatar_name, avatar_time = self.get_avatar_info(mobile)
                    service_status = QueryHelper.get_service_status_by_tmobile(self.db, mobile)

                    acc_status_info = QueryHelper.get_acc_status_info_by_tid(self.client_id, tid, self.db, self.redis)
                    acc_message = acc_status_info['acc_message']

                    car_info=dict(defend_status=terminal['defend_status'] if terminal.get('defend_status', None) is not None else 1,
                                  service_status=service_status,
                                  mannual_status=terminal['mannual_status'] if terminal.get('mannual_status', None) is not None else 1,
                                  acc_message=acc_message,
                                  fob_status=terminal['fob_status'] if terminal.get('fob_status', None) is not None else 0,
                                  timestamp=location['timestamp'] if location else 0,
                                  speed=location.speed if location else 0,
                                  # NOTE: degree's type is Decimal, float() it before json_encode
                                  degree=float(location.degree) if location else 0.00,
                                  locate_error=location.get('locate_error', 20) if location else 20,
                                  name=location.name if location else '',
                                  type=location.type if location else 1,
                                  latitude=location['latitude'] if location else 0,
                                  longitude=location['longitude'] if location else 0, 
                                  clatitude=location['clatitude'] if location else 0,
                                  clongitude=location['clongitude'] if location else 0, 
                                  login=terminal['login'] if terminal['login'] is not None else 0,
                                  bt_name=terminal.get('bt_name', '') if terminal else '',
                                  bt_mac=terminal.get('bt_mac', '') if terminal else '',
                                  dev_type=terminal['dev_type'] if terminal.get('dev_type', None) is not None else 'A',
                                  gps=terminal['gps'] if terminal['gps'] is not None else 0,
                                  gsm=terminal['gsm'] if terminal['gsm'] is not None else 0,
                                  pbat=terminal['pbat'] if terminal['pbat'] is not None else 0,
                                  mobile=terminal['mobile'],
                                  owner_mobile = terminal['owner_mobile'],
                                  alias=terminal['alias'] if terminal['alias'] else terminal['mobile'],
                                  #keys_num=terminal['keys_num'] if terminal['keys_num'] is not None else 0,
                                  keys_num=0,
                                  group_id=group_info['group_id'],
                                  group_name=group_info['group_name'],
                                  icon_type=terminal['icon_type'],
                                  fob_list=terminal['fob_list'] if terminal['fob_list'] else [],
                                  avatar_path=avatar_path,
                                  avatar_time=avatar_time)

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
               
                if int(version_type) >= 1:
                    terminals = []
                    for k, v in res.iteritems():
                        v.update({'tid':k})
                        terminals.append(v)

                    self.write_ret(status, 
                                   dict_=DotDict(terminals=terminals,
                                                 usable=usable,
                                                 lastposition_time=lastposition_time))

                else:
                    self.write_ret(status, 
                                   dict_=DotDict(res=res,
                                                 usable=usable,
                                                 lastposition_time=lastposition_time))
                _now_time = time.time()
                if (_now_time - _start_time) > 5:
                    logging.info("[UWEB] Lastinfo step3 used time: %s > 5s",
                                _now_time - _start_time)
            except Exception as e:
                logging.exception("[UWEB] uid: %s get lastposition failed. Exception: %s", 
                                  self.current_user.uid, e.args) 
                status = ErrorCode.SERVER_BUSY
                self.write_ret(status)
            self.finish()
        self.queue.put((10, _on_finish))


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
