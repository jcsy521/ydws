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

        start_time = int(self.get_argument('start_time', None))
        end_time = start_time + 60 * 60 * 24
        
        businesses = self.db.query("SELECT tc.name AS corp_name, tti.owner_mobile AS umobile, tti.mobile AS tmobile, tti.begintime"
                                   "  FROM T_CORP tc, T_GROUP tg, T_TERMINAL_INFO tti"
                                   "  WHERE tti.group_id = tg.id"
                                   "  AND tg.corp_id = tc.cid"
                                   "  AND tti.begintime BETWEEN %s AND %s",
                                   start_time, end_time)
        
        result = self.db.get("SELECT count(tti.id) AS counts"
                             "  FROM T_CORP tc, T_GROUP tg, T_TERMINAL_INFO tti"
                             "  WHERE tti.group_id = tg.id"
                             "  AND tg.corp_id = tc.cid"
                             "  AND tti.begintime BETWEEN %s AND %s",
                             start_time, end_time)
        if result and result.counts:
            for i, business in enumerate(businesses):
                business['seq'] = i + 1
                for key in business:
                    if business[key] is None:
                        business[key] = ''
        
            self.redis.setvalue(mem_key,(businesses, result.counts, [start_time,]), 
                                time=self.MEMCACHE_EXPIRY)
            return businesses, result.counts, [start_time,]
        else:
            return [], 0, [start_time,]


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
                    businesses=[],
                    counts=0,
                    interval=[],
                    hash_=None)

    @authenticated
    @check_privileges([PRIVILEGES.DAILY_STATISTIC])
    #@check_areas()
    @tornado.web.removeslash
    def post(self):

        m = hashlib.md5()
        m.update(self.request.body)
        hash_ = m.hexdigest()
        businesses, counts, interval = self.prepare_data(hash_)
        
        self.render('report/daily.html',
                    interval=interval, 
                    businesses=businesses,
                    counts=counts,
                    hash_=hash_)


class DailyDownloadHandler(BaseHandler, DailyMixin):

    @authenticated
    @tornado.web.removeslash
    def get(self, hash_):

        mem_key = self.get_memcache_key(hash_)

        r = self.redis.getvalue(mem_key)
        if r:
            results, counts, start_time = r[0], r[1], r[2][0]
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
            ws.write(i, 0, result['seq'])
            ws.write(i, 1, result['corp_name'])
            ws.write(i, 2, result['umobile'])
            ws.write(i, 3, result['tmobile'])
            
            b_time = time.strftime("%Y%m%d%H%M%S", time.localtime(result['begintime']))
            begintime = b_time[:4] + u'年' + b_time[4:6] + u'月' + b_time[6:8] + u'日 ' + b_time[8:10] + u'时' + b_time[10:12] + u'分' + b_time[12:14] + u'秒' 
            ws.write(i, 4, begintime)
        last_row = len(results) + start_line
        ws.write(last_row, 0, u'合计')
        ws.write(last_row, 1, counts) 

        _tmp_file = StringIO()
        wb.save(_tmp_file)
        filename = self.generate_file_name(DAILY_FILE_NAME)
        if start_time:
            s_time = time.strftime("%Y%m%d", time.localtime(start_time))
            filename = s_time[:4] + u'年' + s_time[4:6] + u'月' + s_time[6:] + u'日' + filename

        self.set_header('Content-Type', 'application/force-download')
        self.set_header('Content-Disposition', 'attachment; filename=%s.xls' % (filename,))

        # move the the begging. 
        _tmp_file.seek(0, SEEK_SET)
        self.write(_tmp_file.read())
        _tmp_file.close()
