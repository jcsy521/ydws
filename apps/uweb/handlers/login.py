# -*- coding: utf-8 -*-

import hashlib
import time
import logging
from hashlib import md5

import tornado.web
from tornado.escape import json_encode, json_decode

from utils.dotdict import DotDict
from utils.checker import check_sql_injection, check_phone
from codes.errorcode import ErrorCode
from base import BaseHandler, authenticated
from helpers.notifyhelper import NotifyHelper
from helpers.queryhelper import QueryHelper 
from mixin.login import LoginMixin

class LoginHandler(BaseHandler, LoginMixin):

    @tornado.web.removeslash
    def get(self):
        self.render("login.html",
                    username='',
                    password='',
                    message=None,
                    message_captcha=None)

    @tornado.web.removeslash
    def post(self):
        """We store uid, tid and sim in the cookie to
        authenticate the user.
        """
        username = self.get_argument("username", "")
        password = self.get_argument("password", "")
        captcha = self.get_argument("captcha", "")
        captchahash = self.get_argument("captchahash", "")

        # must check username and password avoid sql injection.
        if not (username.isalnum() and password.isalnum()):
            self.render("login.html",
                        username='',
                        password='',
                        message_captcha=None,
                        message=ErrorCode.ERROR_MESSAGE[ErrorCode.LOGIN_FAILED])
            return

        if not (check_sql_injection(username) and check_sql_injection(password)):
            self.render("login.html",
                        username="",
                        password="",
                        message_captcha=None,
                        message=ErrorCode.ERROR_MESSAGE[ErrorCode.LOGIN_FAILED])
            return

        m = hashlib.md5()
        m.update(captcha.lower())
        hash_ = m.hexdigest()
        if hash_.lower() != captchahash.lower():
            self.render("login.html",
                        username=username,
                        password=password,
                        message=None,
                        message_captcha=ErrorCode.ERROR_MESSAGE[ErrorCode.WRONG_CAPTCHA])
            return

        # check the user, return uid, tid, sim and status
        uid, tid, sim, status = self.login_passwd_auth(username, password)
        if status == ErrorCode.SUCCESS: 
            self.bookkeep(dict(uid=uid,
                               tid=tid,
                               sim=sim))

            user_info = QueryHelper.get_user_by_uid(uid, self.db)
            terminals = self.db.query("SELECT ti.tid, ti.alias, ti.mobile as sim,"
                                      "  ti.login, ti.keys_num"
                                      "  FROM T_TERMINAL_INFO as ti"
                                      "  WHERE ti.owner_mobile = %s ORDER BY LOGIN DESC",
                                      user_info.mobile)
            
            #NOTE: if alias is null, provide sim instead
            for terminal in terminals:
                if not terminal.alias:
                    terminal.alias = terminal.sim
            self.login_sms_remind(uid, user_info.mobile, terminals, login="WEB")
            self.clear_cookie('captchahash')
            self.redirect(self.get_argument("next","/"))
        else:
            logging.info("Login failed, message: %s", ErrorCode.ERROR_MESSAGE[status])
            self.render("login.html",
                        username='',
                        password='',
                        message_captcha=None,
                        message=ErrorCode.ERROR_MESSAGE[status])

class LoginTestHandler(BaseHandler, LoginMixin):

    @tornado.web.removeslash
    def post(self):

        logging.info("Parent is trying to use ABT...")
        username = self.get_argument("username", "")
        self.bookkeep(dict(uid=username,
                           tid="15242410793",
                           sim="15242410793"))

        #NOTE:  Google IFRAME Cookie to know the trick here.
        self.set_header("P3P", "CP=CAO PSA OUR")
        self.redirect(self.get_argument("next", "/"))

class WAPTransferHandler(BaseHandler, LoginMixin):

    @tornado.web.removeslash
    def post(self):
        username = self.get_argument("username")
        password = self.get_argument("password")
        # must check username and password avoid sql injection.
        if not (username.isalnum() and password.isalnum()):
            status= ErrorCode.LOGIN_FAILED
            self.write_ret(status)
            return
        if not (check_sql_injection(username) and check_sql_injection(password)):
            status= ErrorCode.LOGIN_FAILED
            self.write_ret(status)
            return

        # check the user, return uid, tid, sim and status
        uid, tid, sim, status = self.login_passwd_auth(username, password)
        if status == ErrorCode.SUCCESS: 
            self.bookkeep(dict(uid=uid,
                               tid=tid,
                               sim=sim))

            user_info = QueryHelper.get_user_by_uid(uid, self.db)
            terminals = self.db.query("SELECT ti.tid, ti.alias, ti.mobile as sim,"
                                      "  ti.login, ti.keys_num"
                                      "  FROM T_TERMINAL_INFO as ti"
                                      "  WHERE ti.owner_mobile = %s ORDER BY LOGIN DESC",
                                      user_info.mobile)
            
            #NOTE: if alias is null, provide sim instead
            for terminal in terminals:
                if not terminal.alias:
                    terminal.alias = terminal.sim
            self.login_sms_remind(uid, user_info.mobile, terminals, login="WAP")
            self.write_ret(status)
        else:
            logging.info("Login failed, message: %s", ErrorCode.ERROR_MESSAGE[status])
            self.write_ret(status)

