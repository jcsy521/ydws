# -*- coding: utf-8 -*-

import logging 
import os.path
import site

TOP_DIR_ = os.path.abspath(os.path.join(__file__, ".."))
site.addsitedir(TOP_DIR_)

import hashlib
from os import SEEK_SET
import time
from datetime import date
from calendar import monthrange

import tornado.web

from constants import XXT, ADMIN
from utils.dotdict import DotDict

from checker import check_areas, check_privileges
from constants import PRIVILEGES
from utils.misc import str_to_list, DUMMY_IDS
from myutils import city_list, start_of_month, end_of_month, start_end_of_month

from mixin import BaseMixin
from excelheaders import SUBSCRIBER_HEADER, SUBSCRIBER_SHEET, SUBSCRIBER_FILE_NAME
from base import BaseHandler, authenticated
from mongodb.msubscriber import MSubscriber, MSubscriberMixin


class ECSubscriberMixin(BaseMixin):

    KEY_TEMPLATE = "ecsubscriber_report_%s_%s"
    

    def prepare_data(self, hash_):

        mem_key = self.get_memcache_key(hash_)
        data = self.redis.getvalue(mem_key)
        data = None
        if data:
            return data

        results = []
        counts = DotDict(total_corps=0,
                         total_terminals=0)
        cities = self.get_argument('cities', 0)
        start_time = int(self.get_argument('start_time'))
        end_time = int(self.get_argument('end_time'))
        interval = [start_time, end_time]

        if int(cities) == 0:
            cities = [city.city_id for city in self.cities]
        else:
            cities = [city,] 

        cities = [int(c) for c in cities]
        for city in enumerate(cities):
            c = self.db.get("SELECT city_name FROM T_CITY WHERE city_id = %s", city)
            corps = self.db.query("SELECT id, name FROM T_CORP")
            for corp in corps:
                groups = self.db.query("SELECT id FROM T_GROUP WHERE corp_id = %s", corp.id)
                group_ids = [group.id for group in groups]
                terminals = self.db.query("SELECT id FROM T_TERMINAL_INFO"
                                          "  WHERE timestamp BETWEEN %s AND %s"
                                          "    AND group_id IN %s",
                                          start_time, end_time,
                                          tuple(group_ids + DUMMY_IDS))
                result = DotDict(city_name=c.city_name,
                                 corp_name=corp.name,
                                 total_terminals=len(terminals))
                results.append(result)
                counts.total_corps += 1
                counts.total_terminals += len(terminals)

        for i, result in enumerate(results):
            result.seq = i+1
        self.redis.setvalue(mem_key, (results, counts, interval), time=self.MEMCACHE_EXPIRY)

        return results, counts, interval


class ECSubscriberHandler(BaseHandler, ECSubscriberMixin):

    @authenticated
    @check_privileges([PRIVILEGES.COUNT_ECSUBSCRIBER])
    @tornado.web.removeslash
    def prepare(self):
        key = self.get_area_memcache_key(self.current_user.id)
        cities = self.redis.getvalue(key)
        if not cities:
            cities = self.get_privilege_area(self.current_user.id)
            self.redis.setvalue(key, cities)
        self.cities = cities
        res  = self.db.get("SELECT type FROM T_ADMINISTRATOR"
                           "  WHERE id = %s", self.current_user.id)
        self.type = res.type

    @authenticated
    @check_privileges([PRIVILEGES.COUNT_ECSUBSCRIBER])
    @tornado.web.removeslash
    def get(self):
        self.render("report/subscriber.html",
                    results=[],
                    counts={},
                    cities=self.cities, 
                    interval=[],
                    hash_=None)

    @authenticated
    @check_privileges([PRIVILEGES.COUNT_ECSUBSCRIBER])
    @tornado.web.removeslash
    def post(self):
        m = hashlib.md5()
        m.update(self.request.body)
        hash_ = m.hexdigest()
        results, counts, interval = self.prepare_data(hash_)

        self.render("report/ecsubscriber.html",
                    results=results,
                    counts=counts,
                    cities=self.cities,
                    interval=interval,
                    hash_=hash_)

 
class ECSubscriberDownloadHandler(BaseHandler, ECSubscriberMixin):

    @authenticated
    @tornado.web.removeslash
    def get(self, hash_):
        mem_key = self.get_memcache_key(hash_)
        r = self.redis.getvalue(mem_key)
        if not r:
            self.render("errors/download.html")
            return
        results, counts = r[0], r[1]

        import xlwt
        from cStringIO import StringIO

        filename = SUBSCRIBER_FILE_NAME

        wb = xlwt.Workbook()
        ws = wb.add_sheet(SUBSCRIBER_SHEET)

        start_line = 0
        for i, head in enumerate(SUBSCRIBER_HEADER):
            ws.write(0, i, head)

        start_line += 1
        for i, result in zip(range(start_line, len(results) + start_line + 1), results):
            ws.write(i, 0, result['city'])
            ws.write(i, 1, result['group'])
            ws.write(i, 2, result['target'])
            ws.write(i, 3, result['plan1'])
            ws.write(i, 4, result['plan2'])
            ws.write(i, 5, result['plan3'])
        last_row = len(results) + start_line
        ws.write(last_row, 0, u'合计')
        ws.write(last_row, 1, counts.group)
        ws.write(last_row, 2, counts.target)
        ws.write(last_row, 3, counts.plan1)
        ws.write(last_row, 4, counts.plan2)
        ws.write(last_row, 5, counts.plan3)

       
        _tmp_file = StringIO()
        wb.save(_tmp_file)
        filename = self.generate_file_name(filename)
        
        self.set_header('Content-Type', 'application/force-download')
        self.set_header('Content-Disposition', 'attachment; filename=%s.xls' % (filename,))

        # move the the begging. 
        _tmp_file.seek(0, SEEK_SET)
        self.write(_tmp_file.read())
        _tmp_file.close()
