# -*- coding: utf-8 -*-


from base import BaseMixin
from constants import UWEB 
from utils.misc import get_name_cache_key


class TerminalMixin(BaseMixin):
    """Mix-in for terminal related functions."""
    
    def get_terminal_r(self):
        """Get data for termianl param only can be read.
        """
        res = self.db.get("SELECT id, tid, softversion, gsm, "
                          "  gps, vbat, vin, login, plcid, imsi, imei"
                          "  FROM T_TERMINAL_INFO_R"
                          "    WHERE tid = %s"
                          "    LIMIT 1",
                          self.current_user.tid)
        return res

    def get_terminal_w(self):
        """Get data for termianl param can be modified.
        """
        res = self.db.get("SELECT id, tid, psw, domain, freq, trace,"
                          "  pulse, mobile as phone, owner_mobile, radius, vib, "
                          "  vibl, pof, lbv, sleep, vibgps, speed,"
                          "  calllock, calldisp, vibcall, sms, "
                          "  vibchk, poft, wakeupt, sleept,"
                          "  acclt, acclock, stop_service, cid"
                          "    FROM T_TERMINAL_INFO_W"
                          "    WHERE tid = %s"
                          "    LIMIT 1",
                          self.current_user.tid)
        return res

    def update_terminal_db(self, car_sets, tid, tmobile):
        """Update T_TERMINAL_INFO. Here just modify database.
        """
        for key, value in car_sets.iteritems():
            if key == 'white_list':
                whitelists = value.split(":")
                if len(whitelists) <=1:
                    pass
                else:
                    for whitelist in whitelists[1:]:
                        self.db.execute("INSERT INTO T_WHITELIST"
                                        "  VALUES(NULL, %s, %s)"
                                        "  ON DUPLICATE KEY"
                                        "  UPDATE tid = VALUES(tid),"
                                        "    mobile = VALUES(mobile)",
                                        tid, whitelist)

            elif key == 'cellid_status':
                self.db.execute("UPDATE T_TERMINAL_INFO"
                                "  SET cellid_status = %s"
                                "  WHERE tid = %s",
                                value, tid)
            elif key == 'alias':
                self.db.execute("UPDATE T_TERMINAL_INFO"
                                "  SET alias = %s"
                                "  WHERE tid = %s",
                                value, tid)
                # after update db, update redis
                alias_key = get_name_cache_key(tid)
                self.redis.setvalue(alias_key, value)

            # NOTE: T_CAR use tmobile 
            elif key == 'cnum':
                self.db.execute("UPDATE T_CAR"
                                "  SET cnum = %s"
                                "  WHERE tmobile = %s",
                                value, tmobile )
            else:
                sql = "UPDATE T_TERMINAL_INFO SET "+ key+" = '"+ value +"'"
                self.db.execute(sql+ " WHERE tid = %s",
                                tid)

    def update_terminal_info(self, car_sets, old_car_sets, tid):
        """Update T_TERMINAL_INFO.
        When set terminal info,get 0 or 1 from terminal, recomposer car_sets
        and keep it in database.
        workflow:
        for key, value in cars_sets:
            if success:
                s_keys.append(key)
                car_sets[key] = new value
            else:
                f_keys.append(key)
        update car_sets to database
        """
        s_keys = [] 
        f_keys = []
        for key, value in car_sets.iteritems():
            if value == '0':
                if key.lower() == 'white_list' :
                    white_list = old_car_sets['white_list']
                    if len(old_car_sets['white_list']) < 1:
                        pass
                    else:
                        for white in white_list[1:]:
                            self.db.execute("INSERT INTO T_WHITELIST"
                                            "  VALUES(NULL, %s, %s)"
                                            "  ON DUPLICATE KEY"
                                            "  UPDATE tid = VALUES(tid),"
                                            "    mobile = VALUES(mobile)",
                                            tid, white)

                    continue 
                car_sets[key] = old_car_sets[key.lower()]
                s_keys.append(key)
            else: 
                f_keys.append(key)
       
        set_clause = ""
        if not s_keys:
            pass
        for key in s_keys:
            set_clause = set_clause + key.lower() + " = '" + car_sets[key] + "',"
            sql_cmd = "UPDATE T_TERMINAL_INFO SET " + set_clause[0:-1] + " WHERE tid = %s" 
            self.db.execute(sql_cmd, tid)

    def update_terminal_w(self, key, value, tid):
        """Update T_TERMINAL_INFO_W.
        """
        if key == 'owner_mobile':
            self.db.execute("UPDATE T_USER SET mobile = %s"
                            "  WHERE uid = %s",
                            value, self.current_user.uid)
        if key == "phone":
            key = "mobile"
        sql_cmd = "UPDATE T_TERMINAL_INFO_W SET " + key + " = %s WHERE id = %s" 
        self.db.execute(sql_cmd, value, tid)
        
    def check_terminal_by_mobile(self, mobile):
        """Check the mobie where can be registered.
        """
        res = self.db.get("SELECT id FROM T_TERMINAL_INFO_W"
                          "  WHERE mobile = %s"
                          "  AND owner_mobile != '' "
                          "  LIMIT 1",
                          mobile)
        return False if res else True

    def check_terminal_by_tid(self, tid):
        """Check the mobie where can be registered.
        """
        res = self.db.get("SELECT id FROM T_TERMINAL_INFO_W"
                          "  WHERE tid = %s"
                          "  AND owner_mobile != '' "
                          "  LIMIT 1",
                          tid)

        return False if res else True
