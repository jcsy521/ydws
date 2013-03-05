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
from utils.misc import get_terminal_sessionID_key, get_terminal_address_key,\
    get_terminal_info_key, get_lq_sms_key, get_lq_interval_key
from constants import UWEB, GATEWAY

from base import BaseHandler, authenticated
from mixin.base import BaseMixin
from codes.smscode import SMSCode 
from codes.errorcode import ErrorCode


class UNBindHandler(BaseHandler, BaseMixin):

    @tornado.web.removeslash
    def post(self):
        status = ErrorCode.SUCCESS
        try:
            data = DotDict(json_decode(self.request.body))
            logging.info("[UWEB] unbind request: %s", data)
        except Exception as e:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            self.write_ret(status)
            return 

        try:
            tmobile = data.tmobile

            terminal = self.db.get("SELECT id, login FROM T_TERMINAL_INFO"
                                   "  WHERE mobile = %s"
                                   "    AND service_status = %s",
                                   tmobile, 
                                   UWEB.SERVICE_STATUS.ON)
            if not terminal:
                status = ErrorCode.TERMINAL_NOT_EXISTED
                logging.error("The terminal with tmobile: %s does not exist!", tmobile)
                self.write_ret(status)
                return
            elif terminal.login == GATEWAY.TERMINAL_LOGIN.OFFLINE:
                status = ErrorCode.TERMINAL_OFFLINE
                logging.error("The terminal with tmobile:%s is offline!", tmobile)
                self.write_ret(status)
                return

            unbind_sms = SMSCode.SMS_UNBIND  
            ret = SMSHelper.send_to_terminal(tmobile, unbind_sms)
            ret = DotDict(json_decode(ret))
            if ret.status == ErrorCode.SUCCESS:
                self.db.execute("UPDATE T_TERMINAL_INFO"
                                "  SET service_status = %s"
                                "  WHERE id = %s",
                                UWEB.SERVICE_STATUS.TO_BE_UNBIND,
                                terminal.id)
                logging.info("[UWEB] tmobile: %s unbind successfully.",
                             tmobile)
            else:
                status = ErrorCode.UNBIND_FAILED
                logging.error("[UWEB] tmobile: %s unbind failed. Message: %s",
                              tmobile, ErrorCode.ERROR_MESSAGE[status])
            self.write_ret(status)
        except Exception as e:
            logging.exception("[UWEB] tmobile:%s unbind failed. Exception: %s", 
                              data.tmobile, e.args)
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)

