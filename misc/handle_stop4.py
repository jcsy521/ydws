# -*- coding: utf-8 -*-

import sys
import time

import os.path
import site
TOP_DIR_ = os.path.abspath(os.path.join(__file__, "../.."))
site.addsitedir(os.path.join(TOP_DIR_, "libs"))
import logging

from tornado.options import define, options, parse_command_line

from helpers.confhelper import ConfHelper
from utils.public import get_terminal_type_by_tid 
from utils.misc import get_terminal_sessionID_key
from db_.mysql import DBConnection
from utils.myredis import MyRedis
from helpers.lbmphelper import get_distance
from constants import UWEB, LIMIT, EVENTER


class Test():

    def __init__(self):
        self.db = DBConnection().db
        self.redis = MyRedis()

    def get_track(self, tid, start_time, end_time, cellid=False):
        """NOTE: Now, only return gps point.
        """
        if cellid:
            track = self.db.query("SELECT id, latitude, longitude, clatitude,"
                                  "       clongitude, timestamp, name, type, speed, degree, locate_error"
                                  "  FROM T_LOCATION"
                                  "  WHERE tid = %s"
                                  "    AND NOT (latitude = 0 OR longitude = 0)"
                                  "    AND (timestamp BETWEEN %s AND %s)"
                                  "    GROUP BY timestamp"
                                  "    ORDER BY timestamp",
                                  tid, start_time, end_time)
        else: # gps, pvt
            track = self.db.query("SELECT id, latitude, longitude, clatitude,"
                                  "       clongitude, timestamp, name, type, speed, degree, locate_error"
                                  "  FROM T_LOCATION"
                                  "  WHERE tid = %s"
                                  "    AND category = 1"
                                  "    AND NOT (latitude = 0 OR longitude = 0)"
                                  "    AND (timestamp BETWEEN %s AND %s)"
                                  "    AND type = 0"
                                  "    GROUP BY timestamp"
                                  "    ORDER BY timestamp",
                                  tid, start_time, end_time)
        return track 

    #def get_track_distance(self, track):
    #    """Get distance of a section of track.
    #    """
    #    distance = 0 
    #    if not track:
    #        pass
    #    else:
    #        start_point = None
    #        for point in track:
    #            if not start_point: 
    #                start_point = point
    #                continue
    #            else:
    #                distance += get_distance(start_point["longitude"], start_point["latitude"], 
    #                                         point["longitude"], point["latitude"])
    #                start_point = point

    #    return distance

    def handle_stop(self, tid, start_time, end_time):

        track = self.get_track(tid, start_time, end_time)
        print 'track', len(track)
        cnt = 0  

        for i, pvt in enumerate(track):

            #print 'i: %s, speed: %s, pvt: %s' % (i, pvt['speed'], pvt)
            stop_key = 'test_stop_redis:%s' % tid
            stop = self.redis.getvalue(stop_key)

            distance_key = 'test_distance_redis:%s' % tid
            distance = self.redis.get(distance_key) 

            if not distance:
                distance = 0

            last_pvt_key = 'test_last_pvt_redis:%s' % tid
            last_pvt = self.redis.getvalue(last_pvt_key)

            if last_pvt:
                tmp = get_distance(int(last_pvt["longitude"]), int(last_pvt["latitude"]), 
                                                          int(pvt["longitude"]), int(pvt["latitude"])) 


                print 'tmp: %s, distance: %s' % (tmp, distance) 
                distance = float(distance) + tmp 
                print 'last distance: %s' % (distance) 
                #print 'add distance', i, pvt['id'], tmp, distance
                self.redis.setvalue(distance_key, distance, time=EVENTER.STOP_EXPIRY)

            if pvt['speed'] > LIMIT.SPEED_LIMIT: # 5  is moving
                if stop: #NOTE: time_diff is too short, drop the point. 
                    if pvt["timestamp"] - stop['start_time'] < 60: # 60 seconds 
                        cnt += 1  
                        _stop = self.db.get("select distance from T_STOP_bak where lid =%s", stop['lid'])
                        if _stop:
                            tmp_dis = _stop['distance']
                        else:
                            tmp_dis = 0 
                        print 'tmp_dis', tmp_dis
                        distance = float(distance) + tmp_dis 
                        print 'tmp_dis distance', distance 

                        self.db.execute("DELETE FROM T_STOP_bak WHERE lid = %s",
                                        stop['lid'])
                        self.redis.delete(stop_key)
                        self.redis.setvalue(distance_key, distance, time=EVENTER.STOP_EXPIRY) 
                        logging.info("[EVENTER] Stop point is droped: %s", stop)
                    else: # close a stop point
                        cnt += 1  
                        self.redis.delete(stop_key)
                        self.db.execute("UPDATE T_STOP_bak SET end_time = %s WHERE lid = %s",
                                        pvt["timestamp"], stop['lid'])
                        logging.info("[EVENTER] Stop point is closed: %s", stop)
                else:
                    pass
            else: # low speed, may stop
                if stop: 
                    stop['end_time'] = pvt["timestamp"]
                    self.redis.setvalue(stop_key, stop, time=EVENTER.STOP_EXPIRY)
                    logging.info("[EVENTER] Stop point is updated: %s", stop)
                else: # NOTE: start stop. #NOTE:  create a new stop point
                    cnt += 1  
                    lid=pvt['id']
                    stop = dict(lid=lid,
                                tid=tid, 
                                start_time=pvt["timestamp"], 
                                end_time=0, 
                                pre_lon=pvt["longitude"], 
                                pre_lat=pvt["latitude"], 
                                distance=distance)

                    self.db.execute("INSERT INTO T_STOP_bak(lid, tid, start_time, distance) VALUES(%s, %s, %s, %s)",
                                    lid, tid, pvt["timestamp"], distance)
                    self.redis.setvalue(stop_key, stop, time=EVENTER.STOP_EXPIRY)

                    self.redis.delete(distance_key)

                    logging.info("[EVENTER] Stop point is created: %s", stop)
            
            last_pvt = pvt 
            self.redis.setvalue(last_pvt_key, last_pvt, time=EVENTER.STOP_EXPIRY)
            print '---------------------- cnt', cnt

    def clear_stop(self, tid):
        self.db.execute("DELETE FROM T_STOP_bak WHERE tid = %s", tid)
        stop_key = 'test_stop_redis:%s' % tid
        distance_key = 'test_distance_redis:%s' % tid
        last_pvt_key = 'test_last_pvt_redis:%s' % tid
        self.redis.delete(stop_key)
        self.redis.delete(distance_key)
        self.redis.delete(last_pvt_key)

