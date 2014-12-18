# -*- coding: utf-8 -*-

"""This module is designed for blue-tooth.
"""

import logging

from tornado.escape import json_decode
import tornado.web

from utils.dotdict import DotDict
from utils.misc import get_kqly_key, str_to_list
from constants import SMS
from helpers.queryhelper import QueryHelper
from helpers.smshelper import SMSHelper
from codes.errorcode import ErrorCode
from codes.smscode import SMSCode
from utils.public import kqly

from base import BaseHandler, authenticated
from mixin.base import BaseMixin


class KQLYHandler(BaseHandler, BaseMixin):

    """Start the blue-tooth.

    :url /kqly
    """

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
            logging.exception("[UWEB] Invalid data format. body:%s, Exception: %s",
                              self.request.body, e.args)
            self.write_ret(status)
            return

        try:
            tids = str_to_list(tids)
            tids = tids if tids else [self.current_user.tid, ]
            tids = [str(tid) for tid in tids]          
            kqly(self.db, self.redis, tids)
            self.write_ret(status)
        except Exception as e:
            logging.exception("[BLUETOOTH] Kqly failed. uid: %s, tid: %s, Exception: %s. ",
                              self.current_user.uid, self.current_user.tid, e.args)
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)
