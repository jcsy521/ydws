# -*- coding: utf-8 -*-

import logging

from tornado.escape import json_decode

from helpers.smshelper import SMSHelper
from helpers.queryhelper import QueryHelper
from helpers import lbmphelper
from helpers import notifyhelper

from utils.dotdict import DotDict
from utils.misc import get_name_cache_key, get_terminal_time,\
     get_ssdw_sms_key
from codes.smscode import SMSCode
from codes.errorcode import ErrorCode 
from codes.clwcode import CLWCode
from constants import EVENTER
from constants.MEMCACHED import ALIVED


class PacketTask(object):
    
    def __init__(self, packet, db, memcached):
        self.packet = packet
        self.db = db
        self.memcached = memcached

    def run(self):
        """Process the current packet."""

        info = json_decode(self.packet)
        
        if info['t'] == EVENTER.INFO_TYPE.POSITION: # positioninfo:
            self.handle_position_info(info)
        elif info['t'] == EVENTER.INFO_TYPE.REPORT: # reportinfo:
            self.handle_report_info(info)
        elif info['t'] == EVENTER.INFO_TYPE.STATISTICS: # statisticsinfo:
            self.handle_statistics_info(info)
        else:
            pass       

    def get_tname(self, dev_id):
        key = get_name_cache_key(dev_id)
        name = self.memcached.get(key)
        name = name if name else dev_id
        return name or  ""

    def insert_location(self, location):
        # insert data into T_LOCATION
        lid = self.db.execute("INSERT INTO T_LOCATION"
                              "  VALUES (NULL, %s, %s, %s, %s, %s, %s, %s,"
                              "          %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                              location.dev_id, location.lat, location.lon, 
                              location.alt, location.cLat, location.cLon,
                              location.timestamp, location.name,
                              location.category, location.type,
                              location.speed, location.volume,
                              location.degree, location.status,
                              location.cellid, location.gps, location.gsm)
        is_alived = self.memcached.get('is_alived')
        if (is_alived == ALIVED and location.valid == CLWCode.LOCATION_SUCCESS):
            mem_location = DotDict({'id':lid,
                                    'latitude':location.lat,
                                    'longitude':location.lon,
                                    'type':location.type,
                                    'clatitude':location.cLat,
                                    'clongitude':location.cLon,
                                    'timestamp':location.timestamp,
                                    'name':location.name,
                                    'degree':location.degree,
                                    'speed':location.speed})
            self.memcached.set(str(location.dev_id), mem_location, EVENTER.LOCATION_EXPIRY)
        return lid
        
    def realtime_location_hook(self, location):

        r_location = lbmphelper.handle_location(location, self.memcached)
        if r_location:
            for key in ['lon', 'lat', 'cLon', 'cLat', 'name', 'type']:
                location[key] = r_location[key]
        self.insert_location(location)
        key = get_ssdw_sms_key(location.dev_id)                          
        flag = self.memcached.get(key)
        if flag:
            location.name = location.name or ErrorCode.ERROR_MESSAGE[ErrorCode.LOCATION_NAME_NONE]

            # send sms to parents if they are realtime (from sms) query
            sms = SMSCode.SMS_REALTIME_RESULT % (self.get_tname(location.dev_id), 
                                                 location.name,
                                                 get_terminal_time(int(location.timestamp)))
            self.sms_to_parents(location.dev_id, sms)
            self.memcached.delete(key)

    def unknown_location_hook(self, location):
        pass
    
    def handle_position_info(self, location):
        location = DotDict(location)
         
        if location.valid == CLWCode.LOCATION_SUCCESS: 
            location.type = 0
        else:
            location.lon = 0
            location.lat = 0
            location.cLon = 0
            location.cLat = 0
            location.type = 1

        if location.Tid == EVENTER.TRIGGERID.CALL:
            location.category = EVENTER.CATEGORY.REALTIME
            self.realtime_location_hook(location)
        else:
            location.category = EVENTER.CATEGORY.UNKNOWN
            self.unknown_location_hook(location)

    def handle_report_info(self, info):
        """These reports should be handled here:
        POWERLOW
        POWEROFF
        REGION_OUT
        ILLEGALMOVE
        SPEED_OUT
        HEARTBEAT_LOST
        """
        report = DotDict(info)
        name = self.get_tname(report.dev_id)
        terminal_time = get_terminal_time(int(report.timestamp))

        if report.valid == CLWCode.LOCATION_SUCCESS: 
            report.type = 0
        else:
            report.lon = 0
            report.lat = 0
            report.cLon = 0
            report.cLat = 0
            report.type = 1
        # get available location from lbmphelper 
        location = lbmphelper.handle_location(report, self.memcached)
        if location:
            for key in ['lat', 'lon', 'cLat', 'cLon', 'name', 'type', 'category']:
                    report[key] = location[key]
        report_name = report.name or ErrorCode.ERROR_MESSAGE[ErrorCode.LOCATION_NAME_NONE]
        sms = None

        if report.rName == EVENTER.RNAME.POWEROFF:
            sms = SMSCode.SMS_POWEROFF % (name, report_name, terminal_time)
        elif report.rName == EVENTER.RNAME.POWERLOW:
            sms = SMSCode.SMS_POWERLOW % (name, report.volume, terminal_time)
        elif report.rName == EVENTER.RNAME.REGION_OUT:
            sms = SMSCode.SMS_REGION_OUT % (name, report_name, terminal_time)
        elif report.rName == EVENTER.RNAME.SPEED_OUT:
            sms = SMSCode.SMS_SPEED_OUT % (name, report_name, terminal_time)
        elif report.rName == EVENTER.RNAME.ILLEGALMOVE:
            sms = SMSCode.SMS_ILLEGALMOVE % (name, report_name, terminal_time)
        elif report.rName == EVENTER.RNAME.HEARTBEAT_LOST:
            sms = SMSCode.SMS_HEARTBEAT_LOST % (name, terminal_time)
        else:
            pass

        lid = self.insert_location(report)

        if report.category != EVENTER.CATEGORY.UNKNOWN:
            self.event_hook(report.category, report.dev_id, lid)
            self.sms_to_parents(report.dev_id, sms)
            self.notify_to_parents(report.category, report.dev_id, location)
            

    def event_hook(self, category, dev_id, lid):
        self.db.execute("INSERT INTO T_EVENT"
                        "  VALUES (NULL, %s, %s, %s)",
                        dev_id, lid, category)

    def handle_statistics_info(self, info):
        info = DotDict(info)
        if info.STATISTICS == EVENTER.STATISTICS.MILEAGE:
            self.db.execute("INSERT INTO T_STATISTICS_MILEAGE"
                            "  VALUES (NULL, %s, %s, %s)",
                            info.dev_id, info.mileage, info.timestamp)
        else:
            pass

    def sms_to_parents(self, dev_id, sms):
        if not sms:
            return

        user = QueryHelper.get_umobile_by_dev_id(dev_id, self.db) 
        if user:
            SMSHelper.send(user.owner_mobile, sms)


    def notify_to_parents(self, category, dev_id, location):
        # NOtE: if user is not null, notify android
        user = QueryHelper.get_user_by_tid(dev_id, self.db)
        if user:
            notifyhelper.push_to_android(category, user.uid, dev_id, location)      
