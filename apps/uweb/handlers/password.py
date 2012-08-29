# -*- coding: utf-8 -*-

import logging
import datetime
import time
import random
import time
from dateutil.relativedelta import relativedelta

from tornado.escape import json_decode, json_encode
import tornado.web

from helpers.seqgenerator import SeqGenerator
from utils.misc import get_today_last_month
from utils.dotdict import DotDict
from mixin.password import PasswordMixin 
from base import BaseHandler, authenticated
from codes.errorcode import ErrorCode
from codes.smscode import SMSCode
from helpers.smshelper import SMSHelper

class PasswordHandler(BaseHandler, PasswordMixin):
    
    @tornado.web.removeslash
    def get(self):
        self.render('getpassword.html', message='')
    
    
    @authenticated
    @tornado.web.removeslash
    def put(self):
        """Modify the password."""

        try:
            data = DotDict(json_decode(self.request.body))
            old_password = data.old_password
            new_password = data.new_password

            if not self.check_user_by_password(old_password, self.current_user.uid): 
                self.write_ret(ErrorCode.WRONG_PASSWORD)
                return 
            else:    
                self.update_password(new_password, self.current_user.uid)
            self.write_ret(ErrorCode.SUCCESS)
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
            mobile = data.mobile
            info = self.db.get("SELECT mobile"
                               "  FROM T_USER"
                               "  WHERE mobile = %s"
                               "  LIMIT 1",
                               mobile)
            if info:
                password = ""
                for i in range(6):
                    if i % 2 == 0:
                        password = password + chr(random.randint(97, 122))
                    else:
                        password = password + str(random.randint(0, 9))
                        
                self.db.execute("UPDATE T_USER"
                                "  SET password = password(%s)"
                                "  WHERE mobile = %s",
                                password, mobile)
                        
                retrieve_password_sms = SMSCode.SMS_RETRIEVE_PASSWORD % (password) 
                ret = SMSHelper.send(mobile, retrieve_password_sms)
                ret = DotDict(json_decode(ret))
                if ret.status == ErrorCode.SUCCESS:
                    pass
                else:
                    status = ErrorCode.FAILED
            else:
                status = ErrorCode.USER_NOT_ORDER
            self.write_ret(status)
            
        except Exception as e:
            logging.exception("Retrieve password failed. Exception: %s", e.args)
            status = ErrorCode.FAILED
            self.write_ret(status)