class IOSHandler(BaseHandler, LoginMixin):

    @tornado.web.removeslash
    def post(self):
        username = self.get_argument("username")
        password = self.get_argument("password")
        # must check username and password avoid sql injection.
        if not (username.isalnum() and password.isalnum()):
            status= ErrorCode.LOGIN_FAILED
            self.write_ret(status)
            return
        if not (check_sql_injection(username) and check_sql_injection(password)):
            status= ErrorCode.LOGIN_FAILED
            self.write_ret(status)
            return

        # check the user, return uid, tid, sim and status
        uid, tid, sim, status = self.login_passwd_auth(username, password)
        if status == ErrorCode.SUCCESS: 
            self.bookkeep(dict(uid=uid,
                               tid=tid,
                               sim=sim))
            user_info = QueryHelper.get_user_by_uid(uid, self.db)
            terminals = self.db.query("SELECT ti.tid, ti.alias, ti.mobile as sim,"
                                      "  ti.login, ti.keys_num"
                                      "  FROM T_TERMINAL_INFO as ti"
                                      "  WHERE ti.owner_mobile = %s ORDER BY LOGIN DESC",
                                      user_info.mobile)
            
            #NOTE: if alias is null, provide sim instead
            for terminal in terminals:
                if not terminal.alias:
                    terminal.alias = terminal.sim

            self.write_ret(status,
                           dict_=DotDict(name=user_info.name, 
                                         cars=terminals))
            self.login_sms_remind(uid, user_info.mobile, terminals, login="IOS")
        else:
            logging.info("Login failed, message: %s", ErrorCode.ERROR_MESSAGE[status])
            self.write_ret(status)

class AndroidHandler(BaseHandler, LoginMixin):

    @tornado.web.removeslash
    def post(self):
        username = self.get_argument("username")
        password = self.get_argument("password")
        # must check username and password avoid sql injection.
        if not (username.isalnum() and password.isalnum()):
            status= ErrorCode.LOGIN_FAILED
            self.write_ret(status)
            return
        if not (check_sql_injection(username) and check_sql_injection(password)):
            status= ErrorCode.LOGIN_FAILED
            self.write_ret(status)
            return

        # check the user, return uid, tid, sim and status
        uid, tid, sim, status = self.login_passwd_auth(username, password)
        if status == ErrorCode.SUCCESS: 
            self.bookkeep(dict(uid=uid,
                               tid=tid,
                               sim=sim))

            user_info = QueryHelper.get_user_by_uid(uid, self.db)
            terminals = self.db.query("SELECT ti.tid, ti.alias, ti.mobile as sim,"
                                      "  ti.login, ti.keys_num"
                                      "  FROM T_TERMINAL_INFO as ti"
                                      "  WHERE ti.owner_mobile = %s ORDER BY LOGIN DESC",
                                      user_info.mobile)
            
            #NOTE: if alias is null, provide sim instead
            for terminal in terminals:
                if not terminal.alias:
                    terminal.alias = terminal.sim

            push_info = NotifyHelper.get_push_info()
            push_key = NotifyHelper.get_push_key(uid, self.redis)
            self.login_sms_remind(uid, user_info.mobile, terminals, login="ANDROID")
            self.write_ret(status,
                           dict_=DotDict(app_key=push_info.app_key,
                                         push_key=push_key,
                                         name=user_info.name, 
                                         cars=terminals))
        else:
            logging.info("Login failed, message: %s", ErrorCode.ERROR_MESSAGE[status])
            self.write_ret(status)

class LogoutHandler(BaseHandler):

    @authenticated
    @tornado.web.removeslash
    def get(self):
        """Clear the cookie and return to login.html."""
        self.clear_cookie(self.app_name)
        self.redirect(self.get_argument("next", "/"))

