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
from excelheaders import DAILY_HEADER, DAILY_SHEET, DAILY_FILE_NAME
from base import BaseHandler, authenticated

from checker import check_areas, check_privileges
from constants import PRIVILEGES, SMS
from utils.misc import str_to_list, DUMMY_IDS
from myutils import city_list
from mongodb.mdaily import MDaily, MDailyMixin


class DailyMixin(BaseMixin):

    KEY_TEMPLATE = "daily_report_%s_%s"

    def prepare_data(self, hash_):

        mem_key = self.get_memcache_key(hash_)
        
        data = self.redis.getvalue(mem_key)
        if data:
            return data

        city = self.get_argument('cities', 0)
        start_time = int(self.get_argument('start_time', None))
        end_time = int(self.get_argument('end_time', None))
        s_time = time.strftime("%Y%m%d%H%M%S0000", time.localtime(start_time/1000))
        e_time = time.strftime("%Y%m%d%H%M%S0000", time.localtime(end_time/1000))
        # the result of today is inavaliable
        d = datetime.datetime.fromtimestamp(time.time())
        t = datetime.datetime.combine(datetime.date(d.year,d.month, d.day), datetime.time(0, 0, 0))
        today_ = int(time.mktime(t.timetuple())) * 1000
        if start_time >= today_ or end_time >= today_:
            return [], [start_time, end_time]

        results = []
        counts = DotDict(total_groups=0,
                         total_targets=0,
                         new_targets=0)

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
            total_groups = self.db.query("SELECT xxt_id FROM T_XXT_GROUP"
                                         "  WHERE city_id = %s"
                                         "    AND timestamp <= %s",
                                         c.region_code, e_time)
            group_ids = [int(group.xxt_id) for group in total_groups]
            total_targets = self.db.get("SELECT count(*) AS count FROM T_XXT_TARGET"
                                        "  WHERE group_id IN %s"
                                        "    AND optype IN %s"
                                        "    AND timestamp <= %s",
                                        tuple(group_ids + DUMMY_IDS),
                                        optype_status, e_time)
            new_targets = self.db.get("SELECT count(*) AS count FROM T_XXT_TARGET"
                                      "  WHERE group_id IN %s"
                                      "    AND optype = %s"
                                      "    AND timestamp BETWEEN %s AND %s",
                                      tuple(group_ids + DUMMY_IDS),
                                      XXT.OPER_TYPE.CREATE, s_time, e_time)
            result = DotDict(id=i+1,
                             city=c.city_name,
                             total_groups=len(total_groups),
                             total_targets=total_targets.count,
                             new_targets=new_targets.count)
            results.append(result)
            for key in counts:
                counts[key] += result[key]

        self.redis.setvalue(mem_key,(results, counts, [start_time,]), 
                            time=self.MEMCACHE_EXPIRY)
        return results, counts, [start_time,]


class DailyHandler(BaseHandler, DailyMixin):

    @authenticated
    @check_privileges([PRIVILEGES.DAILY_STATISTIC])
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
    @check_privileges([PRIVILEGES.DAILY_STATISTIC])
    @tornado.web.removeslash
    def get(self):

        self.render('report/daily.html',
                    results=[],
                    cities=self.cities,
                    interval=[],
                    counts={},
                    hash_=None)

    @authenticated
    @check_privileges([PRIVILEGES.DAILY_STATISTIC])
    #@check_areas()
    @tornado.web.removeslash
    def post(self):

        m = hashlib.md5()
        m.update(self.request.body)
        hash_ = m.hexdigest()
        results, counts, interval = self.prepare_data(hash_)

        self.render('report/daily.html',
                    results=results,
                    counts=counts,
                    cities=self.cities,
                    interval=interval,
                    hash_=hash_)


class DailyDownloadHandler(BaseHandler, DailyMixin):

    @authenticated
    @tornado.web.removeslash
    def get(self, hash_):

        mem_key = self.get_memcache_key(hash_)

        r = self.redis.getvalue(mem_key)
        if r:
            results, counts = r[0], r[1]
            start_time = r[2][0]
        else:
            self.render("errors/download.html")
            return

        import xlwt
        from cStringIO import StringIO

        date_style = xlwt.easyxf(num_format_str='YYYY-MM-DD HH:mm:ss')
        
        wb = xlwt.Workbook()
        ws = wb.add_sheet(DAILY_SHEET)

        start_line = 0
        for i, head in enumerate(DAILY_HEADER):
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
        filename = self.generate_file_name(DAILY_FILE_NAME)
        if start_time:
            s_time = time.strftime("%Y%m%d", time.localtime(start_time/1000))
            filename = s_time[:4] + u'年' + s_time[4:6] + u'月' + s_time[6:] + u'日' + filename

        
        self.set_header('Content-Type', 'application/force-download')
        self.set_header('Content-Disposition', 'attachment; filename=%s.xls' % (filename,))

        # move the the begging. 
        _tmp_file.seek(0, SEEK_SET)
        self.write(_tmp_file.read())
        _tmp_file.close()
