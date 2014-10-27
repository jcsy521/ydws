# -*- coding: utf-8 -*-

import logging

import tornado.web
from tornado.escape import json_encode, json_decode

from utils.dotdict import DotDict
from utils.misc import DUMMY_IDS_STR, str_to_list
from utils.checker import check_sql_injection
from constants import UWEB
from codes.errorcode import ErrorCode
from base import BaseHandler, authenticated


class BindSingleHandler(BaseHandler):

    @authenticated
    @tornado.web.removeslash
    def get(self):
        """Get all singles binded by the terminal.
        """ 
        status = ErrorCode.SUCCESS
        try:
            tid = self.get_argument('tid')
        except Exception as e:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            logging.exception("[UWEB] cid: %s get single data format illegal. Exception: %s", 
                              self.current_user.cid, e.args) 
            self.write_ret(status)
            return

        try:
            res = self.db.query("SELECT ts.id AS single_id"
                                "  FROM T_SINGLE ts, T_SINGLE_TERMINAL tst"
                                "  WHERE ts.id = tst.sid"
                                "  AND tst.tid = %s",
                                tid)
            
            self.write_ret(status,
                           dict_=DotDict(res=res))
        except Exception as e:
            logging.exception("[UWEB] cid: %s get single bind failed. Exception: %s", 
                              self.current_user.cid, e.args) 
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)
        
    @authenticated
    @tornado.web.removeslash
    def post(self):
        """Handle single bind.
        """
        try:
            data = DotDict(json_decode(self.request.body))
            logging.info("[UWEB] Single bind post request: %s, cid: %s", 
                         data, self.current_user.cid)

        except Exception as e:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            self.write_ret(status)
            return

        try:
            status = ErrorCode.SUCCESS
            single_ids = data.single_ids
            tids = map(str, data.tids)

            #NOTE: Clear the old data first.
            sql = "DELETE FROM T_SINGLE_TERMINAL WHERE tid IN %s " % (tuple(tids + DUMMY_IDS_STR), )
            self.db.execute(sql)

            #NOTE:
            for tid in tids:
                for single_id in single_ids:
                    self.db.execute("INSERT INTO T_SINGLE_TERMINAL(sid, tid)"
                                    "  VALUES(%s, %s)",
                                    single_id, tid)
            
            self.write_ret(status)
        except Exception as e:
            logging.exception("[UWEB] cid: %s single bind post failed. Exception: %s", 
                              self.current_user.cid, e.args) 
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)
