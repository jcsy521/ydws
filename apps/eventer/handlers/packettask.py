# -*- coding: utf-8 -*-

import logging

from tornado.escape import json_decode

from helpers.smshelper import SMSHelper
from helpers.queryhelper import QueryHelper
from helpers import lbmphelper
from helpers.notifyhelper import NotifyHelper

from utils.dotdict import DotDict
from utils.misc import get_location_key, get_terminal_time, get_terminal_info_key 
from codes.smscode import SMSCode
from codes.errorcode import ErrorCode 
from constants import EVENTER, GATEWAY, UWEB 
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
        t = self.db.get("SELECT alias, mobile FROM T_TERMINAL_INFO"
                        "  WHERE tid = %s", dev_id)
        name = t.alias if t.alias else t.mobile 
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
            location_key = get_location_key(location.dev_id)
            self.redis.setvalue(location_key, mem_location, EVENTER.LOCATION_EXPIRY)
        return lid
        
    def realtime_location_hook(self, location):
        self.insert_location(location)

    def unknown_location_hook(self, location):
        pass

    def update_terminal_info(self, location):
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
        terminal_info_key = get_terminal_info_key(location.dev_id)
        terminal_info = self.redis.getvalue(terminal_info_key)
        if not terminal_info:
            terminal_info = DotDict(defend_status=None,
                                    login=None,
                                    gps=None,
                                    gsm=None,
                                    pbat=None,
                                    alias=None,
                                    keys_num=None)
        for key in terminal_info:
            value = location.get(key, None)
            if value is not None:
                terminal_info[key] = value
        self.redis.setvalue(terminal_info_key, terminal_info)
    
    def handle_position_info(self, location):
        location = DotDict(location)
        if location.Tid == EVENTER.TRIGGERID.CALL:
            # get available location from lbmphelper
            location = lbmphelper.handle_location(location, self.redis,
                                                  cellid=False, db=self.db) 
            location.category = EVENTER.CATEGORY.REALTIME
            self.update_terminal_info(location)
            if location.valid == GATEWAY.LOCATION_STATUS.SUCCESS:
                self.realtime_location_hook(location)
        elif location.Tid == EVENTER.TRIGGERID.PVT:
            pass
            #for pvt in location['pvts']:
            #    # get available location from lbmphelper
            #    pvt['dev_id'] = location['dev_id']
            #    location = lbmphelper.handle_location(pvt, self.redis,
            #                                          cellid=False, db=self.db) 
            #    location.category = EVENTER.CATEGORY.REALTIME
            #    self.insert_location(location)
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
                                            cellid=True, db=self.db)
        # save into database
        self.update_terminal_info(report)
        lid = self.insert_location(report)
        fobid = report.get('fobid', None)
        self.event_hook(report.category, report.dev_id, report.terminal_type, lid, report.pbat, fobid)
            
        user = QueryHelper.get_user_by_tid(report.dev_id, self.db) 
        if not user:
            logging.error("[EVENTER] Cannot find USER of terminal: %s", report.dev_id)
            return
            
        sms_option = self.get_sms_option(user.owner_mobile, EVENTER.SMS_CATEGORY[report.rName].lower())
        if sms_option == UWEB.SMS_OPTION.SEND:
            name = QueryHelper.get_alias_by_tid(report.dev_id, self.redis, self.db)
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
                if report.terminal_type == "1":
                    sms = SMSCode.SMS_TRACKER_POWERLOW % (name, int(report.pbat), report_name, terminal_time)
                else:
                    sms = SMSCode.SMS_FOB_POWERLOW % (report.fobid, int(report.pbat), report_name, terminal_time)
            elif report.rName == EVENTER.RNAME.ILLEGALMOVE:
                sms = SMSCode.SMS_ILLEGALMOVE % (name, report_name, terminal_time)
            elif report.rName == EVENTER.RNAME.EMERGENCY:
                sms = SMSCode.SMS_SOS % (name, report_name, terminal_time)
            else:
                pass

            if report.lon and report.lat:
                #wap_url = 'http://api.map.baidu.com/staticimage?center=%s,%s%26width=800%26height=800%26zoom=17%26markers=%s,%s'
                #wap_url = wap_url % (report.lon/3600000.0, report.lat/3600000.0, report.lon/3600000.0, report.lat/3600000.0)
                wap_url = 'http://api.map.baidu.com/staticimage?center=' +\
                          str(report.lon/3600000.0) + ',' + str(report.lat/3600000.0) +\
                          '%26width=800%26height=800%26zoom=17%26markers=' +\
                          str(report.lon/3600000.0) + ',' + str(report.lat/3600000.0)
                sms += u"点击" + wap_url

            self.sms_to_user(report.dev_id, sms, user)

        self.notify_to_parents(report.category, report.dev_id, report)


    def event_hook(self, category, dev_id, terminal_type, lid, pbat=None, fobid=None):
        self.db.execute("INSERT INTO T_EVENT(tid, terminal_type, fobid, lid, pbat, category)"
                        "  VALUES (%s, %s, %s, %s, %s, %s)",
                        dev_id, terminal_type, fobid, lid, pbat, category)

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
            name = QueryHelper.get_alias_by_tid(info.dev_id, self.redis, self.db)
            terminal_time = get_terminal_time(int(info.timestamp))
            sms = SMSCode.SMS_CHARGE % (name, info.content)
            self.sms_to_user(info.dev_id, sms, user)

    def sms_to_user(self, dev_id, sms, user=None):
        if not sms:
            return

        if not user:
            user = QueryHelper.get_user_by_tid(dev_id, self.db) 

        if user:
            SMSHelper.send(user.owner_mobile, sms)


    def notify_to_parents(self, category, dev_id, location):
        # NOTE: if user is not null, notify android
        user = QueryHelper.get_user_by_tid(dev_id, self.db)
        if user:
            name = QueryHelper.get_alias_by_tid(dev_id, self.redis, self.db)
            push_key = NotifyHelper.get_push_key(user.owner_mobile, self.redis) 
            NotifyHelper.push_to_android(category, user.owner_mobile, dev_id, name, location, push_key)      
