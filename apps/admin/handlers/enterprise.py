# -*- coding: utf-8 -*-

from os import SEEK_SET
import datetime, time
import logging
import hashlib

import tornado.web
from tornado.escape import json_decode, json_encode
from tornado.ioloop import IOLoop

from constants import LOCATION, XXT
from utils.dotdict import DotDict

from mixin import BaseMixin
from base import BaseHandler, authenticated
from excelheaders import ENTERPRISE_HEADER_TOP, ENTERPRISE_HEADER, ENTERPRISE_FILE_NAME, ENTERPRISE_SHEET

from checker import check_areas, check_privileges 
from codes.errorcode import ErrorCode 
from utils.checker import check_sql_injection, check_zs_phone
from utils.misc import get_terminal_address_key, get_terminal_sessionID_key,\
     get_terminal_info_key, get_lq_sms_key, get_lq_interval_key
from helpers.smshelper import SMSHelper
from helpers.seqgenerator import SeqGenerator
from helpers.gfsenderhelper import GFSenderHelper
from helpers.queryhelper import QueryHelper 
from codes.smscode import SMSCode 
from constants import PRIVILEGES, SMS, UWEB, GATEWAY
from utils.misc import str_to_list, DUMMY_IDS, get_terminal_info_key
from myutils import city_list


class EnterpriseMixin(BaseMixin):

    KEY_TEMPLATE = "enterprise_report_%s_%s"

    def prepare_data(self, hash_):

        mem_key = self.get_memcache_key(hash_)
        
        data = self.redis.getvalue(mem_key)
        if data:
            return data

        start_time= int(self.get_argument('start_time'))
        end_time = int(self.get_argument('end_time'))

        interval = [start_time, end_time]

        res = []
        d, m = divmod( (end_time - start_time), 60*60*24)
        days = d+1 if m else d
        
        for day in range(days):
            _start_time = start_time + day*60*60*24 
            _end_time =  _start_time  + 60*60*24 - 1
            ret = self.db.get("SELECT corp_add_day, corp_add_month, corp_add_year,"
                              "  terminal_add_day, terminal_add_month, terminal_add_year,"
                              "  terminal_del_day, terminal_del_month, terminal_del_year,"
                              "  login_day, login_month, login_year,"
                              "  active, deactive, terminal_online, terminal_offline, timestamp"
                              "  FROM T_STATISTIC"
                              "  WHERE type= %s"
                              "  AND (timestamp BETWEEN %s AND %s)",
                              1,_start_time, _end_time)
            if not ret:
                ret = {}
            _res = dict(# corp add
                        corp_add_day=ret['corp_add_day'] if ret.get('corp_add_day', None) is not None else 0,
                        corp_add_month=ret['corp_add_month'] if ret.get('corp_add_month', None) is not None else 0,
                        corp_add_year=ret['corp_add_year'] if ret.get('corp_add_year', None) is not None else 0,

                        # terminal add
                        terminal_add_day=ret['terminal_add_day'] if ret.get('terminal_add_day', None) is not None else 0,
                        terminal_add_month=ret['terminal_add_month'] if ret.get('terminal_add_month', None) is not None else 0,
                        terminal_add_year=ret['terminal_add_year'] if ret.get('terminal_add_year', None) is not None else 0,

                        # terminal del
                        terminal_del_day=ret['terminal_del_day'] if ret.get('terminal_del_day', None) is not None else 0,
                        terminal_del_month=ret['terminal_del_month'] if ret.get('terminal_del_month', None) is not None else 0,
                        terminal_del_year=ret['terminal_del_year'] if ret.get('terminal_del_year', None) is not None else 0,

                        # login
                        login_day=ret['login_day'] if ret.get('login_day', None) is not None else 0,
                        login_month=ret['login_month'] if ret.get('login_month', None) is not None else 0,
                        login_year=ret['login_year'] if ret.get('login_year', None) is not None else 0,

                        # active statsu
                        active=ret['active'] if ret.get('active', None) is not None else 0,
                        deactive=ret['deactive'] if ret.get('deactive', None) is not None else 0,

                        # online 
                        terminal_online=ret['terminal_online'] if ret.get('terminal_online', None) is not None else 0,
                        terminal_offline=ret['terminal_offline'] if ret.get('terminal_offline', None) is not None else 0,
                        
                        timestamp=_start_time,
                        type=1
                       )
            res.append(_res)

        if res:
            res.reverse()

        self.redis.setvalue(mem_key, (res, interval), 
                            time=self.MEMCACHE_EXPIRY)

        return res, interval 



