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
     get_ios_id_key, get_power_full_key, get_region_status_key, safe_utf8, safe_unicode

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
        
    def check_region_event(self, location): 
        """ check enter or out region """
        #1.select the terminal's all regions and compare it
        regions = self.db.query("SELECT tr.id AS region_id, tr.name AS region_name, "
                                "       tr.longitude AS region_longitude, tr.latitude AS region_latitude, "
                                "       tr.radius AS region_radius" 
                                "  FROM T_REGION tr, T_REGION_TERMINAL trt "
                                "  WHERE tr.id = trt.rid"
                                "  AND trt.tid = %s",
                                location['dev_id'])
        if regions is None or len(regions) == 0:
            return
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
            logging.info("rname:%s, old status:%s, current status:%s, tid:%s", region.region_name, old_region_status, region_status, location['dev_id'])    

            if not old_region_status:
                # skip the first region event
                continue

            if region_status != old_region_status:
                location['category']=region_status
                location['t'] = EVENTER.INFO_TYPE.REPORT
                location['rName'] = rname
                lid = self.insert_location(location)
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
                         sms = SMSCode.SMS_REGION_OUT % (terminal.mobile, safe_unicode(region.region_name), safe_unicode(location.name), terminal_time)
                    else:
                         sms = SMSCode.SMS_REGION_ENTER % (terminal.mobile, safe_unicode(region.region_name), safe_unicode(location.name), terminal_time)
                    SMSHelper.send(corp.mobile, sms)
                
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
        if (is_alived == ALIVED and location.cLat and location.cLon):
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
        if terminal_info:
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
                                                  cellid=True,
                                                  db=self.db) 
            location.category = EVENTER.CATEGORY.REALTIME
            self.update_terminal_info(location)
            if location.get('cLat') and location.get('cLon'):
                self.realtime_location_hook(location)

            self.check_region_event(location)

        elif location.Tid == EVENTER.TRIGGERID.PVT:
            for pvt in location['pvts']:
                # get available location from lbmphelper
                pvt['dev_id'] = location['dev_id']
                location = lbmphelper.handle_location(pvt, self.redis,
                                                      cellid=False, db=self.db) 
                location.category = EVENTER.CATEGORY.REALTIME
                if location.get('cLat') and location.get('cLon'): 
                    self.insert_location(location)

                self.check_region_event(location)
        else:
            location.category = EVENTER.CATEGORY.UNKNOWN
            self.unknown_location_hook(location)

    def handle_report_info(self, info):
        """These reports should be handled here:
        POWERLOW/POWERFULL/POWEROFF 
        ILLEGALMOVE
        ILLEGALSHAKE
        EMERGENCY

        """
        # get available location from lbmphelper 
        report = lbmphelper.handle_location(info, self.redis,
                                            cellid=True, db=self.db)

        # check region evnent
        #self.check_region_event(report)

        # if undefend, just save location into db
        if info['rName'] in [EVENTER.RNAME.ILLEGALMOVE, EVENTER.RNAME.ILLEGALSHAKE]:
            mannual_status = QueryHelper.get_mannual_status_by_tid(info['dev_id'], self.db)
            if int(mannual_status) == UWEB.DEFEND_STATUS.NO:
                report['category'] = EVENTER.CATEGORY.REALTIME
                self.insert_location(report)
                self.update_terminal_info(report)
                logging.info("[EVENTER] %s mannual_status is undefend, drop %s report.",
                             info['dev_id'], info['rName'])
                return

        # save into database
        lid = self.insert_location(report)
        self.update_terminal_info(report)
        self.event_hook(report.category, report.dev_id, report.terminal_type, lid, report.pbat, report.get('fobid'))

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
                sms = SMSCode.SMS_ILLEGALMOVE % (name, report_name, terminal_time)
            elif report.rName == EVENTER.RNAME.ILLEGALSHAKE:
                sms = SMSCode.SMS_ILLEGALSHAKE % (name, report_name, terminal_time)
            elif report.rName == EVENTER.RNAME.EMERGENCY:
                whitelist = QueryHelper.get_white_list_by_tid(report.dev_id, self.db)      
                if whitelist:
                    white_str = ','.join(white['mobile'] for white in whitelist) 
                    sms = SMSCode.SMS_SOS_OWNER % (name, white_str, report_name, terminal_time)
                    sms_white = SMSCode.SMS_SOS_WHITE % (name, report_name, terminal_time) 
                else:
                    sms = SMSCode.SMS_SOS % (name, report_name, terminal_time)
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
            name = QueryHelper.get_alias_by_tid(dev_id, self.redis, self.db)
            push_key = NotifyHelper.get_push_key(user.owner_mobile, self.redis) 
            NotifyHelper.push_to_android(category, user.owner_mobile, dev_id, name, location, push_key)      
            ios_id, ios_badge = NotifyHelper.get_iosinfo(user.owner_mobile, self.redis)
            if ios_id:
                NotifyHelper.push_to_ios(category, user.owner_mobile, dev_id, name, location, ios_id, ios_badge)      

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
            sms = SMSCode.SMS_POWERLOW_OFF % (name, report_name, terminal_time)
        else:
            sms = SMSCode.SMS_TRACKER_POWERLOW % (name, int(report.pbat), report_name, terminal_time)

        return sms
