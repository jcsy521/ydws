# -*- coding: utf-8 -*-


from base import BaseMixin
from constants import UWEB 


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
            #if key == 'whitelist_2':
            #    self.db.execute("INSERT INTO T_WHITELIST"
            #                    "  VALUES(NULL, %s, %s)"
            #                    "  ON DUPLICATE KEY"
            #                    "  UPDATE tid = VALUES(tid),"
            #                    "    MOBILE = VALUES(mobile)",
            #                    tid, value)

            if key == 'cellid_status':
                self.db.execute("UPDATE T_TERMINAL_INFO"
                                "  SET cellid_status = %s"
                                "  WHERE tid = %s",
                                value, tid)
            if key == 'alias':
                self.db.execute("UPDATE T_TERMINAL_INFO"
                                "  SET alias = %s"
                                "  WHERE tid = %s",
                                value, tid)

            # NOTE: T_CAR use tmobile 
            if key == 'cnum':
                self.db.execute("UPDATE T_CAR"
                                "  SET cnum = %s"
                                "  WHERE tmobile = %s",
                                value, tmobile )

    def update_terminal_info(self, car_sets, old_car_sets, tid):
        """Update T_TERMINAL_INFO.
        """
        for key, value in car_sets.iteritems():
            if value == '0':
                if key == 'white_list' :
                    self.db.execute("update T_WHITELIST set mobile = %",
                                    "  where tid = %s",
                                    value, tid)
                    continue 
                car_sets[key] = old_car_sets[key]
        set_clause = ""
        for key, value in car_sets.iteritems():
            set_clause = set_clause + key + " = '" + value + "',"
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
