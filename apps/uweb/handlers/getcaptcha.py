# -*- coding: utf-8 -*-

import logging
import time
import random
import string

from tornado.escape import json_decode
import tornado.web

from utils.misc import get_captcha_key
from utils.dotdict import DotDict
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
            user = self.db.get("SELECT mobile"
                               "  FROM T_USER"
                               "  WHERE mobile = %s"
                               "  LIMIT 1",
                               mobile)
            if user:
                captcha = ''.join(random.choice(string.digits) for x in range(4))
                getcaptcha_sms = SMSCode.SMS_CAPTCHA % (captcha) 
                ret = SMSHelper.send(mobile, getcaptcha_sms)
                ret = DotDict(json_decode(ret))
                if ret.status == ErrorCode.SUCCESS:
                    logging.info("[UWEB] user uid: %s get captcha success, the captcha: %s", mobile, captcha)
                    captcha_key = get_captcha_key(mobile)
                    self.redis.setvalue(captcha_key, captcha, UWEB.SMS_CAPTCHA_INTERVAL)
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
                captcha = ''.join(random.choice(string.digits) for x in range(4))
                getcaptcha_sms = SMSCode.SMS_CAPTCHA % (captcha)
                ret = SMSHelper.send(mobile, getcaptcha_sms)
                ret = DotDict(json_decode(ret))
                if ret.status == ErrorCode.SUCCESS:
                    logging.info("[UWEB] corp mobile: %s get captcha success, the captcha: %s", mobile, captcha)
                    captcha_key = get_captcha_key(mobile)
                    self.redis.setvalue(captcha_key, captcha, UWEB.SMS_CAPTCHA_INTERVAL)
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
