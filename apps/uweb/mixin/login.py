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

        if user_type == UWEB.USER_TYPE.PERSON: # individual
            user = self.db.get("SELECT uid, mobile"
                               "  FROM T_USER"
                               "    WHERE uid = %s"
                               "      LIMIT 1", 
                               username)
        else: # enterprise
            user = self.db.get("SELECT cid, mobile"
                               "  FROM T_CORP"
                               "    WHERE cid = %s"
                               "      LIMIT 1", 
                               username)
            if not user:
                user = self.db.get("SELECT oid, mobile"
                                   "  FROM T_OPERATOR"
                                   "  WHERE oid = %s"
                                   "      LIMIT 1",
                                   username)
                user_type = UWEB.USER_TYPE.OPERATOR if user else None
        if not user:
            logging.info("[UWEB] user: %s can not be found.",
                          username)
            #return None, None, None, None, None, ErrorCode.USER_NOT_ORDERED
            return None, None, None, None, None, ErrorCode.WRONG_PASSWORD

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
        elif user_type == UWEB.USER_TYPE.OPERATOR:
            user = self.db.get("SELECT oid, mobile"
                               "  FROM T_OPERATOR"
                               "  WHERE oid = %s"
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
            return None, None, None, None, None, status 
        else:    
            if user_type == UWEB.USER_TYPE.PERSON:
                terminals = self.db.query("SELECT id, tid, mobile as sim, login, keys_num"
                                          "  FROM T_TERMINAL_INFO"
                                          "  WHERE service_status = %s"
                                          "    AND owner_mobile = %s"
                                          "    AND login_permit = 1",
                                          UWEB.SERVICE_STATUS.ON, username)
                                          #"    AND (%s BETWEEN begintime AND endtime)",
                                          #UWEB.SERVICE_STATUS.ON, username, int(time.time()))
                #NOTE: provide a dummy_cid for user
                cid = UWEB.DUMMY_CID 
                oid = UWEB.DUMMY_OID

                if not terminals: 
                    logging.info("[UWEB] user: %s can not find invalid terminals",
                                  username)
                    status = ErrorCode.TERMINAL_NOT_ORDERED
                    return None, None, None, None, user_type, status 
                else:
                    uid = user.uid
            else:
                if user_type == UWEB.USER_TYPE.OPERATOR:
                    oid = user.oid
                    groups = self.db.query("SELECT group_id"
                                           "  FROM T_GROUP_OPERATOR"
                                           "  WHERE oper_id = %s",
                                           oid)
                    group_ids = [str(group.group_id) for group in groups]
                    #corp = self.db.get("SELECT corp_id FROM T_GROUP WHERE id = %s", groups[0].group_id)
                    #cid = corp.corp_id
                    # NOTE：the codes above is ugly. one can get cid by T_OPERATOR, rather than T_GROUP
                    operator = self.db.get("SELECT corp_id FROM T_OPERATOR WHERE oid = %s", oid)
                    cid = operator.corp_id
                else: # corp
                    cid = user.cid 
                    oid = UWEB.DUMMY_OID
                    groups = self.db.query("SELECT id, corp_id FROM T_GROUP WHERE corp_id = %s",
                                           user.cid)
                    group_ids = [str(group.id) for group in groups]

                sql_cmd = ("SELECT id, tid, mobile as sim, login, keys_num, owner_mobile"
                           "  FROM T_TERMINAL_INFO"
                           "  WHERE service_status = %s"
                           "    AND group_id IN %s") %\
                           (UWEB.SERVICE_STATUS.ON, str(tuple(group_ids+DUMMY_IDS_STR)))
                terminals = self.db.query(sql_cmd)
                if not terminals: 
                    terminal = DotDict(tid=UWEB.DUMMY_TID,
                                       sim=UWEB.DUMMY_MOBILE)
                    return str(cid), str(oid), UWEB.DUMMY_UID, [terminal,], user_type, status 
                else:
                    uid = terminals[0].owner_mobile 
                 
        return str(cid), str(oid), str(uid), terminals, user_type, status

    def login_sms_remind(self, uid, owner_mobile, terminals, login="WEB"):

        sms_option = QueryHelper.get_sms_option_by_uid(uid, 'login', self.db)
        if sms_option == UWEB.SMS_OPTION.SEND:
            login_time = time.strftime("%Y-%m-%d %H:%M:%S")
            login_method = UWEB.LOGIN_WAY[login] 
            terminal_mobile = u'”，“'.join(terminal.alias for terminal in terminals)
            remind_sms = SMSCode.SMS_LOGIN_REMIND % (login_time, login_method, owner_mobile, terminal_mobile) 
            SMSHelper.send(owner_mobile, remind_sms)
