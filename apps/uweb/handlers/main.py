# -*- coding: utf-8 -*-

import time
import logging

from tornado.escape import json_encode

from base import BaseHandler, authenticated
from helpers.queryhelper import QueryHelper
from helpers.confhelper import ConfHelper
from constants import UWEB, GATEWAY
from codes.errorcode import ErrorCode
from utils.dotdict import DotDict

class MainHandler(BaseHandler):

    # BIG NOTE: never add removeslash decorator here!
    @authenticated
    def get(self):
        status=ErrorCode.SUCCESS
        from_ = self.get_argument('from', '').lower()
        index_html = "index.html"
        if self.current_user.cid != UWEB.DUMMY_CID:
            index_html = "index_corp.html"
            user_info = QueryHelper.get_corp_by_cid(self.current_user.cid, self.db)
            name = user_info.linkman if user_info else u''
        else:
            user_info = QueryHelper.get_user_by_uid(self.current_user.uid, self.db)
            name = user_info.name if user_info else u''
        if not user_info:
            status = ErrorCode.LOGIN_AGAIN
            logging.error("The user with uid: %s does not exist, redirect to login.html", self.current_user.uid)
            self.render("index.html",
                        status=status)
            return

        if from_ == "delegation":
            terminals = self.db.query("SELECT ti.tid, ti.login, ti.keys_num, tc.cnum AS alias"
                                      "  FROM T_TERMINAL_INFO as ti, T_CAR as tc"
                                      "  WHERE ti.tid = %s"
                                      "    AND ti.tid = tc.tid"
                                      "    AND ti.service_status = %s",
                                      self.current_user.tid,
                                      UWEB.SERVICE_STATUS.ON)

        else:
            terminals = self.db.query("SELECT ti.tid, ti.login, ti.keys_num, tc.cnum AS alias"
                                      "  FROM T_TERMINAL_INFO as ti, T_CAR as tc"
                                      "  WHERE ti.owner_mobile = %s"
                                      "    AND ti.tid = tc.tid"
                                      "    AND ti.service_status = %s"
                                      "    ORDER BY LOGIN DESC",
                                      user_info.mobile,
                                      UWEB.SERVICE_STATUS.ON)

        #if alias is null, provide cnum or sim instead
        for terminal in terminals:
            terminal['keys_num'] = 0
            if terminal['login'] == GATEWAY.TERMINAL_LOGIN.SLEEP:
                terminal['login'] = GATEWAY.TERMINAL_LOGIN.ONLINE
            if not terminal['alias']:
                terminal['alias'] = terminal.mobile

        self.render(index_html,
                    map_type=ConfHelper.LBMP_CONF.map_type,
                    status=status,
                    name=name,
                    cars=terminals)
