# -*- coding: utf-8 -*-

import logging
import time
import datetime

import copy
import functools 

from tornado.escape import json_decode

from helpers.smshelper import SMSHelper
from helpers.queryhelper import QueryHelper
from helpers import lbmphelper
from helpers.notifyhelper import NotifyHelper
from helpers.urlhelper import URLHelper
from helpers.confhelper import ConfHelper
from helpers.uwebhelper import UWebHelper
from helpers.weixinpushhelper import WeixinPushHelper

from utils.dotdict import DotDict
from utils.misc import (get_location_key, get_terminal_time, get_terminal_info_key,
     get_ios_id_key, get_power_full_key, get_region_status_key, get_alarm_info_key,
     safe_utf8, safe_unicode, get_ios_push_list_key, get_android_push_list_key,
     get_region_time_key, get_alert_freq_key, get_pbat_message_key,
     get_mileage_key, start_end_of_day, get_single_status_key,
     get_single_time_key, get_speed_limit_key, get_stop_key,
     get_distance_key, get_last_pvt_key)
from utils.public import insert_location
from utils.geometry import PtInPolygon 
from utils.repeatedtimer import RepeatedTimer

from codes.smscode import SMSCode
from codes.errorcode import ErrorCode 
from constants import EVENTER, GATEWAY, UWEB, LIMIT
from constants.MEMCACHED import ALIVED


