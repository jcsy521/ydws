# -*- coding: utf-8 -*-

import logging
import datetime
import time

from tornado.escape import json_decode, json_encode
import tornado.web

from utils.dotdict import DotDict
from utils.misc import (str_to_list, utc_to_date, seconds_to_label,
     get_terminal_sessionID_key, get_track_key, get_lqgz_key, get_lqgz_interval_key)
from constants import UWEB, SMS
from helpers.queryhelper import QueryHelper
from helpers.lbmphelper import get_distance, get_locations_with_clatlon, get_location_name
from helpers.confhelper import ConfHelper
from codes.errorcode import ErrorCode
from codes.smscode import SMSCode
from constants import UWEB, LIMIT

from base import BaseHandler, authenticated
from mixin.track import TrackMixin


class MassPointHandler(BaseHandler, TrackMixin):

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
            cellid_flag = data.get('cellid_flag', 0)
            logging.info("[UWEB] Mass point request: %s, uid: %s, tid: %s", 
                         data, self.current_user.uid, tid)
        except Exception as e:
            logging.exception("[UWEB] Mass point request failed. uid: %s, tid: %s. Exception: %s.", 
                              self.current_user.uid, tid, e.args )
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)
            self.finish()
            return

        def _on_finish(db):
            self.db = db
            track = []
            stop = []
            start = {} 
            end = {} 
            mass_point = 0

            # check track point count
            if len(track) > LIMIT.MASS_POINT_NUMBER or (end_time-start_time) > LIMIT.MASS_POINT_INTERVAL : # mass point
                mass_point = 1
                track = []
            else: # general point
                if cellid_flag == 1: # cellid
                     track = self.get_track(tid, start_time, end_time, cellid=True) 
                else: # gps
                    # cellid_flag is None or 0, only gps track
                     track = self.get_track(tid, start_time, end_time, cellid=False) 

            stop = self.db.query("SELECT ts.lid, ts.start_time, ts.end_time, ts.distance,"
                                 "  tl.latitude, tl.longitude, "
                                 "  tl.clatitude, tl.clongitude, "
                                 "  tl.name, tl.degree, tl.speed, tl.locate_error"
                                 "  FROM T_STOP AS ts, T_LOCATION AS tl"
                                 "  WHERE ts.tid = %s"
                                 "  AND ts.lid = tl.id "
                                 "  AND ts.start_time between %s and %s"
                                 "  ORDER BY ts.id ASC",
                                 tid, start_time, end_time)

            if stop: # some handle for the stop
                oldest_stop = stop[0]
                newest_stop = stop[-1]

                starts = self.get_track(tid, start_time, newest_stop['start_time'])
                if starts:
                    distance = self.get_track_distance(starts)

                    lid=starts[0]['id']
                    location = self.db.get("SELECT * FROM T_LOCATION WHERE id = %s", lid)
                    _start_time=starts[0]["timestamp"] 
                    _end_time=starts[-1]["timestamp"] 
                    start = dict(lid=lid, 
                               tid=tid, 
                               start_time=_start_time,
                               end_time=_end_time, 
                               idle_time=abs(_end_time-_start_time),
                               name=self.get_track_name(location),
                               longitude=location['longitude'],
                               latitude=location['latitude'],
                               clongitude=location['clongitude'],
                               clatitude=location['clatitude'],
                               distance=distance)

                    oldest_stop['distance'] = self.get_track_distance(
                                                   self.get_track( tid,
                                                   start['start_time'],
                                                   oldest_stop['start_time'])) 
                                                   
                ends = self.get_track(tid, newest_stop['start_time'], end_time)
                if ends:
                    lid=ends[-1]['id']
                    location = self.db.get("SELECT * FROM T_LOCATION WHERE id = %s", lid)
                    _start_time=ends[-1]["timestamp"] 
                    _end_time=int(time.time())
                    end = dict(lid=lid, 
                               tid=tid, 
                               start_time=_start_time,
                               end_time=_end_time, 
                               idle_time=abs(_end_time-_start_time),
                               name=self.get_track_name(location),
                               longitude=location['longitude'],
                               latitude=location['latitude'],
                               clongitude=location['clongitude'],
                               clatitude=location['clatitude'],
                               distance=0)

                    #NOTE: special handle for end time
                    end['distance'] = self.get_track_distance(
                                           self.get_track(tid, 
                                                oldest_stop['start_time'], 
                                                end['start_time']))

                    if newest_stop['end_time'] == 0:
                        if location['speed'] < LIMIT.SPEED_LIMIT:
                            newest_stop['start_time'] = end['start_time']
                            # end_time of last one of track is useless
                            newest_stop['end_time'] = end['start_time']
                            newest_stop['distance'] = newest_stop['distance'] + self.get_track_distance(
                                                                                     self.get_track(tid, 
                                                                                          newest_stop['start_time'], 
                                                                                          end['start_time']))
                            end = []
                        else: # it should never happpen
                            pass


                for item in stop:
                    #NOTE: end_time is should be bigger than start_time
                    item['idle_time'] = abs(item['end_time']-item['start_time']) 

                    if item.name is None:
                        name = self.get_track_name(item)

            if track:
                # NOTE: if latlons are legal, but clatlons are illlegal, offset
                # them and update them in db. 
                _start_time = time.time()
                track = get_locations_with_clatlon(track, self.db)
                _now_time = time.time()
                if _now_time - _start_time > 3: # 3 seconds
                    logging.info("[UWEB] Track offset used time: %s s, tid: %s, cid: %s", 
                                 _now_time - _start_time, tid, self.current_user.cid)

                # NOTE: filter point without valid clat and clon 
                _track = []
                for t in track: 
                    if t['clongitude'] and ['clatitude']: 
                        _track.append(t)
                    else:
                        logging.info("[UWEB] Invalid point: %s, drop it, cid: %s", 
                                     t, self.current_user.cid)
                track = _track

            # modify name & degere 
            terminal = QueryHelper.get_terminal_by_tid(tid, self.db)
            for item in track:
                item['degree'] = float(item['degree'])
                if item.name is None:
                    name = '' 

            logging.info("[UEB] Tid:%s mass point query, returned %s points.", tid, len(track))
            self.write_ret(status,
                           dict_=DotDict(track=track,
                                         stop=stop,
                                         start=start,
                                         end=end,
                                         mass_point=mass_point))
            self.finish()
        self.queue.put((10, _on_finish))
