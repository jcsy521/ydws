# -*- coding: utf-8 -*-

from constants import UWEB 
from base import BaseMixin


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

    def update_password(self, password, uid):
        self.db.execute("UPDATE T_USER "
                        "  SET password = password(%s)"
                        "  WHERE uid = %s",
                        password, uid)

    def update_corp_password(self, password, cid):
        self.db.execute("UPDATE T_CORP "
                        "  SET password = password(%s)"
                        "  WHERE cid = %s",
                        password, cid)


 
