# -*- coding: utf-8 -*-

import logging
import datetime
import time

from tornado.escape import json_decode, json_encode
import tornado.web
from tornado.ioloop import IOLoop

from helpers.seqgenerator import SeqGenerator
from helpers.queryhelper import QueryHelper
from helpers.gfsenderhelper import GFSenderHelper
from utils.dotdict import DotDict
from utils.misc import get_terminal_sessionID_key, get_terminal_address_key,\
    get_terminal_info_key, get_lq_sms_key, get_lq_interval_key
from constants import SMS

from base import BaseHandler, authenticated
from mixin.base import BaseMixin
from codes.errorcode import ErrorCode


class UNBindHandler(BaseHandler, BaseMixin):

    @authenticated
    @tornado.web.removeslash
    @tornado.web.asynchronous
    def post(self):
        status = ErrorCode.SUCCESS
        try:
            tid  = self.get_argument('tid')
            logging.info("[UWEB] unbind tid: %s, uid: %s", 
                         tid, self.current_user.uid)
        except Exception as e:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            self.write_ret(status)
            IOLoop.instance().add_callback(self.finish)
            return 

        if not tid:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            self.write_ret(status)
            IOLoop.instance().add_callback(self.finish)
            return 

        def _on_finish(response):
            status = ErrorCode.SUCCESS
            response = json_decode(response)
            if response['success'] == ErrorCode.SUCCESS:
                #user = QueryHelper.get_user_by_tid(tid, self.db)
                #self.db.execute("DELETE FROM T_TERMINAL_INFO"
                #                "  WHERE tid = %s",
                #                tid)
                ## clear redis
                #sessionID_key = get_terminal_sessionID_key(tid)
                #address_key = get_terminal_address_key(tid)
                #info_key = get_terminal_info_key(tid)
                #lq_sms_key = get_lq_sms_key(tid)
                #lq_interval_key = get_lq_interval_key(tid)
                #keys = [sessionID_key, address_key, info_key, lq_sms_key, lq_interval_key]
                #self.redis.delete(*keys)
                #terminals = self.db.query("SELECT id"
                #                          "  FROM T_TERMINAL_INFO"
                #                          "  WHERE owner_mobile = %s",
                #                          user.owner_mobile)
                #if len(terminals) == 0:
                #    self.db.execute("DELETE FROM T_USER"
                #                    "  WHERE mobile = %s",
                #                    user.owner_mobile)
                logging.info("[UWEB] uid:%s, tid:%s unbind successfully", 
                             self.current_user.uid, tid)
            else:
                if response['success'] in (ErrorCode.TERMINAL_OFFLINE, ErrorCode.TERMINAL_TIME_OUT): 
                    self.send_lq_sms(self.current_user.sim, tid, SMS.LQ.WEB)

                status = response['success'] 
                logging.error('[UWEB] uid:%s tid:%s unbind failed, message: %s', 
                              self.current_user.uid, tid, ErrorCode.ERROR_MESSAGE[status])
            self.write_ret(status)
            IOLoop.instance().add_callback(self.finish)

        try:
            terminal = QueryHelper.get_terminal_by_tid(tid, self.db)
            if not terminal:
                status = ErrorCode.TERMINAL_NOT_EXISTED
                logging.error("The terminal with tid: %s does not exist!", tid)
                self.write_ret(status)
                IOLoop.instance().add_callback(self.finish)
                return

            seq = str(int(time.time()*1000))[-4:]
            args = DotDict(seq=seq,
                           tid=tid)
            GFSenderHelper.async_forward(GFSenderHelper.URLS.UNBIND, args, _on_finish)
        except Exception as e:
            logging.exception("[UWEB] uid:%s, tid:%s unbind failed. Exception: %s", 
                              self.current_user.uid, tid, e.args)
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)
            IOLoop.instance().add_callback(self.finish)

