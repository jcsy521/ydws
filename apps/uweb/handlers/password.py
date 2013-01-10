# -*- coding: utf-8 -*-

import logging
import time
import random

from tornado.escape import json_decode, json_encode
import tornado.web

from utils.misc import get_psd
from utils.dotdict import DotDict
from utils.checker import check_sql_injection
from mixin.password import PasswordMixin 
from base import BaseHandler, authenticated
from codes.errorcode import ErrorCode
from codes.smscode import SMSCode
from helpers.smshelper import SMSHelper

class PasswordHandler(BaseHandler, PasswordMixin):
    
    @tornado.web.removeslash
    def get(self):
        self.render('password.html', message='')
    
    @authenticated
    @tornado.web.removeslash
    def put(self):
        """Modify the password."""
        status = ErrorCode.SUCCESS
        try:
            data = DotDict(json_decode(self.request.body))
            logging.info("[UWEB] modify password request: %s, uid: %s, tid: %s", data, self.current_user.uid, self.current_user.tid)
        except Exception as e:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            self.write_ret(status)
            return 

        try:
            old_password = data.old_password
            new_password = data.new_password

            if not (check_sql_injection(old_password) and check_sql_injection(new_password) ):
                status = ErrorCode.ILLEGAL_PASSWORD 
                self.write_ret(status)
                return

            if not self.check_user_by_password(old_password, self.current_user.uid): 
                logging.error("[UWEB] uid: %s change password failed. old passwrod: %s, new passwrod: %s",
                              self.current_user.uid, old_password, new_password)
                status = ErrorCode.WRONG_OLD_PASSWORD
            else:    
                self.update_password(new_password, self.current_user.uid)
            self.write_ret(status)
        except Exception as e:
            logging.exception("Update password failed. Exception: %s", e.args)
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)
            
    @tornado.web.removeslash
    def post(self):
        """Retrieve the password."""
        status = ErrorCode.SUCCESS
        try:
            data = DotDict(json_decode(self.request.body))
            logging.info("[UWEB] retrieve password request: %s", data)
        except Exception as e:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            self.write_ret(status)
            return 

        try:
            mobile = data.mobile
            user = self.db.get("SELECT mobile"
                               "  FROM T_USER"
                               "  WHERE mobile = %s"
                               "  LIMIT 1",
                               mobile)
            if user:
                psd = get_psd()                        
                self.db.execute("UPDATE T_USER"
                                "  SET password = password(%s)"
                                "  WHERE mobile = %s",
                                psd, mobile)
                        
                retrieve_password_sms = SMSCode.SMS_RETRIEVE_PASSWORD % (psd) 
                ret = SMSHelper.send(mobile, retrieve_password_sms)
                ret = DotDict(json_decode(ret))
                if ret.status == ErrorCode.SUCCESS:
                    logging.info("[UWEB] uid: %s retrieve password success, the new passwrod: %s", mobile, psd)
                else:
                    status = ErrorCode.SERVER_BUSY
                    logging.error("[UWEB] uid: %s retrieve password failed.", mobile)
            else:
                logging.error("[UWEB] uid: %s does not exist, retrieve password failed.", mobile)
                status = ErrorCode.USER_NOT_ORDERED
            self.write_ret(status)
            
        except Exception as e:
            logging.exception("[UWEB] uid: %s retrieve password failed.  Exception: %s", mobile, e.args)
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)

class PasswordCorpHandler(BaseHandler, PasswordMixin):
    
    @tornado.web.removeslash
    def get(self):
        self.render('password_corp.html', message='')
    
    @authenticated
    @tornado.web.removeslash
    def put(self):
        """Modify the password."""
        status = ErrorCode.SUCCESS
        try:
            data = DotDict(json_decode(self.request.body))
            logging.info("[UWEB] modify password request: %s, uid: %s, tid: %s", data, self.current_user.uid, self.current_user.tid)
        except Exception as e:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            self.write_ret(status)
            return 

        try:
            old_password = data.old_password
            new_password = data.new_password

            if not (check_sql_injection(old_password) and check_sql_injection(new_password) ):
                status = ErrorCode.ILLEGAL_PASSWORD 
                self.write_ret(status)
                return

            if not self.check_corp_by_password(old_password, self.current_user.cid): 
                logging.error("[UWEB] uid: %s change password failed. old passwrod: %s, new passwrod: %s",
                              self.current_user.uid, old_password, new_password)
                status = ErrorCode.WRONG_OLD_PASSWORD
            else:    
                self.update_corp_password(new_password, self.current_user.cid)
            self.write_ret(status)
        except Exception as e:
            logging.exception("Update password failed. Exception: %s", e.args)
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)
            
    @tornado.web.removeslash
    def post(self):
        """Retrieve the password."""
        status = ErrorCode.SUCCESS
        try:
            data = DotDict(json_decode(self.request.body))
            logging.info("[UWEB] retrieve password request: %s", data)
        except Exception as e:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            self.write_ret(status)
            return 

        try:
            mobile = data.mobile
            user = self.db.get("SELECT mobile"
                               "  FROM T_CORP"
                               "  WHERE mobile = %s"
                               "  LIMIT 1",
                               mobile)
            if user:
                psd = get_psd()                        
                self.db.execute("UPDATE T_CORP"
                                "  SET password = password(%s)"
                                "  WHERE mobile = %s",
                                psd, mobile)
                        
                retrieve_password_sms = SMSCode.SMS_RETRIEVE_PASSWORD % (psd) 
                ret = SMSHelper.send(mobile, retrieve_password_sms)
                ret = DotDict(json_decode(ret))
                if ret.status == ErrorCode.SUCCESS:
                    logging.info("[UWEB] uid: %s retrieve password success, the new passwrod: %s", mobile, psd)
                else:
                    status = ErrorCode.SERVER_BUSY
                    logging.error("[UWEB] uid: %s retrieve password failed.", mobile)
            else:
                logging.error("[UWEB] uid: %s does not exist, retrieve password failed.", mobile)
                status = ErrorCode.USER_NOT_ORDERED
            self.write_ret(status)
            
        except Exception as e:
            logging.exception("[UWEB] uid: %s retrieve password failed.  Exception: %s", mobile, e.args)
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)
