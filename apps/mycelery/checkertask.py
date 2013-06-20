#!/usr/bin/env python
# -*- coding: utf-8 -*-


import os.path
import site
import logging
import time

TOP_DIR_ = os.path.abspath(os.path.join(__file__, "../../../.."))
site.addsitedir(os.path.join(TOP_DIR_, "libs"))

from tornado.options import define, options, parse_command_line
from db_.mysql import DBConnection
from utils.myredis import MyRedis
from constants import GATEWAY
from codes.smscode import SMSCode
from helpers.smshelper import SMSHelper
from helpers.queryhelper import QueryHelper

if not 'conf' in options:
    define('conf', default=os.path.join(TOP_DIR_, "conf/global.conf"))

class CheckTask(object):

    def __init__(self):
        self.db = DBConnection().db
        self.redis = MyRedis()

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
            logging.exception("[CLERY] Check terminal poweroff timeout exception.")

    def update_sms_flag(self, tid):
        self.db.execute("UPDATE T_POWEROFF_TIMEOUT"
                        "  SET sms_flag = %s"
                        "  WHERE tid = %s",
                        GATEWAY.POWEROFF_TIMEOUT_SMS.SEND, tid)

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
                

def check_poweroff():
    ct = CheckTask()
    ct.check_poweroff_timeout()

#def check_charge():
#    ct = CheckTask()
#    ct.check_charge_remind()

if __name__ == '__main__':
    ConfHelper.load(options.conf)
    parse_command_line()
    check_poweroff()
    #check_charge()
else: 
    try: 
        from celery.decorators import task 
        check_poweroff = task(ignore_result=True)(check_poweroff) 
        #check_charge= task(ignore_result=True)(check_charge) 
    except Exception as e: 
        logging.exception("[CELERY] admintask statistic failed. Exception: %s", e.args)

