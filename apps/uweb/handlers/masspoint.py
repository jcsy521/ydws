# -*- coding: utf-8 -*-

"""This module is designed for mileage-static.
#TODO:
#NOTE: deprecated. 
"""

import logging
import time

from tornado.escape import json_decode
import tornado.web

from utils.dotdict import DotDict
from helpers.lbmphelper import get_locations_with_clatlon
from codes.errorcode import ErrorCode
from constants import LIMIT

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
            mass_flag = data.get('mass_flag', 0)
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
            status = ErrorCode.SUCCESS
            self.db = db
            track = []
            stop = []
            start = {} 
            end = {} 
            mass_point = 0

            if start_time < LIMIT.MASS_POINT_QUERY_TIME and (end_time-start_time) > LIMIT.MASS_POINT_QUERY_INTERVAL:
                status = ErrorCode.MASS_POINT_QUERY_EXCESS
                self.write_ret(status,
                               dict_=DotDict(track=track,
                                             stop=stop,
                                             start=start,
                                             end=end,
                                             mass_point=mass_point))
                self.finish()
                return
                
            # check track point count
            if (end_time-start_time) > LIMIT.MASS_POINT_INTERVAL : # mass point
            #if len(track) > LIMIT.MASS_POINT_NUMBER or (end_time-start_time) > LIMIT.MASS_POINT_INTERVAL : # mass point
                mass_point = 1
                track = []
                logging.info("[UWEB] mass point. tid:%s.", tid)
            else: # general point
                if cellid_flag == 1: # cellid
                     track = self.get_track(tid, start_time, end_time, cellid=True) 
                else: # gps
                    # cellid_flag is None or 0, only gps track
                     track = self.get_track(tid, start_time, end_time, cellid=False) 

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


            stop = self.db.query("SELECT ts.id, ts.lid, ts.start_time,"
                                 "    ts.end_time, ts.distance,"
                                 "    tl.latitude, tl.longitude, "
                                 "    tl.clatitude, tl.clongitude, "
                                 "    tl.name, tl.degree, tl.speed, tl.locate_error"
                                 "  FROM T_STOP AS ts, T_LOCATION AS tl"
                                 "  WHERE ts.tid = %s"
                                 "  AND ts.lid = tl.id "
                                 "  AND ts.start_time BETWEEN %s AND %s"
                                 "  AND ts.end_time !=0"
                                 "  AND ts.distance !=0"
                                 "  ORDER BY ts.start_time ASC",
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
                                 end_time=0, 
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
                    location = self.db.get("SELECT * FROM T_LOCATION "
                                           "  WHERE id = %s", 
                                           lid)
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
                                                newest_stop['start_time'], 
                                                end['start_time']))

                    #NOTE: last point is a stop
                    if newest_stop['end_time'] == 0:
                        #if location['speed'] < LIMIT.SPEED_LIMIT: # may be stop
                        if location['speed'] <= LIMIT.SPEED_LIMIT: # may be stop
                            # end_time of last one of track is useless
                            newest_stop['end_time'] = end['start_time']
                            newest_stop['name'] = end['name']
                            newest_stop['idle_time'] = abs(newest_stop['end_time']-newest_stop['start_time'])
                            newest_stop['distance'] = newest_stop['distance'] + self.get_track_distance(
                                                                                     self.get_track(tid, 
                                                                                          newest_stop['start_time'], 
                                                                                          end['start_time']))

                            # special handle for the last point
                            newest_stop['start_time'] = end['start_time']
                            end = newest_stop 
                            stop.pop()
                        else: # it should never happpen
                            pass


                for item in stop:
                    #NOTE: end_time is should be bigger than start_time
                    item['idle_time'] = abs(item['end_time']-item['start_time']) 

            if start and stop:
                if start['start_time'] == oldest_stop['start_time']:
                    start = {}

            if end and stop:
                if end['start_time'] == newest_stop['start_time']:
                    end = {}

            if track and (not stop):
                start = dict(lid=track[0]['id'], 
                             tid=tid, 
                             start_time=track[0]['timestamp'],
                             end_time=0, 
                             idle_time=0,
                             name=self.get_track_name(track[0]),
                             longitude=track[0]['longitude'],
                             latitude=track[0]['latitude'],
                             clongitude=track[0]['clongitude'],
                             clatitude=track[0]['clatitude'],
                             distance=0)

                end = dict(lid=track[-1]['id'], 
                           tid=tid, 
                           start_time=track[-1]['timestamp'],
                           end_time=0, 
                           idle_time=0,
                           name=self.get_track_name(track[-1]),
                           longitude=track[-1]['longitude'],
                           latitude=track[-1]['latitude'],
                           clongitude=track[-1]['clongitude'],
                           clatitude=track[-1]['clatitude'],
                           distance=0)

                end['distance'] = self.get_track_distance(
                                       self.get_track(tid,
                                            start['start_time'], end['start_time']))


            # modify name & degere 
            for item in track:
                item['degree'] = float(item['degree'])

            if mass_flag:
                mass_point = 1
                track = [] 
                logging.info("[UEB] Mass flag is valid, return empty. tid:%s.", tid)

            if len(track) > LIMIT.MASS_POINT_NUMBER: # mass point
                mass_point = 1
                track = []
                logging.info("[UEB] mass point. tid:%s.", tid)

            if mass_point == 1:
                if not (start or end or stop):
                    if cellid_flag == 1: # cellid
                         track = self.get_track(tid, start_time, end_time, cellid=True) 
                    else: # gps
                        # cellid_flag is None or 0, only gps track
                        track = self.get_track(tid, start_time, end_time, cellid=False) 
                    if track:
                        start = dict(lid=track[0]['id'], 
                                     tid=tid, 
                                     start_time=track[0]['timestamp'],
                                     end_time=0, 
                                     idle_time=0,
                                     name=self.get_track_name(track[0]),
                                     longitude=track[0]['longitude'],
                                     latitude=track[0]['latitude'],
                                     clongitude=track[0]['clongitude'],
                                     clatitude=track[0]['clatitude'],
                                     distance=0)

                        end = dict(lid=track[-1]['id'], 
                                   tid=tid, 
                                   start_time=track[-1]['timestamp'],
                                   end_time=0, 
                                   idle_time=0,
                                   name=self.get_track_name(track[-1]),
                                   longitude=track[-1]['longitude'],
                                   latitude=track[-1]['latitude'],
                                   clongitude=track[-1]['clongitude'],
                                   clatitude=track[-1]['clatitude'],
                                   distance=0)

                        end['distance'] = self.get_track_distance(
                                               self.get_track(tid,
                                                    start['start_time'], end['start_time']))

            # if start is equal end, just provide start
            if start and end:
                if start['start_time'] == end['start_time']:
                    end = {} 

            # NOTE: move the distance from next point to last point
            lst = stop[:]
            if start: 
                lst.insert(0, start) 
            if end: 
                lst.append(end) 

            for k, v in enumerate(lst): 
                if k == len(lst) - 1: 
                    break 
                v['distance'] = lst[k+1]['distance'] 

            logging.info("[UEB] Tid:%s mass point query, returned %s points.", tid, len(track))
            self.write_ret(status,
                           dict_=DotDict(track=track,
                                         stop=stop,
                                         start=start,
                                         end=end,
                                         mass_point=mass_point))
            self.finish()
        self.queue.put((10, _on_finish))
