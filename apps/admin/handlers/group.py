# -*- coding:utf-8 -*-

import logging 
import hashlib
from os import SEEK_SET

import tornado.web

from utils.dotdict import DotDict
from constants import AREA, XXT
from utils.misc import DUMMY_IDS

from mixin import BaseMixin
from excelheaders import GROUP_HEADER, GROUP_FILE_NAME, GROUP_SHEET
from base import BaseHandler, authenticated
from mongodb.mgroup import MGroup, MGroupMixin

from checker import check_areas, check_privileges
from constants import PRIVILEGES
from utils.misc import str_to_list
from myutils import city_list


class GroupMixin(BaseMixin):

    KEY_TEMPLATE = "group_report_%s_%s"

    def prepare_data(self, hash_):

        mem_key = self.get_memcache_key(hash_)
        
        data = self.redis.getvalue(mem_key)
        if data:
            return data

        city = self.get_argument('cities', 0)

        results = []
        counts = DotDict(group=0,
                         target=0)
        if int(city) == 0:
            cities = [city.city_id for city in self.cities]
        else:
            cities = [city,] 

        cities = [int(c) for c in cities]
        optype_status = (XXT.OPER_TYPE.CREATE,
                         XXT.OPER_TYPE.RESUME,
                         XXT.OPER_TYPE.UPDATE)
        for city in cities:
            c = self.db.get("SELECT city_name, region_code FROM T_HLR_CITY"
                            "  WHERE city_id = %s",
                            city)
            if self.type == "1":
                groups = self.db.query("SELECT txg.name, txg.xxt_id"
                                       "  FROM T_XXT_GROUP AS txg, T_ADMINISTRATOR AS ta"
                                       "  WHERE txg.city_id = %s"
                                       "    AND txg.phonenum = ta.login"
                                       "    AND ta.id = %s",
                                       c.region_code, self.current_user.id)
            else:
                groups = self.db.query("SELECT name, xxt_id"
                                       "  FROM T_XXT_GROUP"
                                       "  WHERE city_id = %s",
                                       c.region_code)
            for group in groups:
                targets = self.db.get("SELECT count(*) AS count"
                                      "  FROM T_XXT_TARGET"
                                      "  WHERE group_id = %s"
                                      "    AND optype IN %s",
                                      group.xxt_id, tuple(optype_status)) 
                result = DotDict(city=c.city_name,
                                 group_name=group.name,
                                 targets=targets.count)
                results.append(result)
                counts['target'] += targets.count
            counts['group'] += len(groups)
        for i, result in enumerate(results):
            result['id'] = i+1
        self.redis.setvalue(mem_key, (results, counts), time=self.MEMCACHE_EXPIRY)

        return results, counts


class GroupHandler(BaseHandler, GroupMixin):
    
    @authenticated
    @check_privileges([PRIVILEGES.COUNT_GROUP_USER])
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
    @check_privileges([PRIVILEGES.COUNT_GROUP_USER])
    @tornado.web.removeslash
    def get(self):

        self.render('report/group.html',
                    results=[],
                    counts={},
                    cities=self.cities,
                    type=self.type,
                    hash_=None)

    @authenticated
    @check_privileges([PRIVILEGES.COUNT_GROUP_USER])
    #@check_areas()
    @tornado.web.removeslash
    def post(self):

        m = hashlib.md5()
        m.update(self.request.body)
        hash_ = m.hexdigest()
        results, counts = self.prepare_data(hash_)

        self.render('report/group.html',
                    results=results,
                    counts=counts,
                    cities=self.cities,
                    type=self.type,
                    hash_=hash_)


class GroupDownloadHandler(BaseHandler, GroupMixin):

    @authenticated
    @tornado.web.removeslash
    def get(self, hash_):

        mem_key = self.get_memcache_key(hash_)

        res = self.redis.getvalue(mem_key)
        if not res:
            self.render("errors/download.html")
            return
        results, counts = res

        import xlwt
        from cStringIO import StringIO
        date_style = xlwt.easyxf(num_format_str='YYYY-MM-DD HH:mm:ss')
        
        wb = xlwt.Workbook()
        ws = wb.add_sheet(GROUP_SHEET)

        start_line = 0
        for i, head in enumerate(GROUP_HEADER):
            ws.write(0, i, head)

        start_line += 1
        for i, result in zip(range(start_line, len(results) + start_line), results):
            ws.write(i, 0, result['city'])
            ws.write(i, 1, result['group_name'])
            ws.write(i, 2, result['targets'])
        last_row = len(results) + start_line
        ws.write(last_row, 0, u'合计')
        ws.write(last_row, 1, counts['group'])
        ws.write(last_row, 2, counts['target'])

        _tmp_file = StringIO()
        wb.save(_tmp_file)
        filename = self.generate_file_name(GROUP_FILE_NAME)
        
        self.set_header('Content-Type', 'application/force-download')
        self.set_header('Content-Disposition', 'attachment; filename=%s.xls' % (filename,))

        # move the the begging. 
        _tmp_file.seek(0, SEEK_SET)
        self.write(_tmp_file.read())
        _tmp_file.close()
