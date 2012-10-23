# -*- coding: utf-8 -*-

import logging

from tornado.escape import json_decode, json_encode
import tornado.web
from tornado.ioloop import IOLoop

from helpers.seqgenerator import SeqGenerator
from helpers.gfsenderhelper import GFSenderHelper
from helpers.queryhelper import QueryHelper
from utils.misc import get_terminal_info_key 
from utils.dotdict import DotDict
from base import BaseHandler, authenticated
from mixin.base import BaseMixin
from codes.errorcode import ErrorCode
from constants import SMS


class DefendHandler(BaseHandler, BaseMixin):

    @authenticated
    @tornado.web.removeslash
    def get(self):
        status = ErrorCode.SUCCESS
        try:
            terminal = self.db.get("SELECT defend_status"
                                   "  FROM T_TERMINAL_INFO"
                                   "  WHERE tid = %s",
                                   self.current_user.tid)
            if not terminal:
                status = ErrorCode.LOGIN_AGAIN
                logging.error("The terminal with tid: %s does not exist, redirect to login.html", self.current_user.tid)
                self.write_ret(status)
                return

            self.write_ret(status,dict_=DotDict(defend_status=terminal.defend_status))
        except Exception as e:
            logging.exception("[UWEB] uid:%s tid:%s get defed status failed. Exception: %s", 
                              self.current_user.uid, self.current_user.tid, e.args)
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)
            return 

    @authenticated
    @tornado.web.removeslash
    @tornado.web.asynchronous
    def post(self):
        status = ErrorCode.SUCCESS
        try:
            data = DotDict(json_decode(self.request.body))
            logging.info("[UWEB] defend request: %s, uid: %s, tid: %s", 
                         data, self.current_user.uid, self.current_user.tid)
        except Exception as e:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            self.write_ret(status)
            IOLoop.instance().add_callback(self.finish)
            return 

        def _on_finish(response):
            status = ErrorCode.SUCCESS
            response = json_decode(response)
            if response['success'] == ErrorCode.SUCCESS:
                self.db.execute("UPDATE T_TERMINAL_INFO"
                                "  SET defend_status = %s"
                                "  WHERE tid = %s",
                                data.defend_status, self.current_user.tid)

                terminal_info_key = get_terminal_info_key(self.current_user.tid)
                terminal_info = self.redis.getvalue(terminal_info_key)
                terminal_info['defend_status'] = data.defend_status
                self.redis.setvalue(terminal_info_key, terminal_info)
                logging.info("[UWEB] uid:%s, tid:%s  set defend status to %s successfully", 
                             self.current_user.uid,  self.current_user.tid, data.defend_status)
            else:
                if response['success'] in (ErrorCode.TERMINAL_OFFLINE, ErrorCode.TERMINAL_TIME_OUT): 
                    self.send_lq_sms(self.current_user.sim, SMS.LQ.WEB)

                status = response['success'] 
                logging.error('[UWEB] uid:%s tid:%s set defend status to %s failed, message: %s', 
                              self.current_user.uid, self.current_user.tid, data.defend_status, ErrorCode.ERROR_MESSAGE[status])
            self.write_ret(status)
            IOLoop.instance().add_callback(self.finish)

        try:
            terminal = QueryHelper.get_terminal_by_tid(self.current_user.tid, self.db)
            if not terminal:
                status = ErrorCode.LOGIN_AGAIN
                logging.error("The terminal with tid: %s does not exist, redirect to login.html", self.current_user.tid)
                self.write_ret(status)
                IOLoop.instance().add_callback(self.finish)

            args = DotDict(seq=SeqGenerator.next(self.db),
                           tid=self.current_user.tid,
                           defend_status=data.defend_status)

            GFSenderHelper.async_forward(GFSenderHelper.URLS.DEFEND, args, _on_finish)
        except Exception as e:
            logging.exception("[UWEB] uid:%s, tid:%s set defend status to %s failed. Exception: %s", 
                              self.current_user.uid, self.current_user.tid, data.defend_status, e.args)
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)
            IOLoop.instance().add_callback(self.finish)
