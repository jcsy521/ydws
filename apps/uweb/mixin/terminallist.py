# -*- coding: utf-8 -*-

from utils.misc import DUMMY_IDS, str_to_list, get_today_last_month
from constants import UWEB 
from helpers.queryhelper import QueryHelper 
from base import BaseMixin

class TerminalListMixin(BaseMixin):
    """Mix-in for terminallist related functions."""
    
    def get_terminallist(self, uid):
        """Get data for termianl param only can be read.
        """
        umobile = QueryHelper.get_umobile_by_uid(uid, self.db) 

        res = self.db.query("SELECT tiw.id, tiw.tid, tiw.mobile, tiw.psw "
                            "  FROM T_TERMINAL_INFO_W as tiw," 
                            "    T_TERMINAL_INFO_R as tir"
                            "  WHERE tiw.tid = tir.tid "
                            "  AND tiw.owner_mobile = %s"
                            "  LIMIT %s",
                            umobile.mobile, UWEB.LIMIT.TERMINAL)
        return res

    def insert_terminal(self, tlist):
        """Add single or multi terminal.
        """
        umobile = QueryHelper.get_umobile_by_uid(self.current_user.uid, self.db) 

        #NOTE: T_TERMINAL_INFO_W must be first, for it's referenced by T_TERMINAL_INFO_R.
        last_rowid = self.db.executemany(    
            "INSERT INTO T_TERMINAL_INFO_W(tid, mobile, owner_mobile)"
            "  VALUES (%s, %s, %s)"
            "  ON DUPLICATE KEY "
            "  UPDATE tid = VALUES(tid),"
            "         mobile = VALUES(mobile),"
            "         owner_mobile = VALUES(owner_mobile)",
            [(terminal.tid, terminal.mobile, umobile.mobile) for terminal in tlist])

        self.db.executemany(    
            "INSERT INTO T_TERMINAL_INFO_R(tid)"
            "  VALUES (%s)" 
            "  ON DUPLICATE KEY "
            "  UPDATE tid = VALUES(tid)",
            [(terminal.tid) for terminal in tlist])
        
        return last_rowid

    def delete_terminal(self, delete_ids):
        """Delete single terminal.
        #NOTE: here, just set owner_mobile null. 
        """
        self.db.execute("UPDATE T_TERMINAL_INFO_W"
                        "  set owner_mobile = '' "
                        "  WHERE id IN %s",
                        tuple(delete_ids + DUMMY_IDS))

