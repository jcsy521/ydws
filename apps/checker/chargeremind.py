#! /usr/bin/env python

import logging
import os.path
import site
import time, calendar 

TOP_DIR_ = os.path.abspath(os.path.join(__file__, "../../../.."))
site.addsitedir(os.path.join(TOP_DIR_, "libs"))


from db_.mysql import DBConnection
from helpers.smshelper import SMSHelper
from codes.smscode import SMSCode


class ChargeRemind(object):
    """
    charge remind per month. 
    """
    def __init__(self):
        self.db = DBConnection().db

    def check_charge_remind(self):
        try:
            terminals = self.db.query("SELECT tid, mobile, owner_mobile, begintime"
                                      "  FROM T_TERMINAL_INFO")
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
                c_days = calendar.monthrange(c_year, c_month) 

                if b_year > c_year:
                    continue 
                elif b_year == c_year and b_month == c_month:
                    # do not remind user on register month
                    continue 
                elif b_day < c_day:
                    continue 
                elif (b_day == c_day) or (b_day > c_days and c_day == c_days):
                    # 1. equal day
                    # 2. has no equal day on this month, send sms on the last day of this month
                    # send charge remind sms
                    if terminal.owner_mobile:
                        content = SMSCode.SMS_CHARGE_REMIND % terminal.mobile
                        SMSHelper.send(terminal.owner_mobile, content)
                        logging.info("[CK] Send charge remind sms to user: %s", terminal.owner_mobile)
        except KeyboardInterrupt:
            logging.error("Ctrl-C is pressed.")
        except Exception as e:
            logging.exception("[CK] Check charge remind exception: %s", e.args)
                
