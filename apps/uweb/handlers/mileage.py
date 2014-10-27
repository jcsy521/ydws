# -*- coding: utf-8 -*-

import logging
import datetime
import time
import hashlib
from os import SEEK_SET
import xlwt
from cStringIO import StringIO
from decimal import Decimal

from tornado.escape import json_decode, json_encode
import tornado.web

from utils.dotdict import DotDict
from utils.misc import DUMMY_IDS, str_to_list, start_end_of_year, start_end_of_month, start_end_of_day, start_end_of_quarter, days_of_month, get_date_from_utc
from utils.dotdict import DotDict
from helpers.queryhelper import QueryHelper
from helpers.lbmphelper import get_distance
from helpers.confhelper import ConfHelper
from codes.errorcode import ErrorCode
from constants import UWEB, EXCEL
from base import BaseHandler, authenticated


class MileageHandler(BaseHandler):
    """Mileage report: distance of per day"""

    KEY_TEMPLATE = "mileage_statistic_%s_%s"

    @authenticated
    @tornado.web.removeslash
    @tornado.web.asynchronous
    def post(self):
        """ Provide some statistics about terminals.
        """
      
        status = ErrorCode.SUCCESS
        #NOTE: check data format
        try:
            data = DotDict(json_decode(self.request.body))
            page_size = UWEB.LIMIT.PAGE_SIZE
            page_number = int(data.pagenum)
            page_count = int(data.pagecnt)
            start_time= data.start_time
            end_time = data.end_time
            query_type = data.query_type
            if query_type == UWEB.QUERY_TYPE.JUNIOR: # 0
                start_period_ = 0
                end_period_ = 0 
            else:
                start_period= data.start_period
                end_period = data.end_period
                start_period_ = int(start_period[:2])*60*60 + int(start_period[2:])*60
                end_period_ = int(end_period[:2])*60*60 + int(end_period[2:])*60
            tids = str_to_list(data.tids)
            logging.info("[UWEB] mileage request: %s, cid: %s, oid: %s", 
                         data, self.current_user.cid, self.current_user.oid)
        except Exception as e:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            logging.exception("[UWEB] Invalid data format. Exception: %s",
                              e.args)
            self.write_ret(status)
            self.finish()
            return

        #NOTE: prepare  
        try:
            # the interval between start_time and end_time is one week
            if self.current_user.cid != UWEB.DUMMY_CID: # no checks for enterprise
                pass
            elif (int(end_time) - int(start_time)) > UWEB.QUERY_INTERVAL:
                self.write_ret(ErrorCode.QUERY_INTERVAL_EXCESS)
                self.finish()
                return

            statistic_mode = 'single' 
            if not tids: # all terminals
                statistic_mode = 'all' 
                terminals = QueryHelper.get_terminals_by_cid(self.current_user.cid, self.db)
                tids = [terminal.tid for terminal in terminals]
        except Exception as e:
            logging.exception("[UWEB] cid:%s, oid:%s get mileage report failed. Exception: %s",
                              self.current_user.cid, self.current_user.oid, e.args)
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)
            self.finish()
            return

        def _on_finish(db):
            self.db = db
            page_count = int(data.pagecnt)
            if statistic_mode == 'all': # all
                if page_count == -1:
                    count = len(tids)
                    d, m = divmod(count, page_size)
                    page_count = (d + 1) if m else d

                reports = []
                interval = [start_time, end_time]
                for item, tid in enumerate(tids):
                    seq=item+1
                    dis_sum = Decimal()  

                    start_date = get_date_from_utc(start_time)
                    end_date = get_date_from_utc(end_time)
                    start_day = datetime.datetime.fromtimestamp(start_time)
                    end_day = datetime.datetime.fromtimestamp(end_time)
                    # get how many days the end_time and start_time cover
                    days = abs(end_day-start_day).days+1
                    for item in range(days):
                        distance = Decimal()
                        timestamp = start_time+1*60*60*24*(item)
                        date = get_date_from_utc(timestamp)
                        year, month, day = date.year, date.month, date.day
                        start_time_, end_time_ = start_end_of_day(year=year, month=month, day=day)
                 
                        points = self.db.query("SELECT longitude, latitude FROM T_LOCATION"
                                               "  WHERE tid = %s"
                                               "    AND (timestamp BETWEEN %s AND %s)"
                                               "    AND type = 0"
                                               "  ORDER BY timestamp asc",
                                               tid, start_time_+start_period_, start_time_+end_period_)
                        for i in range(len(points)-1):
                            if points[i].longitude and points[i].latitude and \
                               points[i+1].longitude and points[i+1].latitude:
                               dis = get_distance(points[i].longitude, points[i].latitude,
                                                         points[i+1].longitude, points[i+1].latitude) 
                               distance += Decimal(str(dis))
                        # meter --> km
                        distance = '%0.1f' % (distance/1000,)
                        dis_sum += Decimal(distance)

                    alias = QueryHelper.get_alias_by_tid(tid, self.redis, self.db)
                    dct = dict(seq=seq,
                               alias=alias,
                               distance=float(dis_sum))
                    reports.append(dct)

                # orgnize and store the data to be downloaded 
                m = hashlib.md5()
                m.update(self.request.body)
                hash_ = m.hexdigest()
                mem_key = self.KEY_TEMPLATE % (self.current_user.uid, hash_)
                
                self.redis.setvalue(mem_key, (statistic_mode, reports, 0), time=UWEB.STATISTIC_INTERVAL)

                reports= reports[(page_number * page_size):((page_number+1) * page_size)]
                self.write_ret(status,
                               dict_=DotDict(res=reports,
                                             pagecnt=page_count,
                                             hash_=hash_))
            else: # single
                tid = tids[0]
                delta = end_time - start_time # end_time must bigger than start_time
                d, m = divmod(delta, 60*60*24) 
                start_date = get_date_from_utc(start_time)
                end_date = get_date_from_utc(end_time)
                start_day = datetime.datetime.fromtimestamp(start_time)
                end_day = datetime.datetime.fromtimestamp(end_time)
                # get how many days the end_time and start_time cover
                days = abs(end_day-start_day).days+1
                #if days == 0: 
                #    if start_date.day  == end_date.day:   
                #        days = 1
                #    else: 
                #        days = 2
                #else: 
                #    days = days+1 if m else days
                #    if end_day.hour*60*60 + end_day.minute*60 + end_day.second <  start_day.hour*60*60 + start_day.minute*60 + start_day.second:                   
                #        days = days+1 
  
                res = []
                graphics = [] 
                counts = []
                dis_sum = Decimal() 
                current_time = int(time.time()) 

                sql_cmd = ("SELECT longitude, latitude FROM T_LOCATION"
                           "  WHERE tid = %s"
                           "    AND (timestamp BETWEEN %s AND %s)"
                           "    AND type = 0"
                           "  ORDER BY timestamp asc")

                #last_cmd = ("SELECT timestamp FROM T_LOCATION"
                #            "  WHERE tid = %s"
                #            "    AND (timestamp BETWEEN %s AND %s)"
                #            "    AND type = 0"
                #            "  ORDER BY timestamp desc limit 1")

                #next_cmd = ("SELECT timestamp FROM T_LOCATION"
                #            "  WHERE tid = %s"
                #            "    AND (timestamp BETWEEN %s AND %s)"
                #            "    AND type = 0"
                #            "  ORDER BY timestamp asc limit 1")
                 
                if days == 1: # start_time, end_time in the same day
                    timestamp = start_time
                    date = get_date_from_utc(timestamp)

                    re = {} 
                    re['alias'] = '-'.join([str(date.year),str(date.month),str(date.day)]) 
                    distance = Decimal() 

                    points = self.db.query(sql_cmd, tid, start_time+start_period_, start_time+end_period_)
                    for i in range(len(points)-1):
                        if points[i].longitude and points[i].latitude and \
                           points[i+1].longitude and points[i+1].latitude:
                            dis = get_distance(points[i].longitude, points[i].latitude,
                                               points[i+1].longitude, points[i+1].latitude) 
                            distance += Decimal(str(dis)) 
                    # meter --> km
                    distance = '%0.1f' % (distance/1000,)      
                        
                    graphics.append(float(distance))
                    dis_sum += Decimal(distance)

                    re['distance'] = distance 
                    re['seq'] = 1 
                    res.append(re)
                else: # start_time, end_time in different days
                    for item in range(days):
                        timestamp = start_time+1*60*60*24*(item)
                        date = get_date_from_utc(timestamp)
                        year, month, day = date.year, date.month, date.day
                        start_time_, end_time_ = start_end_of_day(year=year, month=month, day=day)
                        ## handle the first day and last day
                        #if item == 0: 
                        #    start_time_ = start_time
                        #if item == days: 
                        #    end_time_ = end_time
                        #last_point = self.db.get(last_cmd, tid, start_time_-60*60*24, start_time_,)
                        #next_point = self.db.get(next_cmd, tid, end_time_, end_time_+60*60*24)
                        #start_time_ = last_point['timestamp'] if last_point else start_time_
                        #end_time_ = next_point['timestamp'] if next_point else end_time_

                        re = {} 
                        re['alias'] = '-'.join([str(year),str(month),str(day)]) 
                        distance = Decimal() 
                        points = self.db.query(sql_cmd, tid, start_time_+start_period_, start_time_+end_period_)
                        for i in range(len(points)-1):
                            if points[i].longitude and points[i].latitude and \
                               points[i+1].longitude and points[i+1].latitude:
                                dis = get_distance(points[i].longitude, points[i].latitude,
                                                   points[i+1].longitude, points[i+1].latitude) 
                                distance += Decimal(str(dis)) 
                        # meter --> km
                        distance = '%0.1f' % (distance/1000,)      
                            
                        graphics.append(float(distance))
                        dis_sum += Decimal(distance)

                        re['distance'] = distance 
                        re['seq'] = item+1 
                        res.append(re)

                counts = [float(dis_sum),]

                if page_count == -1:
                    items_count = len(res) 
                    d, m = divmod(items_count, page_size) 
                    page_count = (d + 1) if m else d
    
                # store resutl in redis
                m = hashlib.md5()
                m.update(self.request.body)
                hash_ = m.hexdigest()
                mem_key = self.KEY_TEMPLATE % (self.current_user.uid, hash_)
                
                self.redis.setvalue(mem_key, (statistic_mode, res, counts,), time=UWEB.STATISTIC_INTERVAL)
    
                res= res[page_number*page_size:(page_number+1)*page_size]
                self.write_ret(status, 
                               dict_=dict(res=res, 
                                          counts=counts,
                                          graphics=graphics,
                                          pagecnt=page_count,
                                          hash_=hash_)) 
            self.finish()
        self.queue.put((10, _on_finish))
  
