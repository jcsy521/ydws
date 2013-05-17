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
            self.db.execute("INSERT INTO T_ONLINE_STATISTIC(online_num, offline_num, time, cid) "
                            "  SELECT sum(tti.login), count(tti.tid) - sum(tti.login), %s, tc.cid "
                            "    FROM T_TERMINAL_INFO tti, T_GROUP tg, T_CORP tc"
                            "    WHERE tti.group_id = tg.id"
                            "    AND tg.corp_id = tc.cid"
                            "    GROUP BY tc.cid",
                            int(epoch_time))
            convert_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(epoch_time)) 
            logging.info("[CK] %s statistic online terminal finish", convert_time)
        except KeyboardInterrupt:
            logging.error("Ctrl-C is pressed.")
        except Exception as e:
            logging.exception("[CK] statistic online terminal exception.")

