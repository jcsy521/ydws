#!/usr/bin/env python
# -*- coding: utf-8 -*-

import hashlib
import logging
import time
from os import SEEK_SET
import xlwt
from cStringIO import StringIO

import tornado.web

from codes.errorcode import ErrorCode
from base import BaseHandler, authenticated
from mixin import BaseMixin
from excelheaders import OwnerService_FILE_NAME, OwnerService_SHEET, OwnerService_HEADER

class OwnerServiceMixin(BaseMixin):
        KEY_TEMPLATE = "owerservice_report_%s_%s"

        def prepare_data(self, hash_):
            mem_key = self.get_memcache_key(hash_)
            data = self.getvalue(mem_key)

            if data:
                return data


class OwnerServiceHandler(BaseHandler, OwnerServiceMixin):

    @authenticated
    @tornado.web.removeslash
    def get(self):
        self.render('activity/ownerservice.html',
                    interval='',
                    res=[],
                    hash_='')

    @authenticated
    @tornado.web.removeslash
    def post(self):

        status = ErrorCode.SUCCESS
        try:
            start_time = self.get_argument('start_time', 0)
            end_time = self.get_argument('end_time', 0)
            interval = [start_time, end_time]
            sql = "SELECT umobile, cnum, car_type,  add_time FROM T_OWNERSERVICE where add_time < %s" \
                  " AND add_time > %s"

            res = []
            retlist = self.db.query(sql, end_time, start_time)
            if not retlist:
                retlist = []

            for ret in retlist:
                _res = dict(umobile=ret.get('umobile', None),
                            car_num=ret.get('cnum', None),
                            car_type=ret.get('car_type', None),
                            add_time=ret.get('add_time', None)
                            )
                res.append(_res)

            m = hashlib.md5()
            m.update(self.request.body)
            hash_ = m.hexdigest()
            mem_key = self.get_memcache_key(hash_)
            self.redis.setvalue(mem_key, res, time=self.MEMCACHE_EXPIRY)

            if len(res) == 0:
                status = ErrorCode.FAILED
                message = ErrorCode.ERROR_MESSAGE[status]
                self.write_ret(status=status, message=message)
            else:
                self.render('activity/ownerservice.html',
                            status=status,
                            interval=interval,
                            res=res,
                            hash_=hash_)
        except Exception as e:
            logging.exception("search owners fail")
            self.render('errors/error.html', message=ErrorCode.FAILED)



class OwnerServiceDownloadHandler(BaseHandler, OwnerServiceMixin):

    @authenticated
    @tornado.web.removeslash
    def get(self, hash_):

        mem_key = self.get_memcache_key(hash_)
        results = self.redis.getvalue(mem_key)
        if not results:
            self.render("error/download.html")
            return

        filename = OwnerService_FILE_NAME
        wb = xlwt.Workbook()
        ws = wb.add_sheet(OwnerService_SHEET)

        start_line = 0
        for i, head in enumerate(OwnerService_HEADER):
            ws.write(0, i, head)

        start_line += 1
        for i, result in zip(range(start_line, len(results)+start_line + 1), results):
            ws.write(i, 0, i)
            ws.write(i, 1, result['umobile'])
            ws.write(i, 2, result['car_num'])
            ws.write(i, 3, result['car_type'])
            ws.write(i, 4, time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(result['add_time'])))

        _tmp_file = StringIO()
        wb.save(_tmp_file)

        filename = self.generate_file_name(filename)
        self.set_header('Content-Type', 'application/force-download')
        self.set_header('Content-Disposition', 'attachment; filename=%s.xls' % (filename,))

        _tmp_file.seek(0, SEEK_SET)
        self.write(_tmp_file.read())
        _tmp_file.close()



