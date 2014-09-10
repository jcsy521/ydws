# -*- coding: utf-8 -*-

import sys
import time
import thread

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

    def handle_stop(self, tid, start_time, end_time):

        track = self.get_track(tid, start_time, end_time)
        #print 'track, tid:%s, len: %s' % (tid, len(track))
        cnt = 0  

        delete_ids = []
        update_item = []
        create_item = []

        for i, pvt in enumerate(track):
            #print '------------i',i, pvt['id']
            #print 'i: %s, speed: %s, pvt: %s' % (i, pvt['speed'], pvt)
            stop_key = 'test_stop_redis:%s' % tid
            stop = self.redis.getvalue(stop_key)

            distance_key = 'test_distance_redis:%s' % tid
            distance = self.redis.get(distance_key) 

            if not distance:
                distance = 0

            last_pvt_key = 'test_last_pvt_redis:%s' % tid
            last_pvt = self.redis.getvalue(last_pvt_key)
            #if i == 0:
            #    print 'last_pvt', last_pvt
            if last_pvt:
                tmp = get_distance(int(last_pvt["longitude"]), int(last_pvt["latitude"]), 
                                   int(pvt["longitude"]), int(pvt["latitude"])) 

                #print 'tmp: %s, distance: %s' % (tmp, distance) 
                distance = float(distance) + tmp 
                #print 'last distance: %s' % (distance) 
                self.redis.setvalue(distance_key, distance, time=EVENTER.STOP_EXPIRY)

            if pvt['speed'] > LIMIT.SPEED_LIMIT: # 5  is moving
                if stop: #NOTE: time_diff is too short, drop the point. 
                    if pvt["timestamp"] - stop['start_time'] < 60: # 60 seconds 
                        cnt += 1  
                        #try:
                        #    _stop = self.db.get("SELECT distance FROM T_STOP WHERE lid =%s ", stop['lid'])
                        #    #_stop = self.db.get("select distance from T_STOP where lid =%s limit 1", stop['lid'])
                        #except Exception as e:
                        #    print e.args, stop

                        _stop = self.db.get("SELECT distance FROM T_STOP WHERE lid =%s ", stop['lid'])
                        if _stop:
                            tmp_dis = _stop['distance']
                        else:
                            tmp_dis = 0 
                        #print 'tmp_dis', tmp_dis
                        distance = float(distance) + tmp_dis 
                        #print 'tmp_dis distance', distance 

                        test_id = self.db.execute("DELETE FROM T_STOP WHERE lid = %s",
                                        stop['lid'])
                        #print '---------delete id', test_id

                        delete_ids.append(stop['lid'])
                        self.redis.delete(stop_key)
                        self.redis.setvalue(distance_key, distance, time=EVENTER.STOP_EXPIRY) 
                        
                        logging.info("[EVENTER] Stop point is droped: %s", stop)
                    else: # close a stop point
                        cnt += 1  
                        self.redis.delete(stop_key)
                        self.db.execute("UPDATE T_STOP SET end_time = %s WHERE lid = %s",
                                        pvt["timestamp"], stop['lid'])
                        update_item.append(dict(timestamp=pvt["timestamp"],
                                                lid=stop['lid']))
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

                    self.db.execute("INSERT INTO T_STOP(lid, tid, start_time, distance) VALUES(%s, %s, %s, %s)",
                                    lid, tid, pvt["timestamp"], distance)

                    create_item.append(dict(distance=distance,
                                            tid=tid,
                                            timestamp=pvt["timestamp"],
                                            lid=lid))
                    self.redis.setvalue(stop_key, stop, time=EVENTER.STOP_EXPIRY)

                    self.redis.delete(distance_key)

                    logging.info("[EVENTER] Stop point is created: %s", stop)
            
            last_pvt = pvt 
            self.redis.setvalue(last_pvt_key, last_pvt, time=EVENTER.STOP_EXPIRY)
            #print '---------------------- cnt', cnt

        #handle db 
        #if delete_ids:
        #    print 'delete_ids', delete_ids 
        #    self.db.executemany("DELETE FROM T_STOP WHERE lid = %s", 
        #                        [(item) for item in delete_ids])
        #if update_item: 
        #    print 'update_item', update_item 
        #    self.db.executemany("UPDATE T_STOP SET end_time = %s WHERE lid = %s",
        #                        [(item['timestamp'], item['lid']) for item in update_item])

        #if create_item: 
        #    _start = time.time()
        #    self.db.executemany("INSERT INTO T_STOP(lid, tid, start_time, distance) VALUES(%s, %s, %s, %s)", 
        #                        [(item['lid'], item['tid'], item['timestamp'], item['distance']) for item in create_item])
        #    _end = time.time()
        #    print 'create_item', create_item 
        #    print 'time_diff',  _end - _start

    def clear_stop(self, tid):
        self.db.execute("DELETE FROM T_STOP WHERE tid = %s", tid)
        stop_key = 'test_stop_redis:%s' % tid
        distance_key = 'test_distance_redis:%s' % tid
        last_pvt_key = 'test_last_pvt_redis:%s' % tid
        self.redis.delete(stop_key)
        self.redis.delete(distance_key)
        self.redis.delete(last_pvt_key)

    def handle_stop_single(self, tid, start_time, end_time):
    
        #begin_time = time.localtime()
        self.clear_stop(tid) 
        self.handle_stop(tid, start_time, end_time) 
        #end_time = time.localtime()
        #print 'begin_time',begin_time
        #print 'end_time',end_time

    def handle_stop_groups(self, tids, start_time, end_time):
        #print ' tids', tids
        #return

        if not tids:
            return 
        for tid in tids:
            self.handle_stop_single(tid, start_time, end_time)

    def get_terminals(self):

        #terminals = self.db.query("SELECT * from T_TERMINAL_INFO"
        #                          "  where tid = '35C2000067'"
        #                          "  limit 50")
        #terminals = self.db.query("SELECT id, tid from T_TERMINAL_INFO LIMIT 13")
        terminals = self.db.query("SELECT id, tid from T_TERMINAL_INFO LIMIT 8000")
        return terminals


