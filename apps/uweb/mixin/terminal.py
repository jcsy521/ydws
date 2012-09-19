# -*- coding: utf-8 -*-


from base import BaseMixin
from constants import UWEB 
from utils.misc import get_terminal_info_key
from helpers.queryhelper import QueryHelper 

class TerminalMixin(BaseMixin):
    """Mix-in for terminal related functions."""
    
    def update_terminal_db(self, car_sets):
        """For cellid_status, alias, cnum, just update database.
        """
        for key, value in car_sets.iteritems():
            if key == 'cellid_status':
                self.db.execute("UPDATE T_TERMINAL_INFO"
                                "  SET cellid_status = %s"
                                "  WHERE tid = %s",
                                value, self.current_user.tid)
            elif key == 'alias':
                self.db.execute("UPDATE T_TERMINAL_INFO"
                                "  SET alias = %s"
                                "  WHERE tid = %s",
                                value, self.current_user.tid)

                terminal_info_key = get_terminal_info_key(self.current_user.tid)
                terminal_info = self.redis.getvalue(terminal_info_key)
                terminal_info[key] = value 
                self.redis.setvalue(terminal_info_key, terminal_info)


            elif key == 'cnum':
                self.db.execute("UPDATE T_CAR"
                                "  SET cnum = %s"
                                "  WHERE tid = %s",
                                value, self.current_user.tid)
                terminal = QueryHelper.get_terminal_by_tid(self.current_user.tid, self.db)
                if not terminal.alias:
                    terminal_info_key = get_terminal_info_key(self.current_user.tid)
                    terminal_info = self.redis.getvalue(terminal_info_key)
                    terminal_info['alias'] = value if value else self.current_user.sim
                    self.redis.setvalue(terminal_info_key, terminal_info)

    def update_terminal_info(self, car_sets, car_sets_res):
        """Update T_TERMINAL_INFO.
        When set terminal info,get 0 or 1 from terminal, recomposer car_sets
        and keep it in database.
        @params: car_sets, DotDict, the terminal sets  
                 car_sets_res, DotDict, the response of terminal's set
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
        for key, value in car_sets_res.iteritems():
            if value == "0":
                if key.lower() == 'white_list' :
                    white_list = car_sets[key.lower()].split(':')
                    if len(car_sets['white_list']) < 1:
                        pass
                    else:
                        self.db.execute("DELETE FROM T_WHITELIST WHERE tid = %s", 
                                        self.current_user.tid)
                        for white in white_list[1:]:
                            self.db.execute("INSERT INTO T_WHITELIST"
                                            "  VALUES(NULL, %s, %s)"
                                            "  ON DUPLICATE KEY"
                                            "  UPDATE tid = VALUES(tid),"
                                            "    mobile = VALUES(mobile)",
                                            self.current_user.tid, white)

                    continue 
                car_sets_res[key] = car_sets[key.lower()]
                s_keys.append(key)
            else: 
                f_keys.append(key)
       
        set_clause = ""
        if not s_keys:
            pass
        for key in s_keys:
            set_clause = set_clause + key.lower() + " = '" + str(car_sets[key.lower()])+  "',"
        if set_clause:
            sql_cmd = "UPDATE T_TERMINAL_INFO SET " + set_clause[0:-1] + " WHERE tid = %s" 
            self.db.execute(sql_cmd, self.current_user.tid)
