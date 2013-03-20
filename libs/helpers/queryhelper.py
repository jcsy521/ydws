# -*- coding:utf-8 -*-
from utils.misc import get_terminal_info_key, get_lq_sms_key
from utils.dotdict import DotDict
from constants import GATEWAY

class QueryHelper(object):
    """A bunch of samll functions to get one attribute from another
    attribute in the db.
    """
    
    @staticmethod
    def get_terminal_by_tid(tid, db):
        """Get terminal's info throught tid.
        """
        terminal = db.get("SELECT mobile, tid, owner_mobile, alias, login"
                          "  FROM T_TERMINAL_INFO"
                          "  WHERE tid = %s LIMIT 1",
                          tid) 
        return terminal 

    @staticmethod
    def get_tmobile_by_tid(tid, redis, db):
        terminal_info_key = get_terminal_info_key(tid)
        terminal_info = redis.getvalue(terminal_info_key)
        if terminal_info:
            if terminal_info.mobile:
                return terminal_info.mobile 

        terminal = QueryHelper.get_terminal_by_tid(tid, db)
        mobile = terminal.mobile if terminal else None 

        return mobile 

    @staticmethod
    def get_alias_by_tid(tid, redis, db):
        """Get a readable alias  throught tid.
        workflow:
        if alias exists in redis:
            return alias 
        else:
            if cnum in db:
                alias = cnum 
            else: 
                alias = sim
        return alias 
        """
        terminal_info_key = get_terminal_info_key(tid)
        terminal_info = redis.getvalue(terminal_info_key)
        if terminal_info:
            if terminal_info.alias:
                return terminal_info.alias 

        car = db.get("SELECT cnum FROM T_CAR"
                     "  WHERE tid = %s LIMIT 1",
                     tid)
        if car and car.cnum:
           alias = car.cnum
        else:
           terminal = QueryHelper.get_terminal_by_tid(tid, db)
           alias = terminal.mobile

        return alias

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
        user = db.get("SELECT mobile, name"
                      "  FROM T_USER"
                      "  WHERE uid= %s LIMIT 1",
                      uid) 
        return user

    @staticmethod
    def get_corp_by_cid(cid, db):
        corp = db.get("SELECT mobile, name, linkman, bizcode"
                      "  FROM T_CORP"
                      "  WHERE cid= %s LIMIT 1",
                      cid) 
        return corp 

    @staticmethod
    def get_corp_by_oid(oid, db):
        corp = db.get("SELECT tc.mobile, tc.name, tc.linkman, tc.bizcode"
                      "  FROM T_CORP AS tc, T_OPERATOR AS toper"
                      "  WHERE toper.oid= %s"
                      "    AND toper.corp_id = tc.cid",
                      oid) 
        return corp 

    @staticmethod
    def get_operator_by_oid(oid, db):
        operator = db.get("SELECT mobile, name"
                          "  FROM T_OPERATOR"
                          "  WHERE oid = %s LIMIT 1",
                          oid)

        return operator

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
    def get_sms_option_by_uid(uid, category, db):
        sms_option = db.get("SELECT " + category +
                            "  FROM T_SMS_OPTION"
                            "  WHERE uid = %s",
                            uid)

        return sms_option

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


    @staticmethod
    def get_white_list_by_tid(tid, db):
        """Get white list throught tid.
        """
        whitelist = db.query("SELECT mobile"
                             "  FROM T_WHITELIST"
                             "  WHERE tid = %s LIMIT 1",
                             tid) 
        return whitelist

    @staticmethod
    def get_fob_list_by_tid(tid, db):
        """Get fob list through tid.
        """
        foblist = db.query("SELECT fobid"
                           "  FROM T_FOB"
                           "  WHERE tid = %s",
                           tid) 
        return foblist
  
    @staticmethod
    def get_mannual_status_by_tid(tid, db):
        """Get mannual status through bid.
        """
        mannual_status = None
        t = db.get("SELECT mannual_status"
                   "  FROM T_TERMINAL_INFO"
                   "  WHERE tid = %s",
                   tid)
        if t:
            mannual_status = t['mannual_status']

        return mannual_status
