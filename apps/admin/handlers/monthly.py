# -*- coding: utf-8 -*-

import logging 
import hashlib
from os import SEEK_SET
import time
import datetime

import tornado.web
from tornado.escape import json_decode, json_encode

from constants import LOCATION, XXT, ADMIN
from utils.dotdict import DotDict

from mixin import BaseMixin
from excelheaders import MONTHLY_HEADER, MONTHLY_FILE_NAME, MONTHLY_SHEET
from base import BaseHandler, authenticated

from checker import check_areas, check_privileges
from constants import PRIVILEGES, SMS
from utils.misc import str_to_list, DUMMY_IDS
from myutils import city_list, start_of_month, days_of_month, start_end_of_month
from mongodb.mmonthly import MMonthly, MMonthlyMixin


class MonthlyMixin(BaseMixin):

    KEY_TEMPLATE = "monthly_report_%s_%s"

    def prepare_data(self, hash_):

        mem_key = self.get_memcache_key(hash_)
        
        data = self.redis.getvalue(mem_key)
        if data:
            return data

        #city = self.get_argument('cities', 0)
        year = int(self.get_argument('year'))
        month = int(self.get_argument('month'))
        timestamp = [year, month]

        #s_time = start_of_month(int(time.time()))
        #if start_time >= s_time:
        #    return [], {}, start_time

        results = []
        counts = dict(new_corps=0,
                      total_corps=0,
                      new_terminals=0,
                      total_terminals=0)
        #if int(city) == 0:
        #    cities = [city.city_id for city in self.cities]
        #else:
        #    cities = [city,]

        #cities = [int(c) for c in cities]
        #for i, city in enumerate(cities):
        #    c = self.db.get("SELECT city_name, region_code FROM T_HLR_CITY"
        #                    "  WHERE city_id = %s",
        #                    city)
        days = days_of_month(year, month)
        t = datetime.datetime.combine(datetime.date(year, month, 1), datetime.time(0, 0))
        s_time = int(time.mktime(t.timetuple()))
        current_time = int(time.time())
        for day in range(days):
            start_time = int(s_time) + day * 86400 
            end_time = start_time + 86399 
            if start_time >= current_time:
                break
            total_corps = self.db.query("SELECT id FROM T_CORP WHERE timestamp <= %s", end_time)
            new_corps = self.db.query("SELECT id FROM T_CORP"
                                      "  WHERE timestamp BETWEEN %s AND %s",
                                      start_time, end_time)
            
            total_terminals = self.db.query("SELECT id FROM T_TERMINAL_INFO WHERE begintime <= %s", end_time)
            new_terminals = self.db.query("SELECT id FROM T_TERMINAL_INFO"
                                          "  WHERE begintime BETWEEN %s AND %s",
                                          start_time, end_time)
            result = dict(seq=day+1,
                          new_corps=len(new_corps),
                          total_corps=len(total_corps),
                          new_terminals=len(new_terminals),
                          total_terminals=len(total_terminals))
            results.append(result)
            counts['new_corps'] += len(new_corps)
            counts['new_terminals'] += len(new_terminals)
        counts['total_corps'] = results[len(results)-1]['total_corps']
        counts['total_terminals'] = results[len(results)-1]['total_terminals']

        self.redis.setvalue(mem_key, (results, counts, timestamp), 
                            time=self.MEMCACHE_EXPIRY)

        return results, counts, timestamp 


class MonthlyHandler(BaseHandler, MonthlyMixin):

    @authenticated
    @check_privileges([PRIVILEGES.MONTHLY_STATISTIC])
    @tornado.web.removeslash
    def prepare(self):

        key = self.get_area_memcache_key(self.current_user.id)
        areas = self.redis.getvalue(key)
        if not areas:
            areas = self.get_privilege_area(self.current_user.id)
            self.redis.setvalue(key, areas)
        self.cities = areas
        res  = self.db.get("SELECT type FROM T_ADMINISTRATOR"
                           "  WHERE id = %s", self.current_user.id)
        self.type = res.type


    @authenticated
    @check_privileges([PRIVILEGES.MONTHLY_STATISTIC])
    @tornado.web.removeslash
    def get(self):

        self.render('report/monthly.html',
                    results=[],
                    counts={},
                    cities=self.cities,
                    timestamp=[],
                    type=self.type,
                    hash_=None)

    @authenticated
    @check_privileges([PRIVILEGES.MONTHLY_STATISTIC])
    #@check_areas()
    @tornado.web.removeslash
    def post(self):

        m = hashlib.md5()
        m.update(self.request.body)
        hash_ = m.hexdigest()
        results, counts, timestamp = self.prepare_data(hash_)

        self.render('report/monthly.html',
                    results=results,
                    counts=counts,
                    cities=self.cities,
                    timestamp=timestamp,
                    type=self.type,
                    hash_=hash_)
 

class MonthlyDownloadHandler(BaseHandler, MonthlyMixin):

    @authenticated
    @tornado.web.removeslash
    def get(self, hash_):

        mem_key = self.get_memcache_key(hash_)

        r = self.redis.getvalue(mem_key)
        if r:
            results, counts, timestamp = r[0], r[1], r[2]
        else:
            self.render("errors/download.html")
            return

        import xlwt
        from cStringIO import StringIO

        filename = MONTHLY_FILE_NAME

        if timestamp:
            filename = str(timestamp[0]) + u'年' + str(timestamp[1]) + u'月份' + filename

        date_style = xlwt.easyxf(num_format_str='YYYY-MM-DD HH:mm:ss')
        wb = xlwt.Workbook()
        ws = wb.add_sheet(MONTHLY_SHEET)

        start_line = 0
        for i, head in enumerate(MONTHLY_HEADER):
            ws.write(0, i, head)
        start_line += 1
        for i, result in zip(range(start_line, len(results) + start_line), results):
            ws.write(i, 0, result['seq'])
            ws.write(i, 1, result['new_corps'])
            ws.write(i, 2, result['total_corps'])
            ws.write(i, 3, result['new_terminals'])
            ws.write(i, 4, result['total_terminals'])
        last_row = len(results) + start_line
        ws.write(last_row, 0, u'合计')
        ws.write(last_row, 1, counts['new_corps']) 
        ws.write(last_row, 2, counts['total_corps']) 
        ws.write(last_row, 3, counts['new_terminals']) 
        ws.write(last_row, 4, counts['total_terminals'])

        _tmp_file = StringIO()
        wb.save(_tmp_file)
        
        filename = self.generate_file_name(filename)

        self.set_header('Content-Type', 'application/force-download')
        self.set_header('Content-Disposition', 'attachment; filename=%s.xls' % (filename,))

        # move the the begging. 
        _tmp_file.seek(0, SEEK_SET)
        self.write(_tmp_file.read())
        _tmp_file.close()
