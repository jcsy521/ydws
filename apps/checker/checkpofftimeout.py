#!/usr/bin/env python
# -*- coding: utf-8 -*-


import os.path
import site
import logging
import time

TOP_DIR_ = os.path.abspath(os.path.join(__file__, "../../../.."))
site.addsitedir(os.path.join(TOP_DIR_, "libs"))

from db_.mysql import DBConnection
from utils.myredis import MyRedis
from constants import GATEWAY
from codes.smscode import SMSCode
from helpers.smshelper import SMSHelper
from helpers.queryhelper import QueryHelper

class Checkpofftimeout(object):
    def __init__(self):
        self.db = DBConnection().db
        self.redis = MyRedis()

    def check_poweroff_timeout(self):
        try:
            terminals = self.db.query("SELECT tpt.tid, tpt.sms_flag, tpt.timestamp"
                                      "  FROM T_POWEROFF_TIMEOUT as tpt, T_TERMINAL_INFO as tti"
                                      "  WHERE tti.tid = tpt.tid"
                                      "  AND tti.login = %s"
                                      "  AND tpt.sms_flag = %s"
                                      "  AND tti.pbat < 5"
                                      "  AND tpt.timestamp < %s",
                                      GATEWAY.TERMINAL_LOGIN.OFFLINE, GATEWAY.POWEROFF_TIMEOUT_SMS.UNSEND, (time.time() - 2*60*60))
            for terminal in terminals:
                t_name = QueryHelper.get_alias_by_tid(terminal.tid, self.redis, self.db)
                user = QueryHelper.get_user_by_tid(terminal.tid, self.db)
                sms = SMSCode.SMS_POWEROFF_TIMEOUT % t_name 
                SMSHelper.send(user.owner_mobile, sms)
                self.update_sms_flag(terminal.tid)
                logging.info("[CK] Send poweroff timeout sms to user:%s, tid:%s", user.owner_mobile, terminal.tid)
        except KeyboardInterrupt:
            logging.error("Ctrl-C is pressed.")
        except Exception as e:
            logging.exception("[CK] Check terminal poweroff timeout exception.")

    def update_sms_flag(self, tid):
        self.db.execute("UPDATE T_POWEROFF_TIMEOUT"
                        "  SET sms_flag = %s"
                        "  WHERE tid = %s",
                        GATEWAY.POWEROFF_TIMEOUT_SMS.SEND, tid)
