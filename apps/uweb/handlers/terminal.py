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
from constants import UWEB
from helpers.queryhelper import QueryHelper  
from mixin.terminal import TerminalMixin 


class TerminalHandler(BaseHandler, TerminalMixin):

    # flush key 8 items, 
    F_KEYS = ['gsm','gps','pbat','freq','pulse','vibchk','trace','white_list','service_status']

    @authenticated
    @tornado.web.removeslash
    def get(self):
        """Get terminal_info.
        workflow:
        if get first:
            get terminal_info from database
        elif flush:
            query terminal_info from terminal itself, then update the database
        """
        status = ErrorCode.SUCCESS
        car_sets = [] 
        flag = self.get_argument('terminal_info','')
        if flag == UWEB.TERMINAL_INFO_CATEGORY.F:
            args = DotDict(seq=SeqGenerator.next(self.db),
                           tid=self.current_user.tid,
                           params=self.F_KEYS)
            ret = GFSenderHelper.forward(GFSenderHelper.URLS.QUERY, args)
            ret = json_decode(ret)
            if ret['success'] == 0:
                for key, value in ret['params'].iteritems():
                    car_sets.append(DotDict(key=key.lower(),
                                            value=value))
                    car_dct = DotDict()
                    for item in car_sets:  
                       car_dct[item.key] = item.value
  
                self.update_terminal_db(car_dct, self.current_user.tid, self.current_user.sim)
            else: 
                status = ErrorCode.FAILED 
                logging.error('[UWEB] Query terminal_info failed.')
        else:            
            # 1: terminal
            terminal = self.db.get("SELECT gsm, gps, pbat, freq, pulse, alias, vibchk,"
                                   "     trace, service_status, cellid_status"
                                   "  FROM T_TERMINAL_INFO"
                                   "  WHERE tid = %s"
                                   "  LIMIT 1",
                                   self.current_user.tid)
            # 2: whitelist
            user = QueryHelper.get_user_by_uid(self.current_user.uid, self.db)
            whitelist = self.db.get("SELECT mobile"
                                    "  FROM T_WHITELIST"
                                    "  WHERE tid = %s"
                                    "  LIMIT 1",
                                    self.current_user.tid)

            # 3: car
            car = self.db.get("SELECT cnum FROM T_CAR"
                              "  WHERE tmobile = %s",
                              self.current_user.sim)

            # add tow dict: terminal, car. add two value: whitelist_1, whitelist_2 
            car_tmp = DotDict()
            car_tmp.update(terminal)
            car_tmp.update(car)
            for key, value in car_tmp.iteritems():
                car_sets.append(DotDict(key=key.lower(),
                                        value=value))
            car_sets.append(DotDict(key='whitelist_1',
                                    value=user.mobile))
            car_sets.append(DotDict(key='whitelist_2',
                                    value=whitelist.mobile if whitelist else ''))

        self.write_ret(status,
                       dict_=dict(car_sets=car_sets))

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
            logging.exception("[UWEB] Set terminal failed. Exception: %s", e.args)
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)
            IOLoop.instance().add_callback(self.finish)
            return 
        
        args = DotDict(seq=SeqGenerator.next(self.db),
                       tid=self.current_user.tid)
        # check the data, some be sent to  
        user = QueryHelper.get_user_by_uid(self.current_user.uid, self.db)
        fields=['alias', 'cnum', 'cellid_status']
        gf_params = DotDict()
        db_params = DotDict()
        for key, value in data.iteritems():
            if key in fields:
                db_params[key]=value
            else:
                if key == 'whitelist_2':
                    key = 'white_list' 
                    gf_params[key]=value+":"+str(user.mobile)
                else:
                    gf_params[key]=value
               
        self.update_terminal_db(db_params, self.current_user.tid, self.current_user.sim) 
        args.params = gf_params 

        def _on_finish(response):
            status = ErrorCode.SUCCESS
            response = json_decode(response)
            if response['success'] == 0:
                self.update_terminal_info(response['params'], data, self.current_user.tid)
            else:
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

    @authenticated
    @tornado.web.removeslash
    def post(self):
        """Some checks for fields.
        """
        # TODO: 
        status = ErrorCode.SUCCESS
        data = DotDict(json_decode(self.request.body))
        check_key = data.check_key
        if check_key == UWEB.CHECK_TERMINAL.MOBILE:
            if not self.check_terminal_by_mobile(data.check_value):
                status = ErrorCode.TERMINAL_MOBILE_EXIST
        elif check_key == UWEB.CHECK_TERMINAL.TID:
            if not self.check_terminal_by_tid(data.check_value):
                status = ErrorCode.TERMINAL_TID_EXIST
        else:
            logging.error("[UWEB] Unknown check_key: %s", check_key)
        self.write_ret(status)

