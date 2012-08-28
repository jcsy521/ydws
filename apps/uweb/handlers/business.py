# -*- coding: utf-8 -*-

from os import SEEK_SET
import datetime, time
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
        status = ErrorCode.FAILED 
        res = self.db.query("SELECT id FROM T_TERMINAL_INFO"
                            "  WHERE owner_mobile = %s",
                            mobile)
        if len(res) < 2:
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
        status = ErrorCode.FAILED 
        res = self.db.get("SELECT id FROM T_TERMINAL_INFO"
                          "  WHERE mobile = %s"
                          "  LIMIT 1",
                          tmobile)
        if not res:
            status = ErrorCode.SUCCESS 
        self.write_ret(status)

class BusinessCreateHandler(BaseHandler, BusinessMixin):

    @authenticated
    @tornado.web.removeslash
    def post(self):
        """Create business for a couple of users.
        """
        print 'business create', self.request.body
        data = DotDict(json_decode(self.request.body))
        print 'data', data

        self.modify_user_terminal_car(data)
