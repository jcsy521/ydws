# -*- coding: utf-8 -*-

import logging 
import hashlib
from os import SEEK_SET
import time
from datetime import date
from calendar import monthrange

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
from myutils import city_list, start_of_month, end_of_month, start_end_of_month
from mongodb.mmonthly import MMonthly, MMonthlyMixin


class MonthlyMixin(BaseMixin):

    KEY_TEMPLATE = "monthly_report_%s_%s"

    def prepare_data(self, hash_):

        mem_key = self.get_memcache_key(hash_)
        
        data = self.redis.getvalue(mem_key)
        if data:
            return data

        city = self.get_argument('cities', 0)
        start_time = int(self.get_argument('timestamp', None))
        end_time = end_of_month(start_time)

        s_time = start_of_month(int(time.time()) * 1000)
        if start_time >= s_time:
            return [], start_time

        results = []
        if int(city) == 0:
            cities = [city.city_id for city in self.cities]
        else:
            cities = [city,]

        cities = [int(c) for c in cities]
        for i, city in enumerate(cities):
            c = self.db.get("SELECT city_name, region_code FROM T_HLR_CITY"
                            "  WHERE city_id = %s",
                            city)
            total_corps = self.db.query("SELECT id FROM T_XXT_CORP")
            new_corps = self.db.query("SELECT id FROM T_XXT_CORP"
                                      "  WHERE AND timestamp <= %s",
                                      e_time)
            
            total_terminals = self.db.get("SELECT id FROM T_TERMINAL_INFO")
            new_terminals = self.db.get("SELECT id FROM T_TERMINAL_INFO"
                                        "  WHERE begintime <= %s",
                                        e_time)
            result = DotDict(seq=i+1,
                             city=c.city_name,
                             new_corps=len(new_corps),
                             total_corps=len(total_corps),
                             new_terminals=len(new_terminals),
                             total_terminals=len(total_terminals))
            results.append(result)

        self.redis.setvalue(mem_key, (results, start_time), 
                           time=self.MEMCACHE_EXPIRY)
        return results, start_time


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
                    cities=self.cities,
                    interval=[],
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
                    cities=self.cities,
                    interval=[timestamp],
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
            y_m = time.strftime('%Y%m', time.localtime(int(timestamp/1000)))
            filename = y_m[:4] + u'年' + y_m[4:] + u'月份' + filename

        date_style = xlwt.easyxf(num_format_str='YYYY-MM-DD HH:mm:ss')
        wb = xlwt.Workbook()
        ws = wb.add_sheet(MONTHLY_SHEET)

        start_line = 0
        for i, head in enumerate(MONTHLY_HEADER):
            ws.write(0, i, head)
        start_line += 1
        for i, result in zip(range(start_line, len(results) + start_line), results):
            ws.write(i, 0, result['city'])
            ws.write(i, 1, result['total_groups'])
            ws.write(i, 2, result['total_targets'])
            ws.write(i, 3, result['new_targets'])
        last_row = len(results) + start_line
        ws.write(last_row, 0, u'合计')
        ws.write(last_row, 1, counts['total_groups']) 
        ws.write(last_row, 2, counts['total_targets']) 
        ws.write(last_row, 3, counts['new_targets'])

        _tmp_file = StringIO()
        wb.save(_tmp_file)
        
        filename = self.generate_file_name(filename)

        self.set_header('Content-Type', 'application/force-download')
        self.set_header('Content-Disposition', 'attachment; filename=%s.xls' % (filename,))

        # move the the begging. 
        _tmp_file.seek(0, SEEK_SET)
        self.write(_tmp_file.read())
        _tmp_file.close()
