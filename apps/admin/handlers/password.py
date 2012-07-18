# -*- coding: utf-8 -*-

import tornado.web

from constants import PRIVILEGES, XXT
from errors import ErrorCode

from checker import check_privileges
from base import BaseHandler, authenticated
from utils.checker import check_sql_injection


class PasswordMixin:

    def do_get(self, is_self=True):
        if is_self:
            administrators = []
        else:
            self_id = self.current_user.id
            administrators = self.db.query("SELECT id, login"
                                           "  FROM T_ADMINISTRATOR"
                                           "  WHERE id != %s"
                                           "  AND valid = %s",
                                           self_id, XXT.VALID.VALID)

        self.render("administrator/password.html",
                    is_response=False,
                    is_self=is_self,
                    administrators=administrators)

    def do_post(self, is_self=True):

        id = self.get_argument('id', self.current_user.id)
        self_id = self.current_user.id

        if is_self:
            old_password = self.get_argument('old_password', '')
            if not check_sql_injection(old_password):
                self.do_get(is_self=True)
                return 
            r = self.db.get("SELECT id FROM T_ADMINISTRATOR"
                            "  WHERE password = password(%s)"
                            "    AND id = %s",
                            old_password, id)
            if not r:
                self.render("administrator/password.html",
                            is_response=True,
                            is_self=is_self,
                            message=ErrorCode.WRONG_PASSWORD)
                return

        new_password = self.get_argument('new_password')
        new_password2 = self.get_argument('new_password2')

        if not (check_sql_injection(new_password) and check_sql_injection(new_password2)): 
            self.do_get(is_self=False)
            return 
        administrators = self.db.query("SELECT id, login"
                                       "  FROM T_ADMINISTRATOR"
                                       "  WHERE id != %s"
                                       "  AND valid = %s",
                                       self_id, XXT.VALID.VALID)
        # TODO: how can this be? they are checked in the webpage. so, I am sure
        # this is dead codes.
        if new_password != new_password2:
            self.render("administrator/password.html",
                        administrators=administrators,
                        is_response=True,
                        is_self=is_self,
                        message=ErrorCode.WRONG_NEW_PASSWORD)
            return

        r = self.db.execute("UPDATE T_ADMINISTRATOR"
                            "  SET password = PASSWORD(%s)"
                            "  WHERE id = %s",
                            new_password, id)

        self.render("administrator/password.html",
                    administrators=administrators,
                    is_self=is_self,
                    is_response=True,
                    message=ErrorCode.UPDATE_PASSWORD_OK)


class MyPasswordHandler(BaseHandler, PasswordMixin):

    @authenticated
    @check_privileges([PRIVILEGES.RESET_MY_PASSWORD])
    @tornado.web.removeslash
    def get(self):

        self.do_get()

    @authenticated
    @check_privileges([PRIVILEGES.RESET_MY_PASSWORD])
    @tornado.web.removeslash
    def post(self):

        self.do_post()


class OtherPasswordHandler(BaseHandler, PasswordMixin):

    @authenticated
    @check_privileges([PRIVILEGES.RESET_OTHER_PASSWORD])
    @tornado.web.removeslash
    def get(self):

        self.do_get(is_self=False)

    @authenticated
    @check_privileges([PRIVILEGES.RESET_OTHER_PASSWORD])
    @tornado.web.removeslash
    def post(self):

        self.do_post(is_self=False)
