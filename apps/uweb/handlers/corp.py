# -*- coding: utf-8 -*-

"""This module is designed for corp.
"""

import logging

import tornado.web
from tornado.escape import json_decode

from utils.dotdict import DotDict
from codes.errorcode import ErrorCode
from base import BaseHandler, authenticated


class CorpHandler(BaseHandler):

    @authenticated
    @tornado.web.removeslash
    def put(self):
        """Modify a existing corporation. 
        """
        try:
            data = DotDict(json_decode(self.request.body))
            logging.info("[UWEB] Modify corp request: %s, cid: %s",
                         data, self.current_user.cid)
        except Exception as e:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            self.write_ret(status)
            return

        try:
            status = ErrorCode.SUCCESS
            cid = data.cid
            name = data.name
            self.db.execute("UPDATE T_CORP"
                            "  SET name = %s"
                            "  WHERE cid = %s",
                            name, cid)
            self.write_ret(status)
        except Exception as e:
            logging.exception("[UWEB] Modify corp failed. cid: %s, Exception: %s",
                              self.current_user.cid, e.args)
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)
