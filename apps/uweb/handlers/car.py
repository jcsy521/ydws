# -*- coding: utf-8 -*-

import logging

import tornado.web
from tornado.escape import json_encode, json_decode

from utils.misc import DUMMY_IDS
from utils.dotdict import DotDict
from codes.errorcode import ErrorCode
from constants import UWEB, SMS
from mixin.base import  BaseMixin
from base import BaseHandler, authenticated

       
class SwitchCarHandler(BaseHandler, BaseMixin):
    """Switch current car for the current user.
    """
    @authenticated
    @tornado.web.removeslash
    def get(self, tid):
        try:
            monitor = self.db.get("SELECT ti.tid, ti.mobile as sim,"
                                  "  ti.login, ti.defend_status "
                                  "  FROM T_TERMINAL_INFO as ti "
                                  "  WHERE ti.tid = %s"
                                  "  LIMIT 1",
                                  tid)
            if monitor: 
                self.send_lq_sms(self.current_user.sim, SMS.LQ.WEB)
                
                self.bookkeep(dict(uid=self.current_user.uid,
                                   tid=tid,
                                   sim=monitor.sim))
                status = ErrorCode.SUCCESS
                self.write_ret(status) 
            else:
                status = ErrorCode.NO_TERMINAL
                self.write_ret(status) 
        except Exception as e:
            logging.exception("Switchcar failded. Exception: %s", e.args) 
            status = ErrorCode.SERVER_ERROR        
            self.write_ret(status)
