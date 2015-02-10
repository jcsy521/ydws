#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""This module is designed for the record of test-sms.
"""

import logging

import tornado.web
from tornado.escape import json_decode

from base import authenticated,BaseHandler
from codes.errorcode import ErrorCode
from utils.dotdict import DotDict
from utils.misc import get_terminal_sessionID_key

from checker import check_privileges
from constants import PRIVILEGES

class TestSMSHandler(BaseHandler):

    @authenticated
    @check_privileges([PRIVILEGES.TERMINAL_QUERY])
    def get(self):
        """Jump to the testsms.html.
        """
        username = self.get_current_user()
        self.render('report/testsms.html',
                    username = username)

    @authenticated
    @check_privileges([PRIVILEGES.TERMINAL_QUERY])
    @tornado.web.removeslash
    def post(self):   
        """QueryHelper individuals according to the 
        given parameters.
        """
        status = ErrorCode.SUCCESS
        try:
            data = json_decode(self.request.body)
            mobile = data.get('mobile')
            logging.info("[ADMIN] Query test, data: %s", data)
        except Exception as e: 
            status = ErrorCode.ILLEGAL_DATA_FORMAT 
            logging.exception("[ADMIN] Invalid data format. Exception: %s",
                              e.args) 
            self.write_ret(status) 
            return

        try:
            res = self.db.get("SELECT mobile, test FROM T_TERMINAL_INFO"
                              "  WHERE mobile = %s",
                              mobile)
            if not res:
                status = ErrorCode.MOBILE_NOT_ORDERED
                message = ErrorCode.ERROR_MESSAGE[status] % mobile
                self.write_ret(status=status, 
                               message=message)
            else:
                self.write_ret(status, 
                               dict_=DotDict(res=res)) 
        except Exception as e:
            logging.exception("[ADMIN] Search test sms failed. Terminal mobile: %s.", 
                              mobile)
            self.render('errors/error.html',
                        message=ErrorCode.FAILED)

    @authenticated
    @check_privileges([PRIVILEGES.TERMINAL_QUERY])
    @tornado.web.removeslash
    def put(self):   
        """Modify the charge of test-sms.
        """
        status = ErrorCode.SUCCESS
        try:
            data = json_decode(self.request.body)
            mobile = data.get('mobile')
            test = data.get('test')
            logging.info("[ADMIN] Modify test, data: %s", data)
        except Exception as e: 
            status = ErrorCode.ILLEGAL_DATA_FORMAT 
            logging.exception("[ADMIN] Invalid data format. Exception: %s",
                              e.args) 
            self.write_ret(status) 
            return

        try:
            res = self.db.get("SELECT tid, mobile, test"
                              " FROM T_TERMINAL_INFO"
                              "  WHERE mobile = %s",
                              mobile)
            if not res:
                status = ErrorCode.MOBILE_NOT_ORDERED
                message = ErrorCode.ERROR_MESSAGE[status] % mobile
                self.write_ret(status=status, 
                               message=message)
            else: 
                self.db.execute("UPDATE T_TERMINAL_INFO SET test=%s WHERE tid = %s",
                                test, res['tid'])
                sessionID_key = get_terminal_sessionID_key(res['tid']) 
                old_sessionid = self.redis.get(sessionID_key) 
                if old_sessionid: 
                    self.redis.delete(sessionID_key)
                logging.info("[ADMIN] Tid: %s set test to %s.",
                             res['tid'], test)

                self.write_ret(status=status)
        except Exception as e:
            logging.exception("[ADMIN] Modify test sms failed. mobile: %s.", 
                              mobile)
            self.render('errors/error.html',
                        message=ErrorCode.FAILED)