def handle_stop_groups(tids, start_time, end_time):

    test = Test()
    test.handle_stop_groups(tids, start_time, end_time) 

def handle_stop_multi():
    try:
        logging.info("terminal stop start!!!!!!!! ")
        test = Test()
        terminals = test.get_terminals()

        tids = [terminal['tid'] for terminal in terminals]
        terminal_num = len(terminals)

        page = 1000 

        d, m = divmod(terminal_num, page)
        thread_num = (d + 1) if m else d

        #print 'terminal group', thread_num 

        start_time = int(time.mktime(time.strptime("%s-%s-%s-%s-%s-%s"%(2014,8,1,0,0,0),"%Y-%m-%d-%H-%M-%S")))
        #start_time = int(time.mktime(time.strptime("%s-%s-%s-%s-%s-%s"%(2014,8,1,0,0,0),"%Y-%m-%d-%H-%M-%S")))
        end_time = int(time.mktime(time.strptime("%s-%s-%s-%s-%s-%s"%(2014,8,2,0,0,0),"%Y-%m-%d-%H-%M-%S")))
        #end_time = int(time.mktime(time.strptime("%s-%s-%s-%s-%s-%s"%(2014,9,10,0,0,0),"%Y-%m-%d-%H-%M-%S")))
        #print time.localtime(start_time)
        #print time.localtime(end_time)

        logging.info("terminal num: %s, page: %s, thread_num: %s, start_time: %s, end_time: %s ", 
                      len(terminals), 
                      page, thread_num, start_time, end_time)

        for i in range(thread_num):
            logging.info("start thread, item: %s", i)
            thread.start_new_thread(handle_stop_groups, (tids[(i)*page:(i+1)*page], start_time, end_time))

        logging.info("terminal stop finished!!!!!!!!! ")

        while True:
            time.sleep(1)
            
    except Exception as e:
        print e.args


def usage():
    print "Usage: python handle_stop.py"

def main():
    handle_stop_multi()

if __name__ == "__main__": 
    ConfHelper.load('../conf/global.conf')
    parse_command_line()
    main()
