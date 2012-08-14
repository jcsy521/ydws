# -*- coding:utf-8 -*-

class QueryHelper(object):
    """A bunch of samll functions to get one attribute from another
    attribute in the db.
    """
    
    @staticmethod
    def get_terminal_by_tid(tid, db):
        """Get terminal's info throught tid.
        """
        terminal = db.get("SELECT mobile, alias"
                          "  FROM T_TERMINAL_INFO"
                          "  WHERE tid = %s LIMIT 1",
                          tid) 
        return terminal 

    @staticmethod
    def get_user_by_tid(tid, db):
        """Get user info throught tid.
        """
        user = db.get("SELECT owner_mobile"
                      "  FROM T_TERMINAL_INFO"
                      "  WHERE tid = %s LIMIT 1",
                      tid) 
        return user

    @staticmethod
    def get_user_by_uid(uid, db):
        user = db.get("SELECT mobile"
                      "  FROM T_USER"
                      "  WHERE uid= %s LIMIT 1",
                      uid) 
        return user

    @staticmethod
    def get_user_by_tmobile(tmobile, db):
        """Get user info throught tmobile.
        """
        user = db.get("SELECT owner_mobile"
                      "  FROM T_TERMINAL_INFO"
                      "  WHERE mobile = %s LIMIT 1",
                      tmobile) 
        return user

    @staticmethod
    def get_user_by_mobile(mobile, db):
        """Get user info throught tmobile.
        """
        user = db.get("SELECT id"
                      "  FROM T_USER"
                      "  WHERE mobile = %s LIMIT 1",
                      mobile) 
        return user



    @staticmethod
    def get_terminal_by_tmobile(tmobile, db):
        """Get terminal info throught tmobile.
        """
        terminal = db.get("SELECT tid, login, msgid"
                          "  FROM T_TERMINAL_INFO"
                          "  WHERE mobile = %s LIMIT 1",
                          tmobile) 
        return terminal

    #@staticmethod
    #def get_user_by_tid(tid, db):
    #    user = db.get("SELECT uid FROM T_USER as tu," 
    #                  "    T_TERMINAL_INFO as tw"
    #                  "  WHERE tw.tid = %s"
    #                  "  AND tu.mobile = tw.owner_mobile",
    #                  tid) 
    #    return user
