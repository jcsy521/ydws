# -*- coding: utf-8 -*-

import os.path
import site

TOP_DIR_ = os.path.abspath(os.path.join(__file__, "../../.."))
site.addsitedir(os.path.join(TOP_DIR_, "libs"))

import logging
import time

from db_.mysql import DBConnection
from utils.misc import start_end_of_day, start_end_of_month, start_end_of_year, safe_unicode, str_to_list, safe_utf8, seconds_to_label, DUMMY_IDS
from utils.dotdict import DotDict
from utils.public import record_terminal_subscription 
from helpers.emailhelper import EmailHelper 
from constants import UWEB 
from tornado.options import define, options, parse_command_line
from helpers.confhelper import ConfHelper

if not 'conf' in options:
    define('conf', default=os.path.join(TOP_DIR_, "conf/global.conf"))

class TerminalStatistic(object):

    def __init__(self):
        self.db = DBConnection().db
        self.to_emails = ['boliang.guan@dbjtech.com']
        self.cc_emails = ['xiaolei.jia@dbjtech.com', 'zhaoxia.guo@dbjtech.com']
        
    def statistic_online_terminal(self, epoch_time):
        start_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time())) 
        logging.info("[CELERY] %s statistic_online_terminal started.", start_time)
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
            logging.info("[CELERY] %s statistic_online_terminal finish.", convert_time)
        except Exception as e:
            logging.exception("[CHECKER] statistic_online_terminal failed, exception: %s", e.args)

    def statistic_user(self, epoch_time):
        try:
            start_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time())) 
            logging.info("[CELERY] %s statistic_user started.", start_time)

            current_day = time.localtime(epoch_time)
            day_start_time, day_end_time = start_end_of_day(current_day.tm_year, current_day.tm_mon, current_day.tm_mday)
            month_start_time, month_end_time = start_end_of_month(current_day.tm_year, current_day.tm_mon)
            year_start_time, year_end_time = start_end_of_year(current_day.tm_year)

            logging.info("[CELERY] day_start_time: %s, day_end_time: %s, month_start_time: %s, month_end_time: %s, year_start_time: %s, year_end_time: %s.", 
                        day_start_time, day_end_time, month_start_time, month_end_time, year_start_time, year_end_time)
            
            sql_terminal_add = ("SELECT tsl.tmobile, tsl.begintime, tsl.add_time, tsl.del_time from T_SUBSCRIPTION_LOG as tsl, T_TERMINAL_INFO as tti"
                                "  WHERE tsl.tmobile = tti.mobile AND tti.service_status=1 AND tsl.op_type = 1 AND tsl.tmobile like '14778%%' AND (tsl.add_time BETWEEN %s AND %s)")

            sql_terminal_del = ("SELECT COUNT(id) AS num from T_SUBSCRIPTION_LOG "
                                "  WHERE op_type = 2 AND tmobile like '14778%%' AND (del_time BETWEEN %s AND %s)")

            sql_corp_add = ("SELECT COUNT(id) as num"
                            "  FROM T_CORP"
                            "  WHERE timestamp BETWEEN %s AND %s")

            sql_in_login = ("SELECT COUNT(distinct tll.uid) AS num"
                            "   FROM T_LOGIN_LOG as tll, T_TERMINAL_INFO as tti"
                            "   WHERE tll.uid = tti.owner_mobile AND tti.mobile like '14778%%' "
                            "       AND tll.role =0 AND (tll.timestamp BETWEEN %s AND %s)") 

            sql_en_login = ("SELECT COUNT(distinct uid) AS num"
                            "   FROM T_LOGIN_LOG" 
                            "   WHERE role != 0 AND (timestamp BETWEEN %s AND %s)")

            sql_terminal_line_count = ("SELECT COUNT(tid) AS num"
                                       " FROM T_TERMINAL_INFO ")

            sql_in_active = ("SELECT COUNT(tmp.uid) AS num"
                             " FROM"
                             " (SELECT uid "
                             " FROM T_LOGIN_LOG as tll, T_TERMINAL_INFO as tti"
                             " WHERE tll.uid = tti.owner_mobile AND tti.mobile like '14778%%' "
                             "     AND  (tll.timestamp BETWEEN %s AND %s)"
                             "     AND tll.role = 0 " 
                             "  GROUP BY tll.uid"
                             "  HAVING count(tll.id) >3) tmp")

            sql_en_active = ("SELECT COUNT(tmp.uid) AS num" 
                             " FROM" 
                             " (SELECT uid " 
                             " FROM T_LOGIN_LOG" 
                             " WHERE (timestamp BETWEEN %s AND %s)" 
                             " AND role != 0 " 
                             " GROUP BY uid" 
                             " HAVING count(id) >3) tmp")


            sql_kept = ("INSERT INTO T_STATISTIC(corp_add_day, corp_add_month, corp_add_year,"
                        "  terminal_add_day, terminal_add_month, terminal_add_year,"
                        "  terminal_del_day, terminal_del_month, terminal_del_year,"
                        "  login_day, login_month, login_year, active, deactive,"
                        "  terminal_online, terminal_offline, timestamp, type)"
                        "  VALUES (%s,%s,%s,"
                        "  %s, %s, %s,"
                        "  %s, %s, %s,"
                        "  %s, %s, %s, %s, %s,"
                        "  %s, %s, %s, %s)"
                        "  ON DUPLICATE KEY"
                        "  UPDATE corp_add_day=values(corp_add_day),"
                        "         corp_add_month=values(corp_add_month), "
                        "         corp_add_year=values(corp_add_year),"
                        "         terminal_add_day=values(terminal_add_day),"
                        "         terminal_add_month=values(terminal_add_month),"
                        "         terminal_add_year=values(terminal_add_year),"
                        "         terminal_del_day=values(terminal_del_day),"
                        "         terminal_del_month=values(terminal_del_month),"
                        "         terminal_del_year=values(terminal_del_year),"
                        "         login_day=values(login_day),"
                        "         login_month=values(login_month),"
                        "         login_year=values(login_year),"
                        "         active=values(active),"
                        "         deactive=values(deactive),"
                        "         terminal_online=values(terminal_online),"
                        "         terminal_offline=values(terminal_offline)")


            def handle_terminal_add(data):
                """Check the terminal is del or not.
                """
                res  = DotDict(num=0)
                if data is None:
                    pass
                else:
                    for item in data:
                        deltime = time.localtime(int(item['del_time']))
                        addtime = time.localtime(int(item['add_time']))
                        if (int(item['del_time']) != 0) and ((deltime.tm_year,deltime.tm_mon,deltime.tm_mday) == (addtime.tm_year,addtime.tm_mon,addtime.tm_mday)):
                            logging.info("[CELERY] tmobile: %s, add and del in the same day, add_time: %s, del_time: %s ", item['tmobile'], addtime, deltime)
                            pass
                        else:
                            res.num += 1
                return res

            #1 individual statistic 
            in_terminal_add_day = self.db.query(sql_terminal_add + " AND tsl.group_id = -1 ",
                                                day_start_time, day_end_time)
            in_terminal_add_day = handle_terminal_add(in_terminal_add_day)
                
            in_terminal_add_month = self.db.query(sql_terminal_add + " AND tsl.group_id = -1 ",
                                               month_start_time, day_end_time)
            in_terminal_add_month = DotDict(num=len(in_terminal_add_month))

            in_terminal_add_year= self.db.query(sql_terminal_add + " AND tsl.group_id = -1 ",
                                             year_start_time, day_end_time)
            in_terminal_add_year = DotDict(num=len(in_terminal_add_year))

            in_terminal_del_day = self.db.get(sql_terminal_del + " AND group_id = -1 ",
                                             day_start_time, day_end_time)

            
            in_terminal_del_month = self.db.get(sql_terminal_del + " AND group_id = -1 ",
                                               month_start_time, day_end_time)

            in_terminal_del_year= self.db.get(sql_terminal_del + " AND group_id = -1 ",
                                             year_start_time, day_end_time)

            in_login_day = self.db.get(sql_in_login,
                                      day_start_time, day_end_time )

            in_login_month = self.db.get(sql_in_login,
                                        month_start_time, day_end_time)

            in_login_year = self.db.get(sql_in_login,
                                       year_start_time, day_end_time)

            in_active = self.db.get(sql_in_active, 
                                   month_start_time, day_end_time)

            individuals = self.db.get("SELECT COUNT(tu.id) AS num"
                                      "  FROM T_USER as tu, T_TERMINAL_INFO as tti"
                                      "  WHERE tu.uid = tti.owner_mobile and tti.mobile like '14778%%'") 
            in_deactive = DotDict(num=individuals.num-in_active.num)

            in_terminal_online_count = self.db.get(sql_terminal_line_count + " WHERE service_status=1 AND group_id=-1 AND login != 0 AND mobile like '14778%%'")

            in_terminal_offline_count = self.db.get(sql_terminal_line_count + " WHERE service_status=1 AND group_id=-1 AND login=0  AND mobile like '14778%%'")

            self.db.execute(sql_kept,
                            0, 0, 0,in_terminal_add_day.num, in_terminal_add_month.num, in_terminal_add_year.num,
                            in_terminal_del_day.num, in_terminal_del_month.num, in_terminal_del_year.num,
                            in_login_day.num, in_login_month.num, in_login_year.num, in_active.num, in_deactive.num,
                            in_terminal_online_count.num,
                            in_terminal_offline_count.num, day_end_time,
                            UWEB.STATISTIC_USER_TYPE.INDIVIDUAL)

            #2: enterprise stattis
            e_corp_add_day = self.db.get(sql_corp_add,
                                         day_start_time, day_end_time )

            e_corp_add_month = self.db.get(sql_corp_add,
                                           month_start_time, day_end_time )

            e_corp_add_year = self.db.get(sql_corp_add,
                                          year_start_time, day_end_time )

            e_terminal_add_day = self.db.query(sql_terminal_add + " AND tsl.group_id != -1",
                                            day_start_time, day_end_time)
            e_terminal_add_day = handle_terminal_add(e_terminal_add_day)

            e_terminal_add_month = self.db.query(sql_terminal_add + " AND tsl.group_id != -1",
                                               month_start_time, day_end_time )
            e_terminal_add_month = DotDict(num=len(e_terminal_add_month))

            e_terminal_add_year= self.db.query(sql_terminal_add + " AND tsl.group_id != -1",
                                           year_start_time, day_end_time )
            e_terminal_add_year = DotDict(num=len(e_terminal_add_year))

            e_terminal_del_day = self.db.get(sql_terminal_del + " AND group_id != -1",
                                            day_start_time, day_end_time)

            e_terminal_del_month = self.db.get(sql_terminal_del + " AND group_id != -1",
                                               month_start_time, day_end_time )

            e_terminal_del_year= self.db.get(sql_terminal_del + " AND group_id != -1",
                                           year_start_time, day_end_time )

            e_login_day = self.db.get(sql_en_login,
                                      day_start_time, day_end_time )

            e_login_month = self.db.get(sql_en_login,
                                        month_start_time, day_end_time )

            e_login_year = self.db.get(sql_en_login,
                                       year_start_time, day_end_time )

            e_active = self.db.get(sql_en_active, 
                                   month_start_time, day_end_time)

            oper = self.db.get("SELECT count(id) as num"
                               "  FROM T_OPERATOR") 

            enterprise = self.db.get("SELECT count(id) as num"
                                     "  FROM T_CORP") 

            e_deactive = DotDict(num=enterprise.num+oper.num-e_active.num) 

            e_terminal_online_count = self.db.get(sql_terminal_line_count + " WHERE service_status=1 AND group_id != -1  AND login != 0 AND mobile like '14778%%'")

            e_terminal_offline_count = self.db.get(sql_terminal_line_count + " WHERE service_status=1 AND group_id != -1 AND login = 0 and mobile like '14778%%'")

            self.db.execute(sql_kept,
                            e_corp_add_day.num, e_corp_add_month.num, e_corp_add_year.num,
                            e_terminal_add_day.num, e_terminal_add_month.num, e_terminal_add_year.num,
                            e_terminal_del_day.num, e_terminal_del_month.num, e_terminal_del_year.num,
                            e_login_day.num, e_login_month.num, e_login_year.num, e_active.num, e_deactive.num,
                            e_terminal_online_count.num, e_terminal_offline_count.num, day_end_time,
                            UWEB.STATISTIC_USER_TYPE.ENTERPRISE)
 
            # 3 total statistic
            self.db.execute(sql_kept,
                            e_corp_add_day.num, e_corp_add_month.num, e_corp_add_year.num,
                            in_terminal_add_day.num + e_terminal_add_day.num,
                            in_terminal_add_month.num + e_terminal_add_month.num, 
                            in_terminal_add_year.num + e_terminal_add_year.num,

                            in_terminal_del_day.num + e_terminal_del_day.num,
                            in_terminal_del_month.num + e_terminal_del_month.num, 
                            in_terminal_del_year.num + e_terminal_del_year.num,

                            in_login_day.num+ e_login_day.num,
                            in_login_month.num + e_login_month.num,
                            in_login_year.num + e_login_year.num, 
                            in_active.num+e_active.num, in_deactive.num+e_deactive.num,
                            in_terminal_online_count.num+e_terminal_online_count.num,
                            in_terminal_offline_count.num+e_terminal_offline_count.num, day_end_time, 
                            UWEB.STATISTIC_USER_TYPE.TOTAL)

            end_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time())) 
            logging.info("[CELERY] %s statistic_user finished", end_time)
        except Exception as e:
            logging.exception("[CELERY] statistic_user terminal exception.")


    def statistic_offline_terminal(self, epoch_time):
        """Export data into excel file.
        """ 
        start_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time())) 
        logging.info("[CELERY] %s statistic_offline_terminal started.", start_time)

        current_day = time.localtime(epoch_time)
        day_start_time, day_end_time = start_end_of_day(current_day.tm_year, current_day.tm_mon, current_day.tm_mday)
        month_start_time, month_end_time = start_end_of_month(current_day.tm_year, current_day.tm_mon)
        year_start_time, year_end_time = start_end_of_year(current_day.tm_year)

        logging.info("[CELERY] day_start_time: %s, day_end_time: %s, month_start_time: %s, month_end_time: %s, year_start_time: %s, year_end_time: %s.", 
                    day_start_time, day_end_time, month_start_time, month_end_time, year_start_time, year_end_time)


        import xlwt 
        import xlrd

        BASE_PATH = '/var/ydcws/reports/' 
        # NOTE: chinese filename cannot download successfully, so here use
        # english filename. wish one day chinese words can work well 
        OFFLINE_FILE_NAME = u"terminals_offline"
        #OFFLINE_FILE_NAME = u"离线用户统计表"
        cur_path = time.strftime("%Y%m%d",time.localtime(epoch_time) ) 
        pre_path = time.strftime("%Y%m%d",time.localtime(epoch_time-60*60*24)) 
        PRE_PATH = BASE_PATH + OFFLINE_FILE_NAME + '-' + pre_path + '.xls'
        CUR_PATH = BASE_PATH + OFFLINE_FILE_NAME + '-' + cur_path + '.xls'

        OFFLINE_HEADER = (u"车主号",
                          u"终端号", 
                          u"电量", 
                          u"离线时间", 
                          u"累计离线时间", 
                          u"离线原因", 
                          u"唤醒指令下发频次", 
                          u"今日新增", 
                          u"当前状态", 
                          u"基站定位结果", 
                          u"备注")

        cur_sql_cmd = ("SELECT id, owner_mobile as umobile, mobile as tmobile, begintime, offline_time, pbat, remark"
                       "  FROM T_TERMINAL_INFO"
                       "  WHERE service_status = 1 AND login =0 "
                       "  AND mobile like '14778%%' "
                       "  AND offline_time BETWEEN %s AND %s ORDER BY pbat")

        terminal_sql_cmd = "SELECT login, remark, offline_time FROM T_TERMINAL_INFO WHERE mobile = %s LIMIT 1"

        cur_res = self.db.query(cur_sql_cmd, day_start_time, epoch_time)

        tmobile_lst = []
        for item in cur_res:
            tmobile_lst.append(item['tmobile'])
            item['offline_period'] = int(time.time()) - item['offline_time']
            item['offline_cause'] =  2 if item['pbat'] < 5 else 1
            item['sim_status'] = u'失败'
            if item['offline_cause'] == 1: # heart beat
                # check the sim status
                terminal_log = self.get("SELECT sim_status FROM T_SUBSCRIPTION_LOG",
                                        "  WHERE mobile = %s",
                                        item['tmobile'])
                if terminal_log.sim_status == 1:
                    item['sim_status'] = u'成功'
            
            item['remark'] = safe_unicode(item['remark'])
        logging.info('[CELERY] the currentrecords to be dealed with, counts: %s, cur_res: %s', len(cur_res), cur_res)

        pre_res = [] 
        if not os.path.isfile(PRE_PATH):
            logging.info("[CELERY] pre_path: %s cannot be found.", PRE_PATH)
        else:
            wb=xlrd.open_workbook(PRE_PATH)
            sh=wb.sheet_by_name(u'离线汇总分析')
            for rownum in range(1,sh.nrows): # get records from the second row

                row = sh.row_values(rownum)

                if row[1] in tmobile_lst:
                    continue
                if row[8] == u'在线':
                    continue

                tmobile = row[1]

                terminal = self.db.get(terminal_sql_cmd, tmobile) 

                current_status = u'离线'
                if not terminal:
                    current_status = u'已解绑'
                    row[8] = current_status
                else:
                    if terminal['login'] !=0:
                        current_status = u'在线'
                        row[8] = current_status

                    offline_period = int(time.time()) - terminal['offline_time']
                    row[4] = seconds_to_label(offline_period)
                    d,m = divmod(offline_period,60*60)
                    count = d+1 if m else d
                    row[6] = count
                    row[10] = safe_unicode(terminal['remark'])
                pre_res.append(row)
            logging.info('[CELERY] the previous records to be dealed with, count: %s, pre_res: %s', len(pre_res), pre_res)

        # some styles
        #date_style = xlwt.easyxf(num_format_str='YYYY-MM-DD HH:mm:ss')
        title_style = xlwt.easyxf('pattern: pattern solid, fore_colour ocean_blue; font: bold off; align: wrap on, vert centre, horiz center;' "borders: top double, bottom double, left double, right double;")
        abnormal_style = xlwt.easyxf('font: colour_index red, bold off; align: wrap on, vert centre, horiz center;')
        add_style = xlwt.easyxf('font: colour_index blue, bold off; align: wrap on, vert centre, horiz center;')
        powerlow_style = xlwt.easyxf('font: colour_index dark_yellow, bold off; align: wrap on, vert centre, horiz center;') 
        online_style = xlwt.easyxf('font: colour_index green, bold off; align: wrap on, vert centre, horiz center;')
        offline_style = xlwt.easyxf('font: colour_index brown, bold off; align: wrap on, vert centre, horiz center;')
        center_style  = xlwt.easyxf('align: wrap on, vert centre, horiz center;')


        wb = xlwt.Workbook()
        ws = wb.add_sheet(u'离线汇总分析')

        start_line = 0
        for i, head in enumerate(OFFLINE_HEADER):
            ws.write(0, i, head, title_style)

        ws.col(0).width = 4000 # umobile 
        ws.col(1).width = 4000 # tmobile 
        ws.col(3).width = 4000 * 2  # offline_time
        ws.col(4).width = 4000 * 2  # offline_period
        ws.col(6).width = 4000      # lq count
        ws.col(9).width = 4000  # sim_status
        ws.col(10).width = 4000 * 4 # remark

        start_line += 1

        results = cur_res
        for i, result in zip(range(start_line, len(results) + start_line), results):
            ws.write(i, 0, result['umobile'], center_style)
            ws.write(i, 1, result['tmobile'], center_style)
            ws.write(i, 2, str(result['pbat'])+'%', center_style)
            ws.write(i, 3, time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(result['offline_time'])), center_style)
            ws.write(i, 4, seconds_to_label(result['offline_period']), center_style)

            if result['offline_cause'] == 2: 
                offline_cause =  u'低电关机' 
                ws.write(i, 5, offline_cause, powerlow_style)
            else:
                offline_cause =  u'通讯异常'
                ws.write(i, 5, offline_cause, abnormal_style)
            d,m = divmod(result['offline_period'],60*60)
            count = d+1 if m else d
            ws.write(i, 6, count)
            terminal = self.db.get("SELECT remark FROM T_TERMINAL_INFO where id = %s", result['id'])

            ws.write(i, 7, u'新增', add_style)
            ws.write(i, 9, safe_unicode(terminal['sim_status']), center_style)
            ws.write(i, 10, safe_unicode(terminal['remark']), center_style)
            start_line += 1

        logging.info('[CELERY] current offline records, count: %s, tmobile_lst: %s', len(tmobile_lst), tmobile_lst)
        results = pre_res
        for i, result in zip(range(start_line, len(results) + start_line), results):
            #for j in range(len(OFFLINE_HEADER)):
            #    ws.write(i, j, result[j])
            #if result[1] in tmobile_lst:
            #    continue
            ws.write(i, 0, result[0], center_style)
            ws.write(i, 1, result[1], center_style)
            ws.write(i, 2, result[2], center_style)
            ws.write(i, 3, result[3], center_style)
            ws.write(i, 4, result[4], center_style)
            if result[5] == u'低电关机':
                ws.write(i, 5, u'低电关机', powerlow_style)
            else:
                ws.write(i, 5, u'通讯异常', abnormal_style)
            ws.write(i, 6, result[6])
            if result[8] == u'在线':
                ws.write(i, 8, u'在线', online_style)
            elif result[8] == u'已解绑': 
                ws.write(i, 8, u'已解绑')
            else:
                pass
            ws.write(i, 9, result[9], center_style)
            ws.write(i, 10, result[10], center_style)

        wb.save(CUR_PATH)

        content = u'附件是 %s 的离线报表统计，请查收! 详情请看：%s ' % (cur_path,ConfHelper.ADMIN_CONF.url)
        EmailHelper.send(self.to_emails, content, self.cc_emails, files=[CUR_PATH]) 
        logging.info("[CELERY] statistic_offline_terminal finished, cur_path: %s", CUR_PATH)

    def prepare_statistic(self):
        """Handle the old data.
        """
        #self.db.execute("truncate T_SUBSCRIPTION_LOG")
        #self.db.execute("truncate T_STATISTIC")
        terminals = self.db.query("select id, tid, mobile, begintime, offline_time, group_id from T_TERMINAL_INFO")
        for terminal in terminals: 
            # 1: record to T_SUBSCRIPTION
            record_terminal_subscription(self.db, terminal['mobile'], terminal['group_id'], terminal['begintime'], terminal['begintime'],1) 
            # 2: modify the offline_time
            if terminal['offline_time'] == 0:
                self.db.execute("UPDATE T_TERMINAL_INFO set offline_time = %s where id = %s ", 
                                terminal['begintime'], terminal['id'])
        
