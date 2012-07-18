# -*- coding: utf-8 -*-

from os import SEEK_SET
import datetime, time
import logging
import hashlib

import tornado.web
from tornado.escape import json_decode, json_encode

from constants import LOCATION, XXT
from utils.dotdict import DotDict

from mixin import BaseMixin
from excelheaders import BUSINESS_HEADER, BUSINESS_SHEET, BUSINESS_FILE_NAME
from base import BaseHandler, authenticated

from checker import check_areas, check_privileges
from constants import PRIVILEGES, SMS
from utils.misc import str_to_list, DUMMY_IDS
from myutils import city_list
from mongodb.mdaily import MDaily, MDailyMixin


class BusinessMixin(BaseMixin):

    KEY_TEMPLATE = "business_report_%s_%s"

    def prepare_data(self, hash_):

        mem_key = self.get_memcache_key(hash_)
        
        data = self.memcached.get(mem_key)
        if data:
            return data

        results = []
        counts = DotDict(new_groups=0,
                         new_targets=0,
                         cancel_targets=0,
                         new_plan1=0,
                         new_plan2=0,
                         new_plan3=0)

        start_time = int(self.get_argument('start_time', None))
        end_time = int(self.get_argument('end_time', None))
        interval = [start_time, end_time]
        s_time = time.strftime("%Y%m%d%H%M%S0000", time.localtime(start_time/1000))
        e_time = time.strftime("%Y%m%d%H%M%S0000", time.localtime(end_time/1000))

        for i, city in enumerate(self.cities):
            c = self.db.get("SELECT city_name, region_code FROM T_HLR_CITY"
                            "  WHERE city_id = %s",
                            city.city_id)
            new_groups = self.db.get("SELECT count(*) AS count FROM T_XXT_GROUP"
                                     "  WHERE city_id = %s"
                                     "    AND timestamp BETWEEN %s AND %s",
                                     c.region_code, s_time, e_time)
            total_groups = self.db.query("SELECT xxt_id FROM T_XXT_GROUP"
                                         "  WHERE city_id = %s",
                                         c.region_code)
            group_ids = [int(group.xxt_id) for group in total_groups]
            new_targets = self.db.query("SELECT id, plan_id FROM T_XXT_TARGET"
                                        "  WHERE group_id IN %s"
                                        "    AND optype = %s"
                                        "    AND timestamp BETWEEN %s AND %s",
                                        tuple(group_ids + DUMMY_IDS),
                                        XXT.OPER_TYPE.CREATE, s_time, e_time)
            plans = [target.plan_id for target in new_targets]
            cancel_targets = self.db.get("SELECT count(*) AS count FROM T_XXT_TARGET"
                                         "  WHERE group_id IN %s"
                                         "    AND optype = %s"
                                         "    AND timestamp BETWEEN %s AND %s",
                                         tuple(group_ids + DUMMY_IDS),
                                         XXT.OPER_TYPE.CANCEL, s_time, e_time)

            result = DotDict(id=i+1,
                             city=c.city_name,
                             new_groups=new_groups.count,
                             new_targets=len(new_targets),
                             cancel_targets=cancel_targets.count,
                             new_plan1=plans.count('40102908')+plans.count('40102918'),
                             new_plan2=plans.count('40102905')+plans.count('40102915'),
                             new_plan3=plans.count('40102906')+plans.count('40102916'))
            results.append(result)
            for key in counts:
                counts[key] += result[key]

        self.memcached.set(mem_key,(results, counts, interval), 
                           time=self.MEMCACHE_EXPIRY)
        return results, counts, interval


class BusinessHandler(BaseHandler, BusinessMixin):

    @authenticated
    @check_privileges([PRIVILEGES.BUSINESS_STATISTIC])
    @tornado.web.removeslash
    def prepare(self):

        key = self.get_area_memcache_key(self.current_user.id)
        areas = self.memcached.get(key)
        if not areas:
            areas = self.get_privilege_area(self.current_user.id)
            self.memcached.set(key, areas)
        self.cities = areas
        res  = self.db.get("SELECT type FROM T_ADMINISTRATOR"
                           "  WHERE id = %s", self.current_user.id)
        self.type = res.type


    @authenticated
    @check_privileges([PRIVILEGES.BUSINESS_STATISTIC])
    @tornado.web.removeslash
    def get(self):

        self.render('report/business.html',
                    results=[],
                    interval=[],
                    counts={},
                    type=self.type,
                    hash_=None)

    @authenticated
    @check_privileges([PRIVILEGES.BUSINESS_STATISTIC])
    #@check_areas()
    @tornado.web.removeslash
    def post(self):

        m = hashlib.md5()
        m.update(self.request.body)
        hash_ = m.hexdigest()
        results, counts, interval = self.prepare_data(hash_)

        self.render('report/business.html',
                    results=results,
                    counts=counts,
                    interval=interval,
                    type=self.type,
                    hash_=hash_)


class BusinessDownloadHandler(BaseHandler, BusinessMixin):

    @authenticated
    @tornado.web.removeslash
    def get(self, hash_):

        mem_key = self.get_memcache_key(hash_)

        r = self.memcached.get(mem_key)
        if r:
            results, counts = r[0], r[1]
        else:
            self.render("errors/download.html")
            return

        import xlwt
        from cStringIO import StringIO

        date_style = xlwt.easyxf(num_format_str='YYYY-MM-DD HH:mm:ss')
        
        wb = xlwt.Workbook()
        ws = wb.add_sheet(BUSINESS_SHEET)

        start_line = 0
        for i, head in enumerate(BUSINESS_HEADER):
            ws.write(0, i, head)

        start_line += 1
        for i, result in zip(range(start_line, len(results) + start_line), results):
            ws.write(i, 0, result['city'])
            ws.write(i, 1, result['new_groups'])
            ws.write(i, 2, result['new_targets'])
            ws.write(i, 3, result['cancel_targets'])
            ws.write(i, 4, result['new_plan1'])
            ws.write(i, 5, result['new_plan2'])
            ws.write(i, 6, result['new_plan3'])
        last_row = len(results) + start_line
        ws.write(last_row, 0, u'合计')
        ws.write(last_row, 1, counts['new_groups']) 
        ws.write(last_row, 2, counts['new_targets']) 
        ws.write(last_row, 3, counts['cancel_targets'])
        ws.write(last_row, 4, counts['new_plan1'])
        ws.write(last_row, 5, counts['new_plan2'])
        ws.write(last_row, 6, counts['new_plan3'])

        _tmp_file = StringIO()
        wb.save(_tmp_file)
        filename = self.generate_file_name(BUSINESS_FILE_NAME)

        
        self.set_header('Content-Type', 'application/force-download')
        self.set_header('Content-Disposition', 'attachment; filename=%s.xls' % (filename,))

        # move the the begging. 
        _tmp_file.seek(0, SEEK_SET)
        self.write(_tmp_file.read())
        _tmp_file.close()
