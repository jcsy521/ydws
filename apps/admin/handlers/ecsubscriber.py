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
from excelheaders import ECSUBSCRIBER_HEADER, ECSUBSCRIBER_SHEET, ECSUBSCRIBER_FILE_NAME
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
        counts = dict(total_corps=0,
                      total_terminals=0)
        #cities = self.get_argument('cities', 0)
        #start_time = int(self.get_argument('start_time'))
        #end_time = int(self.get_argument('end_time'))
        #interval = [start_time, end_time]

        #if int(cities) == 0:
        #    cities = [city.city_id for city in self.cities]
        #else:
        #    cities = [city,] 

        #cities = [int(c) for c in cities]
        #for city in enumerate(cities):
        #    c = self.db.get("SELECT city_name FROM T_CITY WHERE city_id = %s", city)
        corps = self.get_argument('corps', 0)
        if int(corps) == 0:
            corps = self.db.query("SELECT id FROM T_CORP")
            corps = [corp.id for corp in corps]
        else:
            corps = [corps,]
        for corp in corps:
            c = self.db.get("SELECT name, cid FROM T_CORP WHERE id = %s", corp)
            groups = self.db.query("SELECT id FROM T_GROUP WHERE corp_id = %s", c.cid)
            group_ids = [group.id for group in groups]
            terminals = self.db.query("SELECT id FROM T_TERMINAL_INFO"
                                      "  WHERE group_id IN %s",
                                      tuple(group_ids + DUMMY_IDS))
            result = dict(ecname=c.name,
                          total_terminals=len(terminals))
            results.append(result)
            counts['total_corps'] += 1
            counts['total_terminals'] += len(terminals)

        for i, result in enumerate(results):
            result['seq'] = i+1
        self.redis.setvalue(mem_key, (results, counts), time=self.MEMCACHE_EXPIRY)

        return results, counts


class ECSubscriberHandler(BaseHandler, ECSubscriberMixin):

    @authenticated
    @check_privileges([PRIVILEGES.COUNT_ECSUBSCRIBER])
    @tornado.web.removeslash
    def prepare(self):
        self.corplist = self.db.query("SELECT id, name FROM T_CORP")
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
        self.render("report/ecsubscriber.html",
                    results=[],
                    counts={},
                    cities=self.cities, 
                    corplist=self.corplist,
                    hash_=None)

    @authenticated
    @check_privileges([PRIVILEGES.COUNT_ECSUBSCRIBER])
    @tornado.web.removeslash
    def post(self):
        m = hashlib.md5()
        m.update(self.request.body)
        hash_ = m.hexdigest()
        results, counts = self.prepare_data(hash_)

        self.render("report/ecsubscriber.html",
                    results=results,
                    counts=counts,
                    cities=self.cities,
                    corplist=self.corplist,
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

        filename = ECSUBSCRIBER_FILE_NAME

        wb = xlwt.Workbook()
        ws = wb.add_sheet(ECSUBSCRIBER_SHEET)

        start_line = 0
        for i, head in enumerate(ECSUBSCRIBER_HEADER):
            ws.write(0, i, head)

        start_line += 1
        for i, result in zip(range(start_line, len(results) + start_line + 1), results):
            ws.write(i, 0, result['seq'])
            ws.write(i, 1, result['ecname'])
            ws.write(i, 2, result['total_terminals'])
        last_row = len(results) + start_line
        ws.write(last_row, 0, u'合计')
        ws.write(last_row, 1, counts['total_corps'])
        ws.write(last_row, 2, counts['total_terminals'])

       
        _tmp_file = StringIO()
        wb.save(_tmp_file)
        filename = self.generate_file_name(filename)
        
        self.set_header('Content-Type', 'application/force-download')
        self.set_header('Content-Disposition', 'attachment; filename=%s.xls' % (filename,))

        # move the the begging. 
        _tmp_file.seek(0, SEEK_SET)
        self.write(_tmp_file.read())
        _tmp_file.close()
