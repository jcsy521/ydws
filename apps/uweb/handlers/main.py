# -*- coding: utf-8 -*-

import time

from tornado.escape import json_encode

from base import BaseHandler, authenticated
from helpers.queryhelper import QueryHelper
from helpers.smshelper import SMSHelper
from constants import UWEB 
from codes.smscode import SMSCode
from codes.errorcode import ErrorCode
from utils.dotdict import DotDict

class MainHandler(BaseHandler):

    # BIG NOTE: never add removeslash decorator here!
    @authenticated
    def get(self):
      
        from_ = self.get_argument('from', '').lower()
        if from_ == "delegation":
            pass

        else:
            user = self.db.get("SELECT name FROM T_USER"
                               "  WHERE uid=%s LIMIT 1",
                               self.current_user.uid)

            umobile = QueryHelper.get_umobile_by_uid(self.current_user.uid, self.db)

            terminals = self.db.query("SELECT tiw.id, tiw.tid, tiw.mobile as sim, tir.login"
                                      "    FROM T_TERMINAL_INFO_R as tir,"
                                      "    T_TERMINAL_INFO_W as tiw " 
                                      "    WHERE tiw.owner_mobile = %s" 
                                      "    AND tir.tid = tiw.tid",
                                      umobile.mobile)
            url = "index.html"

        if from_ == 'android':

            self.login_sms_remind(umobile.mobile, terminals, login="ANDROID")
            data = DotDict(uid=self.current_user.uid,
                           name=user.name,
                           cars=terminals,
                           from_=from_)
            self.write_ret(ErrorCode.SUCCESS, dict_=data)
            return

        self.set_header("P3P", "CP=CAO PSA OUR")
        self.render(url,
                    uid=self.current_user.uid,
                    name=user.name,
                    cars=terminals, 
                    from_=from_)

    def login_sms_remind(self, owner_mobile, terminals, login="WEB"):

        login_time = time.strftime("%Y-%m-%d %H:%M:%S")
        login_method = UWEB.LOGIN_WAY[login] 
        terminal_mobile = u'，'.join(str(terminal.sim) for terminal in terminals)
        remind_sms = SMSCode.SMS_LOGIN_REMIND % (login_time, login_method, owner_mobile, terminal_mobile) 
        SMSHelper.send(self.current_user.uid, remind_sms)
