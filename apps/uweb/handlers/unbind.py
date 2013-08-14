# -*- coding: utf-8 -*-

import logging
import datetime
import time

from tornado.escape import json_decode, json_encode
import tornado.web
from tornado.ioloop import IOLoop

from helpers.seqgenerator import SeqGenerator
from helpers.smshelper import SMSHelper
from helpers.queryhelper import QueryHelper
from helpers.gfsenderhelper import GFSenderHelper
from utils.dotdict import DotDict
from utils.misc import get_terminal_sessionID_key, get_del_data_key
from constants import UWEB, GATEWAY

from base import BaseHandler, authenticated
from mixin.base import BaseMixin
from codes.smscode import SMSCode 
from codes.errorcode import ErrorCode


class UNBindHandler(BaseHandler, BaseMixin):

    @authenticated
    @tornado.web.removeslash
    @tornado.web.asynchronous
    def post(self):
        status = ErrorCode.SUCCESS
        try:
            data = DotDict(json_decode(self.request.body))
            tmobile = data.tmobile
            flag = data.get('flag', 0)
            logging.info("[UWEB] unbind request: %s", data)
        except Exception as e:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            self.write_ret(status)
            IOLoop.instance().add_callback(self.finish)
            return 

        try:
            terminal = self.db.get("SELECT id, tid, owner_mobile, login FROM T_TERMINAL_INFO"
                                   "  WHERE mobile = %s"
                                   "    AND service_status = %s",
                                   tmobile, 
                                   UWEB.SERVICE_STATUS.ON)
            if not terminal:
                status = ErrorCode.TERMINAL_NOT_EXISTED
                logging.error("The terminal with tmobile: %s does not exist!", tmobile)
                self.write_ret(status)
                IOLoop.instance().add_callback(self.finish)
                return

            # record the del action 
            self.db.execute("UPDATE T_SUBSCRIPTION_LOG SET del_time = %s, op_type=%s" 
                            "  WHERE tmobile = %s ", 
                            int(time.time()), UWEB.OP_TYPE.DEL, tmobile)

            key = get_del_data_key(terminal.tid)
            self.redis.set(key, flag)
            if terminal.login != GATEWAY.TERMINAL_LOGIN.ONLINE:
                status = self.send_jb_sms(tmobile, terminal.owner_mobile, terminal.tid)
                self.write_ret(status)
                IOLoop.instance().add_callback(self.finish)
                return

            def _on_finish(response):
                status = ErrorCode.SUCCESS
                response = json_decode(response)
                if response['success'] == ErrorCode.SUCCESS:
                    logging.info("[UWEB] uid:%s, tid: %s, tmobile:%s GPRS unbind successfully", 
                                 self.current_user.uid, terminal.tid, tmobile)
                else:
                    status = response['success']
                    # unbind failed. clear sessionID for relogin, then unbind it again
                    sessionID_key = get_terminal_sessionID_key(terminal.tid)
                    self.redis.delete(sessionID_key)
                    logging.error('[UWEB] uid:%s, tid: %s, tmobile:%s GPRS unbind failed, message: %s, send JB sms...', 
                                  self.current_user.uid, terminal.tid, tmobile, ErrorCode.ERROR_MESSAGE[status])
                    status = self.send_jb_sms(tmobile, terminal.owner_mobile, terminal.tid)
                self.write_ret(status)
                IOLoop.instance().add_callback(self.finish)

            seq = str(int(time.time()*1000))[-4:]
            args = DotDict(seq=seq,
                           tid=terminal.tid)
            GFSenderHelper.async_forward(GFSenderHelper.URLS.UNBIND, args, _on_finish)
        except Exception as e:
            logging.exception("[UWEB] tmobile:%s unbind failed. Exception: %s", 
                              data.tmobile, e.args)
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)
            IOLoop.instance().add_callback(self.finish)

