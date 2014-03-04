# -*- coding: utf-8 -*-

import logging

import tornado.web
from tornado.escape import json_decode

from utils.dotdict import DotDict
from codes.errorcode import ErrorCode 
from constants import UWEB

from base import BaseHandler, authenticated

class UsernameHandler(BaseHandler):

    @authenticated
    @tornado.web.removeslash
    def post(self):
        try:
            data = json_decode(self.request.body)
            old_username = data.get('old_username', None)
            new_username = data.get('new_username', None)
            user_type = data.get('user_type', UWEB.USER_TYPE.PERSON)
            logging.info("[ADMIN] username modify request, data:%s", 
                          data)
        except Exception as e:
            status = ErrorCode.FAILED 
            logging.exception("[ADMIN] Invalid data format, data:%s, Exception:%s", 
                              data, e.args)
            self.write_ret(status) 
            return

        try:
            status = ErrorCode.SUCCESS 

            if user_type == UWEB.USER_TYPE.PERSON:
                # T_USER, T_TERMINAL_INFO, T_SMS_OPTION
                self.db.execute("UPDATE T_TERMINAL_INFO SET owner_mobile = %s"
                                "  WHERE owner_mobile = %s",
                                new_username, old_username)

                user = self.db.get("SELECT id FROM T_USER"
                                   "  WHERE uid = %s",
                                   new_username)
                if user: # use a existed user
                    self.db.execute("DELETE FROM T_USER WHERE uid = %s",
                                    old_username)
                else:
                    self.db.execute("UPDATE T_USER SET uid = %s, mobile=%s"
                                    "  WHERE uid = %s",
                                    new_username, new_username, old_username)
            else: 
                corp = self.db.get("SELECT id FROM T_CORP"
                                   "  WHERE cid = %s",
                                   new_username)
                REMOVE_CORP = False
                if corp: # use a existed corp
                    REMOVE_CORP = True 
                else:
                    self.db.execute("UPDATE T_CORP SET cid = %s, mobile=%s, linkman =%s"
                                    "  WHERE cid = %s",
                                    new_username, new_username, new_username, old_username)

                    self.db.execute("UPDATE T_USER SET uid = %s, mobile = %s"
                                    "  WHERE uid = %s",
                                    new_username, new_username, old_username)
                self.db.execute("UPDATE T_GROUP SET corp_id = %s"
                                "  WHERE corp_id = %s",
                                new_username, old_username)

                self.db.execute("UPDATE T_OPERATOR SET corp_id = %s"
                                "  WHERE corp_id = %s",
                                new_username, old_username)

                self.db.execute("UPDATE T_TERMINAL_INFO SET owner_mobile = %s"
                                "  WHERE owner_mobile = %s",
                                new_username, old_username)

                if REMOVE_CORP:  
                    self.db.execute("DELETE FROM T_CORP"
                                    "  WHERE cid = %s",
                                    old_username)


            logging.info("[ADMIN] user_type: %s, old_username: %s has been changed to new_username: %s",
                         user_type, old_username, new_username)
            self.write_ret(status) 
        except Exception as e:
            status = ErrorCode.SERVER_BUSY
            logging.exception("[ADMIN] user_type modify failed. Exception:%s", 
                              e.args)
            self.write_ret(status) 
