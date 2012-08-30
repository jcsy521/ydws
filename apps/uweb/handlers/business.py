# -*- coding: utf-8 -*-

from os import SEEK_SET
import datetime, time
from dateutil.relativedelta import relativedelta
import logging
import hashlib

import tornado.web
from tornado.escape import json_decode, json_encode
from tornado.ioloop import IOLoop

from constants import LOCATION, XXT
from utils.dotdict import DotDict

from mixin.business import BusinessMixin
from base import BaseHandler, authenticated

from codes.errorcode import ErrorCode 
from utils.checker import check_sql_injection
from helpers.smshelper import SMSHelper
from helpers.seqgenerator import SeqGenerator
from helpers.gfsenderhelper import GFSenderHelper
from helpers.queryhelper import QueryHelper 
from codes.smscode import SMSCode 
from constants import PRIVILEGES, SMS, UWEB, GATEWAY
from utils.misc import str_to_list, DUMMY_IDS

class BusinessCheckMobileHandler(BaseHandler, BusinessMixin):

    @authenticated
    @tornado.web.removeslash
    def get(self, mobile):
        """Check whether the owner_mobile can order a new terminal.     
        if the ower has two terminal, retrun FAILED, give a message and do not allow continue.
        if not, return SUCESS, let the business go ahead.
        """
        status = ErrorCode.USER_EXCESS 
        res = self.db.query("SELECT id FROM T_TERMINAL_INFO"
                            "  WHERE owner_mobile = %s",
                            mobile)
        if len(res) < UWEB.LIMIT.TERMINAL:
            status = ErrorCode.SUCCESS 
        self.write_ret(status)

class BusinessCheckTMobileHandler(BaseHandler, BusinessMixin):

    @authenticated
    @tornado.web.removeslash
    def get(self, tmobile):
        """Check whether the terminal can be ordered by a new owner.
        if terminal exist, return FAILED, give a message and do not allow continue. 
        if not, return SUCCESS, let the business go ahead.
        """
        status = ErrorCode.TERMINAL_TID_EXIST
        res = self.db.get("SELECT id FROM T_TERMINAL_INFO"
                          "  WHERE mobile = %s"
                          "  LIMIT 1",
                          tmobile)
        if not res:
            status = ErrorCode.SUCCESS 
        self.write_ret(status)

class BusinessCheckStatusHandler(BaseHandler, BusinessMixin):

    @authenticated
    @tornado.web.removeslash
    def get(self, tmobile):
        """Get business status.
        0: success
        1: processing
        3: failed 
        """
        status = ErrorCode.SUCCESS 
        business = 2
        try: 
            sms_status = self.get_sms_status(tmobile)
            if sms_status == 3:
                business_status = 0
            elif sms_status == 0: 
                business_status = 3 
            else:
                business_status = 2 
        except Exception as e:
            status = ErrorCode.FAILED
            logging.exception("Get business status failed. tmobile: %s", tmobile)
        
        self.write_ret(status, dict_=DotDict(business_status=business_status))

class BusinessCreateHandler(BaseHandler, BusinessMixin):

    @authenticated
    @tornado.web.removeslash
    def post(self):
        """Create business for a couple of users.
        """
        data = DotDict(json_decode(self.request.body))
        status = ErrorCode.SUCCESS 
        try:
            begintime = datetime.datetime.now()
            endtime = begintime + relativedelta(years=1)

            data.begintime=int(time.mktime(begintime.timetuple()))
            data.endtime=int(time.mktime(endtime.timetuple()))
            self.modify_user_terminal_car(data)
        except Exception as e:
            status = ErrorCode.FAILED 
            self.write_ret(status)
