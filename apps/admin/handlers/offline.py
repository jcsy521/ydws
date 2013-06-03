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
from excelheaders import OFFLINE_HEADER, OFFLINE_SHEET, OFFLINE_FILE_NAME
from base import BaseHandler, authenticated

from checker import check_areas, check_privileges
from codes.errorcode import ErrorCode 
from constants import PRIVILEGES, SMS
from utils.misc import str_to_list, safe_utf8, safe_unicode, seconds_to_label, DUMMY_IDS
from utils.checker import check_sql_injection
from myutils import city_list


class OfflineMixin(BaseMixin):

    KEY_TEMPLATE = "offline_report_%s_%s"

    def prepare_data(self, hash_):

        mem_key = self.get_memcache_key(hash_)
        
        data = self.redis.getvalue(mem_key)
        if data:
            if isinstance(data, str):
                data = eval(data)
            return data[0], data[1]

        start_time = int(self.get_argument('start_time', None))
        end_time = int(self.get_argument('end_time', None))

        fields = DotDict(offline_cause="offline_cause=%s",
                         offline_period="offline_period>%s")
        for key in fields.iterkeys(): 
            v = self.get_argument(key, None) 
            if v: 
                if not check_sql_injection(v): 
                    self.get() 
                    return  
                fields[key] = fields[key] % (v,) 
            else: 
                fields[key] = None 

        where_clause = ' AND '.join([v for v in fields.itervalues() if v is not None])
        if where_clause:
            where_clause = ' AND ' + where_clause
            
        
        res = self.db.query("SELECT id, umobile, tmobile, offline_time, offline_period, offline_cause, pbat, remark"
                            "  FROM T_OFFLINE_STATISTIC"
                            "  WHERE offline_time between %s and %s AND tmobile like '14778%%'" + where_clause,
                            start_time, end_time)
        for item in res:
            item['remark'] = safe_unicode(item['remark'])
        
        self.redis.setvalue(mem_key,(res, [start_time, end_time]), 
                            time=self.MEMCACHE_EXPIRY)
        return res, [start_time, end_time]


class OfflineHandler(BaseHandler, OfflineMixin):

    @authenticated
    #@check_privileges([PRIVILEGES.OLINE_STATISTIC])
    @tornado.web.removeslash
    def get(self):
        
        self.render('report/offline.html',
                    status=ErrorCode.SUCCESS,
                    message='',
                    interval=[],
                    res=[],
                    hash_=None)


    @authenticated
    #@check_privileges([PRIVILEGES.OLINE_STATISTIC])
    #@check_areas()
    @tornado.web.removeslash
    def post(self):

        m = hashlib.md5()
        m.update(self.request.body)
        hash_ = m.hexdigest()
        res, interval = self.prepare_data(hash_)
        
        self.render('report/offline.html',
                    status=ErrorCode.SUCCESS,
                    message='',
                    interval=interval, 
                    res=res,
                    hash_=hash_)

    @authenticated
    #@check_privileges([PRIVILEGES.OLINE_STATISTIC])
    #@check_areas()
    @tornado.web.removeslash
    def put(self):
        ret = DotDict(status=ErrorCode.SUCCESS,
                              message=None)
        try:
            data = DotDict(json_decode(self.request.body))
            id = data.id 
            remark = data.remark
            self.db.execute("UPDATE T_OFFLINE_STATISTIC"
                            "  SET remark = %s"
                            "  WHERE id = %s",
                            remark, id)
        except Exception as e:
            ret.status = ErrorCode.FAILED
            ret.message = ErrorCode.ERROR_MESSAGE[ret.status]
        self.set_header(*self.JSON_HEADER)
        self.write(json_encode(ret))


class OfflineDownloadHandler(BaseHandler, OfflineMixin):

    @authenticated
    @tornado.web.removeslash
    def get(self, hash_):

        mem_key = self.get_memcache_key(hash_)

        r = self.redis.getvalue(mem_key)
        if r:
            results, interval = r[0], r[1]
        else:
            self.render("errors/download.html")
            return

        import xlwt
        from cStringIO import StringIO

        date_style = xlwt.easyxf(num_format_str='YYYY-MM-DD HH:mm:ss')
        
        wb = xlwt.Workbook()
        ws = wb.add_sheet(OFFLINE_SHEET)

        start_line = 0
        for i, head in enumerate(OFFLINE_HEADER):
            ws.write(0, i, head)

        ws.col(0).width = 4000  
        ws.col(1).width = 4000 
        ws.col(3).width = 4000 * 2 
        ws.col(4).width = 4000 * 2
        ws.col(6).width = 4000 * 4

        start_line += 1

        for i, result in zip(range(start_line, len(results) + start_line), results):
            ws.write(i, 0, result['umobile'])
            ws.write(i, 1, result['tmobile'])
            ws.write(i, 2, str(result['pbat'])+'%')
            ws.write(i, 3, time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(result['offline_time'])))
            ws.write(i, 4, seconds_to_label(result['offline_period']))
            ws.write(i, 5, u'低电关机' if result['offline_cause'] == 2 else u'通讯异常')
            terminal_offline = self.db.get("SELECT remark FROM T_OFFLINE_STATISTIC where id = %s", result['id'])
            ws.write(i, 6, safe_unicode(terminal_offline['remark']))

            
        _tmp_file = StringIO()
        wb.save(_tmp_file)
        filename = self.generate_file_name(OFFLINE_FILE_NAME)

        self.set_header('Content-Type', 'application/force-download')
        self.set_header('Content-Disposition', 'attachment; filename=%s.xls' % (filename,))

        # move the the begging. 
        _tmp_file.seek(0, SEEK_SET)
        self.write(_tmp_file.read())
        _tmp_file.close()
