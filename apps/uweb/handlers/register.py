# -*- coding: utf-8 -*-

import logging
import random
import string

from tornado.escape import json_decode, json_encode
import tornado.web

from utils.misc import get_today_last_month, get_captcha_key
from utils.dotdict import DotDict
from helpers.smshelper import SMSHelper
from helpers.queryhelper import QueryHelper

from base import BaseHandler, authenticated
from codes.errorcode import ErrorCode
from codes.smscode import SMSCode 
from constants import UWEB 


class RegisterHandler(BaseHandler):

    @tornado.web.removeslash
    def get(self):
        """Send captcha to user's phone through sms.
        """
        status = ErrorCode.SUCCESS
        try: 
            umobile = self.get_argument('umobile','')
            psd = ''.join(random.choice(string.digits) for x in range(4))
            captcha_sms = SMSCode.SMS_REG % (psd) 
            ret = SMSHelper.send(umobile, captcha_sms)
            ret = DotDict(json_decode(ret))
            if ret.status == ErrorCode.SUCCESS:
                logging.info("[UWEB] umobile: %s get sms captcha successfully", umobile)
                captcha_key = get_captcha_key(umobile)
                self.redis.setvalue(captcha_key, psd, UWEB.SMS_CAPTCHA_INTERVAL)
            else:
                status = ErrorCode.SERVER_BUSY
                logging.error("[UWEB] umobile: %s get sms captcha failed.", umobile)

            self.write_ret(status)
        except Exception as e:
            logging.exception("[UWEB] umobile:%s get sms captcha failed. Exception: %s", 
                              umobile, e.args) 
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)

    @tornado.web.removeslash
    def post(self):
        """Regist a pair of umobile and tmobile.
        """
        status = ErrorCode.SUCCESS
        try:
            data = DotDict(json_decode(self.request.body))
            logging.info("[UWEB] register request: %s", data)
        except Exception as e:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            self.write_ret(status)
            return 

        try:
            umobile = data.umobile            
            tmobile = data.tmobile            
            captcha = data.captcha         
            captcha_key = get_captcha_key(umobile)
            captcha_old = self.redis.getvalue(captcha_key)
            if captcha_old:
                if captcha == str(captcha_old):
                    terminal = QueryHelper.get_terminal_by_tmobile(tmobile, self.db) 
                    if terminal:
                        status = ErrorCode.TERMINAL_ORDERED
                        logging.info("[UWEB] umobile: %s, tmobile: %s regist failed. Message: %s",
                                     umobile, tmobile, ErrorCode.ERROR_MESSAGE[status])
                    else:
                        register_sms = SMSCode.SMS_REGISTER % (umobile, tmobile) 
                        ret = SMSHelper.send_to_terminal(tmobile, register_sms)
                        ret = DotDict(json_decode(ret))
                        if ret.status == ErrorCode.SUCCESS:
                            logging.info("[UWEB] umobile: %s, tmobile: %s regist successfully.",
                                         umobile, tmobile)
                        else:
                            status = ErrorCode.REGISTER_FAILED
                            logging.error("[UWEB] umobile: %s, tmobile: %s regist failed. Message: %s",
                                          umobile, tmobile, ErrorCode.ERROR_MESSAGE[status])
                else:
                    status = ErrorCode.WRONG_CAPTCHA
                    logging.error("umobile: %s regist failed. captcha: %s, captcha_old: %s, Message: %s",
                                  umobile, captcha, captcha_old, ErrorCode.ERROR_MESSAGE[status])
            else:
                status = ErrorCode.NO_CAPTCHA
                logging.error("umobile: %s regist failed. captcha: %s, Message: %s",
                              umobile, captcha, ErrorCode.ERROR_MESSAGE[status])
            self.write_ret(status)
        except Exception as e:
            logging.exception("[UWEB] umobile: %s tmobile: %s register failed, Exception: %s", 
                              umobile, tmobile, e.args)
            status = ErrorCode.REGISTER_FAILED
            self.write_ret(status)
