# -*- coding: utf-8 -*-

import logging

import tornado.web
from tornado.escape import json_decode

from utils.dotdict import DotDict
from helpers.queryhelper import QueryHelper
from codes.errorcode import ErrorCode 

from base import BaseHandler, authenticated

class UserTypeHandler(BaseHandler):

    @authenticated
    @tornado.web.removeslash
    def post(self):
        try:
            data = json_decode(self.request.body)
            tmobile = data.get('tmobile', None)
            cid = data.get('cid', None)
            logging.info("[ADMIN] user_type modify request, data:%s", 
                          data)
        except Exception as e:
            logging.exception("[ADMIN] Invalid data format, data:%s, Exception:%s", 
                              data, e.args)
            status = ErrorCode.FAILED 
            self.write_ret(status) 
            return

        try:
            status = ErrorCode.SUCCESS 
            if cid: # individual --> enterprise
                group = QueryHelper.get_default_group_by_cid(cid, self.db)
                self.db.execute("UPDATE T_TERMINAL_INFO SET group_id = %s"
                                "  WHERE mobile = %s",
                                group.gid, tmobile)
            else: # enterprise --> individual
                self.db.execute("UPDATE T_TERMINAL_INFO SET group_id = -1"
                                "  WHERE mobile = %s",
                                tmobile)
                logging.info("[ADMIN] Terminal: %s becomes a invididual", 
                              tmobile)
            self.write_ret(status) 
        except Exception as e:
            status = ErrorCode.SERVER_BUSY
            logging.exception("[ADMIN] user_type modify failed. Exception:%s", 
                              e.args)
            self.write_ret(status) 
