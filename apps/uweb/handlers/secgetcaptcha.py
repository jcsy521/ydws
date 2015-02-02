# -*- coding: utf-8 -*-

"""This module is designed for captcha for retrieve-password.
"""

import logging
import time
import random
import string
import hashlib
import re

from tornado.escape import json_decode
import tornado.web

from utils.misc import get_captcha_key, get_date_from_utc, start_end_of_day
from utils.dotdict import DotDict
from utils.public import notify_maintainer
from base import BaseHandler, authenticated
from codes.errorcode import ErrorCode
from codes.smscode import SMSCode
from helpers.smshelper import SMSHelper
from helpers.confhelper import ConfHelper
from constants import UWEB

class SecGetCaptchaHandler(BaseHandler):

    """Get captcha for password of individual.

    :url /secgetcaptcha
    """
    
    @tornado.web.removeslash
    def post(self):
        """Generate a captcha for retrieving the password."""
        status = ErrorCode.SUCCESS
        try:
            data = DotDict(json_decode(self.request.body))
            umobile = data.mobile
            captcha_psd = data.captcha_psd
            logging.info("[UWEB] Get captcha request: %s", data)
        except Exception as e:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            logging.exception("[UWEB] Invalid data format. body: %s, Exception: %s",
                              self.request.body, e.args)
            self.write_ret(status)
            return 

        try:

            status = self.check_privilege(umobile) 
            if status != ErrorCode.SUCCESS: 
                logging.error("[UWEB] User: %s is just for test, has no right to access the function.", 
                              umobile) 
                self.write_ret(status) 
                return
           
            captchahash = self.get_secure_cookie("captchahash_password")

            m = hashlib.md5()
            m.update(captcha_psd.lower())
            m.update(UWEB.HASH_SALT)
            hash_ = m.hexdigest()
            if hash_.lower() != captchahash.lower():
                status = ErrorCode.WRONG_CAPTCHA_IMAGE
                logging.info("[UWEB] Come from browser, captcha-check failed.")
                self.write_ret(status)
                return
            
            user = self.db.get("SELECT mobile"
                               "  FROM T_USER"
                               "  WHERE mobile = %s"
                               "  LIMIT 1",
                               umobile)
            if user:
                remote_ip = self.request.remote_ip
                remote_ip_key = "register_remote_ip:%s" % remote_ip 
                umobile_key = "register_umobile:%s" % umobile
                remote_ip_times = self.redis.getvalue(remote_ip_key)  
                umobile_times = self.redis.getvalue(umobile_key)  
    
                if remote_ip_times is None:
                    remote_ip_times = 0 
    
                if umobile_times is None:
                    umobile_times = 0 
    
                logging.info("[UWEB] Register. umobile: %s, umobile_times: %s, remote_ip: %s, remote_ip_times: %s",
                             umobile, umobile_times, remote_ip, remote_ip_times)
    
                #NOTE: In current day, the same remote_ip allows 10 times, the umobile, 3 times
                current_time = int(time.time())
                date = get_date_from_utc(current_time)
                year, month, day = date.year, date.month, date.day
                start_time_, end_time_ = start_end_of_day(year=year, month=month, day=day)
        
                if umobile_times >= 3: # <= 3 is ok
                    status = ErrorCode.REGISTER_EXCESS
                if remote_ip_times >= 10: # <= 10 is ok
                    status = ErrorCode.REGISTER_EXCESS

                if status == ErrorCode.REGISTER_EXCESS:
                    body = u'管理员您好：检测到频繁注册，请查看. umobile: %s, umobile_times: %s, remote_ip: %s, remote_ip_times: %s' % (
                            umobile, umobile_times, remote_ip, remote_ip_times) 
                    notify_maintainer(self.db, self.redis, body, 'password')
                    self.write_ret(status)
                    return

                captcha = ''.join(random.choice(string.digits) for x in range(4))
                getcaptcha_sms = SMSCode.SMS_CAPTCHA % (captcha) 
                ret = SMSHelper.send(umobile, getcaptcha_sms)
                ret = DotDict(json_decode(ret))
                if ret.status == ErrorCode.SUCCESS:
                    logging.info("[UWEB] user uid: %s get captcha success, the captcha: %s", 
                                 umobile, captcha)
                    captcha_key = get_captcha_key(umobile)
                    self.redis.setvalue(captcha_key, captcha, UWEB.SMS_CAPTCHA_INTERVAL)

                    self.redis.set(umobile_key, umobile_times+1)  
                    self.redis.expireat(umobile_key, end_time_)  
                    self.redis.set(remote_ip_key, remote_ip_times+1)  
                    self.redis.expireat(remote_ip_key, end_time_)  

                else:
                    status = ErrorCode.SERVER_BUSY
                    logging.error("[UWEB] user uid: %s get captcha failed.", umobile)
            else:
                status = ErrorCode.USER_NOT_ORDERED
                logging.error("[UWEB] user uid: %s does not exist, get captcha failed.", 
                              umobile)
            self.write_ret(status)
        except Exception as e:
            logging.exception("[UWEB] user uid: %s retrieve password failed. Exception: %s", 
                              umobile, e.args)
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)

