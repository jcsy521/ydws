# -*- coding: utf-8 -*-

import logging
import time

import tornado.web

from codes.errorcode import ErrorCode
from codes.smscode import SMSCode
from constants import SMS
from helpers.queryhelper import QueryHelper
from helpers.smshelper import SMSHelper
from utils.misc import get_lq_sms_key, get_lq_interval_key

from mixin.base import  BaseMixin
from base import BaseHandler, authenticated
       
class WakeupHandler(BaseHandler, BaseMixin):
    """Wake up the terminal.
    """

    @authenticated
    @tornado.web.removeslash
    def get(self):
        status = ErrorCode.SUCCESS
        try:
            terminal = QueryHelper.get_terminal_by_tid(self.current_user.tid, self.db)
            if terminal: 

                lq_sms_key = get_lq_sms_key(self.current_user.tid) 
                sms = SMSCode.SMS_LQ % SMS.LQ.WEB 
                SMSHelper.send_to_terminal(self.current_user.sim, sms) 
                self.redis.setvalue(lq_sms_key, True, SMS.LQ_INTERVAL)

                lq_interval_key = get_lq_interval_key(self.current_user.tid) 
                self.redis.setvalue(lq_interval_key, int(time.time()), (SMS.LQ.WEB*60 - 160))
                logging.info("[UWEB] wake up, send %s to Sim: %s", sms, self.current_user.sim) 
            else:
                status = ErrorCode.LOGIN_AGAIN
            self.write_ret(status) 
        except Exception as e:
            logging.exception("[UWEB] uid: %s wake up tid: %s failed.  Exception: %s", 
                              self.current_user.uid, self.current_user.tid, e.args) 
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)