class MileageDownloadHandler(MileageHandler):

    @authenticated
    @tornado.web.removeslash
    def get(self):
        """Provide some statistics about terminals.
        """
        status = ErrorCode.SUCCESS
        try:
            hash_ = self.get_argument('hash_', None)

            mem_key = self.KEY_TEMPLATE % (self.current_user.uid, hash_)

            statistic_mode, results, counts = self.redis.getvalue(mem_key)

            if not results:
                logging.exception("[UWEB] mileage statistic export excel failed, find no res by hash_:%s", hash_)
                self.render("error.html",
                            message=ErrorCode.ERROR_MESSAGE[ErrorCode.EXPORT_FAILED],
                            home_url=ConfHelper.UWEB_CONF.url_out)
                return
            if statistic_mode == 'all':
                date_style = xlwt.easyxf(num_format_str='YYYY-MM-DD HH:mm:ss')
                
                wb = xlwt.Workbook()
                ws = wb.add_sheet(EXCEL.MILEAGE_STATISTIC_SHEET_ALL)

                start_line = 0
                for i, head in enumerate(EXCEL.MILEAGE_STATISTIC_HEADER_ALL):
                    ws.write(0, i, head)
                    ws.col(1).width = 4000

                start_line += 1
                for i, result in zip(range(start_line, len(results) + start_line), results):
                    ws.write(i, 0, result['seq'])
                    ws.write(i, 1, result['alias'])
                    ws.write(i, 2, result['distance'])
                last_row = len(results) + start_line
                #NOTE: Here, use merge and center_style
                center_style  = xlwt.easyxf('align: wrap on, vert centre, horiz center;')
                ws.write_merge(last_row, last_row, 0, 1, u'合计', center_style)
                ws.write(last_row, 2, counts[0])
            else: 
                date_style = xlwt.easyxf(num_format_str='YYYY-MM-DD HH:mm:ss')
                
                wb = xlwt.Workbook()
                ws = wb.add_sheet(EXCEL.MILEAGE_STATISTIC_SHEET_SINGLE)

                start_line = 0
                for i, head in enumerate(EXCEL.MILEAGE_STATISTIC_HEADER_SINGLE):
                    ws.write(0, i, head)
                    ws.col(1).width = 4000

                start_line += 1
                for i, result in zip(range(start_line, len(results) + start_line), results):
                    ws.write(i, 0, result['seq'])
                    ws.write(i, 1, result['alias'])
                    ws.write(i, 2, result['distance'])
                last_row = len(results) + start_line
                #NOTE: Here, use merge and center_style
                center_style  = xlwt.easyxf('align: wrap on, vert centre, horiz center;')
                ws.write_merge(last_row, last_row, 0, 1, u'合计', center_style)
                ws.write(last_row, 2, counts[0])

            _tmp_file = StringIO()
            wb.save(_tmp_file)
            filename = self.generate_file_name(EXCEL.MILEAGE_STATISTIC_FILE_NAME_ALL)
            
            self.set_header('Content-Type', 'application/force-download')
            self.set_header('Content-Disposition', 'attachment; filename=%s.xls' % (filename,))

            # move the the begging. 
            _tmp_file.seek(0, SEEK_SET)
            self.write(_tmp_file.read())
            _tmp_file.close()
 
        except Exception as e:
            logging.exception("[UWEB] mileage statistic export excel failed, Exception: %s", e.args)
            self.render("error.html",
                        message=ErrorCode.ERROR_MESSAGE[ErrorCode.EXPORT_FAILED],
                        home_url=ConfHelper.UWEB_CONF.url_out)

