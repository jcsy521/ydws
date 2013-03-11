# -*- coding: utf-8 -*-

import logging
import time

from utils.dotdict import DotDict
from helpers.confhelper import ConfHelper
from helpers.smshelper import SMSHelper
from helpers.queryhelper import QueryHelper
from constants import UWEB 
from utils.misc import DUMMY_IDS_STR
from codes.smscode import SMSCode
from codes.errorcode import ErrorCode
from base import BaseMixin


class LoginMixin(BaseMixin):

    def login_passwd_auth(self, username, password, user_type):
        """Check user whether available."""

        if user_type == UWEB.USER_TYPE.PERSON:
            user = self.db.get("SELECT uid, mobile"
                               "  FROM T_USER"
                               "    WHERE uid = %s"
                               "      LIMIT 1", 
                               username)
        else:
            user = self.db.get("SELECT cid, mobile"
                               "  FROM T_CORP"
                               "    WHERE cid = %s"
                               "      LIMIT 1", 
                               username)
        if not user:
            return None, None, None, ErrorCode.USER_NOT_ORDERED

        return self.__internal_check(username, password, user_type)

    def __internal_check(self, username, password, user_type):
        """
        @return cid, uid, terminals, status 
        """
        status = ErrorCode.SUCCESS

        if user_type == UWEB.USER_TYPE.PERSON:
            user = self.db.get("SELECT uid, mobile"
                               "  FROM T_USER"
                               "    WHERE uid = %s"
                               "      AND password = password(%s)"
                               "      LIMIT 1", 
                               username, password)
        else:
            user = self.db.get("SELECT cid, mobile"
                               "  FROM T_CORP"
                               "    WHERE cid = %s"
                               "      AND password = password(%s)"
                               "      LIMIT 1", 
                               username, password)
        if not user:
            status = ErrorCode.WRONG_PASSWORD
            logging.info("username: %s, password: %s login failed. Message: %s",
                         username, password, ErrorCode.ERROR_MESSAGE[status])
            return None, None, None, status 
        else:    
            if user_type == UWEB.USER_TYPE.PERSON:
                terminals = self.db.query("SELECT id, tid, mobile as sim, login, keys_num"
                                          "  FROM T_TERMINAL_INFO"
                                          "  WHERE service_status = %s"
                                          "    AND owner_mobile = %s"
                                          "    AND group_id = -1"
                                          "    AND (%s BETWEEN begintime AND endtime)",
                                          UWEB.SERVICE_STATUS.ON, username, int(time.time()))
                #NOTE: provide a dummy_cid for user
                cid = UWEB.DUMMY_CID 

                if not terminals: 
                    status = ErrorCode.TERMINAL_NOT_ORDERED
                    return None, None, None, status 
                else:
                    uid = user.uid
            else:
                cid = user.cid 
                groups = self.db.query("SELECT id, corp_id FROM T_GROUP WHERE corp_id = %s",
                                       user.cid)
                group_ids = [str(group.id) for group in groups]

                sql_cmd = ("SELECT id, tid, mobile as sim, login, keys_num, owner_mobile"
                           "  FROM T_TERMINAL_INFO"
                           "  WHERE service_status = %s"
                           "    AND group_id IN %s"
                           "    AND (%s BETWEEN begintime AND endtime) ") %\
                           (UWEB.SERVICE_STATUS.ON, str(tuple(group_ids+DUMMY_IDS_STR)), int(time.time()))
                terminals = self.db.query(sql_cmd)
                if not terminals: 
                    terminal = DotDict(tid=UWEB.DUMMY_TID,
                                       sim=UWEB.DUMMY_MOBILE)
                    return str(cid), UWEB.DUMMY_UID, [terminal,], status 
                else:
                    uid = terminals[0].owner_mobile 
                 
        return str(cid), str(uid), terminals, status

    def login_sms_remind(self, uid, owner_mobile, terminals, login="WEB"):

        sms_option = QueryHelper.get_sms_option_by_uid(uid, 'login', self.db)
        if sms_option.login == 1:
            login_time = time.strftime("%Y-%m-%d %H:%M:%S")
            login_method = UWEB.LOGIN_WAY[login] 
            terminal_mobile = u'”，“'.join(terminal.alias for terminal in terminals)
            remind_sms = SMSCode.SMS_LOGIN_REMIND % (login_time, login_method, owner_mobile, terminal_mobile) 
            SMSHelper.send(owner_mobile, remind_sms)
