# -*- coding: utf-8 -*-

import logging
import random
import string

from tornado.escape import json_decode, json_encode
import tornado.web

from utils.misc import get_today_last_month, get_captcha_key
from utils.misc import get_terminal_sessionID_key, get_terminal_address_key,\
    get_terminal_info_key, get_lq_sms_key, get_lq_interval_key
from utils.checker import check_zs_phone
from utils.dotdict import DotDict
from utils.public import delete_terminal
from helpers.smshelper import SMSHelper
from helpers.queryhelper import QueryHelper

from base import BaseHandler, authenticated
from codes.errorcode import ErrorCode
from codes.smscode import SMSCode 
from constants import UWEB 


class RegisterBrowserHandler(BaseHandler):
    
    @tornado.web.removeslash
    def get(self):
        """Jump to register.html.
        """ 
        self.render('register.html')

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
                logging.info("[UWEB] umobile: %s get sms captcha: %s successfully",
                             umobile, psd)
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

            # check tmobile is whitelist or not
            white_list = check_zs_phone(tmobile, self.db)
            if not white_list:
                logging.info("[UWEB] %s is not whitelist", tmobile)
                status = ErrorCode.MOBILE_NOT_ORDERED
                message = ErrorCode.ERROR_MESSAGE[status] % tmobile
                self.write_ret(status, message=message)
                return

            captcha_key = get_captcha_key(umobile)
            captcha_old = self.redis.get(captcha_key)
            if captcha_old:
                if captcha == str(captcha_old):
                    terminal = QueryHelper.get_terminal_by_tmobile(tmobile, self.db) 
                    if terminal:
                        if terminal.service_status == UWEB.SERVICE_STATUS.TO_BE_UNBIND:
                            # delete to_be_unbind terminal!
                            delete_terminal(terminal.tid, self.db, self.redis)
                        else:
                            status = ErrorCode.TERMINAL_ORDERED
                            logging.info("[UWEB] umobile: %s, tmobile: %s regist failed. Message: %s",
                                         umobile, tmobile, ErrorCode.ERROR_MESSAGE[status])

                            self.write_ret(status)
                            return

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
