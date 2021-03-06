# -*- coding: utf-8 -*-

"""This module is designed for statistic of individual.
"""

from os import SEEK_SET
import time
import hashlib
import xlwt
from cStringIO import StringIO

import tornado.web

from mixin import BaseMixin
from base import BaseHandler, authenticated
from excelheaders import (INDIVIDUAL_HEADER_TOP, INDIVIDUAL_HEADER,
                         INDIVIDUAL_FILE_NAME, INDIVIDUAL_SHEET)

from checker import check_areas, check_privileges
from codes.errorcode import ErrorCode
from constants import PRIVILEGES


class IndividualMixin(BaseMixin):

    KEY_TEMPLATE = "user_report_%s_%s"

    def prepare_data(self, hash_):
        """Associated with the post method.

        workflow:

        if get value according the hash:
            return value
        else:
            retrieve the db and return the result.
        """
        mem_key = self.get_memcache_key(hash_)

        data = self.redis.getvalue(mem_key)
        if data:
            return data

        start_time = int(self.get_argument('start_time'))
        end_time = int(self.get_argument('end_time'))

        interval = [start_time, end_time]

        res = []
        d, m = divmod((end_time - start_time), 60 * 60 * 24)
        days = d + 1 if m else d

        for day in range(days):
            _start_time = start_time + day * 60 * 60 * 24
            _end_time = _start_time + 60 * 60 * 24 - 1
            ret = self.db.get("SELECT corp_add_day, corp_add_month, corp_add_year,"
                              "  terminal_add_day, terminal_add_month, terminal_add_year,"
                              "  terminal_del_day, terminal_del_month, terminal_del_year,"
                              "  login_day, login_month, login_year,"
                              "  active, deactive, terminal_online, terminal_offline, timestamp"
                              "  FROM T_STATISTIC"
                              "  WHERE type= %s"
                              "  AND (timestamp BETWEEN %s AND %s)",
                              0, _start_time, _end_time)
            if not ret:
                ret = {}
            _res = dict(  # corp add
                corp_add_day=ret['corp_add_day'] if ret.get(
                    'corp_add_day', None) is not None else 0,
                corp_add_month=ret['corp_add_month'] if ret.get(
                    'corp_add_month', None) is not None else 0,
                corp_add_year=ret['corp_add_year'] if ret.get(
                    'corp_add_year', None) is not None else 0,

                # terminal add
                terminal_add_day=ret['terminal_add_day'] if ret.get(
                    'terminal_add_day', None) is not None else 0,
                terminal_add_month=ret['terminal_add_month'] if ret.get(
                    'terminal_add_month', None) is not None else 0,
                terminal_add_year=ret['terminal_add_year'] if ret.get(
                    'terminal_add_year', None) is not None else 0,

                # terminal del
                terminal_del_day=ret['terminal_del_day'] if ret.get(
                    'terminal_del_day', None) is not None else 0,
                terminal_del_month=ret['terminal_del_month'] if ret.get(
                    'terminal_del_month', None) is not None else 0,
                terminal_del_year=ret['terminal_del_year'] if ret.get(
                    'terminal_del_year', None) is not None else 0,

                # login
                login_day=ret['login_day'] if ret.get(
                    'login_day', None) is not None else 0,
                login_month=ret['login_month'] if ret.get(
                    'login_month', None) is not None else 0,
                login_year=ret['login_year'] if ret.get(
                    'login_year', None) is not None else 0,

                # active statsu
                active=ret['active'] if ret.get(
                    'active', None) is not None else 0,
                deactive=ret['deactive'] if ret.get(
                    'deactive', None) is not None else 0,

                # online
                terminal_online=ret['terminal_online'] if ret.get(
                    'terminal_online', None) is not None else 0,
                terminal_offline=ret['terminal_offline'] if ret.get(
                    'terminal_offline', None) is not None else 0,

                timestamp=_start_time,
                type=0
            )
            res.append(_res)

        if res:
            res.reverse()

        self.redis.setvalue(mem_key, (res, interval),
                            time=self.MEMCACHE_EXPIRY)

        return res, interval


