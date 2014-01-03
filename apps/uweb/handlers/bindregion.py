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


class BindRegionHandler(BaseHandler):

    @authenticated
    @tornado.web.removeslash
    def get(self):
        """Get all regions binded by the terminal.
        """ 
        status = ErrorCode.SUCCESS
        try:
            tid = self.get_argument('tid')
        except Exception as e:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            logging.exception("[UWEB] cid: %s get region bind data format illegal. Exception: %s", 
                              self.current_user.cid, e.args) 
            self.write_ret(status)
            return

        try:
            res = self.db.query("SELECT tr.id AS region_id"
                                "  FROM T_REGION tr, T_REGION_TERMINAL trt"
                                "  WHERE tr.id = trt.rid"
                                "  AND trt.tid = %s",
                                tid)
            
            self.write_ret(status,
                           dict_=DotDict(res=res))
        except Exception as e:
            logging.exception("[UWEB] cid: %s get regions bind failed. Exception: %s", 
                              self.current_user.cid, e.args) 
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)
        
    @authenticated
    @tornado.web.removeslash
    def post(self):
        """handle region bind.
        """
        try:
            data = DotDict(json_decode(self.request.body))
            logging.info("[UWEB] region bind post request: %s, cid: %s", 
                         data, self.current_user.cid)

        except Exception as e:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            self.write_ret(status)
            return

        try:
            status = ErrorCode.SUCCESS
            region_ids = data.region_ids
            tids = map(str, data.tids)
            sql = "DELETE FROM T_REGION_TERMINAL WHERE tid IN %s " % (tuple(tids + DUMMY_IDS_STR), )
            self.db.execute(sql)
            for tid in tids:
                for region_id in region_ids:
                    self.db.execute("INSERT INTO T_REGION_TERMINAL(rid, tid)"
                                    "  VALUES(%s, %s)",
                                    region_id, tid)
            
            self.write_ret(status)
        except Exception as e:
            logging.exception("[UWEB] cid: %s region bind post failed. Exception: %s", 
                              self.current_user.cid, e.args) 
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)

