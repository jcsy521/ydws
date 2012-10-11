# -*- coding:utf-8 -*-
from utils.misc import get_terminal_info_key
from utils.dotdict import DotDict

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
    def get_tmobile_by_tid(tid, redis, db):
        terminal_info_key = get_terminal_info_key(tid)
        terminal_info = redis.getvalue(terminal_info_key)
        if terminal_info:
            if terminal_info.mobile:
                return terminal_info.mobile 
        else:
            terminal_info = DotDict(defend_status=None,
                                    mobile=None,
                                    login=None,
                                    gps=None,
                                    gsm=None,
                                    pbat=None,
                                    alias=None,
                                    keys_num=None) 

        terminal = QueryHelper.get_terminal_by_tid(tid, db)
        terminal_info['mobile'] = terminal.mobile 
        redis.setvalue(terminal_info_key, terminal_info)

        return terminal_info['mobile'] 

    @staticmethod
    def get_alias_by_tid(tid, redis, db):
        """Get a readable alias  throught tid.
        workflow:
        if alias exists in redis:
            return alias 
        else:
            if alias in db:
                alias = alias 
            elif cnum in db:
                alias = cnum 
            else: 
                alias = sim
        keep alias in redis     
        return alias 
        """
        terminal_info_key = get_terminal_info_key(tid)
        terminal_info = redis.getvalue(terminal_info_key)
        if terminal_info:
            if terminal_info.alias:
                return terminal_info.alias 
        else:
            terminal_info = DotDict(defend_status=None,
                                    mobile=None,
                                    login=None,
                                    gps=None,
                                    gsm=None,
                                    pbat=None,
                                    alias=None,
                                    keys_num=None,
                                    fob_list=[]) 
        terminal = QueryHelper.get_terminal_by_tid(tid, db)
        if terminal.alias:
            alias = terminal.alias
        else:
            car = db.get("SELECT cnum FROM T_CAR"
                         "  WHERE tid = %s LIMIT 1",
                         tid)
            if car.cnum:
               alias = car.cnum
            else:
               alias = terminal.mobile
        terminal_info['alias'] = alias
        redis.setvalue(terminal_info_key, terminal_info)
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
        """Get fob list throught tid.
        """
        foblist = db.query("SELECT fobid"
                           "  FROM T_FOB"
                           "  WHERE tid = %s",
                           tid) 
        return foblist
