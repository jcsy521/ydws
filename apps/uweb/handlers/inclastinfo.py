# -*- coding: utf-8 -*-

import logging
import time

import tornado.web
from tornado.escape import json_encode, json_decode

from utils.dotdict import DotDict
from utils.ordereddict import OrderedDict
from utils.misc import get_terminal_info_key, get_alarm_info_key, get_location_key,\
     get_lastinfo_key, get_lastinfo_time_key, DUMMY_IDS, get_track_key
from codes.errorcode import ErrorCode
from helpers.queryhelper import QueryHelper
from helpers.lbmphelper import get_clocation_from_ge, get_locations_with_clatlon
from constants import UWEB, EVENTER, GATEWAY
from constants.MEMCACHED import ALIVED
from base import BaseHandler, authenticated

       
class IncLastInfoCorpHandler(BaseHandler):
    """Get the newest info of terminal from database.
    NOTE:It just retrieves data from db, not get info from terminal. 
    """
    @authenticated
    @tornado.web.removeslash
    def post(self):
        try:
            data = DotDict(json_decode(self.request.body))
            track_lst = data.get('track_lst', [])
            current_time = int(time.time()) 
            lastinfo_time = data.get('lastinfo_time') 
        except Exception as e:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            logging.info("[UWEB] lastfinfo for corp failed, message: %s, Exception: %s, request: \n%s", 
                         ErrorCode.ERROR_MESSAGE[status], e.args, self.request.body)
            self.write_ret(status)
            return 

        try:
            status = ErrorCode.SUCCESS
            res_type = 0
            #NOTE: first time, lastinfo_time = -1, set the lsstinfo_time as current_time 
            if lastinfo_time == -1:
                res_type = 2
                lastinfo_time = current_time 

            corp = self.db.get("SELECT cid, name, mobile FROM T_CORP WHERE cid = %s", self.current_user.cid)
            if self.current_user.oid == UWEB.DUMMY_OID:
                uid = self.current_user.cid
                groups = self.db.query("SELECT id gid, name FROM T_GROUP WHERE corp_id = %s"
                                       "  ORDER BY id", uid)
            else:
                uid = self.current_user.oid
                groups = self.db.query("SELECT group_id FROM T_GROUP_OPERATOR WHERE oper_id = %s", uid)
                gids = [g.group_id for g in groups]
                groups = self.db.query("SELECT id gid, name FROM T_GROUP WHERE id IN %s"
                                       "  ORDER BY id", tuple(DUMMY_IDS + gids))
                        
            corp_info = dict(name=corp['name'] if corp else '',
                             cid=corp['cid'] if corp else '')

            corp_info_key = 'corp_info:%s' % uid
            corp_info_old = self.redis.getvalue(corp_info_key)

            self.redis.setvalue(corp_info_key, corp_info)


            if corp_info_old:
                if corp_info_old != corp_info:
                    res_type = 2
                else:
 
            res = DotDict(name=corp_info['name'],
                          cid=corp_info['cid'],
                          online=0,
                          offline=0,
                          groups=[],
                          lastinfo_time=current_time)

            group_info_key = 'group_info:%s' % uid
            group_info_old = self.redis.getvalue(group_info_key)
            if group_info_old:
                if group_info_old != groups:
                    res_type = 2
            self.redis.setvalue(group_info_key, groups)
              
            for group in groups:
                group['trackers'] = {} 
                terminals = self.db.query("SELECT tid FROM T_TERMINAL_INFO"
                                          "  WHERE group_id = %s"
                                          "    AND service_status = %s"
                                          "    ORDER BY id",
                                          group.gid, UWEB.SERVICE_STATUS.ON)
                tids = [str(terminal.tid) for terminal in terminals]

                terminal_info_key = 'terminal_info:%s:%s' % (uid, group.gid)
                terminal_info_old = self.redis.getvalue(terminal_info_key)
                if terminal_info_old:
                    if terminal_info_old != tids:
                        res_type = 2
                self.redis.setvalue(terminal_info_key, tids)

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
                        #locations = get_locations_with_clatlon(locations, self.db) 
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
                                    gps=terminal['gps'] if terminal['gps'] is not None else 0,
                                    gsm=terminal['gsm'] if terminal['gsm'] is not None else 0,
                                    pbat=terminal['pbat'] if terminal['pbat'] is not None else 0,
                                    mobile=terminal['mobile'],
                                    owner_mobile=terminal['owner_mobile'],
                                    alias=terminal['alias'],
                                    #keys_num=terminal['keys_num'] if terminal['keys_num'] is not None else 0,
                                    keys_num=0,
                                    icon_type=terminal['icon_type'] if terminal.get('icon_type', None) is not None else 0,
                                    fob_list=terminal['fob_list'] if terminal['fob_list'] else [])

                    #2: build track_info
                    track_info = []
                    for item in track_lst:
                        if tid == item['track_tid']:
                            track_key = get_track_key(tid)
                            self.redis.setvalue(track_key, 1, UWEB.TRACK_INTERVAL)
                            endtime = int(basic_info['timestamp'])-1 if basic_info['timestamp'] else int(current_time)-1
                            points_track = self.db.query("SELECT id, latitude, longitude," 
                                                         "   clatitude, clongitude, type, timestamp"
                                                         "  FROM T_LOCATION"
                                                         "  WHERE tid = %s"
                                                         "    AND NOT (latitude = 0 OR longitude = 0)"
                                                         "    AND (timestamp BETWEEN %s AND %s)"
                                                         "    AND type = 0"
                                                         "    ORDER BY timestamp",
                                                         tid,
                                                         int(item['track_time'])+1, endtime)

                            #points_track = get_locations_with_clatlon(points_track, self.db)
                            for point in points_track: 
                                if point['clatitude'] and point['clongitude']:
                                    t = dict(latitude=point['latitude'],
                                             longitude=point['longitude'],
                                             clatitude=point['clatitude'],
                                             clongitude=point['clongitude'],
                                             type=point['type'],
                                             timestamp=point['timestamp'])
                                    track_info.append(t)
                            break

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
                                                 tid, int(current_time)-60*5, basic_info['timestamp'])

                    #points_trace = get_locations_with_clatlon(points_trace, self.db)
                    points_trace = points_trace[:5] 
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
                        #logging.info("[UWEB] lastinfo_time: %s, alarm_info_key: %s, alarm_info: %s", lastinfo_time,  alarm_info_key, alarm_info)
                        pass

                    for alarm in alarm_info:
                        alarm['alias'] = terminal['alias']

                    group['trackers'][tid]['basic_info'] = basic_info
                    group['trackers'][tid]['track_info'] = track_info 
                    group['trackers'][tid]['trace_info'] = trace_info
                    group['trackers'][tid]['alarm_info'] = alarm_info
                    
                    terminal_detail_key = 'terminal_detail:%s:%s' % (uid, tid)
                    terminal_detail_old = self.redis.getvalue(terminal_detail_key)
                    self.redis.setvalue(terminal_detail_key, group['trackers'][tid])
                    if res_type != 2:
                        if terminal_detail_old:
                            if terminal_detail_old != group['trackers'][tid]: 
                                res_type = 1
                            else:
                                del group['trackers'][tid]

                res.groups.append(group)

            if int(res_type) == 0:
                self.write_ret(status, 
                               dict_=DotDict(res_type=res_type))
            else:
                self.write_ret(status, 
                               dict_=DotDict(res=res, 
                                             res_type=res_type))
        except Exception as e:
            logging.exception("[UWEB] cid: %s get corp lastinfo failed. Exception: %s", 
                              self.current_user.cid, e.args) 
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)
