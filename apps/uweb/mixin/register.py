# -*- coding: utf-8 -*-

from constants import UWEB 
from base import BaseMixin
from codes.errorcode import ErrorCode


class RegisterMixin(BaseMixin):
    """Mix-in for register related functions."""
    
    def insert_user(self, uid, password, name, mobile, address, email):
        """Add an user in database.
        """
        self.db.execute("INSERT INTO T_USER"
                        "  VALUES(NULL,%s,password(%s),%s, %s,%s,%s,NULL,NULL,%s,%s)"
                        "  ON DUPLICATE KEY"
                        "  UPDATE uid = VALUES(uid),"
                        "      password = VALUES(password),"
                        "      name = VALUES(name),"
                        "      mobile = VALUES(mobile),"
                        "      address = VALUES(address),"
                        "      email = VALUES(email),"
                        "      valid = VALUES(valid),"
                        "      category = VALUES(category)",
                        uid, password, name, mobile, address, email,
                        UWEB.USER_VALID.VALID, UWEB.USER_CATEGORY.PERSONAL )


    def insert_terminal(self, tid, mobile, uid):
        """Add an terminal in database.
        """
        if not tid:
            return
        #NOTE: T_TERMINAL_INFO_W must be first, for it's referenced by the other
        self.db.execute("INSERT INTO T_TERMINAL_INFO_W(tid,owner_mobile)"
                        "  VALUES(%s, %s)"
                        "  ON DUPLICATE KEY"
                        "  UPDATE tid = VALUES(tid),"
                        "      owner_mobile= VALUES(owner_mobile)",
                        tid, mobile)

        self.db.execute("INSERT INTO T_TERMINAL_INFO_R(tid)"
                        "  VALUES(%s)"
                        "  ON DUPLICATE KEY"
                        "  UPDATE tid = VALUES(tid)",
                        tid)

    def check_user_by_uid(self, uid):
        """Check the uid whether can be registered.
        if uid existes, return false.
        """
        status = ErrorCode.SUCCESS
        res = self.db.get("SELECT id FROM T_USER"
                          "  WHERE uid = %s"
                          "  LIMIT 1",
                          uid)
        if res:
            status = ErrorCode.USER_UID_EXIST
        return status


    def check_user_by_mobile(self, mobile):
        """Check the mobile whether can be registered.
        if mobile existes, return false.
        """
        status = ErrorCode.SUCCESS
        res = self.db.get("SELECT id FROM T_USER"
                          "  WHERE mobile = %s"
                          "  LIMIT 1",
                          mobile)
        if res:
            status = ErrorCode.USER_MOBILE_EXIST
        return status

