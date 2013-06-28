#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import re

import tornado.web
from tornado.escape import json_decode

from base import authenticated,BaseHandler
from helpers.queryhelper import QueryHelper
from codes.errorcode import ErrorCode
from utils.dotdict import DotDict
from utils.checker import check_zs_phone, ZS_PHONE_CHECKER

class WLSearchHandler(BaseHandler):

    @authenticated
    def get(self):
        username = self.get_current_user()
        self.render('whitelist/whitelist.html',
                    username = username)

    @authenticated
    @tornado.web.removeslash
    def post(self):   
        status = ErrorCode.SUCCESS
        try:
            data = json_decode(self.request.body)
            mobile = data.get('mobile')
            if check_zs_phone(mobile, self.db):
                biz_type = QueryHelper.get_biz_by_mobile(mobile, self.db)
                if biz_type:
                    biz_type = biz_type.get('biz_type')
                else:
                    r = re.compile(r"^(1477847\d{4})$")
                    if r.match(mobile):
                        biz_type = 1
                    else:
                        biz_type = 0
                whitelist = DotDict(mobile=mobile, biz_type=biz_type)
                self.write_ret(status, dict_=DotDict(whitelist=whitelist)) 
            else:
                status = ErrorCode.MOBILE_NOT_ORDERED
                message = ErrorCode.ERROR_MESSAGE[status] % mobile
                self.write_ret(status=status, message=message)
        except Exception as e:
            logging.exception("Search whitelist failed.Terminal mobile: %s, owner mobile: %s", mobile)
            self.render('errors/error.html',
                        message=ErrorCode.FAILED)

class AddWLHandler(BaseHandler):
    
    @authenticated
    @tornado.web.removeslash
    def post(self):
        status = ErrorCode.SUCCESS
        try:
            data = json_decode(self.request.body)
            mobile = data.get('mobile')
            biz_type = data.get('biz_type')
            if check_zs_phone(mobile, self.db):
                status=ErrorCode.DATA_EXIST
                self.write_ret(status)
            else:
                self.db.execute("INSERT INTO T_BIZ_WHITELIST VALUES (NULL, %s, %s)", mobile, biz_type)
                self.write_ret(status)
        except Exception as e:
            logging.exception("Add whitelist failed.Terminal mobile: %s, owner mobile: %s", mobile)
            self.render('errors/error.html', message=ErrorCode.FAILED)

    @authenticated
    @tornado.web.removeslash
    def put(self):
        status = ErrorCode.SUCCESS
        try:
            data = json_decode(self.request.body)
            mobile = data.get('mobile')
            biz_type = data.get('biz_type')
            if check_zs_phone(mobile, self.db):
                self.db.execute("UPDATE T_BIZ_WHITELIST SET biz_type= %s WHERE mobile= %s", biz_type, mobile)
                self.write_ret(status)
            else:
                status = ErrorCode.MOBILE_NOT_ORDERED
                message = ErrorCode.ERROR_MESSAGE[status] % mobile 
                self.write_ret(status=status, message=message)
        except Exception as e:
            logging.exception("Edit whitelist failed.Terminal mobile: %s, owner mobile: %s", mobile)
            self.render('errors/error.html', message=ErrorCode.FAILED)
