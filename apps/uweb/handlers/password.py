# -*- coding: utf-8 -*-

"""This module is designed for password.
"""

import logging
import time
import random
import hashlib

from tornado.escape import json_decode, json_encode
import tornado.web

from utils.misc import get_psd, get_captcha_key
from utils.dotdict import DotDict
from utils.checker import check_sql_injection, check_label
from utils.public import update_password
from mixin.password import PasswordMixin 
from base import BaseHandler, authenticated
from codes.errorcode import ErrorCode
from codes.smscode import SMSCode
from helpers.smshelper import SMSHelper
from helpers.confhelper import ConfHelper
from constants import UWEB

class PasswordHandler(BaseHandler, PasswordMixin):
    
    @tornado.web.removeslash
    def get(self):
        self.render('password.html',
                    message='',
                    map_type=ConfHelper.LBMP_CONF.map_type,
                    user_type=UWEB.USER_TYPE.PERSON)
    
    @authenticated
    @tornado.web.removeslash
    def put(self):
        """Modify the password."""
        status = ErrorCode.SUCCESS
        try:
            data = DotDict(json_decode(self.request.body))
            logging.info("[UWEB] user modify password request: %s, uid: %s", 
                        data, self.current_user.uid)
        except Exception as e:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            self.write_ret(status)
            return 

        try:
            status = self.check_privilege(self.current_user.uid, self.current_user.tid) 
            if status != ErrorCode.SUCCESS: 
                logging.error("[UWEB] Terminal is just for test, has no right to access the function. tid: %s, user: %s", 
                              self.current_user.tid, self.current_user.uid) 
                self.write_ret(status) 
                return
            
            old_password = data.old_password
            new_password = data.new_password

            if not (check_label(old_password) and check_label(new_password) ):
                status = ErrorCode.ILLEGAL_PASSWORD 
                self.write_ret(status)
                return

            if not self.check_user_by_password(old_password, self.current_user.uid): 
                logging.error("[UWEB] User change password failed.  uid: %s,  old passwrod: %s, new passwrod: %s",
                              self.current_user.uid, old_password, new_password)
                status = ErrorCode.WRONG_OLD_PASSWORD
            else:    
                psd_info = dict(user_id=self.current_user.uid,
                                user_type=UWEB.USER_TYPE.PERSON,
                                password=new_password)
                update_password(psd_info, self.db, self.redis)
            self.write_ret(status)
        except Exception as e:
            logging.exception("[UWEB] User update password failed. Exception: %s", e.args)
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)
            
    @tornado.web.removeslash
    def post(self):
        """Retrieve the password."""
        status = ErrorCode.SUCCESS
        try:
            data = DotDict(json_decode(self.request.body))
            mobile = data.mobile
            captcha = data.get('captcha','')
            logging.info("[UWEB] User retrieve password request: %s", data)
        except Exception as e:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            self.write_ret(status)
            return 

        try:
            status = self.check_privilege(data.mobile) 
            if status != ErrorCode.SUCCESS: 
                logging.error("[UWEB] User: %s is just for test, has no right to access the function.", 
                              data.mobile) 
                self.write_ret(status) 
                return

            psd = get_psd()                        
            user = QueryHelper.get_user_by_mobile(mobile, self.db)
            if user:
                psd_info = dict(user_id=mobile,
                                user_type=UWEB.USER_TYPE.PERSON,
                                password=psd)
                if not captcha: # old version               
                    update_password(psd_info, self.db, self.redis)
                    retrieve_password_sms = SMSCode.SMS_RETRIEVE_PASSWORD % (psd) 
                    ret = SMSHelper.send(mobile, retrieve_password_sms)
                    ret = DotDict(json_decode(ret))
                    if ret.status == ErrorCode.SUCCESS:
                        logging.info("[UWEB] user uid: %s retrieve password success, the new passwrod: %s", mobile, psd)
                    else:
                        status = ErrorCode.SERVER_BUSY
                        logging.error("[UWEB] user uid: %s retrieve password failed.", mobile)
                else: # new version
                    captcha_key = get_captcha_key(mobile)
                    captcha_old = self.redis.get(captcha_key)
                    if captcha_old:
                        if captcha == str(captcha_old): 
                            update_password(psd_info, self.db, self.redis)
                            retrieve_password_sms = SMSCode.SMS_RETRIEVE_PASSWORD % (psd) 
                            ret = SMSHelper.send(mobile, retrieve_password_sms)
                            ret = DotDict(json_decode(ret))
                            if ret.status == ErrorCode.SUCCESS:
                                logging.info("[UWEB] user uid: %s retrieve password success, the new passwrod: %s", mobile, psd)
                            else:
                                status = ErrorCode.SERVER_BUSY
                                logging.error("[UWEB] user uid: %s retrieve password failed.", mobile)
                        else:
                            status = ErrorCode.WRONG_CAPTCHA
                            logging.error("mobile: %s retrieve password failed. captcha: %s, captcha_old: %s, Message: %s", 
                                           mobile, captcha, captcha_old, ErrorCode.ERROR_MESSAGE[status])
                    else:
                        status = ErrorCode.NO_CAPTCHA
                        logging.error("mobile: %s retrieve password failed. captcha: %s, Message: %s", 
                                      mobile, captcha, ErrorCode.ERROR_MESSAGE[status])
            else: 
                status = ErrorCode.USER_NOT_ORDERED
                logging.error("[UWEB] umobile: %s does not exist, retrieve password failed.", mobile)
            self.write_ret(status)
        except Exception as e:
            logging.exception("[UWEB] user uid: %s retrieve password failed.  Exception: %s", mobile, e.args)
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)

