#!/usr/bin/env python
# -*- coding: utf-8 -*-


import os.path
import site
import logging
import time
import datetime

TOP_DIR_ = os.path.abspath(os.path.join(__file__, "../../.."))
site.addsitedir(os.path.join(TOP_DIR_, "libs"))

from tornado.options import define, options, parse_command_line
from db_.mysql import DBConnection
from utils.myredis import MyRedis
from utils.misc import get_track_key, get_terminal_sessionID_key, get_terminal_time, safe_unicode
from constants import GATEWAY,UWEB
from codes.smscode import SMSCode
from helpers.smshelper import SMSHelper
from helpers.queryhelper import QueryHelper
from helpers.confhelper import ConfHelper

if not 'conf' in options:
    define('conf', default=os.path.join(TOP_DIR_, "conf/global.conf"))

class CheckTask(object):

    def __init__(self):
        self.db = DBConnection().db
        self.redis = MyRedis()

    def check_track_status(self):
        logging.info("[CELERY] checkertask check track status started.")
        try:
            terminals = self.db.query("SELECT tid FROM T_TERMINAL_INFO"
                                      "  WHERE track = 1"
                                      "    AND service_status = 1")
            for terminal in terminals:
                track_key = get_track_key(terminal.tid)
                track = self.redis.get(track_key)
                logging.info("[CK] track: %s, tid: %s", track, terminal.tid)
                if not track:
                    self.db.execute("UPDATE T_TERMINAL_INFO"
                                    "  SET track = 0"
                                    "  WHERE tid = %s LIMIT 1",
                                    terminal.tid)
                    sessionID_key = get_terminal_sessionID_key(terminal.tid)
                    self.redis.delete(sessionID_key)
                    logging.info("[CK] Turn off track of terminal: %s", terminal.tid)
        except Exception as e:
            logging.exception("[CELERY] Check track status exception.")

    def check_poweroff_timeout(self):
        logging.info("[CELERY] checkertask check poweroff timeout started.")
        try:
            terminals = self.db.query("SELECT tpt.tid, tpt.sms_flag, tpt.timestamp"
                                      "  FROM T_POWEROFF_TIMEOUT as tpt, T_TERMINAL_INFO as tti"
                                      "  WHERE tti.tid = tpt.tid"
                                      "  AND tti.service_status = 1"
                                      "  AND tti.login = %s"
                                      "  AND tpt.sms_flag = %s"
                                      "  AND tpt.timestamp < %s",
                                      GATEWAY.TERMINAL_LOGIN.OFFLINE, GATEWAY.POWEROFF_TIMEOUT_SMS.UNSEND, (time.time() - 2*60*60))
            for terminal in terminals:
                terminal_info = QueryHelper.get_terminal_info(terminal.tid, self.db, self.redis)
                if int(terminal_info['pbat']) < 5:
                    user = QueryHelper.get_user_by_tid(terminal.tid, self.db)
                    sms = SMSCode.SMS_POWEROFF_TIMEOUT % terminal_info['alias'] 
                    SMSHelper.send(user.owner_mobile, sms)
                    self.update_sms_flag(terminal.tid)
                    logging.info("[CELERY] Send poweroff timeout sms to user:%s, tid:%s", user.owner_mobile, terminal.tid)
        except Exception as e:
            logging.exception("[CELERY] Check terminal poweroff timeout exception.")

    def update_sms_flag(self, tid):
        self.db.execute("UPDATE T_POWEROFF_TIMEOUT"
                        "  SET sms_flag = %s"
                        "  WHERE tid = %s",
                        GATEWAY.POWEROFF_TIMEOUT_SMS.SEND, tid)

    def send_offline_remind_sms(self):
        logging.info("[CELERY] checkertask send offline remind sms started.")
        try:
            currenttime = int(time.time())

            terminals = self.db.query("SELECT tid, alias, mobile, owner_mobile, offline_time"
                                      "  FROM T_TERMINAL_INFO"
                                      "  WHERE login = 0"
                                      "  AND service_status = 1"
                                      "  AND offline_time < %s",
                                      (currenttime - 24*60*60))
            for terminal in terminals:
                sms_option = QueryHelper.get_sms_option_by_uid(terminal.owner_mobile, 'heartbeat_lost', self.db)
                if sms_option and sms_option.heartbeat_lost == UWEB.SMS_OPTION.SEND:
                    ctime = get_terminal_time(currenttime)
                    ctime = safe_unicode(ctime)

                    alias = terminal['alias'] if terminal['alias'] else terminal['mobile']
                    sms = SMSCode.SMS_HEARTBEAT_LOST % (alias, ctime)
                    SMSHelper.send(terminal.owner_mobile, sms)
                    logging.info("[CELERY] Send offline remind sms to user:%s, tid:%s", terminal.owner_mobile, terminal.tid)
           
            logging.info("[CELERY] checkertask send offline remind sms finished.")
        except Exception as e:
            logging.exception("[CELERY] Check terminal poweroff timeout exception.")


    def check_charge_remind(self):
        logging.exception("[CELERY] checkertask charge remind started")
        try:
            terminals = self.db.query("SELECT tid, mobile, owner_mobile, begintime"
                                      "  FROM T_TERMINAL_INFO "
                                      "  WHERE service_status = 1")
            for terminal in terminals:
                begintime = int(terminal.begintime)
                begintime = time.strftime("%Y,%m,%d", time.localtime(begintime)).split(",")
                b_year = int(begintime[0])
                b_month = int(begintime[1])
                b_day = int(begintime[2])

                currenttime = int(time.time())
                currenttime = time.strftime("%Y,%m,%d", time.localtime(currenttime)).split(",")
                c_year = int(currenttime[0])
                c_month = int(currenttime[1])
                c_day = int(currenttime[2])
                # get days of current month
                days = calendar.monthrange(c_year, c_month)[1]

                if b_year > c_year:
                    continue 
                elif b_year == c_year and b_month == c_month:
                    # do not remind user on register month
                    continue 
                elif b_day < c_day:
                    continue 
                elif (b_day == c_day) or (b_day > days and c_day == days):
                    # 1. equal day
                    # 2. has no equal day on this month, send sms on the last day of this month
                    # send charge remind sms
                    if terminal.owner_mobile:
                        content = SMSCode.SMS_CHARGE_REMIND % terminal.mobile
                        SMSHelper.send(terminal.owner_mobile, content)
                        logging.info("[CELERY] Send charge remind sms to user: %s", terminal.owner_mobile)
        except Exception as e:
            logging.exception("[CELERY] Check charge remind exception: %s", e.args)

    def mileage_notify(self):
        logging.info("[CELERY] checkertask mileage_notify started.")
        try:
            #NOTE: avoid sms is sent when the server is restart.
            _date = datetime.datetime.fromtimestamp(int(time.time()))
            if _date.hour not in (9,10):
                return
                
            #NOTE: get all terminals which may be notified, record them into T_MILEAGE_NOTIFICATION.
            terminals = self.db.query("SELECT tid, distance_notification, notify_count, left_days"
                                      "  FROM T_MILEAGE_NOTIFICATION"
                                      "  WHERE distance_notification != 0"
                                      "  AND notify_count < 3")
            for terminal in terminals:
                terminal_info = QueryHelper.get_terminal_info(terminal.tid, self.db, self.redis)
                tid = terminal['tid']

                owner_mobile = terminal_info['owner_mobile']
                assist_mobile = terminal_info['assist_mobile']
                distance_current = terminal_info['distance_current']
                mobile = terminal_info['mobile']

                notify_count = terminal['notify_count']
                left_days = terminal['left_days']
                distance_notification= terminal['distance_notification']
                if left_days == 1: # it should be notified this day                           
                    logging.info("[CELERY] Send mileage notification."
                                 "  tid: %s, mobile: %s, owner_mobile: %s, assist_mobile: %s,"
                                 "  distance_notification: %s, distance_current: %s," 
                                 "  notify_count: %s, left_days: %s.", 
                                 tid, mobile, owner_mobile, assist_mobile, distance_notification, 
                                 distance_current, notify_count, left_days)
                    self.db.execute("UPDATE T_MILEAGE_NOTIFICATION"
                                    "  SET notify_count = %s,"
                                    "      left_days = %s"
                                    "  WHERE tid = %s",
                                    notify_count+1, 3, tid)
                    distance_current_ = int(round(distance_current/1000.0))
                    if owner_mobile:
                        sms = SMSCode.SMS_NOTIFY % (distance_current_, terminal_info['alias'])
                        SMSHelper.send(owner_mobile, sms)
                    if assist_mobile:
                        user = QueryHelper.get_user_by_mobile(owner_mobile, self.db)
                        name = safe_unicode(user['name'])
                        sms = SMSCode.SMS_NOTIFY_ASSIST % (mobile, owner_mobile, name, distance_current_)
                        SMSHelper.send(assist_mobile, sms)
                elif left_days in (2, 3): # do not notify, just postpone one day
                    logging.info("[CELERY] Do not send mileage notification this day,"
                                 "  just modify the left_days."
                                 "  tid: %s, mobile: %s, owner_mobile: %s, assist_mobile: %s,"
                                 "  distance_notification: %s, distance_current: %s," 
                                 "  notify_count: %s, left_days: %s.", 
                                 tid, mobile, owner_mobile, assist_mobile, distance_notification, 
                                 distance_current, notify_count, left_days)
                    self.db.execute("UPDATE T_MILEAGE_NOTIFICATION"
                                    "  SET left_days = %s"
                                    "  WHERE tid = %s",
                                    left_days-1,
                                    tid)
                else: #NOTE: It should never occur.
                    logging.info("[CELERY] Invalid left_days: %s, mobile: %s.", 
                                left_days, mobile)
                    
        except Exception as e:
            logging.exception("[CELERY] Mileage notification failed. Exception: %s.",
                              e.args)

    def day_notify(self):
        logging.info("[CELERY] checkertask day_notify started.")
        try:
            #NOTE: avoid sms is sent when the server is restart.
            _date = datetime.datetime.fromtimestamp(int(time.time()))
            if _date.hour not in (9,10):
                return
                
            #NOTE: get all terminals which may be notified, record them into T_MILEAGE_NOTIFICATION.
            terminals = self.db.query("SELECT tid, day_notification, notify_count, left_days"
                                      "  FROM T_DAY_NOTIFICATION"
                                      "  WHERE day_notification != 0"
                                      "  AND notify_count < 3")
            for terminal in terminals:
                if int(time.time()) < terminal['day_notification']:
                    # it's not time to notify
                    continue

                terminal_info = QueryHelper.get_terminal_info(terminal.tid, self.db, self.redis)
                tid = terminal['tid']

                owner_mobile = terminal_info['owner_mobile']
                assist_mobile = terminal_info['assist_mobile']
                distance_current = terminal_info['distance_current']
                mobile = terminal_info['mobile']

                notify_count = terminal['notify_count']
                left_days = terminal['left_days']
                day_notification= terminal['day_notification']

                if left_days == 1: # it should be notified this day                           
                    logging.info("[CELERY] Send day notification."
                                 "  tid: %s, mobile: %s, owner_mobile: %s, assist_mobile: %s,"
                                 "  day_notification: %s" 
                                 "  notify_count: %s, left_days: %s.", 
                                 tid, mobile, owner_mobile, assist_mobile, day_notification, 
                                 notify_count, left_days)
                    self.db.execute("UPDATE T_DAY_NOTIFICATION"
                                    "  SET notify_count = %s,"
                                    "      left_days = %s"
                                    "  WHERE tid = %s",
                                    notify_count+1, 3, tid)
                    if owner_mobile:
                        sms = SMSCode.SMS_NOTIFY_DAY % (terminal_info['alias'])
                        SMSHelper.send(owner_mobile, sms)
                    if assist_mobile:
                        user = QueryHelper.get_user_by_mobile(owner_mobile, self.db)
                        name = safe_unicode(user['name'])
                        sms = SMSCode.SMS_NOTIFY_ASSIST_DAY % (mobile, owner_mobile, name)
                        SMSHelper.send(assist_mobile, sms)
                elif left_days in (2, 3): # do not notify, just postpone one day
                    logging.info("[CELERY] Do not send day notification this day,"
                                 "  just modify the left_days."
                                 "  tid: %s, mobile: %s, owner_mobile: %s, assist_mobile: %s,"
                                 "  day_notification: %s" 
                                 "  notify_count: %s, left_days: %s.", 
                                 tid, mobile, owner_mobile, assist_mobile, day_notification, 
                                 notify_count, left_days)
                    self.db.execute("UPDATE T_DAY_NOTIFICATION"
                                    "  SET left_days = %s"
                                    "  WHERE tid = %s",
                                    left_days-1,
                                    tid)
                else: #NOTE: It should never occur.
                    logging.info("[CELERY] Invalid left_days: %s, mobile: %s.", 
                                left_days, mobile)
                    
        except Exception as e:
            logging.exception("[CELERY] Day notification failed. Exception: %s.",
                              e.args)

def check_poweroff():
    ct = CheckTask()
    ct.check_poweroff_timeout()

#def check_charge():
#    ct = CheckTask()
#    ct.check_charge_remind()

def check_track():
    ct = CheckTask()
    ct.check_track_status()

def offline_remind():
    ct = CheckTask()
    ct.send_offline_remind_sms()

def mileage_notify():
    ct = CheckTask()
    ct.mileage_notify()

def day_notify():
    ct = CheckTask()
    ct.day_notify()

if __name__ == '__main__':
    ConfHelper.load(options.conf)
    parse_command_line()
    #check_charge()
    #offline_remind()
    #mileage_notify()
    day_notify()
else: 
    try: 
        from celery.decorators import task 
        check_poweroff = task(ignore_result=True)(check_poweroff) 
        #check_charge= task(ignore_result=True)(check_charge) 
        check_track = task(ignore_result=True)(check_track)
        offline_remind = task(ignore_result=True)(offline_remind)
        mileage_notify = task(ignore_result=True)(mileage_notify)
    except Exception as e: 
        logging.exception("[CELERY] admintask statistic failed. Exception: %s", e.args)

