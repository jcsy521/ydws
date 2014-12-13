# -*- coding: utf-8 -*-

"""This module is designed for event-statistic.

#NOTE: deprecated
"""

import logging
import datetime
import time
import hashlib
from os import SEEK_SET
from dateutil.relativedelta import relativedelta
import xlwt
from cStringIO import StringIO

from tornado.escape import json_decode, json_encode
import tornado.web

from helpers.queryhelper import QueryHelper 
from helpers.confhelper import ConfHelper
from utils.misc import DUMMY_IDS, str_to_list, start_end_of_year, start_end_of_month, start_end_of_day, start_end_of_quarter, days_of_month
from utils.dotdict import DotDict
from codes.errorcode import ErrorCode
from constants import UWEB, EVENTER, EXCEL
from base import BaseHandler, authenticated

class StatisticHandler(BaseHandler):

    KEY_TEMPLATE = "event_statistic_%s_%s"

    @authenticated
    @tornado.web.removeslash
    def post(self):
        """Provide some statistics about terminals.
        """
        status = ErrorCode.SUCCESS
        try:
            data = DotDict(json_decode(self.request.body))
            logging.info("[UWEB] event statistic request: %s, uid: %s, tid: %s", 
                         data, self.current_user.uid, self.current_user.tid)
        except Exception as e:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            self.write_ret(status)
            return

        try:
            res = []
            page_size = UWEB.LIMIT.PAGE_SIZE
            page_number = int(data.pagenum)
            page_count = int(data.pagecnt)
            start_time = data.start_time
            end_time = data.end_time
            tids = str_to_list(data.tids)
            # the interval between start_time and end_time is one week

            if self.current_user.cid != UWEB.DUMMY_CID: # no checks for enterprise
                pass
            elif (int(end_time) - int(start_time)) > UWEB.QUERY_INTERVAL:
                self.write_ret(ErrorCode.QUERY_INTERVAL_EXCESS)
                return

            CATEGORY_DCT = DotDict(illegalmove=EVENTER.CATEGORY.ILLEGALMOVE,
                                   illegashake=EVENTER.CATEGORY.ILLEGALSHAKE,
                                   #sos=EVENTER.CATEGORY.EMERGENCY,
                                   heartbeat_lost=EVENTER.CATEGORY.HEARTBEAT_LOST, 
                                   powerlow=EVENTER.CATEGORY.POWERLOW)
            if page_count == -1:
                count = len(tids)
                d, m = divmod(count, page_size)
                page_count = (d + 1) if m else d


            for tid in tids: 
                res_item = {} 
                res_item['alias'] = QueryHelper.get_alias_by_tid(tid, self.redis, self.db)
                for key, category in CATEGORY_DCT.iteritems():
                     item = self.db.get("SELECT COUNT(*) as count FROM V_EVENT"
                                        "  WHERE tid = %s"
                                        "    AND (timestamp BETWEEN %s AND %s)"
                                        "    AND category = %s",
                                        tid, start_time, end_time, category)
                     res_item[key] = item.count
                res.append(res_item)

            # store resutl in redis
            m = hashlib.md5()
            m.update(self.request.body)
            hash_ = m.hexdigest()
            mem_key = self.KEY_TEMPLATE % (self.current_user.uid, hash_)
            self.redis.setvalue(mem_key, res, time=UWEB.STATISTIC_INTERVAL)

            res = res[(page_number * page_size):((page_number+1) * page_size)]

            self.write_ret(status, 
                           dict_=DotDict(res=res,
                                         pagecnt=page_count,
                                         hash_=hash_))
        except Exception as e:
            logging.exception("[UWEB] event statistic, uid:%s, tid:%s  failed. Exception: %s",
                              self.current_user.uid, self.current_user.tid, e.args)
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)

