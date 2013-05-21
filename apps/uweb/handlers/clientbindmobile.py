# -*- coding: utf-8 -*-

import logging
import random
import string

import tornado.web
from tornado.escape import json_encode, json_decode

from utils.dotdict import DotDict
from utils.misc import get_captcha_key
from utils.checker import check_sql_injection
from constants import UWEB
from codes.errorcode import ErrorCode
from codes.smscode import SMSCode 
from base import BaseHandler, authenticated
from helpers.smshelper import SMSHelper
       
       
class BindMobileHandler(BaseHandler):

    @tornado.web.removeslash
    def post(self):
        try:
            pid = self.get_argument('pid')
            iosid = self.get_argument('iosid')
            mobile = self.get_argument('mobile')
            cid = self.get_argument('cid')
            captcha = self.get_argument('captcha')
            
            logging.info("[CLIENT] passenger bind mobile request pid : %s, mobile : %s, cid: %s, iosid: %s, captcha: %s", 
                         pid, mobile, cid, iosid, captcha)
        except Exception as e:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            self.write_ret(status)
            return

        try:
            status = ErrorCode.FAILED
            captcha_key = get_captcha_key(mobile)
            redis_captcha = self.redis.get(captcha_key)
            
            if redis_captcha:
                if captcha == redis_captcha:
                    #1.find corp's passenger is exist or not
                    passenger = self.db.get("SELECT pid "
                                            "  FROM T_PASSENGER"
                                            "  WHERE mobile = %s"
                                            "  AND cid = %s",
                                            mobile, cid)
                    print passenger
                    #2.if no passenger,bind mobile else remind passenger
                    if passenger:
                        if passenger.pid == '':
                            self.db.execute("UPDATE T_PASSENGER "
                                            "  SET pid = %s ,"
                                            "      iosid = %s"
                                            "  WHERE mobile = %s "
                                            "  AND cid = %s ",
                                            pid, iosid, mobile, cid)
                            status = ErrorCode.SUCCESS
                        else:
                            status = ErrorCode.PASSENGER_EXIST
                            logging.error("[CLIENT] passenger bind mobile failed. mobile: %s, captcha: %s, Message: %s",
                                          mobile, captcha, ErrorCode.ERROR_MESSAGE[status])
                else:
                    status = ErrorCode.WRONG_CAPTCHA
                    logging.error("[CLIENT] passenger bind mobile failed. mobile: %s, captcha: %s, Message: %s",
                                  mobile, captcha, ErrorCode.ERROR_MESSAGE[status])
            else:
                status = ErrorCode.NO_CAPTCHA
                logging.error("[CLIENT] passenger bind mobile failed. mobile: %s, captcha: %s, Message: %s",
                              mobile, captcha, ErrorCode.ERROR_MESSAGE[status])
                
            self.write_ret(status)
        except Exception as e:
            logging.exception("[CLIENT] passenger bind mobile failed. mobile: %s. Exception: %s", 
                              pid, e.args) 
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)


class ClientCaptchaHandler(BaseHandler):

    @tornado.web.removeslash
    def post(self):
        """Send captcha to user's phone through sms.
        """
        status = ErrorCode.SUCCESS
        try: 
            mobile = self.get_argument('mobile','')
            captcha = ''.join(random.choice(string.digits) for x in range(6))
            ios_captcha_sms = SMSCode.SMS_IOS_CAPTCHA % (captcha) 
            ret = SMSHelper.send(mobile, ios_captcha_sms)
            ret = DotDict(json_decode(ret))
            if ret.status == ErrorCode.SUCCESS:
                logging.info("[CLIENT] passenger get sms captcha: %s successfully, mobile: %s",
                             captcha, mobile)
                captcha_key = get_captcha_key(mobile)
                self.redis.setvalue(captcha_key, captcha, UWEB.SMS_CAPTCHA_INTERVAL)
            else:
                status = ErrorCode.SERVER_BUSY
                logging.error("[CLIENT] passenger get sms captcha failed, mobile: %s", mobile)

            self.write_ret(status)
        except Exception as e:
            logging.exception("[CLIENT] passenger get sms captcha failed, mobile: %s. Exception: %s", 
                              mobile, e.args) 
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)