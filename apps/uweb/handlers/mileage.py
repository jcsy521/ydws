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
from utils.misc import DUMMY_IDS, str_to_list, start_end_of_year, start_end_of_month, start_end_of_day, start_end_of_quarter, days_of_month
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
    def post(self):
        """
        """
        status = ErrorCode.SUCCESS
        try:
            data = DotDict(json_decode(self.request.body))
            page_size = UWEB.LIMIT.PAGE_SIZE
            page_number = int(data.pagenum)
            page_count = int(data.pagecnt)
            start_time= data.start_time
            end_time = data.end_time
            tids = str_to_list(data.tids)
            logging.info("[UWEB] mileage request: %s, cid: %s, oid: %s", 
                         data, self.current_user.cid, self.current_user.oid)
        except Exception as e:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            self.write_ret(status)
            return

        try:
            # the interval between start_time and end_time is one week

            if self.current_user.cid != UWEB.DUMMY_CID: # no checks for  enterprise
                pass
            elif (int(end_time) - int(start_time)) > UWEB.QUERY_INTERVAL:
                self.write_ret(ErrorCode.QUERY_INTERVAL_EXCESS)
                return

            if page_count == -1:
                count = len(tids)
                d, m = divmod(count, page_size)
                page_count = (d + 1) if m else d

            reports = []
            interval = [start_time, end_time]
            for tid in tids:
                distance = 0
                points = self.db.query("SELECT longitude, latitude FROM T_LOCATION"
                                       "  WHERE tid = %s"
                                       "    AND (timestamp BETWEEN %s AND %s)"
                                       "    AND type = 0"
                                       "  ORDER BY timestamp asc",
                                       tid, start_time, end_time)
                for i in range(len(points)-1):
                    if points[i].longitude and points[i].latitude and \
                       points[i+1].longitude and points[i+1].latitude:
                        distance += get_distance(points[i].longitude, points[i].latitude,
                                                 points[i+1].longitude, points[i+1].latitude) 
                # meter --> km
                distance = '%0.1f' % (distance/1000,)
                alias = QueryHelper.get_alias_by_tid(tid, self.redis, self.db)
                dct = dict(tid=tid,
                           alias=alias,
                           distance=distance)
                reports.append(dct)

            # orgnize and store the data to be downloaded 
            m = hashlib.md5()
            m.update(self.request.body)
            hash_ = m.hexdigest()
            mem_key = self.KEY_TEMPLATE % (self.current_user.uid, hash_)
            
            res = [reports, interval]
            self.redis.setvalue(mem_key, res, time=UWEB.STATISTIC_INTERVAL)

            reports= reports[(page_number * page_size):((page_number+1) * page_size)]

            self.write_ret(status,
                           dict_=DotDict(res=reports,
                                         pagecnt=page_count,
                                         hash_=hash_))
        except Exception as e:
            logging.exception("[UWEB] cid:%s, oid:%s get mileage report failed. Exception: %s",
                              self.current_user.cid, self.current_user.oid, e.args)
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)

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

            results, interval = self.redis.getvalue(mem_key)
            if not results:
                logging.exception("[UWEB] mileage statistic export excel failed, find no res by hash_:%s", hash_)
                self.render("error.html",
                            message=ErrorCode.ERROR_MESSAGE[ErrorCode.EXPORT_FAILED],
                            home_url=ConfHelper.UWEB_CONF.url_out)
                return

            date_style = xlwt.easyxf(num_format_str='YYYY-MM-DD HH:mm:ss')
            
            wb = xlwt.Workbook()
            ws = wb.add_sheet(EXCEL.MILEAGE_STATISTIC_SHEET)

            start_line = 0
            for i, head in enumerate(EXCEL.MILEAGE_STATISTIC_HEADER):
                ws.write(0, i, head)
                ws.col(0).width = 4000

            start_line += 1
            for i, result in zip(range(start_line, len(results) + start_line), results):
                ws.write(i, 0, result['alias'])
                ws.write(i, 1, result['distance'])

            _tmp_file = StringIO()
            wb.save(_tmp_file)
            filename = self.generate_file_name(EXCEL.MILEAGE_STATISTIC_FILE_NAME)
            
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
        """Provide some statistics about terminals.
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
                    distance = 0
                    points = self.db.query(sql_cmd, tid, start_time_, end_time_)
                    for i in range(len(points)-1):
                        if points[i].longitude and points[i].latitude and \
                           points[i+1].longitude and points[i+1].latitude:
                            distance += get_distance(points[i].longitude, points[i].latitude,
                                                     points[i+1].longitude, points[i+1].latitude) 
                    # meter --> km
                    distance = '%0.1f' % (distance/1000,)      
                        
                    graphics.append(float(distance))
                    dis_sum += Decimal(distance)

                    re['mileage'] = distance 
                    res.append(re)

                counts = [float(dis_sum),]

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
                    distance = 0
                    points = self.db.query(sql_cmd, tid, start_time_, end_time_)
                    for i in range(len(points)-1):
                        if points[i].longitude and points[i].latitude and \
                           points[i+1].longitude and points[i+1].latitude:
                            distance += get_distance(points[i].longitude, points[i].latitude,
                                                     points[i+1].longitude, points[i+1].latitude) 
                    # meter --> km
                    #dis_sum += distance
                    #graphics.append(distance)
                    distance = '%0.1f' % (distance/1000,)      

                    graphics.append(float(distance))
                    dis_sum += Decimal(distance)
                        
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
            ws = wb.add_sheet(EXCEL.MILEAGE_STATISTIC_SHEET)

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
            filename = self.generate_file_name(label+EXCEL.MILEAGE_STATISTIC_FILE_NAME)
            
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
