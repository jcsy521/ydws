# -*- coding: utf-8 -*-

import logging
import time

from tornado.escape import json_decode

from utils.misc import get_lq_sms_key, get_lq_interval_key
from helpers.smshelper import SMSHelper
from constants import SMS, UWEB
from codes.smscode import SMSCode
from codes.errorcode import ErrorCode


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
            SMSHelper.send_to_terminal(sim, sms) 
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

    def send_jb_sms(self, tmobile, umobile, tid):
        unbind_sms = SMSCode.SMS_UNBIND  
        ret = SMSHelper.send_to_terminal(tmobile, unbind_sms)
        print 'ret', ret
        ret = json_decode(ret)
        status = ret['status']
        if True: 
        #if status == ErrorCode.SUCCESS:
            self.db.execute("UPDATE T_TERMINAL_INFO"
                            "  SET service_status = %s"
                            "  WHERE mobile = %s",
                            UWEB.SERVICE_STATUS.TO_BE_UNBIND,
                            tmobile)
            logging.info("[UWEB] umobile: %s, tid: %s, tmobile: %s SMS unbind successfully.",
                         umobile, tid, tmobile)
        else:
            logging.error("[UWEB] umobile: %s, tid: %s, tmobile: %s SMS unbind failed. Message: %s",
                          umobile, tid, tmobile, ErrorCode.ERROR_MESSAGE[status])

        return status
