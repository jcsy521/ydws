# -*- coding: utf-8 -*-


from base import BaseMixin
from constants import UWEB 
from utils.misc import get_terminal_info_key, get_terminal_sessionID_key
from helpers.queryhelper import QueryHelper 
from utils.dotdict import DotDict

class TerminalMixin(BaseMixin):
    """Mix-in for terminal related functions."""
    
    def update_terminal_db(self, car_sets):
        """Update database.
        """
        terminal_keys = ['cellid_status','white_pop','trace','freq', 'vibchk', 'vibl','push_status']
        terminal_fields = []
        
        for key, value in car_sets.iteritems():
            if key in terminal_keys: 
                if car_sets.get(key, None) is not None:
                    terminal_fields.append(key + ' = ' + str(value))
            elif key == 'white_list':
                white_list = car_sets[key]
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

            elif key == 'alias':
                self.db.execute("UPDATE T_TERMINAL_INFO"
                                "  SET alias = %s"
                                "  WHERE tid = %s",
                                value, self.current_user.tid)

                terminal_info_key = get_terminal_info_key(self.current_user.tid)
                terminal_info = self.redis.getvalue(terminal_info_key)
                if terminal_info:
                    terminal_info[key] = value 
                    self.redis.setvalue(terminal_info_key, terminal_info)

            elif key == 'corp_cnum':
                self.db.execute("UPDATE T_CAR"
                                "  SET cnum = %s"
                                "  WHERE tid = %s",
                                value, self.current_user.tid)
                terminal = QueryHelper.get_terminal_by_tid(self.current_user.tid, self.db)
                if not terminal.alias:
                    terminal_info_key = get_terminal_info_key(self.current_user.tid)
                    terminal_info = self.redis.getvalue(terminal_info_key)
                    if terminal_info:
                        terminal_info['alias'] = value if value else self.current_user.sim
                        self.redis.setvalue(terminal_info_key, terminal_info)

        terminal_clause = ','.join(terminal_fields)        
        if terminal_clause:
            self.db.execute("UPDATE T_TERMINAL_INFO"
                            "  SET " + terminal_clause + 
                            "  WHERE tid = %s ",
                            self.current_user.tid)

        if car_sets.has_key('freq'):
            # clear sessionID
            terminal_sessionID_key = get_terminal_sessionID_key(self.current_user.tid)
            self.redis.delete(terminal_sessionID_key)

    #def update_terminal_info(self, car_sets, car_sets_res):
    #    """Update T_TERMINAL_INFO.
    #    When set terminal info,get 0 or 1 from terminal, recomposer car_sets
    #    and keep it in database.
    #    @params: car_sets, DotDict, the terminal sets  
    #             car_sets_res, DotDict, the response of terminal's set
    #    workflow:
    #    for key, value in cars_sets:
    #        if success:
    #            s_keys.append(key)
    #        else:
    #            f_keys.append(key)
    #    update car_sets to database
    #    """
    #    s_keys = [] 
    #    f_keys = []
    #    for key, value in car_sets_res.iteritems():
    #        if value == "0":
    #            s_keys.append(key)
    #        else: 
    #            f_keys.append(key)
    #    
    #    if not s_keys:
    #        pass
    #    else:   
    #        car_sets_res = DotDict()
    #        for key in s_keys:
    #            car_sets_res[key.lower()] = car_sets[key.lower()]
    #        if car_sets_res:
    #            self.update_terminal_db(car_sets_res)
