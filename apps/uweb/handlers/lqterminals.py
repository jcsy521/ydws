#!/usr/bin/env python
# -*- coding: utf-8 -*-


import os.path
import site
import logging

TOP_DIR_ = os.path.abspath(os.path.join(__file__, "../../../.."))
site.addsitedir(os.path.join(TOP_DIR_, "libs"))

from db_.mysql import DBConnection
from constants import SMS
from codes.smscode import SMSCode
from helpers.smshelper import SMSHelper

class LqterminalHandler(object):
    def __init__(self):
        self.db = DBConnection().db

    def check_sleep_terminal(self):
        try:
            terminals = self.db.query("SELECT mobile"
                                      "  FROM T_TERMINAL_INFO"
                                      "  WHERE login = 2")
            for terminal in terminals:
                interval = SMS.LQ.WEB
                sms = SMSCode.SMS_LQ % interval
                SMSHelper.send_to_terminal(terminal.mobile, sms)
                logging.info("[UWEB] Lq sleep terminal:%s", terminal.mobile)
        except Exception as e:
            logging.exception("Lq terminals exception.")
