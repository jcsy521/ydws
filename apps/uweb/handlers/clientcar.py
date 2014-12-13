# -*- coding: utf-8 -*-

"""This module is designed for ZNBC.

#NOTE：deprecated.
"""

import logging

import tornado.web
from tornado.escape import json_encode, json_decode

from utils.dotdict import DotDict
from utils.misc import DUMMY_IDS, str_to_list
from utils.checker import check_sql_injection
from constants import UWEB
from codes.errorcode import ErrorCode
from base import BaseHandler, authenticated

       
class FocusCarHandler(BaseHandler):

    @tornado.web.removeslash
    def post(self):
        """Create a line attention.
        """
        try:
            pid = self.get_argument('pid')
            line_id = self.get_argument('line_id')
            iosid = self.get_argument('iosid')
            logging.info("[CLIENT] create line attention request pid: %s, line_id: %s", 
                         pid, line_id)
        except Exception as e:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            self.write_ret(status)
            return

        try:
            status = ErrorCode.SUCCESS
            self.db.execute("INSERT T_LINE_PASSENGER(id, line_id, pid)"
                            "  VALUES(NULL, %s, %s)",
                            line_id, pid)
            self.write_ret(status)
        except Exception as e:
            logging.exception("[CLIENT] pid: %s create line attention failed. Exception: %s", 
                              pid, e.args) 
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)


class UnbindCarHandler(BaseHandler):

    @tornado.web.removeslash
    def post(self):
        """delete a line attention.
        """
        try:
            pid = self.get_argument('pid')
            line_id = self.get_argument('line_id')
            iosid = self.get_argument('iosid')
            logging.info("[CLIENT] delete line attention pid : %s, line_id: %s", 
                         pid, line_id)
        except Exception as e:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            self.write_ret(status)
            return

        try:
            status = ErrorCode.SUCCESS
            self.db.execute("DELETE FROM T_LINE_PASSENGER "
                            "  WHERE line_id = %s"
                            "  AND pid = %s",
                            line_id, pid)
            self.write_ret(status)
        except Exception as e:
            logging.exception("[CLIENT] pid: %s delete line attention failed. Exception: %s", 
                              pid, e.args) 
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)

