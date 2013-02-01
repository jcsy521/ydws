#!/usr/bin/python
# -*- coding: UTF-8 -*-
  
import uuid
import hashlib

import tornado.web
import tornado.database

from urllib import quote
from misc import safe_utf8
from base import BaseHandler
from fileconf import FileConf


class Login(BaseHandler):
    
    @tornado.web.removeslash
    def get(self):
        self.render("login.html", 
                    username="",
                    password="",
                    message=None,
                    message_captcha=None)
        return

    @tornado.web.removeslash
    def post(self):
        login = self.get_argument('username', '')
        password = self.get_argument('password', '')

        print 'login', login
        print 'password', password 

        captcha = self.get_argument('captcha', '')
        captchahash = self.get_argument('captchahash', '')
        m = hashlib.md5()
        m.update(captcha.lower())
        hash_ = m.hexdigest()
        if hash_.lower() != captchahash.lower():
            self.render("login.html",
                        username=login,
                        password='',
                        message=None,
                        message_captcha=u"验证码错误")
            return
        else:
            r = self.db.get("SELECT id, name"
                            "  FROM T_LOG_ADMIN"
                            "    WHERE name = %s"
                            "      AND password = password(%s)",
                            login, password)
            if r:
                self.bookkeep(dict(id=r.id, 
                                   session_id=uuid.uuid4().hex),
                                   quote(safe_utf8(r.name)))
                self.redirect("/systemlog")    
            else:
                self.render("login.html", 
                            username=login,
                            password="",
                            message=u"用户名或密码错误",
                            message_captcha=None)
                return
