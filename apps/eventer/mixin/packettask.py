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


class PacketTaskMixin(object):

    #NOTE: check 

    def check_timestamp(self, timestamp): 
        """Check timestamp whether useable.

        @param: timestamp // second 
        
        @return: bool // True, it's usable; False. it's unusable. 

        if timestamp is 3hours ago:
            it's unusable.
        
        """ 
        current_time = int(time.time())
        if timestamp < current_time - 60*60*3: 
            logging.info("[EVENTER] Timestamp is invalid, ignore it.  timestamp: %s.", 
                         timestamp)
            return False 
        return True

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

    #NOTE: notify 
    def notify_report_by_sms(self, report, mobile):

        flag = self.check_timestamp(int(report['timestamp']))
        if not flag: 
            return

        name = QueryHelper.get_alias_by_tid(report.dev_id, self.redis, self.db)
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
                _resend_alarm = functools.partial(self.sms_to_user, report.dev_id, sms+u"重复提醒，如已收到，请忽略。", mobile)
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
                _resend_alarm = functools.partial(self.sms_to_user, report.dev_id, sms+u"此条短信为重复提醒，请注意您的车辆状态。", mobile)
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

        self.sms_to_user(report.dev_id, sms, mobile)

    def notify_report_by_push(self, report, mobile):

        flag = self.check_timestamp(int(report['timestamp']))
        if not flag: 
            return

        name = QueryHelper.get_alias_by_tid(report.dev_id, self.redis, self.db)
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

        # push 
        if report.rName == EVENTER.RNAME.STOP:
            logging.info("[EVENTER] %s altert needn't to push to user. Terminal: %s",
                         report.rName, report.dev_id)
        else:
            self.notify_to_parents(name, report, mobile, region_id) 
            if report.rName in [EVENTER.RNAME.ILLEGALMOVE, EVENTER.RNAME.ILLEGALSHAKE]: 

                _date = datetime.datetime.fromtimestamp(int(report['timestamp']))
                _seconds = _date.hour * 60 * 60 + _date.minute * 60 + _date.second 
                if _seconds < 7 * 60 * 60 or _seconds > 19 * 60 * 60:  
                    _resend_alarm = functools.partial(self.notify_to_parents, name, report, mobile, region_id) 
                    # 30 seconds later, send sms 1 time.  
                    task = RepeatedTimer(30, _resend_alarm, 1) 
                    task.start()

        self.push_to_client(report) 

    #NOTE: hook
    def event_hook(self, category, dev_id, terminal_type, timestamp, lid, pbat=None, fobid=None , rid=None):
        self.db.execute("INSERT INTO T_EVENT(tid, terminal_type, timestamp, fobid, lid, pbat, category, rid)"
                        "  VALUES (%s, %s,  %s, %s, %s, %s, %s, %s)",
                        dev_id, terminal_type, timestamp, fobid, lid, pbat, category, rid)

    def realtime_location_hook(self, location):
        """Handle realtime.
        It's deprecated now.
        """
        insert_location(location, self.db, self.redis)

    def unknown_location_hook(self, location):
        """Now, just do nothing.
        """
        pass

    def sms_to_user(self, dev_id, sms, mobile):
        if not sms:
            return

        if not mobile:
            return

        if mobile:
            SMSHelper.send(mobile, sms)

    def sms_to_whitelist(self, sms, whitelist=None):
        if not sms:
            return

        if whitelist:
            for white in whitelist:
                SMSHelper.send(white['mobile'], sms)

    def notify_to_parents(self, alias, location, mobile, region_id=None):
        """Push information to clinet through push.

        PUSH 1.0
        """
        flag = self.check_timestamp(int(location['timestamp']))
        if not flag: 
            return

        category = location.category
        dev_id = location.dev_id

        if not location['pbat']:
            terminal = QueryHelper.get_terminal_info(dev_id, self.db, self.redis) 
            location['pbat'] = terminal['pbat'] if terminal['pbat'] is not None else 0 

        if mobile:
            # 1: push to android
            android_push_list_key = get_android_push_list_key(mobile) 
            android_push_list = self.redis.getvalue(android_push_list_key) 
            if android_push_list: 
                for push_id in android_push_list: 
                    push_key = NotifyHelper.get_push_key(push_id, self.redis) 
                    NotifyHelper.push_to_android(category, dev_id, alias, location, push_id, push_key, region_id)
            # 2: push  to ios 
            ios_push_list_key = get_ios_push_list_key(mobile) 
            ios_push_list = self.redis.getvalue(ios_push_list_key) 
            if ios_push_list: 
                for ios_id in ios_push_list: 
                    ios_badge = NotifyHelper.get_iosbadge(ios_id, self.redis) 
                    NotifyHelper.push_to_ios(category, dev_id, alias, location, ios_id, ios_badge, region_id)

    def push_to_client(self, location):
        """Push information to weixin and wspush.
        """
        #NOTE: use timestamp first. If it does not work, use gps_time.
        if location.get('timestamp',''):
            timestamp = location['timestamp']
        else:
            timestamp = location['gps_time']
        flag = self.check_timestamp(int(timestamp))
        if not flag: 
            return

        tid = location['dev_id']
        terminal = QueryHelper.get_terminal_info(tid, self.db, self.redis)
        body = dict(tid=tid,
                    category=location['category'], 
                    type=location['type'], 
                    timestamp=timestamp,
                    gps_time=location['gps_time'],
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

        WSPushHelper.pushS5(tid, body, self.db, self.redis)
        WeixinPushHelper.push(tid, body, self.db, self.redis)

    def handle_power_status(self, report, name, report_name, terminal_time):
        """Get sms according the pbat.

        @return sms

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


    def handle_region(self, pvt):
        """Check single-event.
        """
        tid = pvt['dev_id']
        regions = QueryHelper.get_regions(tid, self.db)
        if regions:
            pvt = lbmphelper.handle_location(pvt, self.redis,
                                             cellid=True, db=self.db) 
            for region in regions:
                region_pvt= self.check_region_event(pvt, region)
                if region_pvt and region_pvt['t'] == EVENTER.INFO_TYPE.REPORT:
                    self.handle_report_info(region_pvt)
    
    def handle_single(self, pvt):
        """Check single-event.
        """
        tid = pvt['dev_id']
        singles = QueryHelper.get_singles(tid, self.db)
    
        if singles:
            pvt = lbmphelper.handle_location(pvt, self.redis,
                                             cellid=True, db=self.db) 
            for single in singles:
                #NOTE: report about single may be need in future 
                single_pvt = self.check_single_event(pvt, single)

    def handle_speed(self, pvt):
        """Check the speed limit.
        """
        tid = pvt['dev_id']
        terminal = self.db.get("SELECT speed_limit "
                               "  FROM T_TERMINAL_INFO "
                               "  WHERE tid = %s AND group_id != -1",
                               tid) 
        speed_limit = terminal.get('speed_limit', '') if terminal else ''
        if speed_limit:
            speed_limit_key = get_speed_limit_key(tid)
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

    def handle_mileage(self, pvt):
        """Check the mileage.
        """
        flag = self.check_timestamp(int(pvt['gps_time']))
        if not flag: 
            return

        #NOTE: record the mileage
        tid = pvt['dev_id']
        mileage_key = get_mileage_key(tid)
        mileage = self.redis.getvalue(mileage_key)
        if not mileage:
            logging.info("[EVENTER] Tid: %s, init mileage. pvt: %s.",
                          tid, pvt)
            mileage = dict(lat=pvt.get('lat'),
                           lon=pvt.get('lon'),
                           dis=0,
                           gps_time=pvt['gps_time'])
            self.redis.setvalue(mileage_key, mileage)
        else:
            if pvt['gps_time'] < mileage['gps_time']:
                logging.info("[EVENTER] Tid: %s, gps_time: %s is less than mileage['gps_time']: %s, drop it. pvt: %s, mileage: %s", 
                             tid,
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
                                dis_current, tid)

                logging.info("[EVENTER] Tid: %s, distance: %s. pvt: %s.",
                              tid, dis_current, pvt)

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
                                          tid, day_end_time)
                if mileage_log:
                    dis_day = mileage_log['distance'] + dis
                else:
                    self.db.execute("INSERT INTO T_MILEAGE_LOG(tid, timestamp)"
                                    "  VALUES(%s, %s)",
                                    tid, day_end_time)
                    dis_day = dis

                self.db.execute("INSERT INTO T_MILEAGE_LOG(tid, distance, timestamp)"
                                "  VALUES(%s, %s, %s)"
                                "  ON DUPLICATE KEY"
                                "  UPDATE distance=values(distance)",
                                tid, dis_day, day_end_time)
                logging.info("[EVENTER] Tid: %s, dis_day: %s. pvt: %s.",
                              tid, dis_day, pvt)

    def handle_stop(self, pvt):
        """Handle the stop point.
        """
        flag = self.check_timestamp(int(pvt['gps_time']))
        if not flag: 
            return

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
        
