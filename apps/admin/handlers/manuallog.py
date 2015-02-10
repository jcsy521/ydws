#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""This module is designed for the manual-log of individual.
"""

import logging
import time
from os import SEEK_SET
import hashlib
import xlwt
from cStringIO import StringIO

import tornado.web

from base import BaseHandler, authenticated
from codes.errorcode import ErrorCode
from mixin import BaseMixin
from excelheaders import MANUALLOG_FILE_NAME, MANUALLOG_SHEET, MANUALLOG_HEADER
from checker import check_privileges 
from constants import PRIVILEGES

class ManualLogMixin(BaseMixin):
    KEY_TEMPLATE = "manuallog_report_%s_%s"

class ManualLogSearchHandler(BaseHandler, ManualLogMixin):

    @authenticated
    @check_privileges([PRIVILEGES.TERMINAL_QUERY])
    @tornado.web.removeslash
    def get(self):
        """Jump to the terminalmanuallog.html.
        """
        username = self.get_current_user()
        self.render('report/terminalmanuallog.html',
                    username=username,
                    res=[],
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
            mobile = self.get_argument('mobile', 0)
            sql = ("SELECT tid, tmobile, umobile, group_id, cid, manual_status, timestamp FROM T_MANUAL_LOG"
                   "  WHERE tmobile=%s") % mobile

            res = self.db.query(sql)

            m = hashlib.md5()
            m.update(self.request.body)
            hash_ = m.hexdigest()
            mem_key = self.get_memcache_key(hash_)
            self.redis.setvalue(mem_key, res, time=self.MEMCACHE_EXPIRY)

            if len(res) == 0:
                status = ErrorCode.TERMINAL_NOT_EXISTED
                message = ErrorCode.ERROR_MESSAGE[status]
                self.render('report/terminalmanuallog.html',
                            status=status, res=res, hash_=hash_, message=message)
            else:
                self.render('report/terminalmanuallog.html',
                            status=status, res=res, hash_=hash_)

        except Exception as e:
            logging.exception("Search manual log faild. mobile：%s, Exception: %s.", 
                              mobile, e.args)
            self.render('errors/error.html', message=ErrorCode.FAILED)


class ManualLogDownloadHandler(BaseHandler, ManualLogMixin):

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

        filename = MANUALLOG_FILE_NAME
        green_style = xlwt.easyxf('font: colour_index green, bold off; align: wrap on, vert centre, horiz center;')
        brown_style = xlwt.easyxf('font: colour_index brown, bold off; align: wrap on, vert centre, horiz center;')
        wb = xlwt.Workbook()
        ws = wb.add_sheet(MANUALLOG_SHEET)

        start_line = 0
        for i, head in enumerate(MANUALLOG_HEADER):
            ws.write(0, i, head)

        start_line += 1
        for i, result in zip(range(start_line, len(results) + start_line+1), results):

            if int(result['manual_status']) == 1:
                manual_status = u'强力设防'
                style = green_style
            elif int(result['manual_status']) == 2:
                manual_status = u'智能设防'
                style = brown_style
            else:
                manual_status = u'撤防'
                style = brown_style

            timestamp = result['timestamp']

            ws.write(i, 0, i)
            ws.write(i, 1, result['tmobile'])
            ws.write(i, 2, manual_status, style)
            ws.write(i, 3, time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp)))

        _tmp_file = StringIO()
        wb.save(_tmp_file)
        filename = self.generate_file_name(filename)
        self.set_header('Content-Type', 'application/force-download')
        self.set_header('Content-Disposition', 'attachment; filename=%s.xls' % (filename,))

        _tmp_file.seek(0, SEEK_SET)
        self.write(_tmp_file.read())
        _tmp_file.close()
