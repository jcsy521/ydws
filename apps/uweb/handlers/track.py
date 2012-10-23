# -*- coding: utf-8 -*-

import logging

from tornado.escape import json_decode, json_encode
import tornado.web

from utils.dotdict import DotDict
from constants import UWEB
from helpers.queryhelper import QueryHelper

from base import BaseHandler, authenticated
from codes.errorcode import ErrorCode

class TrackHandler(BaseHandler):


    @authenticated
    @tornado.web.removeslash
    def post(self):
        """Get track through tid in some period."""
        try:
            data = DotDict(json_decode(self.request.body))
            logging.info("[UWEB] track request: %s, uid: %s, tid: %s", 
                         data, self.current_user.uid, self.current_user.tid)
        except Exception as e:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            self.write_ret(status)
            return 

        try:
            start_time = data.start_time
            end_time = data.end_time
            cellid_flag = data.get('cellid_flag')
            # the interval between start_time and end_time is one week
            if (int(end_time) - int(start_time)) > UWEB.QUERY_INTERVAL:
                self.write_ret(ErrorCode.TRACK_QUERY_INTERVAL_EXCESS)
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
            terminal = QueryHelper.get_terminal_by_tid(self.current_user.tid, self.db)
            for item in track:
                item['degree'] = float(item['degree'])
                if item.name is None:
                    item['name'] = ''
                
            self.write_ret(ErrorCode.SUCCESS,
                           dict_=DotDict(track=track))
        except Exception as e:
            logging.exception("[UWEB] uid: %s, tid: %s get track failed. Exception: %s. ", 
                              self.current_user.uid, self.current_user.tid, e.args )
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)