class PasswordCorpHandler(BaseHandler, PasswordMixin):
    
    @tornado.web.removeslash
    def get(self):
        self.render('password_corp.html',
                    message='',
                    map_type=ConfHelper.LBMP_CONF.map_type,
                    user_type=UWEB.USER_TYPE.CORP)
    
    @authenticated
    @tornado.web.removeslash
    def put(self):
        """Modify the password."""
        status = ErrorCode.SUCCESS
        try:
            data = DotDict(json_decode(self.request.body))
            logging.info("[UWEB] corp modify password request: %s, uid: %s", 
                         data, self.current_user.uid)
        except Exception as e:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            self.write_ret(status)
            return 

        try:
            old_password = data.old_password
            new_password = data.new_password

            if not self.check_corp_by_password(old_password, self.current_user.cid): 
                logging.error("[UWEB] Corp change password failed. mobile: %s, old passwrod: %s, new passwrod: %s",
                              self.current_user.cid, old_password, new_password)
                status = ErrorCode.WRONG_OLD_PASSWORD
            else:    
                psd_info = dict(user_id=self.current_user.cid,
                                user_type=UWEB.USER_TYPE.CORP,
                                password=new_password)
                update_password(psd_info, self.db, self.redis)
            self.write_ret(status)
        except Exception as e:
            logging.exception("[UWEB] corp update password failed. Exception: %s", e.args)
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)
            
    @tornado.web.removeslash
    def post(self):
        """Retrieve the password."""
        status = ErrorCode.SUCCESS
        try:
            data = DotDict(json_decode(self.request.body))
            mobile = data.mobile
            captcha = data.get('captcha','')
            logging.info("[UWEB] corp retrieve password request: %s", data)
        except Exception as e:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            self.write_ret(status)
            return 

        try:
            status = ErrorCode.SUCCESS
            psd = get_psd()                        
            user = QueryHelper.get_corp_by_cid(mobile, self.db)         
            if user: # corp
                psd_info = dict(user_id=mobile,
                                user_type=UWEB.USER_TYPE.CORP,
                                password=psd)
                if not captcha: # old version 
                    update_password(psd_info, self.db, self.redis)
                else: # new version
                    captcha_key = get_captcha_key(mobile)
                    captcha_old = self.redis.get(captcha_key)
                    if captcha_old:
                        if captcha == str(captcha_old):                            
                            update_password(psd_info, self.db, self.redis)
                        else:
                            status = ErrorCode.WRONG_CAPTCHA
                            logging.error("[UWEB] Crop retrieve password failed."
                                          "  mobile: %s, captcha: %s, captcha_old: %s, Message: %s", 
                                          mobile, captcha, captcha_old, ErrorCode.ERROR_MESSAGE[status])
                    else:
                        status = ErrorCode.NO_CAPTCHA
                        logging.error("[UWEB] Corp retrieve password failed. mobile: %s, captcha: %s, Message: %s", 
                                      mobile, captcha, ErrorCode.ERROR_MESSAGE[status])
            else: 
                user = QueryHelper.get_operator_by_oid(mobile, self.db)
                if user: # operator
                    psd_info = dict(user_id=mobile,
                                    user_type=UWEB.USER_TYPE.OPERATOR,
                                    password=psd)
                    if not captcha: # old version
                        update_password(psd_info, self.db, self.redis)
                    else: # new version
                        captcha_key = get_captcha_key(mobile)
                        captcha_old = self.redis.get(captcha_key)
                        if captcha_old:
                            if captcha == str(captcha_old):        
                                update_password(psd_info, self.db, self.redis)
                            else:
                                status = ErrorCode.WRONG_CAPTCHA
                                logging.error("[UWEB] Operator retrieve password failed. mobile: %s, captcha: %s, captcha_old: %s, Message: %s", 
                                               mobile, captcha, captcha_old, ErrorCode.ERROR_MESSAGE[status])
                        else:
                            status = ErrorCode.NO_CAPTCHA
                            logging.error("[UWEB] Operator retrieve password failed. mobile: %s, captcha: %s, Message: %s", 
                                          mobile, captcha, ErrorCode.ERROR_MESSAGE[status])
                else:
                    status = ErrorCode.USER_NOT_ORDERED
                    logging.error("[UWEB] Operator does not exist, retrieve password failed. mobile: %s", mobile)

            if status == ErrorCode.SUCCESS:
                retrieve_password_sms = SMSCode.SMS_RETRIEVE_PASSWORD % (psd) 
                ret = SMSHelper.send(mobile, retrieve_password_sms)
                ret = DotDict(json_decode(ret))
                if ret.status == ErrorCode.SUCCESS:
                    logging.info("[UWEB] Corp retrieve password success, mobile: %s, the new passwrod: %s", 
                                 mobile, psd)
                else:
                    status = ErrorCode.SERVER_BUSY
                    logging.error("[UWEB] Corp retrieve password failed. mobile: %s", mobile)
            self.write_ret(status)
        except Exception as e:
            logging.exception("[UWEB] Corp retrieve password failed. mobile: %s, Exception: %s", 
                              mobile, e.args)
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)

class PasswordOperHandler(BaseHandler, PasswordMixin):
    
    @authenticated
    @tornado.web.removeslash
    def put(self):
        """Modify the password."""
        status = ErrorCode.SUCCESS
        try:
            data = DotDict(json_decode(self.request.body))
            logging.info("[UWEB] Operator modify password request: %s, oid: %s", 
                         data, self.current_user.oid)
        except Exception as e:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            self.write_ret(status)
            return 

        try:
            old_password = data.old_password
            new_password = data.new_password

            if not self.check_oper_by_password(old_password, self.current_user.oid): 
                logging.error("[UWEB] Operator change password failed. oid: %s, old passwrod: %s, new passwrod: %s",
                              self.current_user.oid, old_password, new_password)
                status = ErrorCode.WRONG_OLD_PASSWORD
            else:        
                psd_info = dict(user_id=self.current_user.oid,
                                user_type=UWEB.USER_TYPE.OPERATOR,
                                password=new_password)
                update_password(psd_info, self.db, self.redis)
            self.write_ret(status)
        except Exception as e:
            logging.exception("[UWEB] operator update password failed. Exception: %s", e.args)
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)
