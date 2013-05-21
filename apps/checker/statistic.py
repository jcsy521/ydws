# -*- coding: utf-8 -*-

import os.path
import site

TOP_DIR_ = os.path.abspath(os.path.join(__file__, "../../.."))
site.addsitedir(os.path.join(TOP_DIR_, "libs"))

import logging
import time

from db_.mysql import DBConnection


class TerminalStatistic(object):
    def __init__(self):
        self.db = DBConnection().db
        
    def statistic_online_terminal(self, epoch_time):
        try:
            corps = self.db.query("SELECT cid FROM T_CORP")
            for corp in corps:
                if corp:
                    online_count = self.db.get("SELECT COUNT(tti.tid) AS num"
                                               "  FROM T_CORP tc, T_GROUP tg, T_TERMINAL_INFO tti" 
                                               "  WHERE tc.cid = tg.corp_id"
                                               "  AND tg.id = tti.group_id"
                                               "  AND tti.service_status = 1"
                                               "  AND tti.login != 0"
                                               "  AND  tc.cid = %s",
                                               corp.cid)
                    offline_count = self.db.get("SELECT COUNT(tti.tid) AS num"
                                                "  FROM T_CORP tc, T_GROUP tg, T_TERMINAL_INFO tti" 
                                                "  WHERE tc.cid = tg.corp_id"
                                                "  AND tg.id = tti.group_id"
                                                "  AND tti.service_status = 1"
                                                "  AND tti.login = 0"
                                                "  AND  tc.cid = %s",
                                                corp.cid)
                    if online_count:
                        online_num = online_count.num
                    else:
                        online_num = 0
                    if offline_count:
                        offline_num = offline_count.num
                    else:
                        offline_num = 0
                    
                    self.db.execute("INSERT INTO T_ONLINE_STATISTIC(online_num, offline_num, time, cid) "
                                    "  VALUES(%s, %s, %s, %s)",
                                    online_num, offline_num, int(epoch_time), corp.cid)
            convert_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(epoch_time)) 
            logging.info("[CK] %s statistic online terminal finish", convert_time)
        except KeyboardInterrupt:
            logging.error("Ctrl-C is pressed.")
        except Exception as e:
            logging.exception("[CK] statistic online terminal exception.")