class EnterpriseHandler(BaseHandler, EnterpriseMixin):

    @authenticated
    @check_privileges([PRIVILEGES.STATISTIC])
    @tornado.web.removeslash
    def get(self):
        """Just to create.html.
        """
        self.render('report/enterprise.html',
                    status=ErrorCode.SUCCESS,
                    message='',
                    interval=[], 
                    res=[],
                    hash_='') 
                    
    @authenticated
    @check_privileges([PRIVILEGES.STATISTIC])
    @tornado.web.removeslash
    def post(self):
        """Create business for a couple of users.
        """
        m = hashlib.md5()
        m.update(self.request.body)
        hash_ = m.hexdigest()
        res, interval= self.prepare_data(hash_)

        self.render('report/enterprise.html',
                    status=ErrorCode.SUCCESS,
                    message='',
                    interval=interval, 
                    res=res,
                    hash_=hash_)


class EnterpriseDownloadHandler(BaseHandler, EnterpriseMixin):

    @authenticated
    @check_privileges([PRIVILEGES.STATISTIC])
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

        filename = ENTERPRISE_FILE_NAME

        date_style = xlwt.easyxf(num_format_str='YYYY-MM-DD HH:mm:ss')
        wb = xlwt.Workbook()
        ws = wb.add_sheet(ENTERPRISE_SHEET)

        start_line = 0

        ws.write_merge(0,0,0,0+2,ENTERPRISE_HEADER_TOP[0])
        ws.write_merge(0,0,3,3+2,ENTERPRISE_HEADER_TOP[1])
        ws.write_merge(0,0,6,6+2,ENTERPRISE_HEADER_TOP[2])
        ws.write_merge(0,0,9,9+2,ENTERPRISE_HEADER_TOP[3])
        ws.write_merge(0,0,12,12+1,ENTERPRISE_HEADER_TOP[4])
        ws.write_merge(0,0,14,14+1,ENTERPRISE_HEADER_TOP[5])
        ws.write_merge(0,0,16,16+0,ENTERPRISE_HEADER_TOP[6])
        start_line += 1

        for i, head in enumerate(ENTERPRISE_HEADER):
            ws.write(start_line, i, head)
        start_line += 1
        for i, result in zip(range(start_line, len(results) + start_line), results):

            ws.write(i, 0, result['terminal_add_day'])
            ws.write(i, 1, result['terminal_add_month'])
            ws.write(i, 2, result['terminal_add_year'])
            ws.write(i, 3, result['terminal_del_day'])
            ws.write(i, 4, result['terminal_del_month'])
            ws.write(i, 5, result['terminal_del_year'])
            ws.write(i, 6, result['corp_add_day'])
            ws.write(i, 7, result['corp_add_month'])
            ws.write(i, 8, result['corp_add_year'])
            ws.write(i, 9, result['login_day'])
            ws.write(i, 10, result['login_month'])
            ws.write(i, 11, result['login_year'])
            ws.write(i, 12, result['active'])
            ws.write(i, 13, result['deactive'])
            ws.write(i, 14, result['terminal_online'])
            ws.write(i, 15, result['terminal_offline'])
            ws.write(i, 16, time.strftime("%Y-%m-%d",time.localtime(result['timestamp'])))

        _tmp_file = StringIO()
        wb.save(_tmp_file)
        
        filename = self.generate_file_name(filename)

        self.set_header('Content-Type', 'application/force-download')
        self.set_header('Content-Disposition', 'attachment; filename=%s.xls' % (filename,))

        # move the the begging. 
        _tmp_file.seek(0, SEEK_SET)
        self.write(_tmp_file.read())
        _tmp_file.close()
