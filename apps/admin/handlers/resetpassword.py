# -*- coding: utf-8 -*-


"""This module is designed for seset-password of users.
Include individual, enterprise).
"""

import logging

import tornado.web
from tornado.escape import json_decode

from utils.dotdict import DotDict
from base import BaseHandler, authenticated
from checker import check_areas, check_privileges 
from constants import PRIVILEGES, UWEB
from codes.errorcode import ErrorCode 
from utils.checker import check_sql_injection, check_zs_phone
from helpers.smshelper import SMSHelper
from codes.smscode import SMSCode 


class ResetPasswordHandler(BaseHandler):

    @authenticated
    @check_privileges([PRIVILEGES.BUSINESS_QUERY])
    @tornado.web.removeslash
    def get(self):
        """Just to resetpassword.html.
        """
        self.render('business/resetpassword.html',
                    status=ErrorCode.SUCCESS,
                    message='')

    @authenticated
    @check_privileges([PRIVILEGES.BUSINESS_QUERY])
    @tornado.web.removeslash
    def post(self):
        """Create business for a couple of users.
        """
        status = ErrorCode.SUCCESS
        try:
            RESET_PSD = '111111'
            data = DotDict(json_decode(self.request.body))
            user_type = data.user_type
            mobile = data.mobile
            logging.info("[ADMIN] Reset password request: %s.",
                          self.request.body)
        except Exception as e: 
            status = ErrorCode.ILLEGAL_DATA_FORMAT 
            logging.info("[ADMIN] Invalid data format. data: %s, Exception: %s",
                          self.request.body, e.args)
            self.write_ret(status) 
            return 

        try:
            if user_type == UWEB.USER_TYPE.PERSON: 
                user = self.db.get("SELECT id"
                                   "  FROM T_USER"
                                   "    WHERE uid = %s"
                                   "      LIMIT 1",
                                   mobile)

                if not user:
                    status = ErrorCode.USER_NOT_EXIST 
                    logging.info("[ADMIN] user: %s can not be found",
                                  mobile) 
                else:
                    self.db.execute("UPDATE T_USER"
                                    "  set password=password(%s)"
                                    "    WHERE uid = %s",
                                    RESET_PSD, mobile)
                    logging.info("[ADMIN] user: %s reset password to %s.",
                                  mobile, RESET_PSD) 
            elif user_type == UWEB.USER_TYPE.OPERATOR:
                user = self.db.get("SELECT id"
                                   "  FROM T_OPERATOR" 
                                   "  WHERE oid = %s" 
                                   " LIMIT 1", 
                                   mobile)
                if not user:
                    status = ErrorCode.USER_NOT_EXIST 
                    logging.info("[ADMIN] operator: %s can not be found",
                                  mobile) 
                else:
                    self.db.execute("UPDATE T_OPERATOR"
                                    "  SET password=password(%s)"
                                    "    WHERE oid = %s",
                                    RESET_PSD, mobile)
                    logging.info("[ADMIN] operator: %s reset password to %s.",
                                  mobile, RESET_PSD) 
            else:
                user = self.db.get("SELECT id"
                                   "  FROM T_CORP"
                                   "    WHERE cid = %s"
                                   "      LIMIT 1", 
                                   mobile)
                if not user:
                    status = ErrorCode.USER_NOT_EXIST 
                    logging.info("[ADMIN] corp: %s can not be found",
                                  mobile) 
                else:
                    self.db.execute("UPDATE T_CORP"
                                    "  SET password=password(%s)"
                                    "    WHERE cid = %s",
                                    RESET_PSD, mobile)
                    logging.info("[ADMIN] enterprise: %s reset password to %s.",
                                  mobile, RESET_PSD) 
            if status == ErrorCode.SUCCESS:
                reset_password_sms = SMSCode.SMS_RESET_PASSWORD % RESET_PSD 
                SMSHelper.send(mobile, reset_password_sms)
            self.write_ret(status)
        except Exception as e:
            status = ErrorCode.SERVER_BUSY
            logging.exception("[ADMIN] Reset password failed. Exception: %s",
                               e.args)
            self.render('errors/error.html',
                        message=ErrorCode.ERROR_MESSAGE[status])

