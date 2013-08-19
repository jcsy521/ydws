# -*- coding: utf-8 -*-

import logging
import time
import copy

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

    def check_region_event(self, ori_location, region): 
        """check enter or out region """
        if not (ori_location and region): 
            return None

        # BIG NOTE: python grammar, shallow copy will change origen data.
        location = copy.deepcopy(dict(ori_location))
        location = DotDict(location)

        location['valid'] = GATEWAY.LOCATION_STATUS.SUCCESS
        terminal = QueryHelper.get_terminal_by_tid(location['dev_id'], self.db)
        old_region_status_key = get_region_status_key(location['dev_id'], region.region_id)
        old_region_status = self.redis.getvalue(old_region_status_key)
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
        
        self.redis.setvalue(old_region_status_key, region_status)
        logging.info("rname:%s, old status:%s, current status:%s, tid:%s",
                     region.region_name, old_region_status, region_status, location['dev_id'])    

        if not old_region_status:
            # skip the first region event
            return location

        if region_status != old_region_status:
            self.redis.setvalue(old_region_status_key, region_status)
            # 2: complete the location
            location['category']=region_status
            location['t'] = EVENTER.INFO_TYPE.REPORT
            location['rName'] = rname
            location['region'] = region 
            location['region_id'] = region.region_id
        return location
                
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
        regions = self.get_regions(location['dev_id'])
        if location.Tid == EVENTER.TRIGGERID.CALL:
            location = lbmphelper.handle_location(location, self.redis,
                                                  cellid=True, db=self.db) 
            # check regions
            for region in regions:
                region_location = self.check_region_event(location, region)
                if region_location['t'] == EVENTER.INFO_TYPE.REPORT:
                    self.handle_report_info(region_location)

            location['category'] = EVENTER.CATEGORY.REALTIME
            location['type'] = location.get('type', 1)
            self.update_terminal_info(location)
            if location.get('lat') and location.get('lon'):
                self.realtime_location_hook(location)

        elif location.Tid == EVENTER.TRIGGERID.PVT:
            for pvt in location['pvts']:
                # get available location from lbmphelper
                pvt['dev_id'] = location['dev_id']
                pvt['Tid'] = location['Tid']

                regions = self.get_regions(pvt['dev_id'])
                # check regions
                if regions:
                    pvt = lbmphelper.handle_location(pvt, self.redis,
                                                          cellid=True, db=self.db) 
                    for region in regions:
                        region_pvt= self.check_region_event(pvt, region)
                        if region_pvt['t'] == EVENTER.INFO_TYPE.REPORT:
                            self.handle_report_info(region_pvt)
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
        REGION_ENTER
        REGION_OUT
        """
        if not info:
            return
        # 1: get available location from lbmphelper 
        report = lbmphelper.handle_location(info, self.redis,
                                            cellid=True, db=self.db)

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
        
        # keep alarm info
        alarm = dict(tid=report['dev_id'],
                     category=report['category'], 
                     type=report['type'], 
                     timestamp=report.get('gps_time',0),
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
        self.event_hook(report.category, report.dev_id, report.get('terminal_type',1), lid, report.pbat, report.get('fobid'), report.get('region_id', -1))

        # 3: notify the owner 
        user = QueryHelper.get_user_by_tid(report.dev_id, self.db) 
        if not user:
            logging.error("[EVENTER] Cannot find USER of terminal: %s", report.dev_id)
            return
        
        # send sms to owner
        sms_option = self.get_sms_option(user.owner_mobile, EVENTER.SMS_CATEGORY[report.rName].lower())
        name = QueryHelper.get_alias_by_tid(report.dev_id, self.redis, self.db)
        if sms_option == UWEB.SMS_OPTION.SEND:
            terminal_time = get_terminal_time(int(report.gps_time))
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
            elif report.rName == EVENTER.RNAME.REGION_OUT:
                if report_name in [ErrorCode.ERROR_MESSAGE[ErrorCode.LOCATION_NAME_NONE], ErrorCode.ERROR_MESSAGE[ErrorCode.LOCATION_FAILED]]:
                    sms = SMSCode.SMS_REGION_OUT_NOLOC % (name, report['region']['region_name'], terminal_time)
                else:
                    sms = SMSCode.SMS_REGION_OUT % (name, report['region']['region_name'], report_name, terminal_time)
            elif report.rName == EVENTER.RNAME.REGION_ENTER:
                if report_name in [ErrorCode.ERROR_MESSAGE[ErrorCode.LOCATION_NAME_NONE], ErrorCode.ERROR_MESSAGE[ErrorCode.LOCATION_FAILED]]:
                    sms = SMSCode.SMS_REGION_ENTER_NOLOC % (name, report['region']['region_name'], terminal_time)
                else:
                    sms = SMSCode.SMS_REGION_ENTER % (name, report['region']['region_name'], report_name, terminal_time)
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
                    sms += u"点击" + tiny_url + u" 查看定位仪位置。" 
                    if sms_white:
                        sms_white += u"点击" + tiny_url + u" 查看定位仪位置。"
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
         
        # push to owner
        terminal = self.db.get("SELECT push_status FROM T_TERMINAL_INFO"
                               "  WHERE tid = %s", report.dev_id)
        if terminal and terminal.push_status == 1:
            report.comment = ''
            region_id = None
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
            elif report.rName in (EVENTER.RNAME.REGION_ENTER, EVENTER.RNAME.REGION_OUT):
                region = report['region']
                region_id = region.region_id
                if region.get('region_name', None): 
                    region.comment = u"围栏名：%s" % region.region_name
                
            self.notify_to_parents(name, report, user, region_id) 
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


    def notify_to_parents(self, alias, location, user, region_id=None):
        # NOTE: if user is not null, notify android

        category = location.category
        dev_id = location.dev_id

        if not user:
            user = QueryHelper.get_user_by_tid(dev_id, self.db)

        if user:
            # 1: push to android
            android_push_list_key = get_android_push_list_key(user.owner_mobile) 
            android_push_list = self.redis.getvalue(android_push_list_key) 
            if android_push_list: 
                for push_id in android_push_list: 
                    push_key = NotifyHelper.get_push_key(push_id, self.redis) 
                    logging.info("get push key: %s for push_id: %s", push_key, push_id)
                    NotifyHelper.push_to_android(category, dev_id, alias, location, push_id, push_key, region_id)
            # 2: push  to ios 
            ios_push_list_key = get_ios_push_list_key(user.owner_mobile) 
            ios_push_list = self.redis.getvalue(ios_push_list_key) 
            if ios_push_list: 
                for ios_id in ios_push_list: 
                    ios_badge = NotifyHelper.get_iosbadge(ios_id, self.redis) 
                    NotifyHelper.push_to_ios(category, dev_id, alias, location, ios_id, ios_badge, region_id)

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