class PacketTask(object):
    
    def __init__(self, packet, db, redis):
        self.packet = packet
        self.db = db
        self.redis = redis

    def run_position(self):
        """Process the current packet: position/charge"""
        info = self.packet

        if info['t'] == EVENTER.INFO_TYPE.POSITION: # positioninfo
            self.handle_position_info(info)
        elif info['t'] == EVENTER.INFO_TYPE.CHARGE: # chargeinfo
            self.handle_charge_info(info)
        else:
            pass

    def run_report(self):
        """Process the current report packet."""
        info = self.packet
        current_time = int(time.time())
        if info['timestamp'] > (current_time + 24*60*60):
            logging.info("[EVENTER] The info's (timestamp - current_time) is more than 24 hours, so drop it:%s", info)
            return

        self.handle_report_info(info) # reportinfo
        
    def get_regions(self, tid): 
        """Get all regions associated with the tid."""
        regions = self.db.query("SELECT tr.id AS region_id, tr.name AS region_name, "
                                "       tr.longitude AS region_longitude, tr.latitude AS region_latitude, "
                                "       tr.radius AS region_radius," 
                                "       tr.points, tr.shape AS region_shape"
                                "  FROM T_REGION tr, T_REGION_TERMINAL trt "
                                "  WHERE tr.id = trt.rid"
                                "  AND trt.tid = %s",
                                tid)
        if regions is None or len(regions) == 0:
            return []
        else:
            return regions

    def get_singles(self, tid): 
        """Get all singles associated with the tid."""
        singles  = self.db.query("SELECT ts.id AS single_id, ts.name AS single_name, "
                                "       ts.longitude AS single_longitude, ts.latitude AS single_latitude, "
                                "       ts.radius AS single_radius," 
                                "       ts.points, ts.shape AS single_shape"
                                "  FROM T_SINGLE ts, T_SINGLE_TERMINAL tst "
                                "  WHERE ts.id = tst.sid"
                                "  AND tst.tid = %s",
                                tid)
        if singles is None or len(singles) == 0:
            return []
        else:
            return singles

    def check_region_event(self, ori_location, region): 
        """Check enter or out region 

        workflow:
        get old_region_status accordinding to region and tid
        get old_region_time accordinding to region and tid
        check region_status according distance, then keep region_status in redis
        if not old_region_status:
            skip
        if old_region_time and location's gps_time <= old_region_time:
            skip
        check region event according to region_status and old_region_staus
        if region event:
            keep region_status, region_time in redis
        """
        if not (ori_location and region): 
            logging.info("[EVENTER] query data is invalid, ori_location: %s, region: %s, no check", 
                         ori_location, region)
            return None
        if not (ori_location['cLat'] and ori_location['cLon']):
            logging.info("[EVENTER] location is invalid, ori_location: %s, no check", 
                         ori_location)
            return None

        # BIG NOTE: python grammar, shallow copy will change origen data.
        location = copy.deepcopy(dict(ori_location))
        location = DotDict(location)

        old_region_status_key = get_region_status_key(location['dev_id'], region.region_id)
        old_region_status = self.redis.getvalue(old_region_status_key)

        old_region_time_key = get_region_time_key(location['dev_id'], region.region_id)
        old_region_time = self.redis.getvalue(old_region_time_key)

        if region.region_shape == UWEB.REGION_SHAPE.CIRCLE:
            # get distance beteween now location and the centre of the region 
            distance = lbmphelper.get_distance(region.region_longitude,
                                               region.region_latitude,
                                               location.cLon, 
                                               location.cLat)
            
            if distance >= region.region_radius:
                region_status = EVENTER.CATEGORY.REGION_OUT
                rname = EVENTER.RNAME.REGION_OUT
            else:
                region_status = EVENTER.CATEGORY.REGION_ENTER
                rname = EVENTER.RNAME.REGION_ENTER
        elif region.region_shape == UWEB.REGION_SHAPE.POLYGON:
            polygon = {'name':'',
                       'points':[]}
            points = region.points 
            point_lst = points.split(':') 
            for point in point_lst: 
               latlon = point.split(',') 
               dct = {'lat':float(latlon[0])/3600000, 
                      'lon':float(latlon[1])/3600000} 
               polygon['points'].append(dct)

            polygon['name'] = region.region_name

            if PtInPolygon(location, polygon):
                region_status = EVENTER.CATEGORY.REGION_ENTER
                rname = EVENTER.RNAME.REGION_ENTER
            else:
                region_status = EVENTER.CATEGORY.REGION_OUT
                rname = EVENTER.RNAME.REGION_OUT
        else: #NOTE: here should never occur. 
            logging.error("[EVENTER] unknow region_shape: %s, region: %s, skip it", 
                         region.region_shape, region)

        if old_region_time:
            if int(location['gps_time']) <= int(old_region_time):
                logging.info("[EVENTER] current location's gps_time: %s is not bigger than old_region_time: %s, skip it", 
                             location['gps_time'], old_region_time)
                return location
        
        # keep region status 
        self.redis.setvalue(old_region_status_key, region_status)
        logging.info("rname:%s, old status:%s, current status:%s, tid:%s",
                     safe_unicode(region.region_name), old_region_status, region_status, location['dev_id'])    

        if not old_region_status:
            logging.info("[EVENTER] old_region_status: %s is invalid, skip it", 
                         old_region_status)
            # skip the first region event
            return location

        # check region event
        if region_status != old_region_status:
            self.redis.setvalue(old_region_status_key, region_status)
            self.redis.setvalue(old_region_time_key, location['gps_time'])
            # 2: complete the location
            location['category'] = region_status
            location['t'] = EVENTER.INFO_TYPE.REPORT #NOTE: t is need
            location['rName'] = rname
            location['region'] = region 
            location['region_id'] = region.region_id

        return location

    def check_single_event(self, ori_location, single): 
        """Check enter or out single 

        workflow:
        get old_single_status accordinding to single and tid
        get old_single_time accordinding to single and tid
        check single_status according distance, then keep single_status in redis
        if not old_single_status:
            skip
        if old_single_time and location's gps_time <= old_region_time:
            skip
        check single event according to single_status and old_single_staus
        if single event:
            keep single_status, single_time in redis
        """
        if not (ori_location and single): 
            logging.info("[EVENTER] query data is invalid, ori_location: %s, single: %s, do not check.", 
                         ori_location, single)
            return None
        if not (ori_location['cLat'] and ori_location['cLon']):
            logging.info("[EVENTER] location is invalid, ori_location: %s, do not check.", 
                         ori_location)
            return None

        # BIG NOTE: python grammar, shallow copy will change origen data.
        location = copy.deepcopy(dict(ori_location))
        location = DotDict(location)

        old_single_status_key = get_single_status_key(location['dev_id'], single.single_id)
        old_single_status = self.redis.getvalue(old_single_status_key)

        old_single_time_key = get_single_time_key(location['dev_id'], single.single_id)
        old_single_time = self.redis.getvalue(old_single_time_key)

        if single.single_shape == UWEB.SINGLE_SHAPE.CIRCLE:
            # get distance beteween now location and the centre of the region 
            distance = lbmphelper.get_distance(single.single_longitude,
                                               single.single_latitude,
                                               location.cLon, 
                                               location.cLat)
            
            if distance >= single.single_radius:
                single_status = EVENTER.CATEGORY.SINGLE_OUT
                rname = EVENTER.RNAME.SINGLE_OUT
            else:
                single_status = EVENTER.CATEGORY.SINGLE_ENTER
                rname = EVENTER.RNAME.SINGLE_ENTER
        elif single.single_shape == UWEB.SINGLE_SHAPE.POLYGON:
            polygon = {'name':'',
                       'points':[]}
            points = single.points 
            point_lst = points.split(':') 
            for point in point_lst: 
               latlon = point.split(',') 
               dct = {'lat':float(latlon[0])/3600000, 
                      'lon':float(latlon[1])/3600000} 
               polygon['points'].append(dct)

            polygon['name'] = single.single_name

            if PtInPolygon(location, polygon):
                single_status = EVENTER.CATEGORY.SINGLE_ENTER
                rname = EVENTER.RNAME.SINGLE_ENTER
            else:
                single_status = EVENTER.CATEGORY.SINGLE_OUT
                rname = EVENTER.RNAME.SINGLE_OUT
        else: #NOTE: here should never occur. 
            logging.error("[EVENTER] unknow single_shape: %s, single: %s, skip it", 
                         single.single_shape, single)

        #NOTE: skip the time
        if old_single_time:
            if int(location['gps_time']) <= int(old_single_time):
                logging.info("[EVENTER] current location's gps_time: %s is not bigger than old_single_time: %s, skip it", 
                             location['gps_time'], old_single_time)
                return location
        
        logging.info('old_single_status_key: %s, single_status: %s', old_single_status_key, single_status)

        # keep region status 
        self.redis.setvalue(old_single_status_key, single_status)
        logging.info("rname:%s, old status:%s, current status:%s, tid:%s",
                     safe_unicode(single.single_name), old_single_status, single_status, location['dev_id'])    

        if not old_single_status:
            logging.info("[EVENTER] old_single_status: %s is invalid, skip it", 
                         old_single_status)
            # skip the first region event
            return location

        # check single event
        if single_status != old_single_status:
            self.redis.setvalue(old_single_status_key, single_status)
            self.redis.setvalue(old_single_time_key, location['gps_time'])

            # 2: complete the location
            location['category'] = single_status
            location['t'] = EVENTER.INFO_TYPE.REPORT #NOTE: t is need
            location['rName'] = rname
            location['single'] = single 
            location['single_id'] = single.single_id

            # 3. keep it in db
            # out first, then enter
            if single_status == EVENTER.CATEGORY.SINGLE_ENTER:
                single_event = self.db.get("SELECT id as seid, tid, sid, start_time, end_time" 
                                           "  FROM T_SINGLE_EVENT"
                                           "  WHERE tid = %s "
                                           "  AND sid = %s"
                                           "  AND start_time !=0"
                                           "  AND end_time = 0 "
                                           "  ORDER BY id DESC LIMIT 1",
                                           location['dev_id'],
                                           location['single_id'])

                if not single_event:
                    pass
                else:
                    self.db.execute("UPDATE T_SINGLE_EVENT"
                                    "  SET end_time = %s"
                                    "  WHERE id = %s",
                                    location['gps_time'],
                                    single_event['seid'])
            elif single_status == EVENTER.CATEGORY.SINGLE_OUT:
                last_pvt_key = get_last_pvt_key(location['dev_id'])
                last_pvt = self.redis.getvalue(last_pvt_key)
                if last_pvt:
                    gps_time = last_pvt['gps_time']
                else:
                    gps_time = location['gps_time']
                self.db.execute("INSERT INTO T_SINGLE_EVENT(tid, sid, start_time)" 
                                "  VALUES(%s, %s, %s)",
                                location['dev_id'], 
                                location['single_id'],
                                gps_time)
                
        return location

    def get_tname(self, dev_id):
        """Get alias of a terminal.
        It's deprecated now.
        """
        t = self.db.get("SELECT alias, mobile FROM T_TERMINAL_INFO"
                        "  WHERE tid = %s", dev_id)
        name = t.alias if t.alias else t.mobile 
        if isinstance(name, str):
            name = name.decode("utf-8")

        return name

    def realtime_location_hook(self, location):
        """Handle realtime.
        It's deprecated now.
        """
        insert_location(location, self.db, self.redis)

    def unknown_location_hook(self, location):
        """Now, just do nothing.
        """
        pass

    def update_terminal_info(self, location):
        """Update terminal's info in db and redis.
        """
        # db
        fields = []
        keys = ['gps', 'gsm', 'pbat', 'defend_status', 'login']
        for key in keys:
            if location.get(key, None) is not None:
                fields.append(key + " = " + str(location[key]))
        set_clause = ','.join(fields)
        if set_clause:
            self.db.execute("UPDATE T_TERMINAL_INFO"
                            "  SET " + set_clause +
                            "  WHERE tid = %s",
                            location.dev_id)
        # redis
        terminal_info = QueryHelper.get_terminal_info(location.dev_id,
                                                      self.db, self.redis)
        if terminal_info:
            terminal_info_key = get_terminal_info_key(location.dev_id)
            for key in terminal_info:
                value = location.get(key, None)
                if value is not None:
                    terminal_info[key] = value
            self.redis.setvalue(terminal_info_key, terminal_info)
    
    def handle_position_info(self, location):
        """Handle the info of position, include PVT(T11), CALL(T3)
        """
        location = DotDict(location)
        regions = self.get_regions(location['dev_id'])
        current_time = int(time.time())
        #NOTE: Now, it is seldom appears
        if location.Tid == EVENTER.TRIGGERID.CALL:
            if location['gps_time'] > (current_time + 24*60*60):
                logging.info("[EVENTER] The location's (gps_time - current_time) is more than 24 hours, so drop it:%s", location)
                return
            location = lbmphelper.handle_location(location, self.redis,
                                                  cellid=True, db=self.db) 
            ## check regions
            #for region in regions:
            #    region_location = self.check_region_event(location, region)
            #    if region_location and region_location['t'] == EVENTER.INFO_TYPE.REPORT:
            #        self.handle_report_info(region_location)

            location['category'] = EVENTER.CATEGORY.REALTIME
            self.update_terminal_info(location)
            if location.get('lat') and location.get('lon'):
                self.realtime_location_hook(location)

        # NOTE: For pvt(T11)
        elif location.Tid == EVENTER.TRIGGERID.PVT:
            #NOTE: get speed_limit  
            terminal = self.db.get("SELECT speed_limit "
                                   "  FROM T_TERMINAL_INFO "
                                   "  WHERE tid = %s AND group_id != -1",
                                   location['dev_id']) 
            speed_limit = terminal.get('speed_limit', '') if terminal else ''


            for pvt in location['pvts']:
                # The 'future time' is drop 
                if pvt['gps_time'] > (current_time + 24*60*60):
                    logging.info("[EVENTER] The location's (gps_time - current_time) is more than 24 hours, so drop it:%s", pvt)
                    continue

                # get available location from lbmphelper
                pvt['dev_id'] = location['dev_id']
                pvt['Tid'] = location['Tid']
                pvt['valid'] = GATEWAY.LOCATION_STATUS.SUCCESS
                pvt['type'] = 0 

                #self.handle_stop(pvt)
                #NOTE: handle stop 
                tid = pvt['dev_id']
                stop_key = get_stop_key(tid)
                stop = self.redis.getvalue(stop_key)

                distance_key = get_distance_key(tid)
                distance = self.redis.get(distance_key)
                if not distance:
                    distance = 0

                last_pvt_key = get_last_pvt_key(tid) 
                last_pvt = self.redis.getvalue(last_pvt_key)
                if last_pvt:
                    distance = float(distance) + lbmphelper.get_distance(int(last_pvt["lon"]), int(last_pvt["lat"]), 
                                             int(pvt["lon"]),
                                             int(pvt["lat"]))
                    self.redis.setvalue(distance_key, distance, time=EVENTER.STOP_EXPIRY)

                #NOTE: check region-event
                regions = self.get_regions(pvt['dev_id'])
                if regions:
                    pvt = lbmphelper.handle_location(pvt, self.redis,
                                                     cellid=True, db=self.db) 
                    for region in regions:
                        region_pvt= self.check_region_event(pvt, region)
                        if region_pvt and region_pvt['t'] == EVENTER.INFO_TYPE.REPORT:
                            self.handle_report_info(region_pvt)

                #NOTE: check single-event
                singles = self.get_singles(pvt['dev_id'])
                if singles:
                    pvt = lbmphelper.handle_location(pvt, self.redis,
                                                     cellid=True, db=self.db) 
                    for single in singles:
                        #NOTE: report about single may be need in future 
                        single_pvt = self.check_single_event(pvt, single)

                if pvt['speed'] > LIMIT.SPEED_LIMIT: # is moving
                    if stop: #NOTE: time_diff is too short, drop the point. 
                        if pvt["gps_time"] - stop['start_time'] < 60: # 60 seconds 
                            _stop = self.db.get("SELECT distance FROM T_STOP WHERE lid =%s", stop['lid'])
                            if _stop: 
                                tmp_dis = _stop['distance'] 
                            else: 
                                tmp_dis = 0 
                            distance = float(distance) + tmp_dis

                            self.db.execute("DELETE FROM T_STOP WHERE lid = %s",
                                            stop['lid'])
                            self.redis.delete(stop_key)
                            self.redis.setvalue(distance_key, distance, time=EVENTER.STOP_EXPIRY)
                            logging.info("[EVENTER] Stop point is droped: %s", stop)
                        else: # close a stop point
                            self.redis.delete(stop_key)
                            self.db.execute("UPDATE T_STOP SET end_time = %s WHERE lid = %s",
                                            pvt["gps_time"], stop['lid'])
                            logging.info("[EVENTER] Stop point is closed: %s", stop)
                    else:
                        pass
                else: # low speed, may stop
                    if stop: 
                        logging.info("[EVENTER] Stop point is updated: %s", stop)
                        stop['end_time'] = pvt["gps_time"]
                        self.redis.setvalue(stop_key, stop, time=EVENTER.STOP_EXPIRY)
                        logging.info("[EVENTER] Stop point is updated: %s", stop)
                    else: # create a new stop point
                        pvt = lbmphelper.handle_location(pvt, self.redis, cellid=True, db=self.db)
                        lid = insert_location(pvt, self.db, self.redis) 
                        stop = dict(lid=lid, 
                                    tid=tid, 
                                    start_time=pvt["gps_time"], 
                                    end_time=0, 
                                    pre_lon=pvt["lon"], 
                                    pre_lat=pvt["lat"], 
                                    distance=distance)

                        self.db.execute("INSERT INTO T_STOP(lid, tid, start_time, distance) VALUES(%s, %s, %s, %s)",
                                        lid, tid, pvt["gps_time"], distance)
                        self.redis.setvalue(stop_key, stop, time=EVENTER.STOP_EXPIRY)

                        self.redis.delete(distance_key)

                        logging.info("[EVENTER] Stop point is created: %s", stop)
                
                #NOTE: the time of keep last_pvt is import.
                last_pvt = pvt 
                self.redis.setvalue(last_pvt_key, last_pvt, time=EVENTER.STOP_EXPIRY)

                #NOTE: check the speed limit
                if speed_limit:
                    speed_limit_key = get_speed_limit_key(pvt['dev_id'])
                    if int(pvt['speed']) > speed_limit:
                        if self.redis.exists(speed_limit_key): 
                            logging.info("[EVENTER] speed_limit has reported, ignore it. pvt: %s", pvt) 
                            pass
                        else:
                            speed_pvt = lbmphelper.handle_location(pvt, self.redis, cellid=True, db=self.db) 
                            speed_pvt['category'] = EVENTER.CATEGORY.SPEED_LIMIT
                            speed_pvt['t'] = EVENTER.INFO_TYPE.REPORT #NOTE: t is need
                            speed_pvt['rName'] = EVENTER.RNAME.SPEED_LIMIT
                            self.handle_report_info(speed_pvt)
                            self.redis.setvalue(speed_limit_key, True, time=EVENTER.SPEED_LIMIT_EXPIRY)
                            logging.info("[EVENTER] speed_limit works, pvt: %s", speed_pvt) 
                    else: 
                        self.redis.delete(speed_limit_key)
                        logging.info("[EVENTER] speed_limit does not work, ignore it. pvt: %s", pvt) 
                else: 
                    logging.info("[EVENTER] speed_limit is closed, ignore it. pvt: %s", pvt) 

                # NOTE: not offset it
                #location = lbmphelper.handle_location(pvt, self.redis,
                #                                      cellid=False, db=self.db) 
                #NOTE: mileage
                pvt['category'] = EVENTER.CATEGORY.REALTIME
                if pvt.get('lat') and pvt.get('lon'): 
                    insert_location(pvt, self.db, self.redis)

                    #NOTE: record the mileage
                    mileage_key = get_mileage_key(pvt['dev_id'])
                    mileage = self.redis.getvalue(mileage_key)
                    if not mileage:
                        logging.info("[EVENTER] Tid: %s, init mileage. pvt: %s.",
                                      pvt['dev_id'], pvt)
                        mileage = dict(lat=pvt.get('lat'),
                                       lon=pvt.get('lon'),
                                       dis=0,
                                       gps_time=pvt['gps_time'])
                        self.redis.setvalue(mileage_key, mileage)
                    else:
                        if pvt['gps_time'] < mileage['gps_time']:
                            logging.info("[EVENTER] Tid: %s, gps_time: %s is less than mileage['gps_time']: %s, drop it. pvt: %s, mileage: %s", 
                                         pvt['dev_id'],
                                         pvt['gps_time'],
                                         mileage['gps_time'], 
                                         pvt, 
                                         mileage)
                            pass
                        else:
                            dis = lbmphelper.get_distance(int(mileage["lon"]), int(mileage["lat"]),  int(pvt["lon"]) , int(pvt["lat"]))

                            # for mileage notification
                            dis_current = mileage['dis'] +  dis 
                            self.db.execute("UPDATE T_TERMINAL_INFO" 
                                            "  SET distance_current = %s"
                                            "  WHERE tid = %s",
                                            dis_current, pvt['dev_id'])

                            logging.info("[EVENTER] Tid: %s, distance: %s. pvt: %s.",
                                          pvt['dev_id'], dis_current, pvt)

                            mileage = dict(lat=pvt.get('lat'),
                                           lon=pvt.get('lon'),
                                           dis=dis_current,
                                           gps_time=pvt['gps_time'])
                            self.redis.setvalue(mileage_key, mileage)

                            # for mileage junior statistic
                            current_day = time.localtime(pvt['gps_time']) 
                            day_start_time, day_end_time = start_end_of_day(current_day.tm_year, current_day.tm_mon, current_day.tm_mday)

                            mileage_log = self.db.get("SELECT * FROM T_MILEAGE_LOG"
                                                      "  WHERE tid = %s"
                                                      "  AND timestamp = %s",
                                                      pvt['dev_id'], day_end_time)
                            if mileage_log:
                                dis_day = mileage_log['distance'] + dis
                            else:
                                self.db.execute("INSERT INTO T_MILEAGE_LOG(tid, timestamp)"
                                                "  VALUES(%s, %s)",
                                                pvt['dev_id'], day_end_time)
                                dis_day = dis

                            self.db.execute("INSERT INTO T_MILEAGE_LOG(tid, distance, timestamp)"
                                            "  VALUES(%s, %s, %s)"
                                            "  ON DUPLICATE KEY"
                                            "  UPDATE distance=values(distance)",
                                            pvt['dev_id'], dis_day, day_end_time)
                            logging.info("[EVENTER] Tid: %s, dis_day: %s. pvt: %s.",
                                          pvt['dev_id'], dis_day, pvt)

                self.push_to_weixin(pvt) 
        else:
            location.category = EVENTER.CATEGORY.UNKNOWN
            self.unknown_location_hook(location)

    def handle_report_info(self, info):
        """These reports should be handled here:

        POWERLOW/POWERFULL/POWEROFF/POWERDOWN 
        ILLEGALMOVE
        ILLEGALSHAKE
        EMERGENCY
        REGION_ENTER
        REGION_OUT
        STOP
        SPEED_LIMIT
        """
        if not info:
            return
        # 1: get available location from lbmphelper 
        report = lbmphelper.handle_location(info, self.redis,
                                            cellid=True, db=self.db)

        if not (report['cLat'] and report['cLon']):
            #NOTE: Get latest location
            last_location = QueryHelper.get_location_info(report.dev_id, self.db, self.redis)
            if last_location:
                #NOTE: Try to make the location is complete.
                locations = [last_location,] 
                locations = lbmphelper.get_locations_with_clatlon(locations, self.db) 
                last_location = locations[0] 

                report['lat'] = last_location['latitude']
                report['lon'] = last_location['longitude']
                report['cLat'] = last_location['clatitude']
                report['cLon'] = last_location['clongitude']
                report['name'] = last_location['name']
                report['type'] = last_location['type']
                logging.info("[EVENTER] The report has invalid location and use last_location. report: %s", report)
            else:
                logging.info("[EVENTER] The report has invalid location and last_location is invalid. report: %s", report)

        current_time = int(time.time())

        #NOTE: bug fixed: in pvt, timestamp is no used, so use gps_time as timestamp
        if not report.get('timestamp',None):
            report['timestamp'] = report['gps_time']

        if report['timestamp'] > (current_time + 24*60*60):
            logging.info("[EVENTER] The report's (gps_time - current_time) is more than 24 hours, so drop it:%s", report)
            return


        #NOTE: If undefend, just save location into db
        if info['rName'] in [EVENTER.RNAME.ILLEGALMOVE, EVENTER.RNAME.ILLEGALSHAKE]:
            if str(info.get('is_notify','')) == '1': # send notify even if CF 
                logging.info("[EVENTER] Send notify forever, go ahead. Terminal: %s, is_notify: %s",
                             report.dev_id, info.get('is_notify',''))
            else:
                mannual_status = QueryHelper.get_mannual_status_by_tid(info['dev_id'], self.db)
                if int(mannual_status) == UWEB.DEFEND_STATUS.NO:
                    report['category'] = EVENTER.CATEGORY.REALTIME
                    insert_location(report, self.db, self.redis)
                    self.update_terminal_info(report)
                    logging.info("[EVENTER] %s mannual_status is undefend, drop %s report.",
                                 info['dev_id'], info['rName'])
                    return
            
        if info['rName'] in [EVENTER.RNAME.POWERDOWN,]:
            # if alert_freq_key is exists,return
            alert_freq_key = get_alert_freq_key(report.dev_id + info['rName'])
            alert_freq = QueryHelper.get_alert_freq_by_tid(info['dev_id'], self.db)
            if alert_freq != 0:
                if self.redis.exists(alert_freq_key):
                    logging.info("[EVENTER] Don't send duplicate %s alert to terminal:%s in %s seconds", info["rName"], report.dev_id, alert_freq)
                    return
                else:
                    self.redis.setvalue(alert_freq_key, 1, time=alert_freq)

        # keep alarm info
        alarm = dict(tid=report['dev_id'],
                     category=report['category'], 
                     type=report['type'], 
                     timestamp=report.get('timestamp',0),
                     latitude=report.get('lat',0),
                     longitude=report.get('lon',0),
                     clatitude=report.get('cLat',0),
                     clongitude=report.get('cLon',0),
                     name=report['name'] if report.get('name',None) is not None else '',
                     degree=report.get('degree',0),
                     speed=report.get('speed',0))


        if info['rName'] in [EVENTER.RNAME.REGION_OUT, EVENTER.RNAME.REGION_ENTER]:
            region = report['region']
            alarm['region_id'] = region.region_id

        self.record_alarm_info(alarm)

        # 2:  save into database. T_LOCATION, T_EVENT
        lid = insert_location(report, self.db, self.redis)
        self.update_terminal_info(report)
        self.event_hook(report.category, report.dev_id, report.get('terminal_type',1), report.get('timestamp'), lid, report.pbat, report.get('fobid'), report.get('region_id', -1))

        # 3: notify the owner 
        user = QueryHelper.get_user_by_tid(report.dev_id, self.db) 
        if not user:
            logging.error("[EVENTER] Cannot find USER of terminal: %s", report.dev_id)
            return
        
        # send sms to owner
        if report.rName in [EVENTER.RNAME.STOP]:
            logging.info("[EVENTER] %s alert needn't to push to user. Terminal: %s",
                         report.rName, report.dev_id)
            return
            
        #NOTE: check sms option
        sms_option = self.get_sms_option(user.owner_mobile, EVENTER.SMS_CATEGORY[report.rName].lower())
        name = QueryHelper.get_alias_by_tid(report.dev_id, self.redis, self.db)
        if sms_option == UWEB.SMS_OPTION.SEND:
            terminal_time = get_terminal_time(int(report['timestamp']))
            terminal_time = safe_unicode(terminal_time) 

            report_name = report.name
            if not report_name:
                if report.cLon and report.cLat:
                    report_name = ErrorCode.ERROR_MESSAGE[ErrorCode.LOCATION_NAME_NONE]
                else:
                    report_name = ErrorCode.ERROR_MESSAGE[ErrorCode.LOCATION_FAILED]
            sms = '' 
            sms_white = '' 
            if isinstance(report_name, str):
                report_name = report_name.decode('utf-8')
                report_name = unicode(report_name)

            if report.rName == EVENTER.RNAME.POWERLOW:
                if report.terminal_type == "1": # type: terminal
                    if int(report.pbat) == 100:
                        pbat_message_key = get_pbat_message_key(report.dev_id)
                        if self.redis.exists(pbat_message_key) is False:
                            self.redis.setvalue(pbat_message_key, 1, time=24*60*60)        
                        else:
                            logging.info("[EVENTER] Don't send duplicate power full message to terminal:%s in 24 hours", report.dev_id)
                            return
                    elif int(report.pbat) > 20 and int(report.pbat) < 100:
                        logging.info("[EVENTER] Terminal:%s reported power low pbat:%s between 20% and 100%, so skip it", report.dev_id, report.pbat)
                        return
                    sms = self.handle_power_status(report, name, report_name, terminal_time)
                else: # type: fob
                    sms = SMSCode.SMS_FOB_POWERLOW % (report.fobid, terminal_time)
            elif report.rName == EVENTER.RNAME.ILLEGALMOVE:
                if report_name in [ErrorCode.ERROR_MESSAGE[ErrorCode.LOCATION_NAME_NONE], ErrorCode.ERROR_MESSAGE[ErrorCode.LOCATION_FAILED]]:
                    sms = SMSCode.SMS_ILLEGALMOVE_NOLOC % (name, terminal_time)
                else:
                    sms = SMSCode.SMS_ILLEGALMOVE % (name, report_name, terminal_time)


                _date = datetime.datetime.fromtimestamp(int(report['timestamp']))
                _seconds = _date.hour * 60 * 60 + _date.minute * 60 + _date.second 
                if _seconds < 7 * 60 * 60 or _seconds > 19 * 60 * 60:  
                    _resend_alarm = functools.partial(self.sms_to_user, report.dev_id, sms+u"重复提醒，如已收到，请忽略。", user)
                    #NOTE: re-notify
                    # 30 seconds later, send sms 1 time.
                    task = RepeatedTimer(30, _resend_alarm, 1)  
                    task.start()
            elif report.rName == EVENTER.RNAME.ILLEGALSHAKE:
                if report_name in [ErrorCode.ERROR_MESSAGE[ErrorCode.LOCATION_NAME_NONE], ErrorCode.ERROR_MESSAGE[ErrorCode.LOCATION_FAILED]]:
                    sms = SMSCode.SMS_ILLEGALSHAKE_NOLOC % (name, terminal_time)
                else:
                    sms = SMSCode.SMS_ILLEGALSHAKE % (name, report_name, terminal_time)

                #NOTE: re-notify
                _date = datetime.datetime.fromtimestamp(int(report['timestamp']))
                _seconds = _date.hour * 60 * 60 + _date.minute * 60 + _date.second 
                if _seconds < 7 * 60 * 60 or _seconds > 19 * 60 * 60:  
                    _resend_alarm = functools.partial(self.sms_to_user, report.dev_id, sms+u"此条短信为重复提醒，请注意您的车辆状态。", user)
                    # 30 seconds later, send sms 1 time.
                    task = RepeatedTimer(30, _resend_alarm, 1)  
                    task.start()
                
            elif report.rName == EVENTER.RNAME.EMERGENCY:
                whitelist = QueryHelper.get_white_list_by_tid(report.dev_id, self.db)      
                if whitelist:
                    white_str = ','.join(white['mobile'] for white in whitelist) 

                    if report_name in [ErrorCode.ERROR_MESSAGE[ErrorCode.LOCATION_NAME_NONE], ErrorCode.ERROR_MESSAGE[ErrorCode.LOCATION_FAILED]]:
                        sms = SMSCode.SMS_SOS_OWNER_NOLOC % (name, white_str, terminal_time)
                        sms_white = SMSCode.SMS_SOS_WHITE_NOLOC % (name, terminal_time) 
                    else:
                        sms = SMSCode.SMS_SOS_OWNER % (name, white_str, report_name, terminal_time)
                        sms_white = SMSCode.SMS_SOS_WHITE % (name, report_name, terminal_time) 
                else:
                    if report_name in [ErrorCode.ERROR_MESSAGE[ErrorCode.LOCATION_NAME_NONE], ErrorCode.ERROR_MESSAGE[ErrorCode.LOCATION_FAILED]]:
                        sms = SMSCode.SMS_SOS_NOLOC % (name, terminal_time)
                    else:
                        sms = SMSCode.SMS_SOS % (name, report_name, terminal_time)
            elif report.rName == EVENTER.RNAME.POWERDOWN:
                if report_name in [ErrorCode.ERROR_MESSAGE[ErrorCode.LOCATION_NAME_NONE], ErrorCode.ERROR_MESSAGE[ErrorCode.LOCATION_FAILED]]:
                    sms = SMSCode.SMS_POWERDOWN_NOLOC % (name, terminal_time)
                else:
                    sms = SMSCode.SMS_POWERDOWN % (name, report_name, terminal_time)
            elif report.rName == EVENTER.RNAME.REGION_OUT:
                if report_name in [ErrorCode.ERROR_MESSAGE[ErrorCode.LOCATION_NAME_NONE], ErrorCode.ERROR_MESSAGE[ErrorCode.LOCATION_FAILED]]:
                    sms = SMSCode.SMS_REGION_OUT_NOLOC % (name, safe_unicode(report['region']['region_name']), terminal_time)
                else:
                    sms = SMSCode.SMS_REGION_OUT % (name,  safe_unicode(report['region']['region_name']), report_name, terminal_time)
            elif report.rName == EVENTER.RNAME.REGION_ENTER:
                if report_name in [ErrorCode.ERROR_MESSAGE[ErrorCode.LOCATION_NAME_NONE], ErrorCode.ERROR_MESSAGE[ErrorCode.LOCATION_FAILED]]:
                    sms = SMSCode.SMS_REGION_ENTER_NOLOC % (name, safe_unicode(report['region']['region_name']), terminal_time)
                else:
                    sms = SMSCode.SMS_REGION_ENTER % (name, safe_unicode(report['region']['region_name']), report_name, terminal_time)
            elif report.rName == EVENTER.RNAME.SPEED_LIMIT:
                 sms_dct = dict(name=name,
                                report_name=report_name,
                                speed=int(report.get('speed',0)),
                                terminal_time=terminal_time)
                 if report_name in [ErrorCode.ERROR_MESSAGE[ErrorCode.LOCATION_NAME_NONE], ErrorCode.ERROR_MESSAGE[ErrorCode.LOCATION_FAILED]]:
                     sms = SMSCode.SMS_SPEED_LIMIT_NOLOC % sms_dct 
                 else:
                     sms = SMSCode.SMS_SPEED_LIMIT % sms_dct 
            else:
                pass

            #wap_url = 'http://api.map.baidu.com/staticimage?center=%s,%s%26width=800%26height=800%26zoom=17%26markers=%s,%s'
            #wap_url = wap_url % (report.lon/3600000.0, report.lat/3600000.0, report.lon/3600000.0, report.lat/3600000.0)
            #wap_url = 'http://api.map.baidu.com/staticimage?center=' +\
            #          str(report.cLon/3600000.0) + ',' + str(report.cLat/3600000.0) +\
            #          '&width=320&height=480&zoom=17&markers=' +\
            #          str(report.cLon/3600000.0) + ',' + str(report.cLat/3600000.0) 
            if report.cLon and report.cLat:
                clon = '%0.3f' % (report.cLon/3600000.0) 
                clat = '%0.3f' % (report.cLat/3600000.0)
                url = ConfHelper.UWEB_CONF.url_out + '/wapimg?clon=' + clon + '&clat=' + clat 
                tiny_id = URLHelper.get_tinyid(url)
                if tiny_id:
                    base_url = ConfHelper.UWEB_CONF.url_out + UWebHelper.URLS.TINYURL
                    tiny_url = base_url + '/' + tiny_id
                    logging.info("[EVENTER] get tiny url successfully. tiny_url:%s", tiny_url)
                    self.redis.setvalue(tiny_id, url, time=EVENTER.TINYURL_EXPIRY)
                    sms += u"点击" + tiny_url + u" 查看定位器位置。" 
                    if sms_white:
                        sms_white += u"点击" + tiny_url + u" 查看定位器位置。"
                        self.sms_to_whitelist(sms_white, whitelist)
                else:
                    logging.info("[EVENTER] get tiny url failed.")
            else:
                logging.info("[EVENTER] location failed.")
            self.sms_to_user(report.dev_id, sms, user)
            #if report.rName == EVENTER.RNAME.POWERLOW:
            #    corp = self.db.get("SELECT T_CORP.mobile FROM T_CORP, T_GROUP, T_TERMINAL_INFO"
            #                       "  WHERE T_TERMINAL_INFO.tid = %s"
            #                       "    AND T_TERMINAL_INFO.group_id != -1"
            #                       "    AND T_TERMINAL_INFO.group_id = T_GROUP.id"
            #                       "    AND T_GROUP.corp_id = T_CORP.cid",
            #                       report.dev_id)
            #    if (corp and corp.mobile != user.owner_mobile):
            #        SMSHelper.send(corp.mobile, sms)
        else:
            logging.info("[EVENTER] Remind option of %s is closed. Terminal: %s",
                         report.rName, report.dev_id)
         
        #NOTE: push to owner
        report.comment = ''
        region_id = None
        if report.rName == EVENTER.RNAME.POWERLOW:
            if report.terminal_type == "1":
                if int(report.pbat) == 100:
                    report.comment = ErrorCode.ERROR_MESSAGE[ErrorCode.TRACKER_POWER_FULL] 
                elif int(report.pbat) <= 5:
                    report.comment = ErrorCode.ERROR_MESSAGE[ErrorCode.TRACKER_POWER_OFF]
                else:
                    if int(report.pbat) <= 20:
                        report.comment = (ErrorCode.ERROR_MESSAGE[ErrorCode.TRACKER_POWER_LOW]) % report.pbat
            else:
                report.comment = ErrorCode.ERROR_MESSAGE[ErrorCode.FOB_POWER_LOW] % report.fobid
        elif report.rName in (EVENTER.RNAME.REGION_ENTER, EVENTER.RNAME.REGION_OUT):
            region = report['region']
            region_id = region.region_id
            if region.get('region_name', None): 
                region.comment = u"围栏名：%s" % safe_unicode(region.region_name)

        # push to client
        terminal = self.db.get("SELECT push_status FROM T_TERMINAL_INFO"
                               "  WHERE tid = %s", report.dev_id)
        if terminal and terminal.push_status == 1:
            if report.rName == EVENTER.RNAME.STOP:
                logging.info("[EVENTER] %s altert needn't to push to user. Terminal: %s",
                             report.rName, report.dev_id)
            else:
                self.notify_to_parents(name, report, user, region_id) 
                if report.rName in [EVENTER.RNAME.ILLEGALMOVE, EVENTER.RNAME.ILLEGALSHAKE]: 

                    _date = datetime.datetime.fromtimestamp(int(report['timestamp']))
                    _seconds = _date.hour * 60 * 60 + _date.minute * 60 + _date.second 
                    if _seconds < 7 * 60 * 60 or _seconds > 19 * 60 * 60:  
                        _resend_alarm = functools.partial(self.notify_to_parents, name, report, user, region_id) 
                        # 30 seconds later, send sms 1 time.  
                        task = RepeatedTimer(30, _resend_alarm, 1) 
                        task.start()
        else:
            logging.info("[EVENTER] Push option of %s is closed. Terminal: %s",
                         report.rName, report.dev_id)
        self.push_to_weixin(report) 


    def event_hook(self, category, dev_id, terminal_type, timestamp, lid, pbat=None, fobid=None , rid=None):
        self.db.execute("INSERT INTO T_EVENT(tid, terminal_type, timestamp, fobid, lid, pbat, category, rid)"
                        "  VALUES (%s, %s,  %s, %s, %s, %s, %s, %s)",
                        dev_id, terminal_type, timestamp, fobid, lid, pbat, category, rid)

    def get_sms_option(self, uid, category):
        sms_option = self.db.get("SELECT " + category +
                                 "  FROM T_SMS_OPTION"
                                 "  WHERE uid = %s",
                                 uid)

        return sms_option[category]

    def handle_charge_info(self, info):
        info = DotDict(info)
        self.db.execute("INSERT INTO T_CHARGE"
                        "  VALUES (NULL, %s, %s, %s)",
                        info.dev_id, info.content, info.timestamp)
        user = QueryHelper.get_user_by_tid(info.dev_id, self.db) 
        if not user:
            logging.error("[EVENTER] Cannot find USER of terminal: %s", info.dev_id)
            return
            
        sms_option = self.get_sms_option(user.owner_mobile, EVENTER.SMS_CATEGORY.CHARGE.lower())
        if sms_option == UWEB.SMS_OPTION.SEND:
            logging.error("[EVENTER] do not send charge sms temporarily")
            #name = QueryHelper.get_alias_by_tid(info.dev_id, self.redis, self.db)
            #terminal_time = get_terminal_time(int(info.timestamp))
            #sms = SMSCode.SMS_CHARGE % (name, info.content)
            #self.sms_to_user(info.dev_id, sms, user)

    def sms_to_user(self, dev_id, sms, user=None):
        if not sms:
            return

        if not user:
            user = QueryHelper.get_user_by_tid(dev_id, self.db) 

        if user:
            SMSHelper.send(user.owner_mobile, sms)

    def sms_to_whitelist(self, sms, whitelist=None):
        if not sms:
            return

        if whitelist:
            for white in whitelist:
                SMSHelper.send(white['mobile'], sms)


    def notify_to_parents(self, alias, location, user, region_id=None):
        """Push information to clinet through push.

        PUSH 1.0
        """
        category = location.category
        dev_id = location.dev_id

        if not location['pbat']:
            terminal = QueryHelper.get_terminal_info(dev_id, self.db, self.redis) 
            location['pbat'] = terminal['pbat'] if terminal['pbat'] is not None else 0 

        if not user:
            user = QueryHelper.get_user_by_tid(dev_id, self.db)

        if user:
            # 1: push to android
            android_push_list_key = get_android_push_list_key(user.owner_mobile) 
            android_push_list = self.redis.getvalue(android_push_list_key) 
            if android_push_list: 
                for push_id in android_push_list: 
                    push_key = NotifyHelper.get_push_key(push_id, self.redis) 
                    NotifyHelper.push_to_android(category, dev_id, alias, location, push_id, push_key, region_id)
            # 2: push  to ios 
            ios_push_list_key = get_ios_push_list_key(user.owner_mobile) 
            ios_push_list = self.redis.getvalue(ios_push_list_key) 
            if ios_push_list: 
                for ios_id in ios_push_list: 
                    ios_badge = NotifyHelper.get_iosbadge(ios_id, self.redis) 
                    NotifyHelper.push_to_ios(category, dev_id, alias, location, ios_id, ios_badge, region_id)


    def push_to_weixin(self, location):
        """Push information to weixin.
        """
        tid = location['dev_id']
        terminal = QueryHelper.get_terminal_info(tid, self.db, self.redis)
        body = dict(tid=tid,
                    category=location['category'], 
                    type=location['type'], 
                    timestamp=location.get('timestamp',0),
                    latitude=location.get('lat',0),
                    longitude=location.get('lon',0),
                    clatitude=location.get('cLat',0),
                    clongitude=location.get('cLon',0),
                    name=location['name'] if location.get('name',None) is not None else '',
                    degree=location.get('degree',0),
                    speed=location.get('speed',0),
                    locate_error=location.get('locate_error',0),
                    region_id=location.get('region_id',-1),
                    # for terminal
                    alias=terminal.get('alias'),
                    gps=terminal.get('gps'),
                    gsm=terminal.get('gsm'),
                    pbat=terminal.get('pbat'))

        WeixinPushHelper.push(tid, body, self.db, self.redis)

    def handle_power_status(self, report, name, report_name, terminal_time):
        """
        1: 100 --> power_full
        2: (5,100) --> power_low
        3: [0,5] --> power_off
        """
        sms = None
        if int(report.pbat) == 100:
            sms = SMSCode.SMS_POWERFULL % name 
        elif int(report.pbat) <= 5:
            t_time = int(time.time())
            self.db.execute("INSERT INTO T_POWEROFF_TIMEOUT"
                            "  VALUES(NULL, %s, %s, %s)"
                            "  ON DUPLICATE KEY"
                            "  UPDATE tid = VALUES(tid),"
                            "         sms_flag = VALUES(sms_flag),"
                            "         timestamp = VALUES(timestamp)",
                            report.dev_id, GATEWAY.POWEROFF_TIMEOUT_SMS.UNSEND, t_time)
            if report_name in [ErrorCode.ERROR_MESSAGE[ErrorCode.LOCATION_NAME_NONE], ErrorCode.ERROR_MESSAGE[ErrorCode.LOCATION_FAILED]]:
                sms = SMSCode.SMS_POWERLOW_OFF_NOLOC % (name, terminal_time)
            else: 
                sms = SMSCode.SMS_POWERLOW_OFF % (name, report_name, terminal_time)
        else:
            if report_name in [ErrorCode.ERROR_MESSAGE[ErrorCode.LOCATION_NAME_NONE], ErrorCode.ERROR_MESSAGE[ErrorCode.LOCATION_FAILED]]:
                sms = SMSCode.SMS_TRACKER_POWERLOW_NOLOC % (name, int(report.pbat), terminal_time)
            else:
                sms = SMSCode.SMS_TRACKER_POWERLOW % (name, int(report.pbat), report_name, terminal_time)

        return sms

    def record_alarm_info(self, alarm):
        """Record the alarm info in the redis.
        tid --> alarm_info:[
                             {
                               keeptime // keep alarm's keeptime when kept in reids, not timestamp alarm occurs
                               type, 
                               category,
                               latitude,
                               longitude, 
                               clatitude,
                               clongitude,
                               timestamp,
                               name,
                               degree, 
                               speed,
                               # for regions
                               region_id,
                             },
                             ...
                           ]
        alarm_info is a list with one or many alarms.
        """
        alarm_info_key = get_alarm_info_key(alarm['tid'])
        alarm_info = self.redis.getvalue(alarm_info_key)
        alarm_info = alarm_info if alarm_info else []
        alarm['keeptime'] = int(time.time())
        alarm_info.append(alarm)

        #NOTE: only store the alarm during past 10 minutes.
        alarm_info_new = []
        for alarm in alarm_info:
            if alarm.get('keeptime', None) is None:
                alarm['keeptime'] = alarm['timestamp']

            if alarm['keeptime'] + 60*10 < int(time.time()):
                pass
            else:
                alarm_info_new.append(alarm)

        #logging.info("[EVENTER] keep alarm_info_key: %s,  alarm_info: %s in redis.", alarm_info_key,  alarm_info)
        self.redis.setvalue(alarm_info_key, alarm_info_new, EVENTER.ALARM_EXPIRY)
