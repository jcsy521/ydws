# -*- coding: utf-8 -*-

import logging 
import hashlib
import time
from os import SEEK_SET
from datetime import date
from calendar import monthrange

import tornado.web

from constants import LOCATION, ADMIN

from mixin import BaseMixin
from excelheaders import LOCATION_HEADER, LOCATION_SHEET, LOCATION_FILE_NAME
from base import BaseHandler, authenticated

from checker import check_areas, check_privileges
from constants import PRIVILEGES
from utils.misc import str_to_list, DUMMY_IDS
from myutils import city_list, start_of_month, end_of_month, start_end_of_month
from mongodb.mlocation import MLocation, MLocationMixin


class LocationMixin(BaseMixin):

    KEY_TEMPLATE = "location_report_%s_%s"

    def prepare_data(self, hash_):

        mem_key = self.get_memcache_key(hash_)
        
        data = self.redis.getvalue(mem_key)
        if data:
            return data

        # TODO: retrieve all the cities
        # HOW TO BEST PASS province and city?
        provinces = self.get_argument('province_id', None)
        cities = self.get_argument('city_id', None)
        start_time = int(self.get_argument('timestamp', None))
        end_time = end_of_month(start_time)
        d = date.fromtimestamp(start_time/1000)
        year = d.year
        month = d.month

        # only last six days of this month can retrieve results
        s_time = start_of_month(int(time.time())*1000)
        e_time = end_of_month(int(time.time())*1000)
        
        if start_time == s_time:
            # this month
            cal = date.today().timetuple()
            year = cal.tm_year
            month = cal.tm_mon
            day = cal.tm_mday
            maxdays = monthrange(year, month)[1]
            if maxdays - day > ADMIN.MONTH_RETRIEVE_DAYS:
                return [], start_time
        elif start_time > e_time:
            return [], start_time

        if cities is None:
            provinces = str_to_list(provinces)
            cities = city_list(provinces, self.db)
        else:
            cities = str_to_list(cities)

        cities = [int(c) for c in cities]
        cs = self.db.query("SELECT DISTINCT region_code FROM T_HLR_CITY"
                           "  WHERE city_id IN %s",
                           tuple(cities + DUMMY_IDS))
        citylist = [int(c.region_code) for c in cs]

        query_term = {'city_id': {'$in': citylist}, 'year': year, 'month': month}
        try:
            results = list(self.collection.find(query_term, {'_id':0}))
            if not results:
                ins = MLocation()
                results = ins.retrieve(citylist, start_time, end_time)
        except:
            ins = MLocationMixin()
            results = ins.retrieve_mixin(citylist, start_time, end_time)

        self.redis.setvalue(mem_key, (results, start_time), 
                            time=self.MEMCACHE_EXPIRY)
        return results, start_time


class LocationHandler(BaseHandler, LocationMixin):

    @authenticated
    @check_privileges([PRIVILEGES.COUNT_LOCATION])
    @tornado.web.removeslash
    def prepare(self):
        key = self.get_area_memcache_key(self.current_user.id)
        areas = self.redis.getvalue(key)
        if not areas:
            areas = self.get_privilege_area(self.current_user.id)
            self.redis.setvalue(key, areas)
        self.areas = areas
        #self.provinces = self.db.query("SELECT province_id, province_name FROM T_HLR_PROVINCE")
        try:
            self.collection = self.mongodb.location  
        except:
            logging.exception("mongodb connected failed.") 
 
    @authenticated
    @check_privileges([PRIVILEGES.COUNT_LOCATION])
    @tornado.web.removeslash
    def get(self):

        self.render("report/location.html",
                    areas=self.areas,
                    results=[],
                    interval=[],
                    hash_=None)

    @authenticated
    @check_privileges([PRIVILEGES.COUNT_LOCATION])
    @check_areas()
    @tornado.web.removeslash
    def post(self):

        m = hashlib.md5()
        m.update(self.request.body)
        hash_ = m.hexdigest()
        results, timestamp = self.prepare_data(hash_)

        self.render("report/location.html",
                    results=results,
                    areas=self.areas, 
                    interval=[timestamp],
                    hash_=hash_)


class LocationDownloadHandler(BaseHandler, LocationMixin):

    @authenticated
    @tornado.web.removeslash
    def get(self, hash_):

        mem_key = self.get_memcache_key(hash_)
        r = self.redis.getvalue(mem_key)
        if r:
            results, timestamp = r[0], r[1]
        else:
            self.render("errors/download.html")
            return

        import xlwt
        from cStringIO import StringIO

        filename = LOCATION_FILE_NAME

        if timestamp:
            month = time.strftime('%m', time.localtime((timestamp/1000)))
            filename = month + u'月份' + filename

        date_style = xlwt.easyxf(num_format_str='YYYY-MM-DD HH:mm:ss')
        
        wb = xlwt.Workbook()
        ws = wb.add_sheet(LOCATION_SHEET)

        start_line = 0
        for i, head in enumerate(LOCATION_HEADER):
            ws.write(0, i, head)

        start_line += 1
        for i, result in zip(range(start_line, len(results) + start_line), results):
            ws.write(i, 0, result['province'])
            ws.write(i, 1, result['city'])
            ws.write(i, 2, result['group_name'])
            ws.write(i, 3, result['realtime'])
            ws.write(i, 4, result['schedule'])
            #ws.write(i, 5, result['custom'])

        _tmp_file = StringIO()
        wb.save(_tmp_file)
        filename = self.generate_file_name(filename)
         
        self.set_header('Content-Type', 'application/force-download')
        self.set_header('Content-Disposition', 'attachment; filename=%s.xls' % (filename,))

        # move the the begging. 
        _tmp_file.seek(0, SEEK_SET)
        self.write(_tmp_file.read())
        _tmp_file.close()