class IndividualHandler(BaseHandler, IndividualMixin):

    @authenticated
    @check_privileges([PRIVILEGES.STATISTIC])
    @tornado.web.removeslash
    def prepare(self):
        pass

    @authenticated
    @check_privileges([PRIVILEGES.STATISTIC])
    @tornado.web.removeslash
    def get(self):
        """Jump to individual.html.
        """
        self.render('report/individual.html',
                    status=ErrorCode.SUCCESS,
                    message='',
                    interval=[],
                    res=[],
                    hash_='')

    @authenticated
    @check_privileges([PRIVILEGES.STATISTIC])
    @tornado.web.removeslash
    def post(self):
        """QueryHelper individuals according to the 
        given parameters.
        """
        m = hashlib.md5()
        m.update(self.request.body)
        hash_ = m.hexdigest()
        res, interval = self.prepare_data(hash_)

        self.render('report/individual.html',
                    status=ErrorCode.SUCCESS,
                    message='',
                    interval=interval,
                    res=res,
                    hash_=hash_)


class IndividualDownloadHandler(BaseHandler, IndividualMixin):

    @authenticated
    @check_privileges([PRIVILEGES.STATISTIC])
    @tornado.web.removeslash
    def get(self, hash_):
        """Download the records and save it as excel.
        """
        mem_key = self.get_memcache_key(hash_)

        r = self.redis.getvalue(mem_key)
        if r:
            results, interval = r[0], r[1]
        else:
            self.render("errors/download.html")
            return

        filename = INDIVIDUAL_FILE_NAME

        # if timestamp:
        #    filename = str(timestamp[0]) + u'年' + filename

        wb = xlwt.Workbook()
        ws = wb.add_sheet(INDIVIDUAL_SHEET)

        start_line = 0
        ws.write_merge(0, 0, 0, 0 + 2, INDIVIDUAL_HEADER_TOP[0])
        ws.write_merge(0, 0, 3, 3 + 2, INDIVIDUAL_HEADER_TOP[1])
        ws.write_merge(0, 0, 6, 6 + 2, INDIVIDUAL_HEADER_TOP[2])
        ws.write_merge(0, 0, 9, 9 + 1, INDIVIDUAL_HEADER_TOP[3])
        ws.write_merge(0, 0, 11, 11 + 1, INDIVIDUAL_HEADER_TOP[4])
        ws.write_merge(0, 0, 13, 13 + 0, INDIVIDUAL_HEADER_TOP[5])
        start_line += 1

        for i, head in enumerate(INDIVIDUAL_HEADER):
            ws.write(start_line, i, head)
        start_line += 1
        for i, result in zip(range(start_line, len(results) + start_line), results):
            ws.write(i, 0, result['terminal_add_day'])
            ws.write(i, 1, result['terminal_add_month'])
            ws.write(i, 2, result['terminal_add_year'])
            ws.write(i, 3, result['terminal_del_day'])
            ws.write(i, 4, result['terminal_del_month'])
            ws.write(i, 5, result['terminal_del_year'])
            ws.write(i, 6, result['login_day'])
            ws.write(i, 7, result['login_month'])
            ws.write(i, 8, result['login_year'])
            ws.write(i, 9, result['active'])
            ws.write(i, 10, result['deactive'])
            ws.write(i, 11, result['terminal_online'])
            ws.write(i, 12, result['terminal_offline'])
            ws.write(
                i, 13, time.strftime("%Y-%m-%d", time.localtime(result['timestamp'])))

        _tmp_file = StringIO()
        wb.save(_tmp_file)

        filename = self.generate_file_name(filename)

        self.set_header('Content-Type', 'application/force-download')
        self.set_header(
            'Content-Disposition', 'attachment; filename=%s.xls' % (filename,))

        # move the the begging.
        _tmp_file.seek(0, SEEK_SET)
        self.write(_tmp_file.read())
        _tmp_file.close()