def statistic_offline_terminal():
    ts = TerminalStatistic()
    ts.statistic_offline_terminal(int(time.time()))

def statistic_online_terminal():
    ts = TerminalStatistic()
    ts.statistic_online_terminal(int(time.time()))

def statistic_user():
    ts = TerminalStatistic()
    ts.statistic_user(int(time.time()))
 
def statistic_misc():
    ts = TerminalStatistic()
    ts.prepare_statistic()

if __name__ == '__main__':
    ConfHelper.load(options.conf)
    parse_command_line()
    #NOTE: here, you can name the date to be statisticed.
    year = '2013'
    month = '01'
    day =  '14'
    timestamp = int(time.mktime(time.strptime("%s-%s-%s-23-59"%(year,month,day),"%Y-%m-%d-%H-%M")))
    logging.info('[CHECKER] year: %s, month: %s, day: %s, timestamp: %s. ' , year, month, day,timestamp)
    ts = TerminalStatistic()
    #ts.statistic_online_terminal(timestamp) 
    #ts.statistic_offline_terminal(timestamp) 
    #ts.statistic_misc() 
else: 
    try: 
        from celery.decorators import task 
        statistic_offline_terminal = task(ignore_result=True)(statistic_offline_terminal) 
        statistic_online_terminal = task(ignore_result=True)(statistic_online_terminal) 
        statistic_user = task(ignore_result=True)(statistic_user) 
    except Exception as e: 
        logging.exception("[CELERY] admintask statistic failed. Exception: %s", e.args)

