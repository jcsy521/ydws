# -*- coding: utf-8 -*-

import os.path
import site

TOP_DIR_ = os.path.abspath(os.path.join(__file__, "../../.."))
site.addsitedir(os.path.join(TOP_DIR_, "libs"))

import logging
import time

from db_.mysql import DBConnection
from utils.misc import start_end_of_day, start_end_of_month, start_end_of_year
from utils.dotdict import DotDict


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
            logging.exception("[CHECKER] statistic online terminal exception.")

    def statistic_terminal(self, epoch_time):
        try:
            # NOTE: here, just static the info current day
            # instance, this day is 2013-05-28, we get data in 2013-05-28
            # NOTE: epoch_time, 

            start_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time())) 
            logging.info("[CK] %s statistic terminal started.", start_time)

            current_day = time.localtime(epoch_time)
            day_start_time, day_end_time = start_end_of_day(current_day.tm_year, current_day.tm_mon, current_day.tm_mday)
            month_start_time, month_end_time = start_end_of_month(current_day.tm_year, current_day.tm_mon)
            year_start_time, year_end_time = start_end_of_year(current_day.tm_year)
            logging.info("[CK] day_start_time: %s, day_end_time: %s, month_start_time: %s, month_end_time: %s, year_start_time: %s, year_end_time: %s.", 
                        day_start_time, day_end_time, month_start_time, month_end_time, year_start_time, year_end_time)
            

            sql_terminal_add = ("SELECT COUNT(tid) AS num"
                                "  FROM T_TERMINAL_INFO"
                                "  WHERE (begintime BETWEEN %s AND %s)")

            sql_corp_add = ("SELECT COUNT(id) as num"
                            "  FROM T_CORP"
                            "  WHERE timestamp BETWEEN %s AND %s")

            sql_login = ("SELECT COUNT(id) AS num"
                        "   FROM T_LOGIN_LOG"
                        "   WHERE (timestamp BETWEEN %s AND %s)") 

            sql_terminal_line_count = ("SELECT COUNT(tid) AS num"
                                       " FROM T_TERMINAL_INFO ")

            sql_in_active = ("SELECT COUNT(tmp.uid) AS num"
                         " FROM"
                         " (SELECT uid "
                         " FROM T_LOGIN_LOG"
                         " WHERE (timestamp BETWEEN %s AND %s)"
                         " AND role = 0 " 
                         "  GROUP BY uid"
                         "  HAVING count(id) >3) tmp")

            sql_en_active = ("SELECT COUNT(tmp.uid) AS num"
                         " FROM"
                         " (SELECT uid "
                         " FROM T_LOGIN_LOG"
                         " WHERE (timestamp BETWEEN %s AND %s)"
                         " AND role != 0 " 
                         "  GROUP BY uid"
                         "  HAVING count(id) >3) tmp")

            sql_kept = ("INSERT INTO T_STATISTIC(corp_add_day, corp_add_month, corp_add_year,"
                        "  terminal_add_day, terminal_add_month, terminal_add_year,"
                        "  login_day, login_month, login_year, active, deactive,"
                        "  terminal_online, terminal_offline, timestamp, type)"
                        "  VALUES (%s,%s,%s,"
                        "  %s, %s, %s,"
                        "  %s, %s, %s, %s, %s,"
                        "  %s, %s, %s, %s)"
                        "  ON DUPLICATE KEY"
                        "  UPDATE corp_add_day=values(corp_add_day),"
                        "        corp_add_month=values(corp_add_month), "
                        "        corp_add_year=values(corp_add_year),"
                        "        terminal_add_day=values(terminal_add_day),"
                        "        terminal_add_month=values(terminal_add_month),"
                        "        terminal_add_year=values(terminal_add_year),"
                        "        login_day=values(login_day),"
                        "        login_month=values(login_month),"
                        "        login_year=values(login_year),"
                        "        active=values(active),"
                        "        deactive=values(deactive),"
                        "        terminal_online=values(terminal_online),"
                        "        terminal_offline=values(terminal_offline)")

            #1 persional
            p_terminal_add_day = self.db.get(sql_terminal_add + " AND group_id = -1 ",
                                             day_start_time, day_end_time)
            
            p_terminal_add_month = self.db.get(sql_terminal_add + " AND group_id = -1 ",
                                               month_start_time, day_end_time)

            p_terminal_add_year= self.db.get(sql_terminal_add + " AND group_id = -1 ",
                                             year_start_time, day_end_time)

            p_login_day = self.db.get(sql_login + " AND role = 0",
                                      day_start_time, day_end_time )

            p_login_month = self.db.get(sql_login + " AND role = 0",
                                        month_start_time, day_end_time)

            p_login_year = self.db.get(sql_login  + " AND role = 0",
                                       year_start_time, day_end_time)

            p_active = self.db.get(sql_in_active, 
                                   month_start_time, day_end_time)
            individual = self.db.get("SELECT count(id) as num"
                                     "  FROM T_USER") 
            p_deactive = DotDict(num=individual.num-p_active.num)

            p_terminal_online_count = self.db.get(sql_terminal_line_count + " WHERE group_id = -1 AND login != 0")

            p_terminal_offline_count = self.db.get(sql_terminal_line_count + " WHERE group_id = -1 AND login = 0")

            self.db.execute(sql_kept,
                            0, 0, 0,p_terminal_add_day.num, p_terminal_add_month.num, p_terminal_add_year.num,
                            p_login_day.num, p_login_month.num, p_login_year.num, p_active.num, p_deactive.num,
                            p_terminal_online_count.num, p_terminal_offline_count.num, day_end_time, 0)
            #2: enterprise
            e_corp_add_day = self.db.get(sql_corp_add,
                                         day_start_time, day_end_time )

            e_corp_add_month = self.db.get(sql_corp_add,
                                           month_start_time, day_end_time )

            e_corp_add_year = self.db.get(sql_corp_add,
                                          year_start_time, day_end_time )

            e_terminal_add_day = self.db.get(sql_terminal_add + " AND group_id != -1",
                                            day_start_time, day_end_time)

            e_terminal_add_month = self.db.get(sql_terminal_add + " AND group_id != -1",
                                               month_start_time, day_end_time )

            e_terminal_add_year= self.db.get(sql_terminal_add + " AND group_id != -1",
                                           year_start_time, day_end_time )

            e_login_day = self.db.get(sql_login + " AND role != 0" ,
                                      day_start_time, day_end_time )

            e_login_month = self.db.get(sql_login + " AND role != 0" ,
                                        month_start_time, day_end_time )

            e_login_year = self.db.get(sql_login + " AND role != 0" ,
                                       year_start_time, day_end_time )

            e_active = self.db.get(sql_en_active, 
                                   month_start_time, day_end_time)

            oper = self.db.get("SELECT count(id) as num"
                               "  FROM T_OPERATOR") 

            enterprise = self.db.get("SELECT count(id) as num"
                                     "  FROM T_CORP") 

            e_deactive = DotDict(num=enterprise.num+oper.num-e_active.num) 

            e_terminal_online_count = self.db.get(sql_terminal_line_count + " WHERE group_id != -1  AND login != 0")

            e_terminal_offline_count = self.db.get(sql_terminal_line_count + " WHERE group_id != -1 AND login = 0")

            self.db.execute(sql_kept,
                            e_corp_add_day.num, e_corp_add_month.num, e_corp_add_year.num,
                            e_terminal_add_day.num, e_terminal_add_month.num, e_terminal_add_year.num,
                            e_login_day.num, e_login_month.num, e_login_year.num, e_active.num, e_deactive.num,
                            e_terminal_online_count.num, e_terminal_offline_count.num, day_end_time, 1)
 
            # 3 total 
            self.db.execute(sql_kept,
                            e_corp_add_day.num, e_corp_add_month.num, e_corp_add_year.num,
                            p_terminal_add_day.num + e_terminal_add_day.num,
                            p_terminal_add_month.num + e_terminal_add_month.num, 
                            p_terminal_add_year.num + e_terminal_add_year.num,
                            p_login_day.num+ e_login_day.num,
                            p_login_month.num + e_login_month.num,
                            p_login_year.num + e_login_year.num, 
                            p_active.num+e_active.num, p_deactive.num+e_deactive.num,
                            p_terminal_online_count.num+e_terminal_online_count.num,
                            p_terminal_offline_count.num+e_terminal_offline_count.num, day_end_time, 2)

            terminals_offline = self.db.query("select tid, mobile as tmobile, owner_mobile as umobile, offline_time, pbat  from T_TERMINAL_INFO where offline_time != 0 AND mobile like '14778%'")
            for terminal in terminals_offline:
                #NOTE: if pbat < 5, set it as 'power low'
                offline_cause = 2 if terminal.pbat < 5 else 1
                self.db.execute("INSERT INTO T_OFFLINE_STATISTIC(tid, umobile, tmobile, offline_time, offline_period, offline_cause, pbat)"
                                "  values(%s, %s, %s, %s, %s, %s, %s)"
                                "  on duplicate key"
                                "  update tid=values(tid),"
                                "         umobile=values(umobile),"
                                "         tmobile=values(tmobile),"
                                "         offline_time=values(offline_time),"
                                "         offline_cause=values(offline_cause),"
                                "         pbat=values(pbat)",
                                terminal.tid, terminal.umobile,
                                terminal.tmobile, terminal.offline_time,
                                int(time.time())-terminal.offline_time,
                                offline_cause, terminal.pbat)
           
            end_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time())) 
            logging.info("[CK] %s statistic terminal finished", end_time)
        except KeyboardInterrupt:
            logging.error("Ctrl-C is pressed.")
        except Exception as e:
            logging.exception("[CK] statistic online terminal exception.")


if __name__ == '__main__':
    
    from tornado.options import define, options, parse_command_line
    from helpers.confhelper import ConfHelper
    define('conf', default=os.path.join(TOP_DIR_, "conf/global.conf"))

    ConfHelper.load(options.conf)
    parse_command_line()

    year = '2013'
    month = '05'
    day =  '29'
    timestamp = int(time.mktime(time.strptime("%s-%s-%s"%(year,month,day),"%Y-%m-%d")))
    logging.info('[CHECKER] year: %s, month: %s, day: %s, timestamp: %s. ' , year, month, day,timestamp)

    ts = TerminalStatistic()
    ts.statistic_terminal(timestamp)
