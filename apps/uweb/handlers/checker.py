# -*- coding: utf-8 -*-

import logging

import tornado.web

from codes.errorcode import ErrorCode
from constants import UWEB
from base import BaseHandler

from utils.checker import check_zs_phone

       
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
                              "    AND service_status != %s" 
                              "   LIMIT 1",
                              tmobile, UWEB.SERVICE_STATUS.TO_BE_UNBIND)
            if res:
                status = ErrorCode.TERMINAL_BINDED
            else: 
                white_list = check_zs_phone(tmobile, self.db) 
                if not white_list: 
                    logging.error("[UWEB] mobile: %s is not whitelist.", tmobile) 
                    status = ErrorCode.MOBILE_NOT_ORDERED
                    message = message = ErrorCode.ERROR_MESSAGE[status] % tmobile
                    self.write_ret(status, message=message)
                    return
                else:
                    status = ErrorCode.SUCCESS
                
            self.write_ret(status)
        except Exception as e:
            logging.exception("[UWEB] Check tmobile failed. tmobile: %s, Exception: %s", 
                              tmobile, e.args) 
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)

class CheckCNameHandler(BaseHandler):

    @tornado.web.removeslash
    def get(self, name):
        """Check crop's name whether exists in T_CORP.
        """
        try:
            status = ErrorCode.SUCCESS
            res = self.db.get("SELECT id"
                              "  FROM T_CORP"
                              "  WHERE name = %s"
                              "   LIMIT 1",
                              name)
            if res:
                #TODO: the status is ugly, maybe should be replaced on someday.
                status = ErrorCode.SERVER_BUSY
            self.write_ret(status)
        except Exception as e:
            logging.exception("[UWEB] uid: %s check corp's namefailed. Exception: %s", 
                              self.current_user.uid, e.args) 
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)

class CheckCNumHandler(BaseHandler):

    @tornado.web.removeslash
    def get(self, cnum):
        """Check cnum whether exists in T_CAR.
        """
        try:
            status = ErrorCode.SUCCESS
            res = self.db.get("SELECT id"
                              "  FROM T_CAR"
                              "  WHERE cnum = %s"
                              "   LIMIT 1",
                              cnum)
            if res:
                status = ErrorCode.TERMINAL_BINDED
            self.write_ret(status)
        except Exception as e:
            logging.exception("[UWEB] uid: %s check cnum failed. Exception: %s", 
                              self.current_user.uid, e.args) 
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)


class CheckOperMobileHandler(BaseHandler):

    @tornado.web.removeslash
    def get(self, omobile):
        """Check tmobile whether exists in T_TERMINAL_INFO.
        """
        try:
            status = ErrorCode.SUCCESS

            corp = self.db.get("SELECT id"
                               "  FROM T_CORP"
                               "  WHERE cid = %s"
                               "   LIMIT 1",
                               omobile)
            if corp:
                status = ErrorCode.CORP_EXIST
            else:
                operator = self.db.get("SELECT id"
                                       "  FROM T_OPERATOR"
                                       "  WHERE mobile = %s"
                                       "   LIMIT 1",
                                       omobile)
                if operator:
                    status = ErrorCode.OPERATOR_EXIST
            self.write_ret(status)
        except Exception as e:
            logging.exception("[UWEB] uid: %s check tmobile failed. Exception: %s", 
                              self.current_user.uid, e.args) 
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)
            
            
class CheckPassengerMobileHandler(BaseHandler):

    @tornado.web.removeslash
    def get(self, mobile):
        """one corp one passenger, one passenger one corp.
        """
        try:
            status = ErrorCode.SUCCESS
            res = self.db.get("SELECT id"
                              "  FROM T_PASSENGER"
                              "  WHERE mobile = %s"
                              "  AND cid = %s",
                              mobile, self.current_user.cid)
            if res:
                status = ErrorCode.DATA_EXIST
            self.write_ret(status)
        except Exception as e:
            logging.exception("[UWEB] uid: %s check tmobile failed. Exception: %s", 
                              self.current_user.uid, e.args) 
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)

