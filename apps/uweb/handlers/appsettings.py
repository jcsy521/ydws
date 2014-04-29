# -*- coding: utf-8 -*-

import logging
import time

import tornado.web
from tornado.escape import json_decode, json_encode
from tornado.ioloop import IOLoop

from helpers.seqgenerator import SeqGenerator
from helpers.gfsenderhelper import GFSenderHelper
from utils.misc import get_today_last_month
from utils.dotdict import DotDict
from utils.checker import check_sql_injection
from base import BaseHandler, authenticated
from codes.errorcode import ErrorCode
from constants import UWEB, SMS, GATEWAY
from helpers.queryhelper import QueryHelper  
from mixin.terminal import TerminalMixin 


class AppSettingsHandler(BaseHandler, TerminalMixin):

    @authenticated
    @tornado.web.removeslash
    def get(self):
        """Get terminal info.
        """
        status = ErrorCode.SUCCESS
        try:
            tid = self.get_argument('tid',None) 
            # check tid whether exist in request and update current_user
            self.check_tid(tid)
  
            ## part 1: terminal
            tracker = DotDict() 
            # 1: terminal 
            terminal = self.db.get("SELECT white_pop as sos_pop, push_status, vibl, static_val, move_val, owner_mobile"
                                   "  FROM T_TERMINAL_INFO"
                                   "  WHERE trim(tid) = %s"
                                   "    AND service_status = %s"
                                   "  LIMIT 1",
                                   self.current_user.tid,
                                   UWEB.SERVICE_STATUS.ON)
            if not terminal:
                status = ErrorCode.LOGIN_AGAIN
                logging.error("The terminal with tid: %s does not exist, redirect to login.html", self.current_user.tid)
                self.write_ret(status)
                return
            else:
                if terminal['move_val'] == 0:  # move_val:0, static_val: 120 
                    terminal['parking_defend'] = 1
                else: # move_val:60, static_val:0  
                    terminal['parking_defend'] = 0
            # 2: sos 
            user = QueryHelper.get_user_by_uid(self.current_user.uid, self.db)
            if not user:
                logging.error("The user with uid: %s does not exist, redirect to login.html", self.current_user.uid)
                self.clear_cookie(self.app_name)
                self.write_ret(ErrorCode.LOGIN_AGAIN)
                return

            sos = self.db.get("SELECT mobile"
                              "  FROM T_WHITELIST"
                              "  WHERE trim(tid) = %s lIMIT 1",
                              self.current_user.tid)
            #NOTE: if sos is null, provide some default value.
            if not sos:
                sos = dict(mobile='')
            tracker.update(sos)
            tracker.update(dict(push_status=terminal.push_status))
            tracker.update(dict(sos_pop=terminal.sos_pop))
            tracker.update(dict(vibl=terminal.vibl))
            tracker.update(dict(static_val=terminal.static_val)) 
            tracker.update(dict(parking_defend=terminal.parking_defend)) 
            tracker.update(dict(owner_mobile=terminal.owner_mobile)) 
            ## part 2: profile

            profile = DotDict()
            # 1: user
            user = self.db.get("SELECT name, mobile, email"
                               "  FROM T_USER"
                               "  WHERE uid = %s"
                               "  LIMIT 1",
                               self.current_user.uid) 
            if not user:
                status = ErrorCode.LOGIN_AGAIN
                logging.error("The user with uid: %s does not exist, redirect to login.html", self.current_user.uid)
                self.write_ret(status)
                return
            
            # 2: car
            car = self.db.get("SELECT cnum FROM T_CAR"
                              "  WHERE trim(tid) = %s",
                              self.current_user.tid)
            
            profile.update(user)
            profile.update(car)

            ## part 3: sms option
            sms_options = self.db.get("SELECT login, powerlow, powerdown, illegalshake,"
                                      "       illegalmove, sos, heartbeat_lost, charge,"
                                      "       region_enter, region_out"
                                      "  FROM T_SMS_OPTION"
                                      "  WHERE uid = %s"
                                      "  LIMIT 1",
                                      self.current_user.uid) 
            ### part 4: email option
            #email_options = self.db.get("SELECT login, powerlow, illegalshake,"
            #                            "       illegalmove, sos, heartbeat_lost, charge"
            #                            "  FROM T_EMAIL_OPTION"
            #                            "  WHERE uid = %s"
            #                            "  LIMIT 1",
            #                            self.current_user.uid) 
            
            ## part 5: corp info
            corp = DotDict()
            corp = self.db.get("SELECT name c_name, mobile c_mobile, alert_mobile c_alert_mobile, address c_address, email c_email, linkman c_linkman"
                               "  FROM T_CORP"
                               "  WHERE cid = %s"
                               "  LIMIT 1",
                               self.current_user.cid)

            self.write_ret(status,
                           dict_=dict(tracker=tracker,
                                      sms_options=sms_options,
                                      #email_options=email_options,
                                      profile=profile,
                                      corp=corp))
        except Exception as e: 
            status = ErrorCode.SERVER_BUSY
            logging.exception("[UWEB] uid: %s tid: %s get terminal failed. Exception: %s", 
                              self.current_user.uid, self.current_user.tid, e.args) 
            self.write_ret(status)
