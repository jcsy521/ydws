# -*- coding: utf-8 -*-

import logging

from tornado.escape import json_decode, json_encode
import tornado.web

from utils.misc import get_today_last_month
from utils.dotdict import DotDict
from utils.checker import check_sql_injection

from base import BaseHandler, authenticated
from codes.errorcode import ErrorCode


class ProfileHandler(BaseHandler):

    @authenticated
    @tornado.web.removeslash
    def get(self):
        """Display profile of current user.
        """
        status = ErrorCode.SUCCESS
        try: 
            user = self.db.get("SELECT name, mobile, address, email, remark"
                               "  FROM T_USER"
                               "  WHERE uid = %s"
                               "  LIMIT 1",
                               self.current_user.uid) 
            if not user:
                status = ErrorCode.LOGIN_AGAIN
                logging.error("The user with uid: %s does not exist, redirect to login.html", self.current_user.uid)
                self.write_ret(status)
                return
            self.write_ret(status,
                           dict_=dict(profile=user))
        except Exception as e:
            logging.exception("[UWEB] uid:%s tid:%s get profile failed. Exception: %s", 
                              self.current_user.uid, self.current_user.tid, e.args) 
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)

    @authenticated
    @tornado.web.removeslash
    def put(self):
        """Modify profile of current user.
        """
        status = ErrorCode.SUCCESS
        try:
            data = DotDict(json_decode(self.request.body))
            logging.info("[UWEB] profile request: %s, uid: %s, tid: %s", 
                         data, self.current_user.uid, self.current_user.tid)
        except Exception as e:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            self.write_ret(status)
            return 

        try:
            if data.has_key('name')  and not check_sql_injection(data.name):
                status = ErrorCode.ILLEGAL_NAME 
                self.write_ret(status)
                return

            if data.has_key('address')  and not check_sql_injection(data.address):
                status = ErrorCode.ILLEGAL_ADDRESS
                self.write_ret(status)
                return

            if data.has_key('email')  and not check_sql_injection(data.email):
                status = ErrorCode.ILLEGAL_EMAIL 
                self.write_ret(status)
                return

            if data.has_key('remark')  and not check_sql_injection(data.remark):
                status = ErrorCode.ILLEGAL_REMARK 
                self.write_ret(status)
                return

            fields_ = DotDict()
            fields = DotDict(name="name = '%s'",
                             mobile="mobile = '%s'",
                             address="address = '%s'",
                             email="email = '%s'",
                             remark="remark = '%s'")
            for key, value in data.iteritems():
                fields_.setdefault(key, fields[key] % value) 
            set_clause = ','.join([v for v in fields_.itervalues() if v is not None])
            if set_clause:
                self.db.execute("UPDATE T_USER SET " + set_clause +
                                "  WHERE uid = %s",
                                self.current_user.uid)
            self.write_ret(status)
        except Exception as e:
            logging.exception("[UWEB] uid:%s tid:%s update profile failed.  Exception: %s", 
                              self.current_user.uid, self.current_user.tid, e.args)
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)