class StatisticDownloadHandler(StatisticHandler):

    @authenticated
    @tornado.web.removeslash
    def get(self):
        """Provie some statistics about terminals.
        """
        status = ErrorCode.SUCCESS
        try:
            hash_ = self.get_argument('hash_', None)

            mem_key = self.KEY_TEMPLATE % (self.current_user.uid, hash_)

            res = self.redis.getvalue(mem_key)
            if not res:
                logging.exception("[UWEB] event statistic export excel failed, find no res by hash_:%s", hash_)
                self.render("error.html",
                            message=ErrorCode.ERROR_MESSAGE[ErrorCode.EXPORT_FAILED],
                            home_url=ConfHelper.UWEB_CONF.url_out)
                return
            results = res

            date_style = xlwt.easyxf(num_format_str='YYYY-MM-DD HH:mm:ss')
            
            wb = xlwt.Workbook()
            ws = wb.add_sheet(EXCEL.EVENT_STATISTIC_SHEET)

            start_line = 0
            for i, head in enumerate(EXCEL.EVENT_STATISTIC_HEADER):
                ws.write(0, i, head)

            start_line += 1
            for i, result in zip(range(start_line, len(results) + start_line), results):
                ws.write(i, 0, result['alias'])
                ws.write(i, 1, result['illegalmove'])
                ws.write(i, 2, result['illegashake'])
                ws.write(i, 3, result['heartbeat_lost'])
                ws.write(i, 4, result['powerlow'])

            _tmp_file = StringIO()
            wb.save(_tmp_file)
            filename = self.generate_file_name(EXCEL.EVENT_STATISTIC_FILE_NAME)
            
            self.set_header('Content-Type', 'application/force-download')
            self.set_header('Content-Disposition', 'attachment; filename=%s.xls' % (filename,))

            # move the the begging. 
            _tmp_file.seek(0, SEEK_SET)
            self.write(_tmp_file.read())
            _tmp_file.close()
 
        except Exception as e:
            logging.exception("[UWEB] event statistic export excel failed, Exception: %s", e.args)
            self.render("error.html",
                        message=ErrorCode.ERROR_MESSAGE[ErrorCode.EXPORT_FAILED],
                        home_url=ConfHelper.UWEB_CONF.url_out)

class StatisticSingleHandler(BaseHandler):

    KEY_TEMPLATE = "event_single_statistic_%s_%s"

    @authenticated
    @tornado.web.removeslash
    def post(self):
        """Provie some statistics for one terminals.
        """
        status = ErrorCode.SUCCESS
        try:
            data = DotDict(json_decode(self.request.body))
            logging.info("[UWEB] event single statistic request: %s, uid: %s, tid: %s", 
                         data, self.current_user.uid, self.current_user.tid)
        except Exception as e:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            self.write_ret(status)
            return

        try:
            page_size = UWEB.LIMIT.PAGE_SIZE_STATISTICS
            page_number = int(data.pagenum)
            page_count = int(data.pagecnt)
            tid = data.tid
           
            res = []
            graphics = []
            counts_dct= {} 
            counts = []
            label = u''
            
            sql_cmd = ("SELECT COUNT(*) as count FROM V_EVENT"
                       "  WHERE tid = %s"
                       "    AND (timestamp BETWEEN %s AND %s) AND category != 5 ")

            sql_cmd_category =  sql_cmd + "  AND category =%s"

            current_time = int(time.time()) 

            CATEGORY_DCT = DotDict(powerlow=EVENTER.CATEGORY.POWERLOW,
                                   illegashake=EVENTER.CATEGORY.ILLEGALSHAKE,
                                   illegalmove=EVENTER.CATEGORY.ILLEGALMOVE,
                                   #sos=EVENTER.CATEGORY.EMERGENCY,
                                   heartbeat_lost=EVENTER.CATEGORY.HEARTBEAT_LOST)

            CATEGORY_KEY = ['illegalmove','illegashake', 'heartbeat_lost', 'powerlow' ] 

            for key in CATEGORY_KEY:
                counts_dct[key] = 0 
            
            statistics_type = data.statistics_type
            if statistics_type == UWEB.STATISTICS_TYPE.YEAR:
                label = data.year + u'年' 
                start_time, end_time = start_end_of_year(year=data.year)
                for month in range(1,12+1):
                    start_time_, end_time_ = start_end_of_month(year=data.year, month=str(month))
                    if start_time_ > current_time:
                        break

                    re = {} 
                    re['name'] = str(month)

                    events = {} 

                    for key in CATEGORY_KEY:
                         res_item = {} 
                         item = self.db.get(sql_cmd_category, tid, start_time_, end_time_, CATEGORY_DCT[key])
                         res_item[key] = item.count
                         events.update(res_item)
                    
                    #event = self.db.get(sql_cmd, tid, start_time_, end_time_)
                    #graphics.append(event.count)
                        
                    re['events'] = events
                    res.append(re)

                #for category in CATEGORY_DCT.itervalues():  
                #    event_count = self.db.get(sql_cmd_category, tid, start_time, end_time, category)
                #    counts.append(event_count.count)


                for r in res:
                    graphics.append(sum(r['events'].itervalues()))
                    event = r['events']
                    for key in CATEGORY_KEY:
                        counts_dct[key] += event[key]

                for key in CATEGORY_KEY:
                    counts.append(counts_dct[key])

            elif statistics_type == UWEB.STATISTICS_TYPE.MONTH:
                label = data.year + u'年' + data.month + u'月'
                start_time, end_time = start_end_of_month(year=data.year, month=data.month)
                days = days_of_month(year=data.year, month=data.month)
                for day in range(1,days+1):
                    start_time_, end_time_ = start_end_of_day(year=data.year, month=data.month, day=str(day))
                    if start_time_ > current_time:
                        break

                    re = {} 
                    re['name'] = str(day)

                    events = {} 

                    for key in CATEGORY_KEY:
                         res_item = {} 
                         item = self.db.get(sql_cmd_category, tid, start_time_, end_time_, CATEGORY_DCT[key])
                         res_item[key] = item.count
                         events.update(res_item)
                    
                    re['events'] = events
                    res.append(re)

                for r in res:
                    graphics.append(sum(r['events'].itervalues()))
                    event = r['events']
                    for key in CATEGORY_KEY:
                        counts_dct[key] += event[key]

                for key in CATEGORY_KEY:
                    counts.append(counts_dct[key])
            else:
                logging.error("[UWEB] Error statistics type: %s", statistics_type)
            
            if page_count == -1:
                items_count = len(res) 
                d, m = divmod(items_count, page_size) 
                page_count = (d + 1) if m else d
      
            # store resutl in redis
            m = hashlib.md5()
            m.update(self.request.body)
            hash_ = m.hexdigest()
            mem_key = self.KEY_TEMPLATE % (self.current_user.uid, hash_)
            
            self.redis.setvalue(mem_key, (res, counts, label), time=UWEB.STATISTIC_INTERVAL)
           
            res= res[page_number*page_size:(page_number+1)*page_size]
            self.write_ret(status, 
                           dict_=dict(res=res, 
                                      counts=counts,
                                      graphics=graphics,
                                      pagecnt=page_count,
                                      hash_=hash_)) 

        except Exception as e:
            logging.exception("[UWEB] event statistic, uid:%s, tid:%s failed. Exception: %s",
                              self.current_user.uid, self.current_user.tid, e.args)
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)

