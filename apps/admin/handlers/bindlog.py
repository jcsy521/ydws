#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import time
from os import SEEK_SET
import hashlib
import xlwt
from cStringIO import StringIO

import tornado.web
from tornado.escape import json_decode

from base import BaseHandler, authenticated
from codes.errorcode import ErrorCode
from mixin import BaseMixin
from excelheaders import BINDLOG_FILE_NAME, BINDLOG_SHEET, BINDLOG_HEADER
from utils.misc import safe_unicode

from checker import check_privileges 
from constants import PRIVILEGES

class BindLogMixin(BaseMixin):
    KEY_TEMPLATE = "binglog_report_%s_%s"

    def prepare_data(self, hash_):
        mem_key = self.get_memcache_key(hash_)
        data = self.getvalue(mem_key)

        if data:
            return data



class BindLogSearchHandler(BaseHandler, BindLogMixin):

    @authenticated
    @check_privileges([PRIVILEGES.TERMINAL_QUERY])
    @tornado.web.removeslash
    def get(self):
        username = self.get_current_user()
        self.render('report/terminalbindlog.html',
                    username=username,
                    res=[],
                    hash_='')

    @authenticated
    @check_privileges([PRIVILEGES.TERMINAL_QUERY])
    @tornado.web.removeslash
    def post(self):

        status = ErrorCode.SUCCESS
        try:
            mobile = self.get_argument('mobile', 0)
            sql = ("SELECT tmobile, op_type, add_time, del_time FROM T_BIND_LOG"
                   " WHERE tmobile=%s") % mobile
            retlist = self.db.query(sql)
            res = []
            if not retlist:
                retlist = []
            for ret in retlist:
                if ret.get('op_type', None) is not None:
                    op_type = ret.get('op_type', None)
                else:
                    op_type = 0
                _res = dict(op_type=op_type,
                            mobile=mobile,
                            add_time=ret.get('add_time'),
                            del_time=ret.get('del_time'))
                res.append(_res)

            m = hashlib.md5()
            m.update(self.request.body)
            hash_ = m.hexdigest()
            mem_key = self.get_memcache_key(hash_)
            self.redis.setvalue(mem_key, res, time=self.MEMCACHE_EXPIRY)

            if len(res) == 0:
                status = ErrorCode.TERMINAL_NOT_EXISTED
                message = ErrorCode.ERROR_MESSAGE[status]
                self.render('report/terminalbindlog.html',
                            status=status, res=res, hash_=hash_, message=message)
            else:
                self.render('report/terminalbindlog.html',
                            status=status, res=res, hash_=hash_)

        except Exception as e:
            logging.exception("Search bing log for %s,it is does'\nt exists", mobile)
            self.render('errors/error.html', message=ErrorCode.FAILED)


class BindLogDownloadHandler(BaseHandler, BindLogMixin):

    @authenticated
    @check_privileges([PRIVILEGES.TERMINAL_QUERY])
    @tornado.web.removeslash
    def get(self, hash_):
        
        mem_key = self.get_memcache_key(hash_)
        results = self.redis.getvalue(mem_key)
        if not results:
            self.render("errors/download.html")
            return

        filename = BINDLOG_FILE_NAME
        date_syle = xlwt.easyxf(num_format_str='YYYY-MM-DD HH:mm:ss')
        bind_style = xlwt.easyxf('font: colour_index green, bold off; align: wrap on, vert centre, horiz center;')
        re_style = xlwt.easyxf('font: colour_index brown, bold off; align: wrap on, vert centre, horiz center;')
        wb = xlwt.Workbook()
        ws = wb.add_sheet(BINDLOG_SHEET)

        start_line = 0
        for i, head in enumerate(BINDLOG_HEADER):
            ws.write(0, i, head)

        start_line += 1
        for i, result in zip(range(start_line, len(results) + start_line+1), results):
            if int(result['op_type']) == 2:
                bind = u'解绑'
                style = bind_style
            else:
                bind = u'注册'
                style = re_style

            if result['add_time'] == 0:
                add_time = 0
            else:
                add_time = result['add_time']
            if result['del_time'] == 0:
                del_time = 0
            else:
                del_time = result['del_time']

            ws.write(i, 0, i)
            ws.write(i, 1, result['mobile'])
            ws.write(i, 2, bind, style)
            if add_time == 0:
                ws.write(i, 3, '')
            else:
                ws.write(i, 3, time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(add_time)))
            if del_time == 0:
                ws.write(i, 4, '')
            else:
                ws.write(i, 4, time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(del_time)))

        _tmp_file = StringIO()
        wb.save(_tmp_file)
        filename = self.generate_file_name(filename)
        self.set_header('Content-Type', 'application/force-download')
        self.set_header('Content-Disposition', 'attachment; filename=%s.xls' % (filename,))

        _tmp_file.seek(0, SEEK_SET)
        self.write(_tmp_file.read())
        _tmp_file.close()
