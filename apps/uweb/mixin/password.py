# -*- coding: utf-8 -*-

import logging

from constants import UWEB 
from base import BaseMixin
from utils.misc import get_ios_push_list_key, get_ios_badge_key 


class PasswordMixin(BaseMixin):
    """Mix-in for passwrod related functions."""
    
    def check_user_by_password(self, password, uid):
        """Check the password whether be avaliable.
        """
        res = self.db.get("SELECT id FROM T_USER"
                          "  WHERE password = password(%s)"
                          "    AND uid = %s"
                          "    LIMIT 1",
                          password, uid)

        return True if res else False 

    def check_corp_by_password(self, password, cid):
        """Check the password whether be avaliable.
        """
        res = self.db.get("SELECT id FROM T_CORP"
                          "  WHERE password = password(%s)"
                          "    AND cid = %s"
                          "    LIMIT 1",
                          password, cid)

        return True if res else False 

    def check_oper_by_password(self, password, oid):
        """Check the password whether be avaliable.
        """
        res = self.db.get("SELECT id FROM T_OPERATOR"
                          "  WHERE password = password(%s)"
                          "    AND oid = %s"
                          "    LIMIT 1",
                          password, oid)

        return True if res else False 

    def update_password(self, password, uid):
        self.db.execute("UPDATE T_USER "
                        "  SET password = password(%s)"
                        "  WHERE uid = %s",
                        password, uid)

        #NOTE: clear ios push list 
        ios_push_list_key = get_ios_push_list_key(uid) 
        ios_push_list = self.redis.getvalue(ios_push_list_key) 
        ios_push_list = ios_push_list if ios_push_list else []
        for iosid in ios_push_list: 
            ios_badge_key = get_ios_badge_key(iosid) 
            self.redis.delete(ios_badge_key) 
            ios_push_list.remove(iosid) 
        self.redis.set(ios_push_list_key, []) 
        logging.info("[UWEB] uid:%s clear ios_push_list.", uid)

    def update_corp_password(self, password, cid):
        self.db.execute("UPDATE T_CORP "
                        "  SET password = password(%s)"
                        "  WHERE cid = %s",
                        password, cid)

    def update_oper_password(self, password, oid):
        self.db.execute("UPDATE T_OPERATOR"
                        "  SET password = password(%s)"
                        "  WHERE oid = %s",
                        password, oid)
