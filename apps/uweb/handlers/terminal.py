# -*- coding: utf-8 -*-

import logging

import tornado.web
from tornado.escape import json_decode, json_encode
from tornado.ioloop import IOLoop

from helpers.seqgenerator import SeqGenerator
from helpers.gfsenderhelper import GFSenderHelper
from utils.misc import get_today_last_month
from utils.dotdict import DotDict
from base import BaseHandler, authenticated
from codes.errorcode import ErrorCode
from constants import UWEB, SMS
from helpers.queryhelper import QueryHelper  
from mixin.terminal import TerminalMixin 


class TerminalHandler(BaseHandler, TerminalMixin):

    # flush key 8 items, 
    F_KEYS = ['gsm','gps','pbat','freq','pulse','vibchk','trace','white_list','service_status']

    @authenticated
    @tornado.web.removeslash
    def get(self):
        """Get terminal info.
        """
        status = ErrorCode.SUCCESS
        try:
            car_sets = DotDict() 
            terminal = self.db.get("SELECT freq, alias, trace, cellid_status, vibchk, tid as sn, mobile, vibl"
                                   "  FROM T_TERMINAL_INFO"
                                   "  WHERE tid = %s"
                                   "  LIMIT 1",
                                   self.current_user.tid)
            if not terminal:
                status = ErrorCode.LOGIN_AGAIN
                logging.error("The terminal with tid: %s is noexist, redirect to login.html", self.current_user.tid)
                self.write_ret(status)
                return
            # 2: whitelist
            user = QueryHelper.get_user_by_uid(self.current_user.uid, self.db)
            if not user:
                logging.error("The user with uid: %s is noexist, redirect to login.html", self.current_user.uid)
                self.clear_cookie(self.app_name)
                self.write_ret(ErrorCode.LOGIN_AGAIN)
                return

            whitelist = self.db.query("SELECT mobile"
                                      "  FROM T_WHITELIST"
                                      "  WHERE tid = %s",
                                      self.current_user.tid)

            # 3: car
            car = self.db.get("SELECT cnum FROM T_CAR"
                              "  WHERE tid = %s",
                              self.current_user.tid)

            # add tow dict: terminal, car. add two value: whitelist_1, whitelist_2 
            car_sets.update(terminal)
            car_sets.update(car)
            white_list = [user.mobile]
            for item in whitelist: 
                white_list.append(item['mobile'])
            car_sets.update(DotDict(white_list=white_list))

            self.write_ret(status,
                           dict_=dict(car_sets=car_sets))
        except Exception as e: 
            status = ErrorCode.SERVER_BUSY
            logging.exception("Get terminal failed. Exception: %s", e.args) 
            self.write_ret(status)

    @authenticated
    @tornado.web.removeslash
    @tornado.web.asynchronous
    def put(self):
        """Update the params of terminal.
        """
        status = ErrorCode.SUCCESS
        try:
            data = DotDict(json_decode(self.request.body))
        except Exception as e:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            self.write_ret(status)
            IOLoop.instance().add_callback(self.finish)
            return 
        
        try:
            args = DotDict(seq=SeqGenerator.next(self.db),
                           tid=self.current_user.tid)

            # check the data. some be sent to terminal, some just be modified in db 
            user = QueryHelper.get_user_by_uid(self.current_user.uid, self.db)
            if not user:
                status = ErrorCode.LOGIN_AGAIN
                logging.error("The user with uid: %s is noexist, redirect to login.html", self.current_user.uid)
                self.write_ret(status)
                IOLoop.instance().add_callback(self.finish)
                return
   
            db_fields=['alias', 'cnum', 'cellid_status']
            gf_params = DotDict()
            db_params = DotDict()
            for key, value in data.iteritems():
                if key in db_fields:
                    db_params[key]=value
                else:
                    if key == 'white_list':
                        if len(value) == 1:
                            self.db.execute("DELETE FROM T_WHITELIST WHERE tid = %s", self.current_user.tid)
                        gf_params[key]=":".join(value)
                    else:
                        gf_params[key]=value
                   
            self.update_terminal_db(db_params, self.current_user.tid, self.current_user.sim) 
            args.params = gf_params 

            def _on_finish(response):
                status = ErrorCode.SUCCESS
                response = json_decode(response)
                if response['success'] == ErrorCode.SUCCESS:
                    for key, value in response['params'].iteritems():
                        if value != "0":
                            status = ErrorCode.TERMINAL_SET_FAILED
                            break
                    self.update_terminal_info(response['params'], data, self.current_user.tid)
                else:
                    if response['success'] in (ErrorCode.TERMINAL_OFFLINE, ErrorCode.TERMINAL_TIME_OUT): 
                        self.send_lq_sms(self.current_user.sim, SMS.LQ.WEB)
                    status = response['success'] 
                    logging.error("[UWEB] Set terminal failed. status: %s, message: %s", 
                                   status, ErrorCode.ERROR_MESSAGE[status] )
                self.write_ret(status)
                IOLoop.instance().add_callback(self.finish)

            if args.params:
                GFSenderHelper.async_forward(GFSenderHelper.URLS.TERMINAL, args,
                                                  _on_finish)
            else: 
                self.write_ret(status)
                IOLoop.instance().add_callback(self.finish)
        except Exception as e:
            logging.exception("Update detail failed. Exception: %s", e.args)
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)
            IOLoop.instance().add_callback(self.finish)

