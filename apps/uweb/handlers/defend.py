# -*- coding: utf-8 -*-

import logging
import datetime
import time
from dateutil.relativedelta import relativedelta

from tornado.escape import json_decode, json_encode
import tornado.web
from tornado.ioloop import IOLoop

from helpers.seqgenerator import SeqGenerator
from helpers.gfsenderhelper import GFSenderHelper
from utils.misc import get_today_last_month
from utils.dotdict import DotDict
from base import BaseHandler, authenticated
from mixin.base import BaseMixin
from codes.errorcode import ErrorCode
from constants import UWEB, SMS


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
                logging.error("The terminal with tid: %s is noexist, redirect to login.html", tid)
                self.write_ret(status)
                return

            self.write_ret(status,dict_=DotDict(defend_status=terminal.defend_status))
        except Exception as e:
            logging.exception("Set terminal failed. Exception: %s", e.args)
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
            print 'data', self.request.body
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
            else:
                if response['success'] in (ErrorCode.TERMINAL_OFFLINE, ErrorCode.TERMINAL_TIME_OUT): 
                    self.send_lq_sms(self.current_user.sim, SMS.LQ.WEB)

                status = response['success'] 
                logging.error('Set defend_status failed. status: %s, message: %s', status, ErrorCode.ERROR_MESSAGE[status] )
            self.write_ret(status)
            IOLoop.instance().add_callback(self.finish)

        try:
           #NOTE: in defend, should invoke get before post. if tid is inexistence, there is no need to handle here.
           args = DotDict(seq=SeqGenerator.next(self.db),
                          tid=self.current_user.tid,
                          defend_status=data.defend_status)

           logging.info("Set defend_status to %d", data.defend_status)
           GFSenderHelper.async_forward(GFSenderHelper.URLS.DEFEND, args, _on_finish)
        except Exception as e:
            logging.exception("Set defend_status failed. Exception: %s", e.args)
            status = ErrorCode.SERVER_ERROR
            self.write_ret(status)
            IOLoop.instance().add_callback(self.finish)
