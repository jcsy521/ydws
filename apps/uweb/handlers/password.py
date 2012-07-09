# -*- coding: utf-8 -*-

import logging
import datetime
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

class PasswordHandler(BaseHandler, PasswordMixin):
    """Modify the password."""
    
    @authenticated
    @tornado.web.removeslash
    def put(self):
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
