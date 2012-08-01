# -*- coding: utf-8 -*-

import logging
import time

from utils.misc import get_name_cache_key 
from utils.dotdict import DotDict
from helpers.confhelper import ConfHelper
from helpers.smshelper import SMSHelper
from constants import UWEB 
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
                                   "    AND (%s BETWEEN begintime AND endtime)",
                                   UWEB.SERVICE_STATUS.ON, user.mobile, int(time.time()))
            if not terminal: 
                status = ErrorCode.TERMINAL_NOT_ORDERED
                return None, None, None, status 

        #NOTE: now, if a user is avaliabe, he can log in the platform.
        #here, just provide a untrust tid and sim, and hope they can be 
        #reseted by switch
        return str(user.uid), str(terminal.tid), str(terminal.mobile), status
