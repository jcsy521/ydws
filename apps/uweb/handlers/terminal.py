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
from mixin.terminal import TerminalMixin 


class TerminalHandler(BaseHandler, TerminalMixin):

    # 9 items
    R_KEY = ['softversion','gsm','gps','vbat','vin','login','plcid','imsi','imei']
    # 7 items
    F_KEY = ['softversion','gsm','gps','vbat','vin','login','plcid']
    # 27 items
    W_KEY = ['psw','domain','freq','trace','pulse','phone','owner_mobile','radius','vib',
             'vibl','pof','lbv','sleep','vibgps','speed','calllock','calldisp','vibcall','sms',
             'vibchk', 'poft','wakeupt','sleept','acclt','acclock','stop_service','cid']

    @authenticated
    @tornado.web.removeslash
    def get(self):
        """Get terminal_info.
        """
        flag = self.get_argument('terminal_info')
        car_sets = []
        if flag == UWEB.TERMINAL_INFO_CATEGORY.F:
            tid = self.get_argument('id')
            for key in self.F_KEY:  
                args = DotDict(seq=SeqGenerator.next(self.db),
                               tid=self.current_user.tid,
                               f_key=key)
                ret = GFSenderHelper.forward(GFSenderHelper.URLS.QUERY, args)
                ret = json_decode(ret)
                if ret['success'] == 0:
                    value = ret[key.upper()]
                    car_sets.append(dict(key=key, 
                                         name=UWEB.TERMINAL_PARAMS[key],
                                         value=value,
                                         unit=UWEB.TERMINAL_UNIT[key]))
                    self.update_terminal_r(key, value, tid)
                else: 
                    #NOTE: when one item failed, abort the flush and return data.
                    logging.error('[UWEB] Query value of %s failed, and abort the flush.', key)
                    self.write_ret(ErrorCode.SUCCESS,
                                   dict_=dict(
                                         id=tid,
                                         car_sets=car_sets))
                    return 
            self.write_ret(ErrorCode.SUCCESS,
                           dict_=dict(
                                 id=tid,
                                 car_sets=car_sets))
        elif flag == UWEB.TERMINAL_INFO_CATEGORY.R:
            data = self.get_terminal_r()
            for key in self.R_KEY:
                car_sets.append(dict(key=key,
                                     name=UWEB.TERMINAL_PARAMS[key],
                                     value=data[key],
                                     unit=UWEB.TERMINAL_UNIT[key]))
            self.write_ret(ErrorCode.SUCCESS,
                           dict_=dict(
                                 id=data.id,
                                 car_sets=car_sets))
        else:
            data = self.get_terminal_w()
            for key in self.W_KEY:
                car_sets.append(dict(key=key,
                                     name=UWEB.TERMINAL_PARAMS[key],
                                     value=data[key],
                                     unit=UWEB.TERMINAL_UNIT[key]))
            self.write_ret(ErrorCode.SUCCESS,
                           dict_=dict(
                                 id=data.id,
                                 car_sets=car_sets))

    @authenticated
    @tornado.web.removeslash
    @tornado.web.asynchronous
    def put(self):
        """Update the params of terminal.
        """
        status = ErrorCode.SUCCESS
        try:
            data = DotDict(json_decode(self.request.body))
            # NOTE: in python, id is a keyword. so use tid instead
            tid = data.id
            key = data.car_sets['key']
            value = data.car_sets['value']
        except Exception as e:
            logging.exception("[UWEB] Set terminal failed. Exception: %s", e.args)
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)
            IOLoop.instance().add_callback(self.finish)
            return 
        
        def _on_finish(response):
            status = ErrorCode.SUCCESS
            response = json_decode(response)
            if response['success'] == 0:
                self.update_terminal_w(key, value, tid)
            else:
                status = response['success'] 
                logging.error("[UWEB] Set terminal failed. status: %s, message: %s", 
                               status, ErrorCode.ERROR_MESSAGE[status] )
            self.write_ret(status)
            IOLoop.instance().add_callback(self.finish)

        args = DotDict(seq=SeqGenerator.next(self.db),
                       tid=self.current_user.tid)
        # add key in args. in the agreement, the key should be in upper
        args[key.upper()] = value
        GFSenderHelper.async_forward(GFSenderHelper.URLS.TERMINAL, args,
                                          _on_finish)

    @authenticated
    @tornado.web.removeslash
    def post(self):
        """Add some params for terminal.
        """
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
