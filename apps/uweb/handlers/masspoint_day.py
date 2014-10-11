# -*- coding: utf-8 -*-

import logging
import datetime
import time

from tornado.escape import json_decode, json_encode
import tornado.web

from utils.dotdict import DotDict
from utils.misc import get_date_from_utc, start_end_of_day
     
from constants import UWEB, SMS
from helpers.queryhelper import QueryHelper
from helpers.lbmphelper import get_locations_with_clatlon
from helpers.confhelper import ConfHelper
from codes.errorcode import ErrorCode
from codes.smscode import SMSCode
from constants import UWEB, LIMIT

from base import BaseHandler, authenticated
from mixin.track import TrackMixin


class MassPointDayHandler(BaseHandler, TrackMixin):

    @authenticated
    @tornado.web.removeslash
    @tornado.web.asynchronous
    def post(self):
        """Get mass point through tid in some period."""
        status = ErrorCode.SUCCESS
        try:
            data = DotDict(json_decode(self.request.body))
            tid = data.tid 
            start_time = data.start_time
            end_time = data.end_time

            start_day = datetime.datetime.fromtimestamp(start_time)
            end_day = datetime.datetime.fromtimestamp(end_time)
            # get how many days the end_time and start_time cover
            days = abs(end_day-start_day).days+1

            cellid_flag = data.get('cellid_flag', 0)
            logging.info("[UWEB] Mass point day request: %s, uid: %s, tid: %s", 
                         data, self.current_user.uid, tid)
        except Exception as e:
            status = ErrorCode.SERVER_BUSY
            logging.exception("[UWEB] Mass point day request failed. uid: %s, tid: %s. Exception: %s.", 
                              self.current_user.uid, tid, e.args )
            self.write_ret(status)
            self.finish()
            return

        def _on_finish(db):
            try:
                status = ErrorCode.SUCCESS
                self.db = db
                res = []
                stop = []

                # 2014.08.01  a week.
                if start_time < LIMIT.MASS_POINT_QUERY_TIME and (end_time-start_time) > LIMIT.MASS_POINT_QUERY_INTERVAL:
                    status = ErrorCode.MASS_POINT_QUERY_EXCESS
                    self.write_ret(status)
                    self.finish()
                    return

                for item in range(days):
                    timestamp = start_time+1*60*60*24*(item)
                    date = get_date_from_utc(timestamp)
                    year, month, day = date.year, date.month, date.day
                    start_time_, end_time_ = start_end_of_day(year=year, month=month, day=day)
                    
                    if cellid_flag == 1: # cellid
                         track = self.get_track(tid, start_time_, end_time_, cellid=True) 
                    else: # gps
                         # cellid_flag is None or 0, only gps track
                         track = self.get_track(tid, start_time_, end_time_, cellid=False) 

                    if track:
                        last_point = track[-1]
                        last_point = get_locations_with_clatlon([last_point], self.db)[0]
                        distance = self.get_track_distance(track)
                        r = dict(timestamp=last_point.timestamp,
                                 distance=distance,
                                 latitude=last_point.latitude,
                                 longitude=last_point.longitude,
                                 clatitude=last_point.clatitude,
                                 clongitude=last_point.clongitude,
                                 name=last_point.name,)
                        res.append(r)

                stop = self.get_stop_point(tid, start_time, end_time)

                res.reverse()
                stop.reverse()

                self.write_ret(status,
                               dict_=DotDict(res=res,
                                             stop=stop))
                self.finish()

            except Exception as e:
                status = ErrorCode.SERVER_BUSY
                logging.exception("[UWEB] Mass-point day request failed. uid: %s, tid: %s. Exception: %s.", 
                                  self.current_user.uid, tid, e.args )
                self.write_ret(status)
                self.finish()

        self.queue.put((10, _on_finish))
