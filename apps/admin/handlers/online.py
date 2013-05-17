# -*- coding: utf-8 -*-

from os import SEEK_SET
import datetime, time
import logging
import hashlib
from decimal import Decimal

import tornado.web
from tornado.escape import json_decode, json_encode

from constants import LOCATION, XXT
from utils.dotdict import DotDict

from mixin import BaseMixin
from excelheaders import OLINE_HEADER, OLINE_SHEET, OLINE_FILE_NAME
from base import BaseHandler, authenticated

from checker import check_areas, check_privileges
from constants import PRIVILEGES, SMS
from utils.misc import str_to_list, DUMMY_IDS
from myutils import city_list


class OlineMixin(BaseMixin):

    KEY_TEMPLATE = "online_report_%s_%s"

    def prepare_data(self, hash_):

        mem_key = self.get_memcache_key(hash_)
        
        data = self.redis.getvalue(mem_key)
        if data:
            data = eval(data)
            return data[0], data[1]

        cid = self.get_argument('cid', None)
        start_time = int(self.get_argument('begintime', None))
        end_time = int(self.get_argument('endtime', None))
        
        if cid:
            cid_condition = "  AND cid = %s" % cid
        else:
            cid_condition = ""
            
        results = self.db.query("SELECT sum(online_num) AS online_num, sum(offline_num) AS offline_num, time, (sum(online_num) + sum(offline_num)) AS total_num "
                                "  FROM T_ONLINE_STATISTIC"
                                "  WHERE time BETWEEN %s AND %s" + cid_condition + 
                                "  GROUP BY time"
                                "  ORDER BY time DESC",
                                start_time, end_time)
        
        for i, result in enumerate(results):
                result['seq'] = i + 1
                for key in result:
                    if result[key] is None:
                        result[key] = ''
                            
        self.redis.setvalue(mem_key,(results, [start_time, end_time]), 
                            time=self.MEMCACHE_EXPIRY)
        return results, [start_time, end_time]


class OnlineHandler(BaseHandler, OlineMixin):

    @authenticated
    @check_privileges([PRIVILEGES.OLINE_STATISTIC])
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
    @check_privileges([PRIVILEGES.OLINE_STATISTIC])
    @tornado.web.removeslash
    def get(self):
        
        corps = self.db.query("SELECT name AS corp_name, cid FROM T_CORP")

        self.render('report/online.html',
                    corps=corps if corps else [],
                    results=[],
                    interval=[],
                    hash_=None)


    @authenticated
    @check_privileges([PRIVILEGES.OLINE_STATISTIC])
    #@check_areas()
    @tornado.web.removeslash
    def post(self):

        m = hashlib.md5()
        m.update(self.request.body)
        hash_ = m.hexdigest()
        results, interval = self.prepare_data(hash_)
        corps = self.db.query("SELECT name AS corp_name, cid FROM T_CORP")
        
        self.render('report/online.html',
                    corps=corps, 
                    interval=interval, 
                    results=results,
                    hash_=hash_)


class OnlineDownloadHandler(BaseHandler, OlineMixin):

    @authenticated
    @tornado.web.removeslash
    def get(self, hash_):

        mem_key = self.get_memcache_key(hash_)

        r = self.redis.getvalue(mem_key)
        if r:
            r = eval(r)
            results, start_time, end_time = r[0], r[1][0], r[1][1]
        else:
            self.render("errors/download.html")
            return

        import xlwt
        from cStringIO import StringIO

        date_style = xlwt.easyxf(num_format_str='YYYY-MM-DD HH:mm:ss')
        
        wb = xlwt.Workbook()
        ws = wb.add_sheet(OLINE_SHEET)

        start_line = 0
        for i, head in enumerate(OLINE_HEADER):
            ws.write(0, i, head)

        start_line += 1
        for i, result in zip(range(start_line, len(results) + start_line), results):
            t = time.strftime("%Y%m%d", time.localtime(int(result['time'])))
            online_time = t[:4] + u'年' + t[4:6] + u'月' + t[6:8] + u'日 '
            ws.write(i, 0, online_time)
            ws.write(i, 1, result['online_num'])
            ws.write(i, 2, result['offline_num'])
            ws.write(i, 3, result['total_num'])
            
        _tmp_file = StringIO()
        wb.save(_tmp_file)
        filename = self.generate_file_name(OLINE_FILE_NAME)
        if start_time:
            s_time = time.strftime("%Y%m%d", time.localtime(start_time))
            e_time = time.strftime("%Y%m%d", time.localtime(end_time))
            filename = s_time[:4] + u'年' + s_time[4:6] + u'月' + s_time[6:] + u'日--' + e_time[:4] + u'年' + e_time[4:6] + u'月' + e_time[6:] + u'日' + filename

        self.set_header('Content-Type', 'application/force-download')
        self.set_header('Content-Disposition', 'attachment; filename=%s.xls' % (filename,))

        # move the the begging. 
        _tmp_file.seek(0, SEEK_SET)
        self.write(_tmp_file.read())
        _tmp_file.close()
