# -*- coding: utf-8 -*-

"""This module is designed for ZNBC.

#NOTE: deprecated.
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


class LinesGetHandler(BaseHandler):

    @authenticated
    @tornado.web.removeslash
    def get(self):
        """ """ 
        status = ErrorCode.SUCCESS

        try:
            lines = self.db.query("SELECT id AS line_id, name AS line_name "
                                  "  FROM T_LINE"
                                  "  WHERE cid = %s",
                                  self.current_user.cid)
            self.write_ret(status,
                           dict_=DotDict(lines=lines))
        except Exception as e:
            logging.exception("[UWEB] cid: %s get lines failed. Exception: %s", 
                              self.current_user.cid, e.args) 
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)
        
       
class BindlineHandler(BaseHandler):

    @authenticated
    @tornado.web.removeslash
    def get(self):
        """ """ 
        status = ErrorCode.SUCCESS
        try:
            tid = self.get_argument('tid')
        except Exception as e:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            logging.exception("[UWEB] cid: %s get line bind data format illegal. Exception: %s", 
                              self.current_user.cid, e.args) 
            self.write_ret(status)
            return

        try:
            line = self.db.get("SELECT id AS line_id, name AS line_name "
                               "  FROM T_LINE, T_CAR_LINE"
                               "  WHERE T_LINE.id = T_CAR_LINE.line_id"
                               "  AND tid = %s",
                               tid)
            
            self.write_ret(status,
                           dict_=DotDict(line=line if line else ''))
        except Exception as e:
            logging.exception("[UWEB] cid: %s get line bind failed. Exception: %s", 
                              self.current_user.cid, e.args) 
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)
        

    @authenticated
    @tornado.web.removeslash
    def post(self):
        """A car bind a line.
        """
        try:
            data = DotDict(json_decode(self.request.body))
            logging.info("[UWEB] add line bind request: %s, cid: %s", 
                         data, self.current_user.cid)
        except Exception as e:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            self.write_ret(status)
            return

        try:
            status = ErrorCode.SUCCESS
            line_id = data.line_id
            tid = data.tid
            self.db.execute("INSERT INTO T_CAR_LINE(tid, line_id)"
                            "  VALUES(%s, %s)",
                            tid, line_id)
            
            self.write_ret(status)
        except Exception as e:
            logging.exception("[UWEB] cid: %s, tid: %s line bind failed. Exception: %s", 
                              self.current_user.cid, tid, e.args) 
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)


    @authenticated
    @tornado.web.removeslash
    def put(self):
        """Modify line bind.
        """
        try:
            data = DotDict(json_decode(self.request.body))
            logging.info("[UWEB] modify line bind request: %s, cid: %s", 
                         data, self.current_user.cid)

        except Exception as e:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            self.write_ret(status)
            return

        try:
            status = ErrorCode.SUCCESS
            line_id = int(data.line_id)
            tid = data.tid
            # line_id is 0 : unbind line
            if line_id == 0:
                self.db.execute("DELETE FROM T_CAR_LINE"
                                "  WHERE tid = %s", 
                                tid)
            else:
                self.db.execute("UPDATE T_CAR_LINE"
                                "  SET line_id = %s"
                                "  WHERE tid = %s",
                                line_id, tid)
            self.write_ret(status)
        except Exception as e:
            logging.exception("[UWEB] cid: %s modify line bind failed. Exception: %s", 
                              self.current_user.cid, e.args) 
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)

