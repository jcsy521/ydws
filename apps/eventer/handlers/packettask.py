# -*- coding: utf-8 -*-

import logging
import time

from tornado.escape import json_decode

from helpers.smshelper import SMSHelper
from helpers.queryhelper import QueryHelper
from helpers import lbmphelper
from helpers.notifyhelper import NotifyHelper
from helpers.urlhelper import URLHelper
from helpers.confhelper import ConfHelper
from helpers.uwebhelper import UWebHelper

from utils.dotdict import DotDict
from utils.misc import get_location_key, get_terminal_time, get_terminal_info_key,\
     get_ios_id_key, get_power_full_key, get_region_status_key, get_alarm_info_key,\
     safe_utf8, safe_unicode, get_ios_push_list_key, get_android_push_list_key
from utils.public import insert_location

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
        
    def get_regions(self, tid): 
        """Get all regions associated with the tid."""
        #1.select the terminal's all regions and compare it
        regions = self.db.query("SELECT tr.id AS region_id, tr.name AS region_name, "
                                "       tr.longitude AS region_longitude, tr.latitude AS region_latitude, "
                                "       tr.radius AS region_radius" 
                                "  FROM T_REGION tr, T_REGION_TERMINAL trt "
                                "  WHERE tr.id = trt.rid"
                                "  AND trt.tid = %s",
                                tid)
        if regions is None or len(regions) == 0:
            return []
        else:
            return regions

    def check_region_event(self, location, regions): 
        """check enter or out region """
        #1.select the terminal's all regions and compare it
        location['valid'] = GATEWAY.LOCATION_STATUS.SUCCESS
        terminal = QueryHelper.get_terminal_by_tid(location['dev_id'], self.db)
        for region in regions:
            old_region_status_key = get_region_status_key(location['dev_id'], region.region_id)
            old_region_status = self.redis.getvalue(old_region_status_key)
            #2.get distance that now location and the centre of the region 
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
            
            self.redis.setvalue(old_region_status_key, region_status)
            logging.info("rname:%s, old status:%s, current status:%s, tid:%s",
                         region.region_name, old_region_status, region_status, location['dev_id'])    

            if not old_region_status:
                # skip the first region event
                continue

            if region_status != old_region_status:
                
                # keep the region alarm 
                alarm = dict(tid=location['dev_id'],
                             category=region_status,
                             timestamp=location.get('gps_time',0),
                             latitude=location.get('lat',0),
                             longitude=location.get('lon',0),
                             clatitude=location.get('cLat',0),
                             clongitude=location.get('cLon',0),
                             name=location['name'] if location.get('name',None) is not None else '',
                             degree=location.get('degree',0),
                             speed=location.get('speed',0),
                             #3# for regions
                             region_id=region.region_id,
                             region_radius=region.region_radius,
                             bounds=[region.region_latitude, region.region_longitude]
                             )
                self.record_alarm_info(alarm)
                location['category']=region_status
                location['t'] = EVENTER.INFO_TYPE.REPORT
                location['rName'] = rname
                lid = insert_location(location, self.db, self.redis)
                self.event_hook(region_status, location['dev_id'], 1, lid, location.pbat, None, region.region_id)
                self.redis.setvalue(old_region_status_key, region_status)
                corp = self.db.get("SELECT T_CORP.mobile FROM T_CORP, T_GROUP, T_TERMINAL_INFO"
                                   "  WHERE T_TERMINAL_INFO.tid = %s"
                                   "    AND T_TERMINAL_INFO.group_id != -1"
                                   "    AND T_TERMINAL_INFO.group_id = T_GROUP.id"
                                   "    AND T_GROUP.corp_id = T_CORP.cid",
                                   location['dev_id'])
                if corp and corp.mobile:
                    terminal_time = get_terminal_time(int(location.gps_time))
                    if region_status == EVENTER.CATEGORY.REGION_OUT:
                        if location.name:
                            sms = SMSCode.SMS_REGION_OUT % (terminal.mobile,
                                                            safe_unicode(region.region_name),
                                                            safe_unicode(location.name), terminal_time)
                        else:
                            sms = SMSCode.SMS_REGION_ENTER_NO_ADDRESS % (terminal.mobile,
                                                                         safe_unicode(region.region_name),
                                                                         terminal_time)
                    else:
                        if location.name:
                            sms = SMSCode.SMS_REGION_ENTER % (terminal.mobile,
                                                              safe_unicode(region.region_name),
                                                              safe_unicode(location.name), terminal_time)
                        else:
                            sms = SMSCode.SMS_REGION_OUT_NO_ADDRESS % (terminal.mobile,
                                                                       safe_unicode(region.region_name),
                                                                       terminal_time)
                    if location.cLon and location.cLat:
                        clon = '%0.3f' % (location.cLon/3600000.0) 
                        clat = '%0.3f' % (location.cLat/3600000.0)
                        url = ConfHelper.UWEB_CONF.url_out + '/wapimg?clon=' + clon + '&clat=' + clat 
                        tiny_id = URLHelper.get_tinyid(url)
                        if tiny_id:
                            base_url = ConfHelper.UWEB_CONF.url_out + UWebHelper.URLS.TINYURL
                            tiny_url = base_url + '/' + tiny_id
                            logging.info("[EVENTER] get tiny url successfully. tiny_url:%s", tiny_url)
                            self.redis.setvalue(tiny_id, url, time=EVENTER.TINYURL_EXPIRY)
                            sms += u"点击" + tiny_url + u" 查看车辆位置。" 
                        else:
                            logging.info("[EVENTER] get tiny url failed.")
                    SMSHelper.send(corp.mobile, sms)
                
    def get_tname(self, dev_id):
        t = self.db.get("SELECT alias, mobile FROM T_TERMINAL_INFO"
                        "  WHERE tid = %s", dev_id)
        name = t.alias if t.alias else t.mobile 
        if isinstance(name, str):
            name = name.decode("utf-8")

        return name

    def realtime_location_hook(self, location):
        insert_location(location, self.db, self.redis)

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
        location = DotDict(location)
        if location.Tid == EVENTER.TRIGGERID.CALL:
            #location = lbmphelper.handle_location(location, self.redis,
            #                                      cellid=True, db=self.db) 
            regions = self.get_regions(location['dev_id'])
            if regions:
                location = lbmphelper.handle_location(location, self.redis,
                                                      cellid=True, db=self.db) 
                self.check_region_event(location, regions)
            location['category'] = EVENTER.CATEGORY.REALTIME
            location['type'] = location.get('type', 1)
            self.update_terminal_info(location)
            if location.get('lat') and location.get('lon'):
                self.realtime_location_hook(location)

        elif location.Tid == EVENTER.TRIGGERID.PVT:
            for pvt in location['pvts']:
                # get available location from lbmphelper
                pvt['dev_id'] = location['dev_id']

                regions = self.get_regions(pvt['dev_id'])
                if regions:
                    pvt = lbmphelper.handle_location(pvt, self.redis,
                                                          cellid=True, db=self.db) 
                    self.check_region_event(pvt, regions)
                # NOTE: not offset it
                #location = lbmphelper.handle_location(pvt, self.redis,
                #                                      cellid=False, db=self.db) 
                pvt['category'] = EVENTER.CATEGORY.REALTIME
                pvt['type'] = location.get('type', 0)
                if pvt.get('lat') and pvt.get('lon'): 
                    insert_location(pvt, self.db, self.redis)

        else:
            location.category = EVENTER.CATEGORY.UNKNOWN
            self.unknown_location_hook(location)

    def handle_report_info(self, info):
        """These reports should be handled here:
        POWERLOW/POWERFULL/POWEROFF/POWERDOWN 
        ILLEGALMOVE
        ILLEGALSHAKE
        EMERGENCY

        """
        # 1: get available location from lbmphelper 
        report = lbmphelper.handle_location(info, self.redis,
                                            cellid=True, db=self.db)


        # check region evnent
        #self.check_region_event(report)

        #NOTE: if undefend, just save location into db
        if info['rName'] in [EVENTER.RNAME.ILLEGALMOVE, EVENTER.RNAME.ILLEGALSHAKE]:
            mannual_status = QueryHelper.get_mannual_status_by_tid(info['dev_id'], self.db)
            if int(mannual_status) == UWEB.DEFEND_STATUS.NO:
                report['category'] = EVENTER.CATEGORY.REALTIME
                insert_location(report, self.db, self.redis)
                self.update_terminal_info(report)
                logging.info("[EVENTER] %s mannual_status is undefend, drop %s report.",
                             info['dev_id'], info['rName'])
                return

        alarm = dict(tid=report['dev_id'],
                     category=report['category'], 
                     latitude=report['lat'], 
                     longitude=report['lon'], 
                     clatitude=report['cLat'], 
                     clongitude=report['cLon'], 
                     timestamp=report['gps_time'], 
                     name=report['name'] if report.get('name',None) is not None else '',
                     degree=report['degree'], 
                     speed=report['speed'])

        self.record_alarm_info(alarm)

        # 2:  save into database. T_LOCATION, T_EVENT
        lid = insert_location(report, self.db, self.redis)
        self.update_terminal_info(report)
        self.event_hook(report.category, report.dev_id, report.terminal_type, lid, report.pbat, report.get('fobid'))

        # 3: notify the owner 
        user = QueryHelper.get_user_by_tid(report.dev_id, self.db) 
        if not user:
            logging.error("[EVENTER] Cannot find USER of terminal: %s", report.dev_id)
            return
        
        sms_option = self.get_sms_option(user.owner_mobile, EVENTER.SMS_CATEGORY[report.rName].lower())
        if sms_option == UWEB.SMS_OPTION.SEND:
            name = QueryHelper.get_alias_by_tid(report.dev_id, self.redis, self.db)
            terminal_time = get_terminal_time(int(report.gps_time))

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
                    sms = self.handle_power_status(report, name, report_name, terminal_time)
                else: # type: fob
                    sms = SMSCode.SMS_FOB_POWERLOW % (report.fobid, terminal_time)
            elif report.rName == EVENTER.RNAME.ILLEGALMOVE:
                if report_name in [ErrorCode.ERROR_MESSAGE[ErrorCode.LOCATION_NAME_NONE], ErrorCode.ERROR_MESSAGE[ErrorCode.LOCATION_FAILED]]:
                    sms = SMSCode.SMS_ILLEGALMOVE_NOLOC % (name, terminal_time)
                else:
                    sms = SMSCode.SMS_ILLEGALMOVE % (name, report_name, terminal_time)
            elif report.rName == EVENTER.RNAME.ILLEGALSHAKE:
                if report_name in [ErrorCode.ERROR_MESSAGE[ErrorCode.LOCATION_NAME_NONE], ErrorCode.ERROR_MESSAGE[ErrorCode.LOCATION_FAILED]]:
                    sms = SMSCode.SMS_ILLEGALSHAKE_NOLOC % (name, terminal_time)
                else:
                    sms = SMSCode.SMS_ILLEGALSHAKE % (name, report_name, terminal_time)
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
                    sms += u"点击" + tiny_url + u" 查看车辆位置。" 
                    if sms_white:
                        sms_white += u"点击" + tiny_url + u" 查看车辆位置。"
                        self.sms_to_whitelist(sms_white, whitelist)
                else:
                    logging.info("[EVENTER] get tiny url failed.")
            else:
                logging.info("[EVENTER] location failed.")
            self.sms_to_user(report.dev_id, sms, user)
            if report.rName == EVENTER.RNAME.POWERLOW:
                corp = self.db.get("SELECT T_CORP.mobile FROM T_CORP, T_GROUP, T_TERMINAL_INFO"
                                   "  WHERE T_TERMINAL_INFO.tid = %s"
                                   "    AND T_TERMINAL_INFO.group_id != -1"
                                   "    AND T_TERMINAL_INFO.group_id = T_GROUP.id"
                                   "    AND T_GROUP.corp_id = T_CORP.cid",
                                   report.dev_id)
                if (corp and corp.mobile != user.owner_mobile):
                    SMSHelper.send(corp.mobile, sms)
        else:
            logging.info("[EVENTER] Remind option of %s is closed. Terminal: %s",
                         report.rName, report.dev_id)

        terminal = self.db.get("SELECT push_status FROM T_TERMINAL_INFO"
                               "  WHERE tid = %s", report.dev_id)
        if terminal and terminal.push_status == 1:
            report.comment = ''
            if report.rName == EVENTER.RNAME.POWERLOW:
                if report.terminal_type == "1":
                    if int(report.pbat) == 100:
                        report.comment = ErrorCode.ERROR_MESSAGE[ErrorCode.TRACKER_POWER_FULL] 
                    elif int(report.pbat) <= 5:
                        report.comment = ErrorCode.ERROR_MESSAGE[ErrorCode.TRACKER_POWER_OFF]
                    else:
                        report.comment = (ErrorCode.ERROR_MESSAGE[ErrorCode.TRACKER_POWER_LOW]) % report.pbat
                else:
                    report.comment = ErrorCode.ERROR_MESSAGE[ErrorCode.FOB_POWER_LOW] % report.fobid

            self.notify_to_parents(report.category, report.dev_id, report, user) 
        else:
            logging.info("[EVENTER] Push option of %s is closed. Terminal: %s",
                         report.rName, report.dev_id)


    def event_hook(self, category, dev_id, terminal_type, lid, pbat=None, fobid=None , rid=None):
        self.db.execute("INSERT INTO T_EVENT(tid, terminal_type, fobid, lid, pbat, category, rid)"
                        "  VALUES (%s, %s, %s, %s, %s, %s, %s)",
                        dev_id, terminal_type, fobid, lid, pbat, category, rid)

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


    def notify_to_parents(self, category, dev_id, location, user=None):
        # NOTE: if user is not null, notify android
        if not user:
            user = QueryHelper.get_user_by_tid(dev_id, self.db)

        if user:
            t_alias = QueryHelper.get_alias_by_tid(dev_id, self.redis, self.db)
            # 1: push to android
            android_push_list_key = get_android_push_list_key(user.uid) 
            android_push_list = self.redis.getvalue(android_push_list_key) 
            if android_push_list: 
                for push_id in android_push_list: 
                    push_key = NotifyHelper.get_push_key(push_id, self.redis) 
                    NotifyHelper.push_to_android(category, dev_id, t_alias, location, push_id, push_key)
            # 2: push  to ios 
            ios_push_list_key = get_ios_push_list_key(user.uid) 
            ios_push_list = self.redis.getvalue(ios_push_list_key) 
            if ios_push_list: 
                for iosid in ios_push_list: 
                    ios_badge = NotifyHelper.get_iosbadge(iosid, self.redis) 
                    NotifyHelper.push_to_ios(category, dev_id, t_alias, location, ios_id, ios_badge)

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
                               region_name,
                               region_radius,
                               bounds,
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
