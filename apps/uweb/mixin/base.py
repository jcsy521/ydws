# -*- coding: utf-8 -*-

import logging
import time


from utils.misc import get_lq_sms_key, get_lq_interval_key
from helpers.smshelper import SMSHelper

from constants import SMS, UWEB
from codes.smscode import SMSCode

class BaseMixin(object):

    def send_lq_sms(self, sim, tid, interval):
        """Send LQ Message to terminal.

        lq_sms_key: when send lq sms to terminal, keep it in redis
        for 3 minutes. in 3 minutes, do not send lq sms twice.

        lq_interval_key: when send lq sms to terminal, keep it in redis
        for interval. in the period of interval, terminal is been awaken. 
        when the period of interval is past, lq_sms should be send again
        """
        lq_sms_key = get_lq_sms_key(tid) 

        lq_interval_key = get_lq_interval_key(tid) 
        self.redis.setvalue(lq_interval_key, int(time.time()), (interval*60 - 160))

        if not self.redis.getvalue(lq_sms_key): 
            sms = SMSCode.SMS_LQ % interval 
#            SMSHelper.send_to_terminal(sim, sms) 
            logging.info("[UWEB] send %s to Sim: %s", sms, sim) 
            self.redis.setvalue(lq_sms_key, True, SMS.LQ_INTERVAL)

    def keep_waking(self, sim, tid):
        """Send LQ Message to terminal.

        lq_sms_key: when send lq sms to terminal, keep it in redis
        for 3 minutes. in 3 minutes, do not send lq sms twice.

        lq_interval_key: when send lq sms to terminal, keep it in redis
        for interval. in the period of interval, terminal is been awaken. 
        when the period of interval is past, lq_sms should be send again
        """
        lq_interval_key = get_lq_interval_key(tid) 
        lq_time = self.redis.getvalue(lq_interval_key)
        if not lq_time:
            self.send_lq_sms(sim, tid, SMS.LQ.WEB)
        else:
            if abs(int(time.time()) - lq_time) < UWEB.WAKEUP_INTERVAL:
                self.send_lq_sms(sim, tid, SMS.LQ.WEB)
