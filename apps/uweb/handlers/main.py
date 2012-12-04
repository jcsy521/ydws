# -*- coding: utf-8 -*-

import time
import logging

from tornado.escape import json_encode

from base import BaseHandler, authenticated
from helpers.queryhelper import QueryHelper
from constants import UWEB, GATEWAY
from codes.errorcode import ErrorCode
from utils.dotdict import DotDict

class MainHandler(BaseHandler):

    # BIG NOTE: never add removeslash decorator here!
    @authenticated
    def get(self):
      
        status=ErrorCode.SUCCESS
        from_ = self.get_argument('from', '').lower()

        user_info = QueryHelper.get_user_by_uid(self.current_user.uid, self.db)
        if not user_info:
            status = ErrorCode.LOGIN_AGAIN
            logging.error("The user with uid: %s does not exist, redirect to login.html", self.current_user.uid)
            self.render("index.html",
                        status=status)
            return

        if from_ == "delegation":
            terminals = self.db.query("SELECT ti.tid, ti.mobile, ti.login, ti.keys_num, tc.cnum AS alias"
                                      "  FROM T_TERMINAL_INFO as ti, T_CAR as tc"
                                      "  WHERE ti.tid = %s"
                                      "    AND ti.tid = tc.tid",
                                      self.current_user.tid)

        else:
            terminals = self.db.query("SELECT ti.tid, ti.mobile, ti.login, ti.keys_num, tc.cnum AS alias"
                                      "  FROM T_TERMINAL_INFO as ti, T_CAR as tc"
                                      "  WHERE ti.owner_mobile = %s"
                                      "    AND ti.tid = tc.tid"
                                      "    ORDER BY LOGIN DESC",
                                      user_info.mobile)

        #if alias is null, provide cnum or sim instead
        for terminal in terminals:
            terminal['keys_num'] = 0
            if terminal['login'] == GATEWAY.TERMINAL_LOGIN.SLEEP:
                terminal['login'] = GATEWAY.TERMINAL_LOGIN.ONLINE
            if not terminal['alias']:
                terminal['alias'] = terminal.mobile

        self.render("index.html",
                    status=status,
                    uid=self.current_user.uid,
                    name=user_info.name,
                    cars=terminals)
