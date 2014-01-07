# -*- coding: utf-8 -*-

import logging
import datetime
import re
import hashlib
from os import SEEK_SET

from tornado.escape import json_decode, json_encode
import tornado.web

from utils.dotdict import DotDict
from utils.misc import str_to_list, get_terminal_sessionID_key, get_track_key, get_kqly_key
from constants import UWEB, SMS
from helpers.queryhelper import QueryHelper
from helpers.smshelper import SMSHelper
from helpers.confhelper import ConfHelper
from codes.errorcode import ErrorCode
from codes.smscode import SMSCode

from base import BaseHandler, authenticated
from mixin.base import  BaseMixin

class KQLYHandler(BaseHandler, BaseMixin):

    @authenticated
    @tornado.web.removeslash
    def post(self):
        """Turn on buletooth."""
        status = ErrorCode.SUCCESS
        try:
            data = DotDict(json_decode(self.request.body))
            tid = data.get('tid', None)
            tids = data.get('tids', None)
            self.check_tid(tid)
            logging.info("[BLUETOOTH] kqly request: %s, uid: %s, tids: %s", 
                         data, self.current_user.uid, tids)
        except Exception as e:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            self.write_ret(status)
            return 

        try:
            tids = str_to_list(tids)
            tids = tids if tids else [self.current_user.tid, ]
            tids = [str(tid) for tid in tids]

            for tid in tids:
                ##NOTE: just send KQLY 
                terminal = QueryHelper.get_terminal_by_tid(tid, self.db)
                kqly_key = get_kqly_key(tid)
                kqly_value = self.redis.getvalue(kqly_key)
                if not kqly_value:
                    interval = 30 # in minute
                    sms = SMSCode.SMS_KQLY % interval
                    SMSHelper.send_to_terminal(terminal.mobile, sms)
                    self.redis.setvalue(kqly_key, True, SMS.KQLY_SMS_INTERVAL)
            self.write_ret(status)
        except Exception as e:
            logging.exception("[BLUETOOTH] uid: %s, tid: %s kqbt failed. Exception: %s. ", 
                              self.current_user.uid, self.current_user.tid, e.args )
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)
