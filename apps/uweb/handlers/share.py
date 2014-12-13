# -*- coding: utf-8 -*-

"""This module is designed for querying of share-record.
"""

import logging

import tornado.web
from tornado.escape import json_decode

from utils.dotdict import DotDict
from codes.errorcode import ErrorCode
from utils.public import record_share
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
            record_share(self.db, locals())
            self.write_ret(status)
        except Exception as e:
            status = ErrorCode.SERVER_BUSY
            logging.exception("[UWEB] Record share failed, Exception: %s", e.args)
            self.write_ret(status)
