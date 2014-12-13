# -*- coding: utf-8 -*-

"""This module is designed for waking-up terminal. Now it's unused.

#NOTE: deprecated.
"""

import logging
import time

import tornado.web

from codes.errorcode import ErrorCode
from codes.smscode import SMSCode
from constants import SMS, UWEB
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
            tid = self.get_argument('tid',None) 
            # check tid whether exist in request and update current_user
            self.check_tid(tid)

            terminal = self.db.get("SELECT id FROM T_TERMINAL_INFO"
                                   "  WHERE tid = %s"
                                   "    AND service_status = %s",
                                   self.current_user.tid,
                                   UWEB.SERVICE_STATUS.ON)
            if terminal: 
                lq_sms_key = get_lq_sms_key(self.current_user.tid) 
                sms = SMSCode.SMS_LQ % SMS.LQ.WEB 
                biz_type = QueryHelper.get_biz_type_by_tmobile(self.current_user.sim, self.db)
                if biz_type != UWEB.BIZ_TYPE.YDWS:
                    pass
                else:
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