class MileageSingleHandler(BaseHandler):

    KEY_TEMPLATE = "mileage_single_statistic_%s_%s"

    @authenticated
    @tornado.web.removeslash
    def post(self):
        """Provide statistics about terminal.
        """
        status = ErrorCode.SUCCESS
        try:
            data = DotDict(json_decode(self.request.body))
            logging.info("[UWEB] statistic request: %s, uid: %s, tid: %s", 
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
            counts = []
            label = u''
           
            sql_cmd = ("SELECT longitude, latitude FROM T_LOCATION"
                       "  WHERE tid = %s"
                       "    AND (timestamp BETWEEN %s AND %s)"
                       "    AND type = 0"
                       "  ORDER BY timestamp asc")

            last_cmd = ("SELECT timestamp FROM T_LOCATION"
                        "  WHERE tid = %s"
                        "    AND (timestamp BETWEEN %s AND %s)"
                        "    AND type = 0"
                        "  ORDER BY timestamp desc limit 1")

            next_cmd = ("SELECT timestamp FROM T_LOCATION"
                        "  WHERE tid = %s"
                        "    AND (timestamp BETWEEN %s AND %s)"
                        "    AND type = 0"
                        "  ORDER BY timestamp asc limit 1")

            dis_sum = Decimal() 
            
            current_time = int(time.time()) 

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
                    distance = Decimal() 
                    points = self.db.query(sql_cmd, tid, start_time_, end_time_)
                    for i in range(len(points)-1):
                        if points[i].longitude and points[i].latitude and \
                           points[i+1].longitude and points[i+1].latitude:
                            dis = get_distance(points[i].longitude, points[i].latitude,
                                               points[i+1].longitude, points[i+1].latitude) 
                            distance += Decimal(str(dis)) 
                    # meter --> km
                    distance = '%0.1f' % (distance/1000,)      
                    if float(distance) == 0:
                        distance = 0
                        
                    graphics.append(float(distance))
                    dis_sum += Decimal(distance)

                    re['mileage'] = distance 
                    res.append(re)

                counts = [float(dis_sum),]

            elif statistics_type == UWEB.STATISTICS_TYPE.MONTH:
                label = data.year + u'年' + data.month + u'月'
                start_time, end_time = start_end_of_month(year=data.year, month=data.month)
                days = days_of_month(year=data.year, month=data.month)

                distance = Decimal() 
                points_ = self.db.query(sql_cmd, tid, start_time, end_time)
                for i in range(len(points_)-1):
                    if points_[i].longitude and points_[i].latitude and \
                        points_[i+1].longitude and points_[i+1].latitude:
                        dis = get_distance(points_[i].longitude, points_[i].latitude, 
                            points_[i+1].longitude, points_[i+1].latitude)
                        dis=Decimal(str(dis))
                        distance += dis

                distance = '%0.1f' % (distance/1000,)
                dis_sum = distance

                for day in range(1,days+1):
                    start_time_, end_time_ = start_end_of_day(year=data.year, month=data.month, day=str(day))
                    if start_time_ > current_time:
                        break

                    last_point = self.db.get(last_cmd, tid, start_time_-60*60*24, start_time_,)
                    next_point = self.db.get(next_cmd, tid, end_time_, end_time_+60*60*24)
                    start_time_ = last_point['timestamp'] if last_point else start_time_
                    end_time_ = next_point['timestamp'] if next_point else end_time_

                    re = {} 
                    re['name'] = str(day)
                    distance = Decimal() 
                    points = self.db.query(sql_cmd, tid, start_time_, end_time_)
                    for i in range(len(points)-1):
                        if points[i].longitude and points[i].latitude and \
                           points[i+1].longitude and points[i+1].latitude:
                            dis = get_distance(points[i].longitude, points[i].latitude,
                                               points[i+1].longitude, points[i+1].latitude) 
                            distance += Decimal(str(dis)) 
                    # meter --> km
                    distance = '%0.1f' % (distance/1000,)      
                    if float(distance) == 0:
                        distance = 0

                    graphics.append(float(distance))
                        
                    re['mileage'] = distance 
                    res.append(re)

                counts = [float(dis_sum),]

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
            
            self.redis.setvalue(mem_key, (res, counts, label, statistics_type), time=UWEB.STATISTIC_INTERVAL)

            res= res[page_number*page_size:(page_number+1)*page_size]

            self.write_ret(status, 
                           dict_=dict(res=res, 
                                      counts=counts,
                                      graphics=graphics,
                                      pagecnt=page_count,
                                      hash_=hash_)) 
        except Exception as e:
            logging.exception("[UWEB] uid:%s, tid:%s statistic failed. Exception: %s",
                              self.current_user.uid, self.current_user.tid, e.args)
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)

