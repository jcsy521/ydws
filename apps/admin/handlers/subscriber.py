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


class SubscriberMixin(BaseMixin):

    KEY_TEMPLATE = "subscriber_report_%s_%s"
    

    def prepare_data(self, hash_):

        mem_key = self.get_memcache_key(hash_)
        data = self.redis.getvalue(mem_key)
        data = None
        if data:
            return data

        city = self.get_argument('cities', 0)
        start_time = int(self.get_argument('start_time'))
        end_time = int(self.get_argument('end_time'))
        interval = [start_time, end_time]
        start_time = time.strftime("%Y%m%d%H%M%S0000", time.localtime(start_time/1000)) 
        end_time = time.strftime("%Y%m%d%H%M%S0000", time.localtime(end_time/1000)) 

        results = []
        counts = DotDict(group=0,
                         target=0,
                         plan1=0,
                         plan2=0,
                         plan3=0)
        if int(city) == 0:
            cities = [city.city_id for city in self.cities]
        else:
            cities = [city,] 

        cities = [int(c) for c in cities]
        optype_status = (XXT.OPER_TYPE.CREATE,
                         XXT.OPER_TYPE.RESUME,
                         XXT.OPER_TYPE.UPDATE)
        for i, city in enumerate(cities):
            c = self.db.get("SELECT city_name, region_code FROM T_HLR_CITY"
                            "  WHERE city_id = %s",
                            city)
            if self.type == "1":
                groups = self.db.query("SELECT txg.xxt_id"
                                       "  FROM T_XXT_GROUP AS txg, T_ADMINISTRATOR AS ta"
                                       "  WHERE txg.city_id = %s"
                                       "    AND txg.phonenum = ta.login"
                                       "    AND txg.timestamp BETWEEN %s AND %s"
                                       "    AND ta.id = %s",
                                       c.region_code, start_time, end_time,
                                       self.current_user.id)
            else:
                groups = self.db.query("SELECT xxt_id FROM T_XXT_GROUP"
                                       "  WHERE city_id = %s"
                                       "    AND timestamp BETWEEN %s AND %s",
                                       c.region_code, start_time, end_time)
            group_ids = [int(group.xxt_id) for group in groups]
            targets = self.db.query("SELECT id, plan_id FROM T_XXT_TARGET"
                                    "  WHERE group_id IN %s"
                                    "    AND timestamp BETWEEN %s AND %s"
                                    "    AND optype IN %s",
                                    tuple(group_ids + DUMMY_IDS), start_time,
                                    end_time, optype_status)
            plans = [target.plan_id for target in targets]
            result = DotDict(id=i+1,
                             city=c.city_name,
                             group=len(groups),
                             target=len(targets),
                             plan1=plans.count('40102908')+plans.count('40102918'),
                             plan2=plans.count('40102905')+plans.count('40102915'),
                             plan3=plans.count('40102906')+plans.count('40102916'))
            results.append(result)
            for key in counts:
                counts[key] += result[key]
        self.redis.setvalue(mem_key, (results, counts, interval), time=self.MEMCACHE_EXPIRY)

        return results, counts, interval


class SubscriberHandler(BaseHandler, SubscriberMixin):

    @authenticated
    @check_privileges([PRIVILEGES.COUNT_USER])
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
    @check_privileges([PRIVILEGES.COUNT_USER])
    @tornado.web.removeslash
    def get(self):
        self.render("report/subscriber.html",
                    results=[],
                    counts=[],
                    cities=self.cities, 
                    interval=[],
                    hash_=None)

    @authenticated
    @check_privileges([PRIVILEGES.COUNT_USER])
    #@check_areas()
    @tornado.web.removeslash
    def post(self):
        m = hashlib.md5()
        m.update(self.request.body)
        hash_ = m.hexdigest()
        results, counts, interval = self.prepare_data(hash_)

        self.render("report/subscriber.html",
                    results=results,
                    cities=self.cities,
                    counts=counts,
                    interval=interval,
                    hash_=hash_)

 
class SubscriberDownloadHandler(BaseHandler, SubscriberMixin):

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
