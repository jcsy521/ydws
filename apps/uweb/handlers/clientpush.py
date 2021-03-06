# -*- coding: utf-8 -*-

"""This module is designed for ZNBC.

#NOTE：deprecated.
"""

import logging

import tornado.web

from codes.errorcode import ErrorCode
from base import BaseHandler

       
class PushHandler(BaseHandler):

    @tornado.web.removeslash
    def post(self):
        try:
            pid = self.get_argument('pid')
            push = self.get_argument('push')
            logging.info("[CLIENT] switch push status request pid : %s, push : %s", 
                         pid, push)
        except Exception as e:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            self.write_ret(status)
            return

        try:
            status = ErrorCode.SUCCESS
            self.db.execute("UPDATE T_PASSENGER "
                            "  SET push = %s "
                            "  WHERE pid = %s ",
                            push, pid)
            self.write_ret(status)
        except Exception as e:
            logging.exception("[CLIENT] pid: %s switch push status failed. Exception: %s", 
                              pid, e.args) 
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)
