# -*- coding: utf-8 -*-

import logging

import tornado.web
from tornado.escape import json_encode, json_decode

from utils.dotdict import DotDict
from utils.checker import check_sql_injection, check_phone
from codes.errorcode import ErrorCode
from constants import UWEB 
from base import BaseHandler, authenticated
from mixin.register import RegisterMixin 

class RegisterHandler(BaseHandler, RegisterMixin):

    @tornado.web.removeslash
    def get(self):
        self.render("register.html")

    @tornado.web.removeslash
    def post(self):
        """We store uid, tid and sim in the cookie to
        authenticate the user.
        """
        uid = self.get_argument("uid", "")
        mobile = self.get_argument("mobile", "")
        password = self.get_argument("password", "")
        name = self.get_argument("name", "")
        address = self.get_argument("address", "")
        email = self.get_argument("email", "")

        #NOTE: when user register first time, mobile and tid may be null
        tid = self.get_argument("tid", "")

        # must check username and password avoid sql injection.
        if not uid.isalnum() and password.isalnum():
            self.render("register.html",
                        message=ErrorCode.ERROR_MESSAGE[ErrorCode.REGISTER_FAILED])
            return

        if not (check_sql_injection(uid) and check_sql_injection(password)):
            self.render("register.html",
                        message=ErrorCode.ERROR_MESSAGE[ErrorCode.REGISTER_FAILED])
            return

        try:
            self.insert_user(uid, password, name, mobile, address, email)
            # NOTE: if tid and sim are not provided, nothing is inserted in
            # database, and untrust uid and sim are stored in cookie, hoping 
            # to be modified when a true terminal is registered. it's same with login
            self.insert_terminal(tid, mobile, uid)
            self.bookkeep(dict(uid=uid,
                               tid=tid if tid else str(uid),
                               sim=mobile))

            self.redirect(self.get_argument("next","/"))
        except Exception as e:
            self.render("register.html",
                        message=ErrorCode.ERROR_MESSAGE[ErrorCode.REGISTER_FAILED])
            logging.exception('Register failed. Exception: %s', e.args)


    @tornado.web.removeslash
    def put(self):
        """We store uid, tid and sim in the cookie to
        authenticate the user.
        """
        uid = self.get_argument("uid","")
        mobile = self.get_argument("mobile","")
        status = ErrorCode.SUCCESS
        if uid:
            status =  self.check_user_by_uid(uid)
        if mobile:
            status =  self.check_user_by_mobile(mobile)
        self.write_ret(status)
