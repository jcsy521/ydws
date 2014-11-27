# -*- coding: utf-8 -*-

import logging
import time
import random
import string

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

class GetCaptchaHandler(BaseHandler):
    
    @tornado.web.removeslash
    def post(self):
        """Generate a captcha for retrieving the password."""
        status = ErrorCode.SUCCESS
        try:
            data = DotDict(json_decode(self.request.body))
            logging.info("[UWEB] get captcha request: %s", data)
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

            mobile = data.mobile
            umobile = data.mobile
            user = self.db.get("SELECT mobile"
                               "  FROM T_USER"
                               "  WHERE mobile = %s"
                               "  LIMIT 1",
                               mobile)
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
                    body = u'管理员您好：检测到频繁注册，请查看. umobile: %s, umobile_times: %s, remote_ip: %s, remote_ip_times: %s' % (umobile, umobile_times, remote_ip, remote_ip_times) 
                    notify_maintainer(self.db, self.redis, body, 'password')
                    self.write_ret(status)
                    return

                captcha = ''.join(random.choice(string.digits) for x in range(4))
                getcaptcha_sms = SMSCode.SMS_CAPTCHA % (captcha) 
                ret = SMSHelper.send(mobile, getcaptcha_sms)
                ret = DotDict(json_decode(ret))
                if ret.status == ErrorCode.SUCCESS:
                    logging.info("[UWEB] user uid: %s get captcha success, the captcha: %s", mobile, captcha)
                    captcha_key = get_captcha_key(mobile)
                    self.redis.setvalue(captcha_key, captcha, UWEB.SMS_CAPTCHA_INTERVAL)

                    self.redis.set(umobile_key, umobile_times+1)  
                    self.redis.expireat(umobile_key, end_time_)  
                    self.redis.set(remote_ip_key, remote_ip_times+1)  
                    self.redis.expireat(remote_ip_key, end_time_)  

                else:
                    status = ErrorCode.SERVER_BUSY
                    logging.error("[UWEB] user uid: %s get captcha failed.", mobile)
            else:
                status = ErrorCode.USER_NOT_ORDERED
                logging.error("[UWEB] user uid: %s does not exist, get captcha failed.", mobile)
            self.write_ret(status)
        except Exception as e:
            logging.exception("[UWEB] user uid: %s retrieve password failed.  Exception: %s", mobile, e.args)
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)

class GetCaptchaCorpHandler(BaseHandler):
    
    @tornado.web.removeslash
    def post(self):
        """Retrieve the password."""
        status = ErrorCode.SUCCESS
        try:
            data = DotDict(json_decode(self.request.body))
            logging.info("[UWEB] corp retrieve password request: %s", data)
        except Exception as e:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            self.write_ret(status)
            return 

        try:
            mobile = data.mobile
            umobile = data.mobile
            user = self.db.get("SELECT mobile"
                               "  FROM T_CORP"
                               "  WHERE cid = %s"
                               "  LIMIT 1",
                               mobile)
            if not user:
                user = self.db.get("SELECT mobile"
                                   "  FROM T_OPERATOR"
                                   "  WHERE oid = %s"
                                   "  LIMIT 1",
                                   mobile)

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
                    body = u'管理员您好：检测到频繁注册，请查看. umobile: %s, umobile_times: %s, remote_ip: %s, remote_ip_times: %s' % (umobile, umobile_times, remote_ip, remote_ip_times) 
                    notify_maintainer(self.db, self.redis, body, 'password')
                    self.write_ret(status)
                    return

                captcha = ''.join(random.choice(string.digits) for x in range(4))
                getcaptcha_sms = SMSCode.SMS_CAPTCHA % (captcha)
                ret = SMSHelper.send(mobile, getcaptcha_sms)
                ret = DotDict(json_decode(ret))
                if ret.status == ErrorCode.SUCCESS:
                    logging.info("[UWEB] corp mobile: %s get captcha success, the captcha: %s", mobile, captcha)
                    captcha_key = get_captcha_key(mobile)
                    self.redis.setvalue(captcha_key, captcha, UWEB.SMS_CAPTCHA_INTERVAL)

                    self.redis.set(umobile_key, umobile_times+1)  
                    self.redis.expireat(umobile_key, end_time_)  
                    self.redis.set(remote_ip_key, remote_ip_times+1)  
                    self.redis.expireat(remote_ip_key, end_time_)  
                else:
                    status = ErrorCode.SERVER_BUSY
                    logging.error("[UWEB] corp mobile: %s get captcha failed.", mobile)
            else:
                logging.error("[UWEB] corp mobile: %s does not exist, get captcha failed.", mobile)
                status = ErrorCode.USER_NOT_ORDERED
            self.write_ret(status)
        except Exception as e:
            logging.exception("[UWEB] corp mobile: %s get captcha failed. Exception: %s", mobile, e.args)
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)
