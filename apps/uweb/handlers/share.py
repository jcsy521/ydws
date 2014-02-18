# -*- coding: utf-8 -*-

import logging
import time

import tornado.web
from tornado.escape import json_encode, json_decode

from utils.dotdict import DotDict
from codes.errorcode import ErrorCode
from base import BaseHandler

class ShareHandler(BaseHandler):
    """Record the share info.
    """

    @tornado.web.removeslash
    def post(self):
        """Insert new items."""
        status = ErrorCode.SUCCESS
        try:
            data = DotDict(json_decode(self.request.body))
            umobile = data.umobile
            umobile = data.platform
            tmobile = data.get('tmobile','')
            tid = data.get('tid','')
            platform = data.get('platform','')
            logging.info("[UWEB] share log request: %s", data)
        except Exception as e:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            self.write_ret(status)
            return 

        try:
            self.db.execute("INSERT INTO T_SHARE_LOG(umobile, platform, timestamp, tmobile, tid)"
                            "  VALUES(%s, %s, %s, %s, %s)",
                            umobile, platform, int(time.time()), 
                            tmobile, tid)
            self.write_ret(status)
        except Exception as e:
            status = ErrorCode.SERVER_BUSY
            logging.exception("[UWEB] record share failed, Exception: %s", e.args)
            self.write_ret(status)
