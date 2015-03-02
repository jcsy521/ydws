# -*- coding: utf-8 -*-

"""This module is designed for single-binding.
"""

import logging

import tornado.web
from tornado.escape import json_decode

from utils.dotdict import DotDict
from utils.public import bind_single
from helpers.queryhelper import QueryHelper
from codes.errorcode import ErrorCode
from base import BaseHandler, authenticated


class BindSingleHandler(BaseHandler):

    """Handle singles-bind for corp.

    :url /bindsingle
    """

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
            logging.exception("[UWEB] Invalid data format. Exception: %s",
                              e.args)
            self.write_ret(status)
            return

        try:
            res = QueryHelper.get_bind_single(tid, self.db)            
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
            logging.exception("[UWEB] Invalid data format. body: %s, Exception: %s",
                              self.request.body, e.args)
            self.write_ret(status)
            return

        try:
            status = ErrorCode.SUCCESS
            single_ids = data.single_ids
            tids = map(str, data.tids)

            bind_single(self.db, tids, single_ids)
            self.write_ret(status)
        except Exception as e:
            logging.exception("[UWEB] Single bind failed. cid: %s, Exception: %s", 
                              self.current_user.cid, e.args) 
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)