class StatisticSingleDownloadHandler(StatisticSingleHandler):

    @authenticated
    @tornado.web.removeslash
    def get(self):
        """Provide some statistics about terminals.
        """
        status = ErrorCode.SUCCESS
        try:
            hash_ = self.get_argument('hash_', None)

            mem_key = self.KEY_TEMPLATE % (self.current_user.uid, hash_)

            res = self.redis.getvalue(mem_key)
            if not res:
                logging.exception("[UWEB] Export excel failed, find no res by hash_:%s", hash_)
                self.render("error.html",
                            message=ErrorCode.ERROR_MESSAGE[ErrorCode.EXPORT_FAILED],
                            home_url=ConfHelper.UWEB_CONF.url_out)
                return
            results, counts, label = res

            date_style = xlwt.easyxf(num_format_str='YYYY-MM-DD HH:mm:ss')
            
            wb = xlwt.Workbook()
            ws = wb.add_sheet(EXCEL.EVENT_SINGLE_STATISTIC_SHEET)

            start_line = 0
            for i, head in enumerate(EXCEL.EVENT_SINGLE_STATISTIC_HEADER):
                ws.write(0, i, head)

            start_line += 1
            for i, result in zip(range(start_line, len(results) + start_line), results):
                ws.write(i, 0, result['name'])
                ws.write(i, 1, result['events']['heartbeat_lost'])
                ws.write(i, 2, result['events']['illegashake'])
                ws.write(i, 3, result['events']['illegalmove'])
                ws.write(i, 4, result['events']['powerlow'])
            last_row = len(results) + start_line
            ws.write(last_row, 0, u'合计')
            ws.write(last_row, 1, counts[0])
            ws.write(last_row, 2, counts[1])
            ws.write(last_row, 3, counts[2])
            ws.write(last_row, 4, counts[3])

            _tmp_file = StringIO()
            wb.save(_tmp_file)
            filename = self.generate_file_name(label+EXCEL.EVENT_SINGLE_STATISTIC_FILE_NAME)
            
            self.set_header('Content-Type', 'application/force-download')
            self.set_header('Content-Disposition', 'attachment; filename=%s.xls' % (filename,))

            # move the the begging. 
            _tmp_file.seek(0, SEEK_SET)
            self.write(_tmp_file.read())
            _tmp_file.close()
 
        except Exception as e:
            logging.exception("[UWEB] event single statistic export excel failed, Exception: %s", e.args)
            self.render("error.html",
                        message=ErrorCode.ERROR_MESSAGE[ErrorCode.EXPORT_FAILED],
                        home_url=ConfHelper.UWEB_CONF.url_out)

