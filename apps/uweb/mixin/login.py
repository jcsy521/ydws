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
                           "      AND password = password(%s)"
                           "      LIMIT 1", 
                           username, password)

        return self.__internal_check(username, user)

    def __internal_check(self, mobile, user):
        """
        @return uid, tid, sim, status 
        """
        status = ErrorCode.SUCCESS
        if not user:
            status = ErrorCode.PARENT_NOT_ORDERED
            logging.info("%s login failed. Message: %s", mobile, ErrorCode.ERROR_MESSAGE[status])
            return None, None, None, status 
        else:    
            terminal = self.db.get("SELECT id, tid, mobile FROM T_TERMINAL_INFO"
                                   "  WHERE service_status = %s"
                                   "    AND owner_mobile = %s"
                                   "    AND (%s BETWEEN begintime AND endtime)"
                                   "  LIMIT 1",
                                   UWEB.SERVICE_STATUS.ON, user.mobile, int(time.time()))
            if not terminal: 
                status = ErrorCode.TERMINAL_NOT_ORDERED
                return None, None, None, status 

        #NOTE: now, if a user is avaliabe, he can log in the platform.
        #here, just provide a untrust tid and sim, and hope they can be 
        #reseted by switch
        return str(user.uid), str(terminal.tid), str(terminal.mobile), status

    def login_sms_remind(self, uid,  owner_mobile, terminals, login="WEB"):

        sms_option = QueryHelper.get_sms_option_by_uid(uid, 'login', self.db)
        if sms_option.login == 1:
            login_time = time.strftime("%Y-%m-%d %H:%M:%S")
            login_method = UWEB.LOGIN_WAY[login] 
            terminal_mobile = u'，'.join(str(terminal.alias) for terminal in terminals)
            remind_sms = SMSCode.SMS_LOGIN_REMIND % (login_time, login_method, owner_mobile, terminal_mobile) 
            SMSHelper.send(owner_mobile, remind_sms)
