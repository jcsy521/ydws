# -*- coding: utf-8 -*-

import logging

import tornado.web
from tornado.escape import json_encode, json_decode

from utils.dotdict import DotDict
from codes.errorcode import ErrorCode
from constants import SMS
from mixin.base import  BaseMixin
from base import BaseHandler, authenticated
       
class SwitchCarHandler(BaseHandler, BaseMixin):
    """Switch current car for the current user.
    """
    @authenticated
    @tornado.web.removeslash
    def get(self, tid):
        status = ErrorCode.SUCCESS
        try:
            terminal = self.db.get("SELECT ti.tid, ti.mobile as sim,"
                                  "  ti.login, ti.defend_status "
                                  "  FROM T_TERMINAL_INFO as ti "
                                  "  WHERE ti.tid = %s"
                                  "  LIMIT 1",
                                  tid)
            if terminal: 
                self.send_lq_sms(self.current_user.sim, SMS.LQ.WEB)
                self.bookkeep(dict(uid=self.current_user.uid,
                                   tid=tid,
                                   sim=terminal.sim))
            else:
                status = ErrorCode.LOGIN_AGAIN
            self.write_ret(status) 
        except Exception as e:
            logging.exception("[UWEB] uid: %s switchcar to tid:%s failed.  Exception: %s", 
                              self.current_user.uid, tid, e.args) 
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)
