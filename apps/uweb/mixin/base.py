# -*- coding: utf-8 -*-

import logging

from utils.misc import get_lq_sms_key
from helpers.smshelper import SMSHelper

from constants import SMS

class BaseMixin(object):

    def send_lq_sms(self, sim, interval):
        """Send LQ Message to terminal.
        """
        lq_sms_key = get_lq_sms_key(sim) 
        if not self.memcached.get(lq_sms_key): 
            sms = "LQ %s" % interval 
            SMSHelper.send(sim, sms) 
            logging.info("Send %s to Sim: %s", sms, sim) 
            self.memcached.set(lq_sms_key, True, SMS.LQ_INTERVAL)
