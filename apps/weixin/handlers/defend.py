# -*- coding: utf-8 -*-

import logging
import MySQLdb

import tornado.web
from tornado.escape import json_decode, json_encode

from base import BaseHandler, authenticated
from codes.wxerrorcode import WXErrorCode
from utils.dotdict import DotDict


class DefendHandler(BaseHandler):

    @tornado.web.removeslash
    def get(self):
        status = WXErrorCode.SUCCESS
        try:
            tid = self.get_argument('tid', None)
            terminal = self.db.get("SELECT mannual_status, defend_status, service_status"
                                   "FROM T_TERMINAL_INFO WHERE tid =%s", tid)

            if terminal:
                service_status = terminal['service_status']
                if int(service_status) == 0:
                    status = WXErrorCode.OUTSERVICE
                    self.write_ret(status=status,
                                   message=WXErrorCode.ERROR_MESSAGE[status])
                    return

            self.write_ret(status=status,
                           dict_=DotDict(defend_status=terminal.defend_status,
                                         mannual_status=terminal.mannual_status))

        except Exception as e:
            logging.exception("[WEIXIN] tid:%s get defend status failed. Exception: %s",
                              tid, e.args)
            status = WXErrorCode.SERVER_BUSY
            self.write_ret(status=status,
                           message=WXErrorCode.ERROR_MESSAGE[status])
            return

    @tornado.web.removeslash
    def post(self):
        status = WXErrorCode.SUCCESS
        try:
            data = DotDict(json_decode(self.request.body))
            tid = data.get('tid', None)
            mannual_status = data.get('mannual_status', None)
            
            terminal = self.db.get("SELECT mannual_status, defend_status, service_status FROM T_TERMINAL_INFO WHERE tid = %s ", tid)

            if terminal:
                service_status = terminal['service_status']
                if int(service_status) == 0:
                    status = WXErrorCode.OUTSERVICE
                    self.write_ret(status=status,
                                   message=WXErrorCode.ERROR_MESSAGE[status])
                    return

             
            try:
                self.db.execute("UPDATE T_TERMINAL_INFO SET mannual_status = %s"
                                "WHERE tid = %s", mannual_status, tid)
            except MySQLdb.Error as e:
                logging.exception("[WEIXIN] execute update sql terminal:%s mannual_stauts failed ",
                                  tid, e.args)
                status = WXErrorCode.SERVER_BUSY

            self.write_ret(status=status,
                           message=WXErrorCode.ERROR_MESSAGE[status])

        except Exception as e:
            logging.exception("[WEIXIN] update terminal:%s mannual_stauts failed", tid)
            status = WXErrorCode.FAILED
            self.write_ret(status=status,
                           message=WXErrorCode.ERROR_MESSAGE[status])






