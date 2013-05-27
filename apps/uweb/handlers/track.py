# -*- coding: utf-8 -*-

import logging
import re

from tornado.escape import json_decode, json_encode
import tornado.web

from utils.dotdict import DotDict
from utils.misc import get_lqgz_key, str_to_list
from constants import UWEB, SMS
from helpers.queryhelper import QueryHelper
from helpers.smshelper import SMSHelper
from helpers.lbmphelper import get_distance 
from codes.errorcode import ErrorCode
from codes.smscode import SMSCode

from base import BaseHandler, authenticated
from mixin.base import  BaseMixin

class TrackLQHandler(BaseHandler, BaseMixin):

    @authenticated
    @tornado.web.removeslash
    def post(self):
        """Turn on tracing."""
        status = ErrorCode.SUCCESS
        try:
            data = DotDict(json_decode(self.request.body))
            tid = data.get('tid',None) 
            tids = data.get('tids', None)
            # check tid whether exist in request and update current_user
            self.check_tid(tid)
            logging.info("[UWEB] track LQ request: %s, uid: %s, tid: %s, tids: %s", 
                         data, self.current_user.uid, tid, tids)
        except Exception as e:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            self.write_ret(status)
            return 

        try:

            tids = str_to_list(tids)
            tids = tids if tids else [self.current_user.tid, ]
            tids = [str(tid) for tid in tids]

            for tid in tids:
                terminal = QueryHelper.get_terminal_by_tid(tid, self.db)
                lqgz_key = get_lqgz_key(tid)
                lqgz_value = self.redis.getvalue(lqgz_key)
                if not lqgz_value:
                    # in mill second
                    #interval = int(data.interval) * 60 * 1000
                    interval = int(data.interval)
                    sms = SMSCode.SMS_LQGZ % interval 
                    SMSHelper.send_to_terminal(terminal.mobile, sms) 
                    self.redis.setvalue(lqgz_key, True, SMS.LQGZ_INTERVAL)
            self.write_ret(status)
        except Exception as e:
            logging.exception("[UWEB] uid: %s, tid: %s send lqgz failed. Exception: %s. ", 
                              self.current_user.uid, self.current_user.tid, e.args )
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)

class TrackHandler(BaseHandler):

    @authenticated
    @tornado.web.removeslash
    def post(self):
        """Get track through tid in some period."""
        status = ErrorCode.SUCCESS
        try:
            data = DotDict(json_decode(self.request.body))
            tid = data.get('tid',None) 
            # check tid whether exist in request and update current_user
            self.check_tid(tid)
            logging.info("[UWEB] track request: %s, uid: %s, tid: %s", 
                         data, self.current_user.uid, self.current_user.tid)
        except Exception as e:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            self.write_ret(status)
            return 

        try:
            # check the tracker whether can be tracked
            biz = QueryHelper.get_biz_by_mobile(self.current_user.sim, self.db)
            if biz: 
                if biz.biz_type == UWEB.BIZ_TYPE.ELECTROCAR:
                    status = ErrorCode.QUERY_TRACK_FORBID
                    self.write_ret(status)
                    logging.info("[UWEB] sim:%s, biz_type:%s, track is not permited.", 
                                 self.current_user.sim, biz.biz_type)
                    return
            else:
                # 1477874**** cannot query track
                r = re.compile(UWEB.SIMPLE_YDCWS_PATTERN)
                if r.match(self.current_user.sim):
                    status = ErrorCode.QUERY_TRACK_FORBID
                    self.write_ret(status)
                    logging.info("[UWEB] sim:%s, track is not permited.", 
                                 self.current_user.sim)
                    return

            start_time = data.start_time
            end_time = data.end_time
            cellid_flag = data.get('cellid_flag')
            # the interval between start_time and end_time is one week
            if (int(end_time) - int(start_time)) > UWEB.QUERY_INTERVAL:
                self.write_ret(ErrorCode.QUERY_INTERVAL_EXCESS)
                return

            if cellid_flag == 1:
                # gps track and cellid track
                track = self.db.query("SELECT latitude, longitude, clatitude,"
                                      "       clongitude, timestamp, name, type, speed, degree"
                                      "  FROM T_LOCATION"
                                      "  WHERE tid = %s"
                                      "    AND NOT (clatitude = 0 OR clongitude = 0)"
                                      "    AND (timestamp BETWEEN %s AND %s)"
                                      "    ORDER BY timestamp",
                                      self.current_user.tid, start_time, end_time)
            else:
                # cellid_flag is None or 0, only gps track
                track = self.db.query("SELECT latitude, longitude, clatitude,"
                                      "       clongitude, timestamp, name, type, speed, degree"
                                      "  FROM T_LOCATION"
                                      "  WHERE tid = %s"
                                      "    AND NOT (clatitude = 0 OR clongitude = 0)"
                                      "    AND (timestamp BETWEEN %s AND %s)"
                                      "    AND type = 0"
                                      "    ORDER BY timestamp",
                                      self.current_user.tid, start_time, end_time)

            # add idle_points  
            # track1, track2, track3,...
            # when the distance between two points is larger than 10 meters and the interval is less than 5 minutes, 
            # they are regarded as idle_points
            idle_lst = []
            idle_points = []
            for i, item_start in enumerate(track):
               is_idle = False 
               if i in idle_lst:
                   continue
               for j in range(i+1,len(track)):
                   item_end = track[j]
                   distance = get_distance(item_start.clongitude, item_start.clatitude, item_end.clongitude, item_end.clatitude) 
                   if distance >= UWEB.IDLE_DISTANCE:
                       break
                   else:
                       idle_time = item_end['timestamp'] - item_start['timestamp']
                       item_start['idle_time'] = idle_time
                       item_start['start_time'] = item_start['timestamp']
                       item_start['end_time'] = item_end['timestamp']
                       idle_lst.append(j)
                       is_idle = True
               if is_idle and item_start['idle_time'] > UWEB.IDLE_INTERVAL: 
                   idle_points.append(item_start)

            # modify name & degere 
            terminal = QueryHelper.get_terminal_by_tid(self.current_user.tid, self.db)
            for item in track:
                item['degree'] = float(item['degree'])
                if item.name is None:
                    item['name'] = ''

            self.write_ret(status,
                           dict_=DotDict(track=track,
                                         idle_points=idle_points))
        except Exception as e:
            logging.exception("[UWEB] uid: %s, tid: %s get track failed. Exception: %s. ", 
                              self.current_user.uid, self.current_user.tid, e.args )
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)
