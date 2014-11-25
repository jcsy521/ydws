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
from helpers.wspushhelper import WSPushHelper
from helpers.weixinpushhelper import WeixinPushHelper

from utils.dotdict import DotDict
from utils.misc import (get_location_key, get_terminal_time, get_terminal_info_key,
     get_ios_id_key, get_power_full_key, get_region_status_key, get_alarm_info_key,
     safe_utf8, safe_unicode, get_ios_push_list_key, get_android_push_list_key,
     get_region_time_key, get_alert_freq_key, get_pbat_message_key,
     get_mileage_key, start_end_of_day, get_single_status_key,
     get_single_time_key, get_speed_limit_key, get_stop_key,
     get_distance_key, get_last_pvt_key)
from utils.public import (insert_location, get_alarm_mobile, update_terminal_dynamic_info,
     record_alarm_info)   
from utils.geometry import PtInPolygon 
from utils.repeatedtimer import RepeatedTimer

from codes.smscode import SMSCode
from codes.errorcode import ErrorCode 
from constants import EVENTER, GATEWAY, UWEB, LIMIT
from constants.MEMCACHED import ALIVED

from mixin.packettask import PacketTaskMixin


class PacketTask(PacketTaskMixin):
    
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
        
    def handle_position_info(self, location):
        """Handle the info of position, include PVT(T11), CALL(T3)
        """
        location = DotDict(location)

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
            update_terminal_dynamic_info(self.db, self.redis, location)

            if location.get('lat') and location.get('lon'):
                self.realtime_location_hook(location)

        # NOTE: For pvt(T11)
        elif location.Tid == EVENTER.TRIGGERID.PVT:
            #NOTE: get speed_limit  

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

                #NOTE: handle stop 
                self.handle_stop(pvt)

                #NOTE: handle region 
                self.handle_region(pvt)

                #NOTE: handle single 
                self.handle_single(pvt)

                #NOTE: handle speed 
                self.handle_speed(pvt)


                #NOTE: the time of keep last_pvt is import.
                last_pvt_key = get_last_pvt_key(location['dev_id'])
                last_pvt = pvt 
                self.redis.setvalue(last_pvt_key, last_pvt, time=EVENTER.STOP_EXPIRY)

                # NOTE: not offset it
                #location = lbmphelper.handle_location(pvt, self.redis,
                #                                      cellid=False, db=self.db) 
                #NOTE: mileage
                pvt['category'] = EVENTER.CATEGORY.REALTIME
                if pvt.get('lat') and pvt.get('lon'): 
                    insert_location(pvt, self.db, self.redis)
                    #NOTE: handle mileage 
                    self.handle_mileage(pvt)
                self.push_to_client(pvt) 
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

        alarm_mobile = get_alarm_mobile(report.dev_id, self.db, self.redis)

        #NOTE: in pvt, timestamp is no used, so use gps_time as timestamp
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
            elif alarm_mobile:
                logging.info("[EVENTER] Send notify forever , go ahead.  Terminal: %s, alarm_mobile: %s",
                             report.dev_id, alarm_mobile)
            else:
                mannual_status = QueryHelper.get_mannual_status_by_tid(info['dev_id'], self.db)
                if int(mannual_status) == UWEB.DEFEND_STATUS.NO:
                    report['category'] = EVENTER.CATEGORY.REALTIME
                    insert_location(report, self.db, self.redis)
                    update_terminal_dynamic_info(self.db, self.redis, report)
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

        #NOTE: keep alarm info
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

        record_alarm_info(self.db, self.redis, alarm)

        # 2:  save into database. T_LOCATION, T_EVENT
        lid = insert_location(report, self.db, self.redis)
        update_terminal_dynamic_info(self.db, self.redis, report)
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
            
        #NOTE: notify user by sms
        sms_option = QueryHelper.get_sms_option_by_uid(user.owner_mobile, EVENTER.SMS_CATEGORY[report.rName].lower(), self.db)
        if sms_option == UWEB.SMS_OPTION.SEND:
            logging.info("[EVENTER] Notify report to user by sms. category: %s, tid: %s, mobile: %s",
                         report.rName, report.dev_id, user['owner_mobile'])
            self.notify_report_by_sms(report, user['owner_mobile'])
        else:
            logging.info("[EVENTER] Remind option of %s is closed. Terminal: %s",
                         report.rName, report.dev_id)

        if alarm_mobile:
            logging.info("[EVENTER] Notify report to user by sms. category: %s, tid: %s, alarm_mobile: %s",
                         report.rName, report.dev_id, alarm_mobile)
            self.notify_report_by_sms(report, alarm_mobile)

        #NOTE: notify user by push
        terminal = self.db.get("SELECT push_status FROM T_TERMINAL_INFO"
                               "  WHERE tid = %s", report.dev_id)
        if terminal and terminal.push_status == 1:
            logging.info("[EVENTER] Notify report to user by push. category: %s, tid: %s, mobile: %s",
                         report.rName, report.dev_id, user['owner_mobile'])
            self.notify_report_by_push(report, user['owner_mobile'])
        else:
            logging.info("[EVENTER] Push option of %s is closed. Terminal: %s",
                         report.rName, report.dev_id)

        #NOTE: notify alarm_mobile
        if alarm_mobile:
            logging.info("[EVENTER] Notify report to user by push. category: %s, tid: %s, alarm_mobile: %s",
                         report.rName, report.dev_id, alarm_mobile)
            self.notify_report_by_push(report, alarm_mobile)

    def handle_charge_info(self, info):
        info = DotDict(info)
        self.db.execute("INSERT INTO T_CHARGE"
                        "  VALUES (NULL, %s, %s, %s)",
                        info.dev_id, info.content, info.timestamp)
        user = QueryHelper.get_user_by_tid(info.dev_id, self.db) 
        if not user:
            logging.error("[EVENTER] Cannot find USER of terminal: %s", info.dev_id)
            return
            
        sms_option = QueryHelper.get_sms_option_by_uid(user.owner_mobile, EVENTER.SMS_CATEGORY.CHARGE.lower(), self.db)
        if sms_option == UWEB.SMS_OPTION.SEND:
            logging.error("[EVENTER] do not send charge sms temporarily")
            #name = QueryHelper.get_alias_by_tid(info.dev_id, self.redis, self.db)
            #terminal_time = get_terminal_time(int(info.timestamp))
            #sms = SMSCode.SMS_CHARGE % (name, info.content)
            #self.sms_to_user(info.dev_id, sms, user)

