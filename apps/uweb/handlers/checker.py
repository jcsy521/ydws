# -*- coding: utf-8 -*-

import logging

import tornado.web
from tornado.escape import json_encode, json_decode

from utils.dotdict import DotDict
from utils.misc import DUMMY_IDS, get_terminal_info_key, get_location_key, str_to_list
from codes.errorcode import ErrorCode
from helpers.queryhelper import QueryHelper
from constants import UWEB, EVENTER, GATEWAY
from constants.MEMCACHED import ALIVED
from base import BaseHandler, authenticated

       
class CheckTMobileHandler(BaseHandler):

    @tornado.web.removeslash
    def get(self, tmobile):
        """Check tmobile whether exists in T_TERMINAL_INFO.
        """
        try:
            status = ErrorCode.SUCCESS
            res = self.db.get("SELECT id"
                              "  FROM T_TERMINAL_INFO"
                              "  WHERE mobile = %s"
                              "   LIMIT 1",
                              tmobile)
            if res:
                #TODO: the status is ugly, maybe should be replaced on someday.
                status = ErrorCode.SERVER_BUSY
            self.write_ret(status)
        except Exception as e:
            logging.exception("[UWEB] uid: %s check tmobile failed. Exception: %s", 
                              self.current_user.uid, e.args) 
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)