class SecGetCaptchaCorpHandler(BaseHandler):
    
    """Get captcha for password of enterprise.
    
    :url /secgetcaptcha/corp
    """

    @tornado.web.removeslash
    def post(self):
        """Retrieve the password."""
        status = ErrorCode.SUCCESS
        try:
            data = DotDict(json_decode(self.request.body))
            umobile = data.mobile
            captcha_psd = data.captcha_psd
            captchahash = self.get_secure_cookie("captchahash_password")
            logging.info("[UWEB] Corp retrieve password request: %s", data)
        except Exception as e:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            logging.exception("[UWEB] Invalid data format. body: %s, Exception: %s",
                              self.request.body, e.args)
            self.write_ret(status)
            return 

        try:         
            m = hashlib.md5()
            m.update(captcha_psd.lower())
            m.update(UWEB.HASH_SALT)
            hash_ = m.hexdigest()
            if hash_.lower() != captchahash.lower():
                status = ErrorCode.WRONG_CAPTCHA_IMAGE
                logging.info("[UWEB] Come from browser, captcha-check failed.")
                self.write_ret(status)
                return            

            user = self.db.get("SELECT mobile"
                               "  FROM T_CORP"
                               "  WHERE cid = %s"
                               "  LIMIT 1",
                               umobile)
            if not user:
                user = self.db.get("SELECT mobile"
                                   "  FROM T_OPERATOR"
                                   "  WHERE oid = %s"
                                   "  LIMIT 1",
                                   umobile)

            if user:
                remote_ip = self.request.remote_ip
                remote_ip_key = "register_remote_ip:%s" % remote_ip 
                umobile_key = "register_umobile:%s" % umobile
                remote_ip_times = self.redis.getvalue(remote_ip_key)  
                umobile_times = self.redis.getvalue(umobile_key)  
    
                if remote_ip_times is None:
                    remote_ip_times = 0 
    
                if umobile_times is None:
                    umobile_times = 0 
    
                logging.info("[UWEB] Register. umobile: %s, umobile_times: %s, remote_ip: %s, remote_ip_times: %s",
                             umobile, umobile_times, remote_ip, remote_ip_times)
    
                #NOTE: In current day, the same remote_ip allows 10 times, the umobile, 3 times
                current_time = int(time.time())
                date = get_date_from_utc(current_time)
                year, month, day = date.year, date.month, date.day
                start_time_, end_time_ = start_end_of_day(year=year, month=month, day=day)
        
                if umobile_times >= 3: # <= 3 is ok
                    status = ErrorCode.REGISTER_EXCESS
                if remote_ip_times >= 10: # <= 10 is ok
                    status = ErrorCode.REGISTER_EXCESS

                if status == ErrorCode.REGISTER_EXCESS:
                    body = u'管理员您好：检测到频繁注册，请查看. umobile: %s, umobile_times: %s, remote_ip: %s, remote_ip_times: %s' % (
                        umobile, umobile_times, remote_ip, remote_ip_times) 
                    notify_maintainer(self.db, self.redis, body, 'password')
                    self.write_ret(status)
                    return

                captcha = ''.join(random.choice(string.digits) for x in range(4))
                getcaptcha_sms = SMSCode.SMS_CAPTCHA % (captcha)
                ret = SMSHelper.send(umobile, getcaptcha_sms)
                ret = DotDict(json_decode(ret))
                if ret.status == ErrorCode.SUCCESS:
                    logging.info("[UWEB] corp mobile: %s get captcha success, the captcha: %s", 
                                 umobile, captcha)
                    captcha_key = get_captcha_key(umobile)
                    self.redis.setvalue(captcha_key, captcha, UWEB.SMS_CAPTCHA_INTERVAL)

                    self.redis.set(umobile_key, umobile_times+1)  
                    self.redis.expireat(umobile_key, end_time_)  
                    self.redis.set(remote_ip_key, remote_ip_times+1)  
                    self.redis.expireat(remote_ip_key, end_time_)  
                else:
                    status = ErrorCode.SERVER_BUSY
                    logging.error("[UWEB] Get captcha failed. corp mobile: %s", 
                                  umobile)
            else:
                logging.error("[UWEB] Get captcha failed. corp mobile: %s does not exist.", 
                              umobile)
                status = ErrorCode.USER_NOT_ORDERED
            self.write_ret(status)
        except Exception as e:
            logging.exception("[UWEB] Get captcha failed. corp mobile: %s, Exception: %s", 
                               umobile, e.args)
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)
