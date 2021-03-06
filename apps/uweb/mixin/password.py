# -*- coding: utf-8 -*-
 

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

    def check_oper_by_password(self, password, oid):
        """Check the password whether be avaliable.
        """
        res = self.db.get("SELECT id FROM T_OPERATOR"
                          "  WHERE password = password(%s)"
                          "    AND oid = %s"
                          "    LIMIT 1",
                          password, oid)

        return True if res else False 
