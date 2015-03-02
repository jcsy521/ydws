# -*- coding: utf-8 -*-

"""This module is designed for region-binding.
"""

import logging

import tornado.web
from tornado.escape import json_decode

from utils.dotdict import DotDict
from utils.public import bind_region
from helpers.queryhelper import QueryHelper
from codes.errorcode import ErrorCode
from base import BaseHandler, authenticated


class BindRegionHandler(BaseHandler):

    """Handle regions-bind for corp.

    :url /bindregion
    """

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
            logging.exception("[UWEB] Invalid data format. Exception: %s",
                              e.args)
            self.write_ret(status)
            return

        try:
            res = QueryHelper.get_bind_region(tid, self.db)
            self.write_ret(status,
                           dict_=DotDict(res=res))
        except Exception as e:
            logging.exception("[UWEB] Get regions bind failed. cid: %s, Exception: %s",
                              self.current_user.cid, e.args)
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)

    @authenticated
    @tornado.web.removeslash
    def post(self):
        """Bind region bind for the terminals.
        """
        status = ErrorCode.SUCCESS
        try:
            data = DotDict(json_decode(self.request.body))
            region_ids = data.region_ids
            tids = map(str, data.tids)
            logging.info("[UWEB] Region bind post request: %s, cid: %s",
                         data, self.current_user.cid)
        except Exception as e:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            logging.exception("[UWEB] Invalid data format. body: %s, Exception: %s",
                              self.request.body, e.args)
            self.write_ret(status)
            return

        try:          
            bind_region(self.db, tids, region_ids)
            self.write_ret(status)
        except Exception as e:
            logging.exception("[UWEB] Region bind post failed. cid: %s, Exception: %s",
                              self.current_user.cid, e.args)
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)
