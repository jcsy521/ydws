# -*- coding:utf-8 -*-

"""This module is designed for login.
"""

import os.path
import uuid
import hashlib
from urllib import quote
from time import time
from datetime import datetime

import tornado.web

from utils.misc import safe_utf8
from utils.checker import check_sql_injection
from mixin import BaseMixin
from errors import ErrorCode
from constants import XXT

from base import BaseHandler, authenticated

from iptoaddress import QQWry

qqwry = QQWry()
_dat = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'qqwry.dat')
print "Initializing IP database...."
with open(_dat, 'rb') as f:
    qqwry.open(f)
    print "IP database initialized."


class LoginHandler(BaseHandler, BaseMixin):

    @tornado.web.removeslash
    def get(self):
        """Jump to the page login.html.
        """
        self.render("login.html",
                    username="",
                    password="",
                    message_captcha=None,
                    message=None)

    @tornado.web.removeslash
    def post(self):
        """Check the parameters of login and check whether or not prevent it.
        """
        login = self.get_argument('username', '')
        password = self.get_argument('password', '')
        captcha = self.get_argument('captcha', '')
        # NOTE: Get captchahash from cookie
        captchahash = self.get_secure_cookie("captchahash")

        # must check username and password avoid sql injection.
        if not login.isalnum():
            self.render("login.html",
                        username="",
                        password="",
                        message_captcha=None,
                        message=ErrorCode.LOGIN_FAILED)
            return

        if not (check_sql_injection(login) and check_sql_injection(password)):
            self.render("login.html",
                        username="",
                        password="",
                        message_captcha=None,
                        message=ErrorCode.LOGIN_FAILED)
            return

        # check the captcha(hash)
        m = hashlib.md5()
        m.update(captcha.lower())
        hash_ = m.hexdigest()
        if hash_.lower() != captchahash.lower():
            self.render("login.html",
                        username=login,
                        password='',
                        message=None,
                        message_captcha=ErrorCode.WRONG_CAPTCHA)
            return

        # check username and password
        r = self.db.get("SELECT id, name, type FROM T_ADMINISTRATOR"
                        "  WHERE login = %s"
                        "    AND password = password(%s)"
                        "    AND valid = %s",
                        login, password, XXT.VALID.VALID)
        if r:
            self.__log(r.id)
            self.bookkeep(dict(id=r.id,
                               session_id=uuid.uuid4().hex),
                          quote(safe_utf8(r.name)))
            # update the privilege_area for current user.(through BaseMixin)
            key = self.get_area_memcache_key(r.id)
            areas = self.get_privilege_area(r.id)
            self.redis.setvalue(key, areas)

            self.clear_cookie('captchahash')
            self.redirect(self.get_argument("next", "/"))
        else:
            self.render("login.html",
                        username=login,
                        password='',
                        message_captcha=None,
                        message=ErrorCode.LOGIN_FAILED)

    def __log(self, id):
        """Keep the log of login.
        """
        if 'X-Real-Ip' in self.request.headers:
            # work behind nginx
            remote_ip = self.request.headers['X-Real-Ip']
        else:
            remote_ip = self.request.remote_ip
        self.db.execute("INSERT INTO T_ADMINISTRATOR_LOGIN_LOG"
                        "  VALUES (NULL, %s, %s, %s)",
                        id, remote_ip, int(time() * 1000))


class LoginHistoryHandler(BaseHandler):

    @authenticated
    @tornado.web.removeslash
    def get(self):
        """Get the latest 20 records of login.
        """
        logins = self.db.query("SELECT source, timestamp"
                               "  FROM T_ADMINISTRATOR_LOGIN_LOG"
                               "  WHERE administrator_id = %s"
                               "  ORDER BY id DESC"
                               "  LIMIT 20",
                               self.current_user.id)
        #NOTE: get address form IP.
        # python-MySQLdb coverts the date to GMT internally.
        for item in logins:
            item.timestamp = datetime.fromtimestamp(item.timestamp / 1000)
            address = qqwry.getRecordByIP(item.source)
            if address:
                item.address = u'，'.join(
                    [address[2].decode('gbk'), address[3].decode('gbk')])
            else:
                item.address = u'未知区域'
        # logins.sort(key=lambda item: item.timestamp, reverse=True)

        self.render("login_history.html", logins=logins)
