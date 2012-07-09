# -*- coding:utf-8 -*-

class QueryHelper(object):
    """A bunch of samll functions to get one attribute from another
    attribute in the db.
    """
    
    @staticmethod
    def get_mobile_by_dev_id(dev_id, db):
        user = db.get("SELECT mobile"
                      "  FROM T_TERMINAL_INFO_W"
                      "  WHERE tid = %s LIMIT 1",
                      dev_id) 
        return user

    @staticmethod
    def get_umobile_by_dev_id(dev_id, db):
        user = db.get("SELECT owner_mobile"
                      "  FROM T_TERMINAL_INFO_W"
                      "  WHERE tid = %s LIMIT 1",
                      dev_id) 
        return user

    @staticmethod
    def get_umobile_by_uid(uid, db):
        user = db.get("SELECT mobile"
                      "  FROM T_USER"
                      "  WHERE uid= %s LIMIT 1",
                      uid) 
        return user

    @staticmethod
    def get_user_by_tid(tid, db):
        user = db.get("SELECT uid FROM T_USER as tu," 
                      "    T_TERMINAL_INFO_W as tw"
                      "  WHERE tw.tid = %s"
                      "  AND tu.mobile = tw.owner_mobile",
                      tid) 
        return user