class MileageSingleDownloadHandler(MileageSingleHandler):

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
                logging.exception("[UWEB] mileage single export excel failed, find no res by hash_:%s", hash_)
                self.render("error.html",
                            message=ErrorCode.ERROR_MESSAGE[ERRORCODE.EXPORT_FAILED],
                            home_url=ConfHelper.UWEB_CONF.url_out)
                return 
            results, counts, label, statistics_type = res

            date_style = xlwt.easyxf(num_format_str='YYYY-MM-DD HH:mm:ss')
            
            wb = xlwt.Workbook()
            ws = wb.add_sheet(EXCEL.MILEAGE_STATISTIC_SHEET_SINGLE)

            start_line = 0
            if statistics_type == UWEB.STATISTICS_TYPE.YEAR:
                for i, head in enumerate(EXCEL.MILEAGE_SINGLE_YEARLY_STATISTIC_HEADER):
                    ws.write(0, i, head)
            elif statistics_type == UWEB.STATISTICS_TYPE.MONTH:
                for i, head in enumerate(EXCEL.MILEAGE_SINGLE_MONTHLY_STATISTIC_HEADER):
                    ws.write(0, i, head)

            start_line += 1
            for i, result in zip(range(start_line, len(results) + start_line), results):
                ws.write(i, 0, result['name'])
                ws.write(i, 1, result['mileage'])
            last_row = len(results) + start_line
            ws.write(last_row, 0, u'合计')
            ws.write(last_row, 1, counts[0])

            _tmp_file = StringIO()
            wb.save(_tmp_file)
            filename = self.generate_file_name(label+EXCEL.MILEAGE_STATISTIC_FILE_NAME_SINGLE)
            
            self.set_header('Content-Type', 'application/force-download')
            self.set_header('Content-Disposition', 'attachment; filename=%s.xls' % (filename,))

            # move the the begging. 
            _tmp_file.seek(0, SEEK_SET)
            self.write(_tmp_file.read())
            _tmp_file.close()
 
        except Exception as e:
            logging.exception("[UWEB] Mileage single statistic  export excel failed, Exception: %s", e.args)
            self.render("error.html",
                        message=ErrorCode.ERROR_MESSAGE[ErrorCode.EXPORT_FAILED],
                        home_url=ConfHelper.UWEB_CONF.url_out)
