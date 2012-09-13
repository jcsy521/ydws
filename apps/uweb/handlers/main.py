# -*- coding: utf-8 -*-

import time
import logging

from tornado.escape import json_encode

from base import BaseHandler, authenticated
from helpers.queryhelper import QueryHelper
from constants import UWEB 
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
            user_info = QueryHelper.get_user_by_uid(self.current_user.uid, self.db)
            if not user_info:
                status = ErrorCode.LOGIN_AGAIN
                # is nuser_info is None, means cookie is invalid, so redirectlogin.html
                logging.error("The user with uid: %s is noexist, redirect to login.html", self.current_user.uid)
                #self.clear_cookie(self.app_name)
                #self.redirect(self.get_argument("next", "/"))
                self.write_ret(status)
                return

            # terminal which is login show first.
            terminals = self.db.query("SELECT ti.tid, ti.alias, ti.mobile as sim,"
                                      "  ti.login, ti.keys_num"
                                      "  FROM T_TERMINAL_INFO as ti"
                                      "  WHERE ti.owner_mobile = %s ORDER BY LOGIN DESC",
                                      user_info.mobile)
            #NOTE: if alias is null, provide tid instead
            for terminal in terminals:
                if not terminal.alias:
                    terminal.alias = terminal.sim
            url = "index.html"

        self.set_header("P3P", "CP=CAO PSA OUR")
        self.render(url,
                    uid=self.current_user.uid,
                    name=user_info.name,
                    cars=terminals)


