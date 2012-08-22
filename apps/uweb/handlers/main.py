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

            user_info = QueryHelper.get_user_by_uid(self.current_user.uid, self.db)

            terminals = self.db.query("SELECT ti.id, ti.tid, ti.alias, ti.mobile as sim,"
                                      "  ti.login, ti.cellid_status, ti.keys_num"
                                      "  FROM T_TERMINAL_INFO as ti"
                                      "  WHERE ti.owner_mobile = %s",
                                      user_info.mobile)
            #NOTE: if aliasa is null, provide tid instead
            for terminal in terminals:
                if not terminal.alias:
                    terminal.alias = terminal.sim
            url = "index.html"

        if from_ == 'android':
            self.login_sms_remind(user_info.mobile, terminals, login="ANDROID")
            data = DotDict(uid=self.current_user.uid,
                           name=user.name,
                           cars=terminals,
                           from_=from_)
            self.write_ret(ErrorCode.SUCCESS, dict_=data)
            return

        if from_ == 'ios':
            self.login_sms_remind(user_info.mobile, terminals, login="IOS")
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
