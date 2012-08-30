# -*- coding: utf-8 -*-

import logging

from tornado.escape import json_decode

from helpers.smshelper import SMSHelper
from helpers.queryhelper import QueryHelper
from helpers import lbmphelper
from helpers import notifyhelper

from utils.dotdict import DotDict
from utils.misc import get_terminal_time,\
     get_ssdw_sms_key
from codes.smscode import SMSCode
from codes.errorcode import ErrorCode 
from constants import EVENTER, GATEWAY
from constants.MEMCACHED import ALIVED


class PacketTask(object):
    
    def __init__(self, packet, db, redis):
        self.packet = packet
        self.db = db
        self.redis = redis

    def run(self):
        """Process the current packet."""

        info = json_decode(self.packet)
        
        if info['t'] == EVENTER.INFO_TYPE.POSITION: # positioninfo:
            self.handle_position_info(info)
        elif info['t'] == EVENTER.INFO_TYPE.REPORT: # reportinfo:
            self.handle_report_info(info)
        elif info['t'] == EVENTER.INFO_TYPE.CHARGE: # chargeinfo:
            self.handle_charge_info(info)
        else:
            pass       

    def get_tname(self, dev_id):
        key = get_alias_key(dev_id)
        name = self.redis.getvalue(key)
        if not name:
            t = self.db.get("SELECT alias, mobile FROM T_TERMINAL_INFO"
                            "  WHERE tid = %s", dev_id)
            name = t.alias if t.alias else t.mobile 
            self.redis.setvalue(key, name)
        if isinstance(name, str):
            name = name.decode("utf-8")

        return name

    def insert_location(self, location):
        # insert data into T_LOCATION
        lid = self.db.execute("INSERT INTO T_LOCATION"
                              "  VALUES (NULL, %s, %s, %s, %s, %s, %s, %s,"
                              "          %s, %s, %s, %s, %s, %s)",
                              location.dev_id, location.lat, location.lon, 
                              location.alt, location.cLat, location.cLon,
                              location.gps_time, location.name,
                              location.category, location.type,
                              location.speed, location.degree,
                              location.cellid)
        is_alived = self.redis.getvalue('is_alived')
        if (is_alived == ALIVED and location.valid == GATEWAY.LOCATION_STATUS.SUCCESS):
            mem_location = DotDict({'id':lid,
                                    'latitude':location.lat,
                                    'longitude':location.lon,
                                    'type':location.type,
                                    'clatitude':location.cLat,
                                    'clongitude':location.cLon,
                                    'timestamp':location.gps_time,
                                    'name':location.name,
                                    'degree':location.degree,
                                    'speed':location.speed})
            self.redis.setvalue(str(location.dev_id), mem_location, EVENTER.LOCATION_EXPIRY)
        return lid
        
    def realtime_location_hook(self, location):
        self.insert_location(location)
        key = get_ssdw_sms_key(location.dev_id)                          
        flag = self.redis.getvalue(key)
        if flag:
            location.name = location.name or ErrorCode.ERROR_MESSAGE[ErrorCode.LOCATION_NAME_NONE]

            # send sms to parents if they are realtime (from sms) query
            sms = SMSCode.SMS_REALTIME_RESULT % (self.get_tname(location.dev_id), 
                                                 location.name,
                                                 get_terminal_time(int(location.timestamp)))
            self.sms_to_user(location.dev_id, sms)
            self.redis.delete(key)

    def unknown_location_hook(self, location):
        pass

    def update_terminal_status(self, location):
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
    
    def handle_position_info(self, location):
        location = DotDict(location)
        if location.Tid == EVENTER.TRIGGERID.CALL:
            # get available location from lbmphelper
            location = lbmphelper.handle_location(location, self.redis,
                                                  cellid=False, db=self.db) 
            location.category = EVENTER.CATEGORY.REALTIME
            self.update_terminal_status(location)
            if location.valid == GATEWAY.LOCATION_STATUS.SUCCESS:
                self.realtime_location_hook(location)
        elif location.Tid == EVENTER.TRIGGERID.PVT:
            for pvt in location['pvts']:
                # get available location from lbmphelper
                pvt['dev_id'] = location['dev_id']
                location = lbmphelper.handle_location(pvt, self.redis,
                                                      cellid=False, db=self.db) 
                location.category = EVENTER.CATEGORY.REALTIME
                self.insert_location(location)
        else:
            location.category = EVENTER.CATEGORY.UNKNOWN
            self.unknown_location_hook(location)

    def handle_report_info(self, info):
        """These reports should be handled here:
        POWERLOW
        POWEROFF
        ILLEGALMOVE
        HEARTBEAT_LOST
        EMERGENCY

        CHARGE
        """
        # get available location from lbmphelper 
        report = lbmphelper.handle_location(info, self.redis,
                                            cellid=False, db=self.db)
        name = self.get_tname(report.dev_id)
        terminal_time = get_terminal_time(int(report.gps_time))

        report_name = report.name or ErrorCode.ERROR_MESSAGE[ErrorCode.LOCATION_NAME_NONE]
        sms = None
        if isinstance(report_name, str):
            report_name = report_name.decode('utf-8')
            report_name = unicode(report_name)

        if report.rName == EVENTER.RNAME.POWEROFF:
            report.login = GATEWAY.TERMINAL_LOGIN.LOGIN
            sms = SMSCode.SMS_POWEROFF % (name, report_name, terminal_time)
        elif report.rName == EVENTER.RNAME.POWERLOW:
            if report.dev_type == "1":
                sms = SMSCode.SMS_TRACKER_POWERLOW % (name, int(report.pbat), report_name, terminal_time)
            else:
                sms = SMSCode.SMS_POB_POWERLOW % (name, int(report.pbat), report_name, terminal_time)
        #elif report.rName == EVENTER.RNAME.REGION_OUT:
        #    sms = SMSCode.SMS_REGION_OUT % (name, report_name, terminal_time)
        #elif report.rName == EVENTER.RNAME.SPEED_OUT:
        #    sms = SMSCode.SMS_SPEED_OUT % (name, report_name, terminal_time)
        elif report.rName == EVENTER.RNAME.ILLEGALMOVE:
            sms = SMSCode.SMS_ILLEGALMOVE % (name, report_name, terminal_time)
        #elif report.rName == EVENTER.RNAME.HEARTBEAT_LOST:
        #    sms = SMSCode.SMS_HEARTBEAT_LOST % (name, terminal_time)
        elif report.rName == EVENTER.RNAME.EMERGENCY:
            sms = SMSCode.SMS_SOS % (name, report_name, terminal_time)
        else:
            pass

        self.update_terminal_status(report)
        lid = self.insert_location(report)

        if report.category != EVENTER.CATEGORY.UNKNOWN:
            self.event_hook(report.category, report.dev_id, report.dev_type, lid, report.pbat)
            self.sms_to_user(report.dev_id, sms)
            self.notify_to_parents(report.category, report.dev_id, report)
            

    def event_hook(self, category, dev_id, dev_type, lid, pbat=None):
        self.db.execute("INSERT INTO T_EVENT"
                        "  VALUES (NULL, %s, %s, %s, %s, %s)",
                        dev_id, dev_type, lid, pbat, category)

    def handle_charge_info(self, info):
        #TODO, parse charge 
        info = DotDict(info)
        self.db.execute("INSERT INTO T_CHARGE"
                        "  VALUES (NULL, %s, %s, %s)",
                        info.dev_id, info.content, info.timestamp)
        name = self.get_tname(info.dev_id)
        terminal_time = get_terminal_time(int(info.timestamp))
        sms = SMSCode.SMS_CHARGE % (name, info.content, terminal_time)
        self.sms_to_user(info.dev_id, sms)

    def sms_to_user(self, dev_id, sms):
        if not sms:
            return

        user = QueryHelper.get_user_by_tid(dev_id, self.db) 
        if user:
            SMSHelper.send(user.owner_mobile, sms)


    def notify_to_parents(self, category, dev_id, location):
        # NOTE: if user is not null, notify android
        user = QueryHelper.get_user_by_tid(dev_id, self.db)
        if user:
            notifyhelper.push_to_android(category, user.owner_mobile, dev_id, location)      
