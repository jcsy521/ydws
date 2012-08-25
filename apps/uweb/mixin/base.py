# -*- coding: utf-8 -*-

import logging

from utils.misc import get_lq_sms_key, get_lq_interval_key
from helpers.smshelper import SMSHelper

from constants import SMS
from codes.smscode import SMSCode

class BaseMixin(object):

    def send_lq_sms(self, sim, interval):
        """Send LQ Message to terminal.
        """
        lq_sms_key = get_lq_sms_key(sim) 
        # keep the interval_key for interval
        lq_interval_key = get_lq_interval_key(self.current_user.tid) 
        self.redis.setvalue(lq_interval_key, interval*60)
        if not self.redis.getvalue(lq_sms_key): 
            sms = SMSCode.SMS_LQ % interval 
            SMSHelper.send(sim, sms) 
            logging.info("Send %s to Sim: %s", sms, sim) 
            self.redis.setvalue(lq_sms_key, True, SMS.LQ_INTERVAL)
