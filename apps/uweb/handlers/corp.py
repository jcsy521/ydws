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

       
class CorpHandler(BaseHandler):

    @authenticated
    @tornado.web.removeslash
    def put(self):
        """Modify a existing corporation. 
        """
        try:
            data = DotDict(json_decode(self.request.body))
        except:
            self.write_ret(ErrorCode.ILLEGAL_DATA_FORMAT) 
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
            logging.exception("[UWEB] uid: %s update corp failed. Exception: %s", 
                              self.current_user.uid, e.args) 
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)


