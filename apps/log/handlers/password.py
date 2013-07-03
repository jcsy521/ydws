#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging

import tornado.web
from tornado.escape import  json_decode

from codes.errorcode import ErrorCode
from base import authenticated, BaseHandler

class LOGPasswordHandler(BaseHandler):

    @authenticated
    def get(self):
        username = self.get_current_user()
        n_role = self.db.get("select role from T_LOG_ADMIN where name = %s", username)
        self.render("password/password.html",
                     username=username,
					 role=n_role.role)

    @authenticated
    @tornado.web.removeslash
    def put(self):
        username = self.get_current_user()
        try:
            data = json_decode(self.request.body)
            old_password = data.get("old_password")
            new_password = data.get("new_password")
        except Exception as e:
            logging.exception("[LOG] Wrong data format. Exception: %s",
                               e.args)
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            self.write_ret(status)
            return

        try:
            r = self.db.get("SELECT id FROM T_LOG_ADMIN"
                            "  WHERE password = password(%s)"
                            "    AND name = %s",
                            old_password, username)
            if not r:
                self.write_ret(ErrorCode.WRONG_OLD_PASSWORD)
            elif r:
                r = self.db.execute("UPDATE T_LOG_ADMIN"
                                "  SET password = PASSWORD(%s)"
                                "  WHERE name = %s",
                                new_password, username)
                self.write_ret(ErrorCode.SUCCESS)

        except Exception as e:
            logging.exception("[LOG] USER: %s 's password change is failed. Exception: %s",
                              username, e.args)
            self.write_ret(ErrorCode.FAILED)
