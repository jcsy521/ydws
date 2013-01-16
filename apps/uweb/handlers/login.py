# -*- coding: utf-8 -*-

import hashlib
import time
import logging
from hashlib import md5

import tornado.web
from tornado.escape import json_encode, json_decode

from utils.dotdict import DotDict
from utils.misc import get_ios_id_key, get_ios_badge_key
from utils.checker import check_sql_injection, check_phone
from codes.errorcode import ErrorCode
from constants import GATEWAY, UWEB
from base import BaseHandler, authenticated
from helpers.notifyhelper import NotifyHelper
from helpers.queryhelper import QueryHelper 
from helpers.downloadhelper import get_version_info 

from mixin.login import LoginMixin

class LoginHandler(BaseHandler, LoginMixin):

    @tornado.web.removeslash
    def get(self):
        self.render("login.html",
                    username='',
                    password='',
                    user_type=UWEB.USER_TYPE.PERSON,
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
        user_type = self.get_argument("user_type", UWEB.USER_TYPE.PERSON)
        captchahash = self.get_argument("captchahash", "")

        logging.info("[UWEB] Browser login request, username: %s, password: %s, user_type: %s", username, password, user_type)

        # must check username and password avoid sql injection.
        if not (username.isalnum() and password.isalnum()):
            self.render("login.html",
                        username='',
                        password='',
                        user_type=user_type,
                        message_captcha=None,
                        message=ErrorCode.ERROR_MESSAGE[ErrorCode.LOGIN_FAILED])
            return

        if not (check_sql_injection(username) and check_sql_injection(password)):
            self.render("login.html",
                        username="",
                        password="",
                        user_type=user_type,
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
                        user_type=user_type,
                        message=None,
                        message_captcha=ErrorCode.ERROR_MESSAGE[ErrorCode.WRONG_CAPTCHA])
            return

        # check the user, return uid, tid, sim and status
        cid, uid, tid, sim, status = self.login_passwd_auth(username, password, user_type)
        if status == ErrorCode.SUCCESS: 
            self.bookkeep(dict(cid=cid,
                               uid=uid,
                               tid=tid,
                               sim=sim))
            user_info = QueryHelper.get_user_by_uid(uid, self.db)
            #NOTE: if corp has no user and terminal, allow it log in without sms.  
            if user_info: 
                terminals = self.db.query("SELECT ti.tid, ti.alias, ti.mobile as sim,"
                                          "  ti.login, ti.keys_num"
                                          "  FROM T_TERMINAL_INFO as ti"
                                          "  WHERE ti.owner_mobile = %s ORDER BY LOGIN DESC",
                                          user_info.mobile)
                #NOTE: if alias is null, provide cnum or sim instead
                for terminal in terminals:
                    terminal['keys_num'] = 0
                    if not terminal.alias:
                        terminal['alias'] = QueryHelper.get_alias_by_tid(terminal.tid, self.redis, self.db)
                
                self.login_sms_remind(uid, user_info.mobile, terminals, login="WEB")
            else: 
                pass
            self.clear_cookie('captchahash')
            self.redirect(self.get_argument("next","/"))
        else:
            logging.info("[UWEB] username: %s login failed, message: %s", username, ErrorCode.ERROR_MESSAGE[status])
            self.render("login.html",
                        username=username,
                        password=password,
                        user_type=user_type,
                        message_captcha=None,
                        message=ErrorCode.ERROR_MESSAGE[status])

class IOSHandler(BaseHandler, LoginMixin):

    @tornado.web.removeslash
    def post(self):
        username = self.get_argument("username")
        password = self.get_argument("password")
        iosid = self.get_argument("iosid",'')
        user_type = self.get_argument("user_type", UWEB.USER_TYPE.PERSON)
        logging.info("[UWEB] IOS login request, username: %s, password: %s, iosid: %s, user_type: %s", username, password, iosid, user_type)
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
        cid, uid, tid, sim, status = self.login_passwd_auth(username, password, user_type)
        if status == ErrorCode.SUCCESS: 
            self.bookkeep(dict(cid=cid,
                               uid=uid,
                               tid=tid,
                               sim=sim))
            user_info = QueryHelper.get_user_by_uid(uid, self.db)
            terminals = self.db.query("SELECT ti.tid, ti.alias, ti.mobile as sim,"
                                      "  ti.login, ti.keys_num"
                                      "  FROM T_TERMINAL_INFO as ti"
                                      "  WHERE ti.owner_mobile = %s ORDER BY LOGIN DESC",
                                      user_info.mobile)
            #NOTE: if alias is null, provide cnum or sim instead
            for terminal in terminals:
                terminal['keys_num'] = 0
                if terminal['login'] == GATEWAY.TERMINAL_LOGIN.SLEEP:
                    terminal['login'] = GATEWAY.TERMINAL_LOGIN.ONLINE
                if not terminal.alias:
                    terminal['alias'] = QueryHelper.get_alias_by_tid(terminal.tid, self.redis, self.db)

            ios_id_key = get_ios_id_key(username)
            self.redis.setvalue(ios_id_key, iosid, UWEB.IOS_ID_INTERVAL)
            ios_badge_key = get_ios_badge_key(username)
            self.redis.setvalue(ios_badge_key, 0, UWEB.IOS_ID_INTERVAL)
            self.login_sms_remind(uid, user_info.mobile, terminals, login="IOS")
            self.write_ret(status,
                           dict_=DotDict(name=user_info.name, 
                                         cars=terminals))
        else:
            logging.info("[UWEB] username: %s login failed, message: %s", username, ErrorCode.ERROR_MESSAGE[status])
            self.write_ret(status)

class AndroidHandler(BaseHandler, LoginMixin):

    @tornado.web.removeslash
    def post(self):
        username = self.get_argument("username")
        password = self.get_argument("password")
        user_type = self.get_argument("user_type", UWEB.USER_TYPE.PERSON)
        logging.info("[UWEB] Android login request, username: %s, password: %s, user_type: %s", username, password, user_type)
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
        cid, uid, tid, sim, status = self.login_passwd_auth(username, password, user_type)
        if status == ErrorCode.SUCCESS: 
            self.bookkeep(dict(cid=cid,
                               uid=uid,
                               tid=tid,
                               sim=sim))

            user_info = QueryHelper.get_user_by_uid(uid, self.db)
            terminals = self.db.query("SELECT ti.tid, ti.alias, ti.mobile as sim,"
                                      "  ti.login, ti.keys_num"
                                      "  FROM T_TERMINAL_INFO as ti"
                                      "  WHERE ti.owner_mobile = %s ORDER BY LOGIN DESC",
                                      user_info.mobile)
            #NOTE: if alias is null, provide cnum or sim instead
            for terminal in terminals:
                terminal['keys_num'] = 0
                if terminal['login'] == GATEWAY.TERMINAL_LOGIN.SLEEP:
                    terminal['login'] = GATEWAY.TERMINAL_LOGIN.ONLINE
                if not terminal.alias:
                    terminal['alias'] = QueryHelper.get_alias_by_tid(terminal.tid, self.redis, self.db)
            
            push_info = NotifyHelper.get_push_info()
            push_key = NotifyHelper.get_push_key(uid, self.redis)
            version_info = get_version_info("android")
            self.login_sms_remind(uid, user_info.mobile, terminals, login="ANDROID")
            self.write_ret(status,
                           dict_=DotDict(push_id=uid,
                                         app_key=push_info.app_key,
                                         push_key=push_key,
                                         name=user_info.name, 
                                         cars=terminals,
                                         version_info=version_info))
        else:
            logging.info("[UWEB] username: %s login failed, message: %s", username, ErrorCode.ERROR_MESSAGE[status])
            self.write_ret(status)

class LogoutHandler(BaseHandler):

    @authenticated
    @tornado.web.removeslash
    def get(self):
        """Clear the cookie and return to login.html."""
        self.clear_cookie(self.app_name)
        self.redirect(self.get_argument("next", "/"))