def usage():
    print "Usage: python handle_stop.py"

def main():
    test = Test()
    start_time = int(time.mktime(time.strptime("%s-%s-%s-%s-%s-%s"%(2014,8,1,0,0,0),"%Y-%m-%d-%H-%M-%S")))
    #start_time = int(time.mktime(time.strptime("%s-%s-%s-%s-%s-%s"%(2014,8,1,0,0,0),"%Y-%m-%d-%H-%M-%S")))
    #end_time = int(time.mktime(time.strptime("%s-%s-%s-%s-%s-%s"%(2014,8,1,19,0,0),"%Y-%m-%d-%H-%M-%S")))
    end_time = int(time.mktime(time.strptime("%s-%s-%s-%s-%s-%s"%(2014,9,10,0,0,0),"%Y-%m-%d-%H-%M-%S")))
    print time.localtime(start_time)
    print time.localtime(end_time)
    
    tid = '35C2000067'

    #tid = '3A28200102'
    #tid = 'T123SIMULATOR'

    begin_time = time.localtime()
    test.clear_stop(tid) 
    test.handle_stop(tid, start_time, end_time) 
    end_time = time.localtime()
    print 'begin_time',begin_time
    print 'end_time',end_time

if __name__ == "__main__": 
    ConfHelper.load('../conf/global.conf')
    parse_command_line()
    main()
