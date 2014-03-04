# -*- coding:utf-8 -*-

from utils.misc import get_terminal_info_key, get_lq_sms_key,\
     get_location_key, get_login_time_key, get_activation_code
from utils.dotdict import DotDict
from constants import GATEWAY, EVENTER

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
    def get_biz_by_mobile(mobile, db):
        """Get user info through tmobile.
        """
        biz = db.get("SELECT biz_type"
                      "  FROM T_BIZ_WHITELIST"
                      "  WHERE mobile = %s LIMIT 1",
                      mobile) 
        return biz 

    @staticmethod
    def get_terminal_by_tmobile(tmobile, db):
        """Get terminal info through tmobile.
        """
        terminal = db.get("SELECT tid, login, msgid, service_status"
                          "  FROM T_TERMINAL_INFO"
                          "  WHERE mobile = %s LIMIT 1",
                          tmobile) 
        return terminal


    @staticmethod
    def get_white_list_by_tid(tid, db):
        """Get white list through tid.
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
        """Get tracker's mannual status.
        """
        mannual_status = None
        t = db.get("SELECT mannual_status"
                   "  FROM T_TERMINAL_INFO"
                   "  WHERE tid = %s",
                   tid)
        if t:
            mannual_status = t['mannual_status']

        return mannual_status

    @staticmethod
    def get_terminal_info(tid, db, redis):
        """Get tracker's terminal info.
        """
        terminal_info_key = get_terminal_info_key(tid)
        terminal_info = redis.getvalue(terminal_info_key)
        if not terminal_info:
            terminal_info = db.get("SELECT mannual_status, defend_status,"
                                   "  fob_status, mobile, owner_mobile, login, gps, gsm,"
                                   "  pbat, keys_num, icon_type, bt_name, bt_mac"
                                   "  FROM T_TERMINAL_INFO"
                                   "  WHERE tid = %s", tid)
            car = db.get("SELECT cnum FROM T_CAR"
                         "  WHERE tid = %s", tid)
            fobs = db.query("SELECT fobid FROM T_FOB"
                            "  WHERE tid = %s", tid)
            if car:
                terminal_info['alias'] = car.cnum if car.cnum else terminal_info.mobile
            else:
                terminal_info['alias'] =  terminal_info.mobile
            terminal_info['fob_list'] = [fob.fobid for fob in fobs]
            redis.setvalue(terminal_info_key, terminal_info)

        return terminal_info

    @staticmethod
    def get_login_time_by_tid(tid, db, redis):
        """Get tracker's login_time.
        """
        login_time_key = get_login_time_key(tid)
        login_time = redis.get(login_time_key)
        if not login_time:
            t = db.get("SELECT login_time FROM T_TERMINAL_INFO"
                       "  WHERE tid = %s LIMIT 1",
                       tid)
            login_time = t.login_time
            redis.set(login_time_key, login_time)

        return int(login_time)

    @staticmethod
    def get_terminals_by_cid(cid, db):
        """Get all trackers belongs to a corp.
        """
        terminals = db.query("SELECT tt.mobile, tt.owner_mobile, tt.tid FROM T_TERMINAL_INFO as tt, T_GROUP as tg, T_CORP as tc" 
                             "  WHERE tt.service_status = 1 AND tc.cid = %s AND tc.cid = tg.corp_id AND tt.group_id = tg.id", 
                             cid)
        return terminals

    @staticmethod
    def get_location_info(tid, db, redis):
        """Get tracker's last location and keep a copy in redis.
        """
        location_key = get_location_key(str(tid))
        location = redis.getvalue(location_key)
        if not location:
            location = db.get("SELECT id, speed, timestamp, category, name,"
                              "  degree, type, latitude, longitude, clatitude, clongitude,"
                              "  timestamp, locate_error"
                              "  FROM T_LOCATION"
                              "  WHERE tid = %s"
                              "    AND NOT (latitude = 0 AND longitude = 0)"
                              "    ORDER BY timestamp DESC"
                              "    LIMIT 1",
                              tid)
            if location:
                mem_location = DotDict({'id':location.id,
                                        'latitude':location.latitude,
                                        'longitude':location.longitude,
                                        'type':location.type,
                                        'clatitude':location.clatitude,
                                        'clongitude':location.clongitude,
                                        'timestamp':location.timestamp,
                                        'name':location.name,
                                        'degree':float(location.degree),
                                        'speed':float(location.speed),
                                        'locate_error':int(location.locate_error)})

                redis.setvalue(location_key, mem_location, EVENTER.LOCATION_EXPIRY)
        return location

    @staticmethod
    def get_alert_freq_by_tid(tid,db):
        """Get tracker's alert_freq.
        """
        alert_freq = db.get("SELECT alert_freq FROM T_TERMINAL_INFO WHERE tid=%s", tid)
        return int(alert_freq['alert_freq'])

    @staticmethod
    def get_activation_code(db):
        """Generate a actiation_code which is never been used in db.
        workflow:
        for i in 0~9: # try it at most 10 times
            try to get a actiation_code
            if actiation_code is valid:
                return it
            else:
                continue to try
        """
        activation_code = '' 
        times = 10 
        for i in range(times): 
            activation_code = get_activation_code() 
            t = db.get("SELECT id FROM T_TERMINAL_INFO WHERE activation_code = %s LIMIT 1", 
                       activation_code) 
            if not t: 
                break 
            else: 
                activation_code = '' 
        if not activation_code: 
            logging.error("[QUERYHELPER] After times: %s, there is not a invalid actiation_code is got, have a check!", 
                          times) 
        return activation_code

    @staticmethod
    def get_corp_by_groupid(groupid, db):
        corp = DotDict()
        res = db.get("SELECT tc.cid, tc.name FROM T_GROUP AS tg, T_CORP AS tc"
                     "  WHERE tg.corp_id = tc.cid"
                     "  AND tg.id = %s",
                     groupid)
        if res:
            corp.name = res['name']
            corp.cid = res['cid']
            
        return corp

    @staticmethod
    def get_default_group_by_cid(cid, db):
        group = DotDict()
        res = db.get("SELECT id, name from T_GROUP"
                     "  WHERE corp_id = %s"
                     "  AND type=0",
                     cid)
        if res:
            group.name = res['name']
            group.gid = res['id']
        else:
            gid = db.execute("INSERT INTO T_GROUP(corp_id)"
                             "  values(%s)",
                             cid) 
            group.name = u'默认组' 
            group.gid = gid 
        return group 
