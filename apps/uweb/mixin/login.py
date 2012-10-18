# -*- coding: utf-8 -*-

import logging
import time

from utils.dotdict import DotDict
from helpers.confhelper import ConfHelper
from helpers.smshelper import SMSHelper
from helpers.queryhelper import QueryHelper
from constants import UWEB 
from codes.smscode import SMSCode
from codes.errorcode import ErrorCode
from base import BaseMixin


class LoginMixin(BaseMixin):

    def login_passwd_auth(self, username, password):
        """Check user whether available."""

        user = self.db.get("SELECT uid, mobile"
                           "  FROM T_USER"
                           "    WHERE uid = %s"
                           "      LIMIT 1", 
                           username)
        if not user:
            return None, None, None, ErrorCode.USER_NOT_ORDERED

        return self.__internal_check(username, password)

    def __internal_check(self, username, password):
        """
        @return uid, tid, sim, status 
        """
        status = ErrorCode.SUCCESS

        user = self.db.get("SELECT uid, mobile"
                           "  FROM T_USER"
                           "    WHERE uid = %s"
                           "      AND password = password(%s)"
                           "      LIMIT 1", 
                           username, password)
        if not user:
            status = ErrorCode.LOGIN_FAILED
            logging.info("username: %s, password: %s login failed. Message: %s", username, password,  ErrorCode.ERROR_MESSAGE[status])
            return None, None, None, status 
        else:    
            terminals = self.db.query("SELECT id, tid, mobile FROM T_TERMINAL_INFO"
                                      "  WHERE service_status = %s"
                                      "    AND owner_mobile = %s"
                                      "    AND (%s BETWEEN begintime AND endtime)",
                                      UWEB.SERVICE_STATUS.ON, username, int(time.time()))
            if not terminals: 
                status = ErrorCode.TERMINAL_NOT_ORDERED
                return None, None, None, status 
            else:
                # provide a valid terminal
                terminal = terminals[0]  
        return str(user.uid), str(terminal.tid), str(terminal.mobile), status

    def login_sms_remind(self, uid,  owner_mobile, terminals, login="WEB"):

        sms_option = QueryHelper.get_sms_option_by_uid(uid, 'login', self.db)
        if sms_option.login == 1:
            login_time = time.strftime("%Y-%m-%d %H:%M:%S")
            login_method = UWEB.LOGIN_WAY[login] 
            terminal_mobile = u'，'.join(terminal.alias for terminal in terminals)
            remind_sms = SMSCode.SMS_LOGIN_REMIND % (login_time, login_method, owner_mobile, terminal_mobile) 
            SMSHelper.send(owner_mobile, remind_sms)
