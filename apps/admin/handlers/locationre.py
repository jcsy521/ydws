# -*- coding: utf-8 -*-

import logging 
import hashlib
import time
import xlwt
from cStringIO import StringIO
from os import SEEK_SET

import tornado.web

from mixin import BaseMixin
from base import BaseHandler, authenticated
from excelheaders import LOCATION_FILE_NAME, LOCATION_SHEET, LOCATION_HEADER

from checker import check_areas, check_privileges
from constants import PRIVILEGES
from codes.errorcode import ErrorCode


class LocationMixin(BaseMixin):

    KEY_TEMPLATE = "location_report_%s_%s"

class LocationSearchHandler(BaseHandler, LocationMixin):
    
    @authenticated
    @check_privileges([PRIVILEGES.TERMINAL_QUERY])
    @tornado.web.removeslash
    def get(self):
        """Jump to the terminallocation.html.
        """
        username = self.get_current_user()
        self.render('report/terminallocation.html',
                    username=username,
                    res=[],
                    interval='',
                    hash_='')

    @authenticated
    @check_privileges([PRIVILEGES.TERMINAL_QUERY])
    @tornado.web.removeslash
    def post(self):
        """QueryHelper individuals according to the 
        given parameters.
        """
        status = ErrorCode.SUCCESS
        try:
            mobile = self.get_argument('mobile', '')
            type = self.get_argument('type', 0)
            start_time = self.get_argument('start_time', 0)
            end_time = int(self.get_argument('end_time', 0))
            interval = [start_time, end_time]
            tid_sql = ("SELECT tid FROM T_TERMINAL_INFO WHERE mobile = %s") % mobile
            tidlist = self.db.query(tid_sql)
            res = []

            for t in tidlist:
                tid = t.get('tid', None)
                if int(type) == 2:
                    sql = ("SELECT tid, latitude, longitude, clatitude, "
                           "clongitude, name, timestamp, type, speed, "
                           "locate_error, cellid FROM T_LOCATION  WHERE tid = '%s' AND "
                           "timestamp < %s and timestamp > %s ") % (tid, end_time, start_time)
                else:
                    sql = ("SELECT tid, latitude, longitude, clatitude, "
                           "clongitude, name, timestamp, type, speed, "
                           "locate_error, cellid FROM T_LOCATION  WHERE tid = '%s' AND "
                           "timestamp < %s and timestamp > %s AND type = %s") % (tid, end_time, start_time, type)

                retlist = self.db.query(sql)
                if not retlist:
                    retlist = []

                for ret in retlist:
                    _res = dict(mobile=mobile,
                                tid=ret.get('tid', None),
                                latitude=ret.get('latitude', None),
                                longitude=ret.get('longitude', None),
                                clatitude=ret.get('clatitude', None),
                                clongitude=ret.get('clongitude', None),
                                name=ret.get('name', '') if ret.get('name', None) is not None else '',
                                timestamp=ret.get('timestamp', None),
                                type=ret.get('type', None),
                                speed=ret.get('speed', None),
                                locate_error=ret.get('locate_error', None),
                                cellid=ret.get('cellid', None))
                    res.append(_res)

            m = hashlib.md5()
            m.update(self.request.body)
            hash_ = m.hexdigest()
            mem_key = self.get_memcache_key(hash_)
            self.redis.setvalue(mem_key, res, time=self.MEMCACHE_EXPIRY)

            if len(res) == 0:
                status = -1
            self.render('report/terminallocation.html',
                        status=status,
                        res=res,
                        interval=interval,
                        hash_=hash_)
        except Exception as e:
            logging.exception("Exception: %s", e.args)
            status = -1
            message = ErrorCode.ERROR_MESSAGE[status]
            self.write_ret(status=status, message=message)


class LocationSearchDownloadHandler(BaseHandler, LocationMixin):

    @authenticated
    @check_privileges([PRIVILEGES.TERMINAL_QUERY])
    @tornado.web.removeslash
    def get(self, hash_):
        """Download the records and save it as excel.
        """
        mem_key = self.get_memcache_key(hash_)
        results = self.redis.getvalue(mem_key)

        if not results:
            self.render("errors/download.html")
            return

        filename = LOCATION_FILE_NAME
        base_style = xlwt.easyxf('font: colour_index green, bold off; align: wrap on, vert centre, horiz center;')
        gps_style = xlwt.easyxf('font: colour_index brown, bold off; align: wrap on, vert centre, horiz center;')

        wb = xlwt.Workbook()
        ws = wb.add_sheet(LOCATION_SHEET)

        start_line = 0
        for i, head in enumerate(LOCATION_HEADER):
            ws.write(0, i, head)

        start_line += 1
        for i, result in zip(range(start_line, len(results) + start_line), results):
            if int(result['type']) == 1:
                position_type = u'基站定位'
                stlye = base_style
            else:
                position_type = u'GPS定位'
                stlye = gps_style
            ws.write(i, 0, i)
            ws.write(i, 1, result['mobile'])
            ws.write(i, 2, result['tid'])
            ws.write(i, 3, result['latitude']/3600000.0)
            ws.write(i, 4, result['longitude']/3600000.0)
            ws.write(i, 5, result['clatitude']/3600000.0)
            ws.write(i, 6, result['clongitude']/3600000.0)
            ws.write(i, 7, result['name'])
            ws.write(i, 8, time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(result['timestamp'])))
            ws.write(i, 9, position_type, stlye)
            ws.write(i, 10, result['speed'])
            ws.write(i, 11, result['locate_error'])
            ws.write(i, 12, result['cellid'])

        _tmp_file = StringIO()
        wb.save(_tmp_file)
        filename = self.generate_file_name(filename)

        self.set_header('Content-Type', 'application/force-download')
        self.set_header('Content-Disposition', 'attachment; filename=%s.xls' % (filename,))

        _tmp_file.seek(0, SEEK_SET)
        self.write(_tmp_file.read())
        _tmp_file.close()
