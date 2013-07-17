# -*- coding:utf-8 -*-

import logging 
import hashlib
from os import SEEK_SET
import tornado.web
from tornado.escape import json_decode, json_encode
import time
import datetime
import re

from mixin import BaseMixin
from excelheaders import SMS_HEADER, SMS_SHEET, SMS_FILE_NAME
from base import BaseHandler, authenticated

from checker import check_areas, check_privileges
from constants import PRIVILEGES
from utils.misc import str_to_list, DUMMY_IDS
from utils.checker import check_sql_injection
from utils.dotdict import DotDict
from myutils import city_list
from mongodb.msms import MSms, MSmsMixin
from codes.errorcode import ErrorCode
from codes.smscode import SMSCode 
from helpers.smshelper import SMSHelper


class SMSMixin(BaseMixin):

    KEY_TEMPLATE = "sms_report_%s_%s"

    def prepare_data(self, hash_):

        mem_key = self.get_memcache_key(hash_)

        data = self.redis.getvalue(mem_key)
        if data:
            return data

        provinces = self.get_argument('province_id', None)
        cities = self.get_argument('city_id', None)
        start_time = int(self.get_argument('start_time', None))
        end_time = int(self.get_argument('end_time', None))
        group = self.get_argument('group', None)
        user_name = self.get_argument('user_name', None)
        mobile = self.get_argument('mobile', None)

        #if user_name and  (not check_sql_injection(user_name)):
        #    return [], [start_time, end_time]
        #if mobile  and  (not check_sql_injection(mobile)):
        #    return [], [start_time, end_time]
            
        # the result of today is inavaliable
        d = datetime.datetime.fromtimestamp(time.time())
        t = datetime.datetime.combine(datetime.date(d.year,d.month, d.day), datetime.time(0, 0, 0))
        today_ = int(time.mktime(t.timetuple())) * 1000
        if start_time >= today_:
            return [], [start_time, end_time]

        results = []
        if not (cities or provinces):
            return results, [start_time, end_time]
        elif not cities:
            provinces = str_to_list(provinces)
            cities = city_list(provinces, self.db)
        else:
            cities = str_to_list(cities)

        cities = [int(c) for c in cities]
        cs = self.db.query("SELECT DISTINCT region_code FROM T_HLR_CITY"
                           "  WHERE city_id IN %s",
                           tuple(cities + DUMMY_IDS))
        citylist = [c.region_code for c in cs]

        query_term = {'city_id':{'$in':citylist},
                      'fetchtime':{'$gte':start_time, '$lte':end_time},
                      'group_id': None,
                      'user_name': None,
                      'mobile': None}
        for term in ['user_name', 'mobile']:
            v = self.get_argument(term, None)
            if v:
                query_term[term] = {'$regex': '\S*'+v+'\S*'}
            else:
                query_term.pop(term)
        if group: 
            query_term['group_id'] = str(self.get_argument('group'))
        else:
            query_term.pop('group_id')

        display_term = {'province':1, 'city':1, 'group_name':1,
                        'user_name':1, 'mobile':1, '_id':0}

        res = []
        try:
            mobiles = self.collection.find(query_term, {'mobile':1}).distinct('mobile')
            if mobiles:
                for m in mobiles:
                    count = self.collection.find({'mobile':m,
                        'fetchtime':{'$gte':start_time, '$lte':end_time}}).count()
                    r = self.collection.find_one({'mobile':m,
                        'fetchtime':{'$gte':start_time, '$lte':end_time}}, display_term)
                    r['count'] = count
                    res.append(r)
            if not res:
                ins = MSms()
                res = ins.retrieve(citylist, start_time, end_time)
                
        except:
            ins = MSmsMixin()
            res = ins.retrieve_mixin(citylist, start_time, end_time)
            res = ins.distinct(res)

        if user_name:
            p_name = re.compile(user_name)
        if mobile:
            p_mobile = re.compile(mobile)
        results = []
        for r in res:
            flag = True
            if group and r['group_id'] != group:
                flag &= False
            if user_name and not p_name.findall(r['user_name']):
                flag &= False
            if mobile and not p_mobile.findall(r['mobile']):
                flag &= False
            if flag:
                results.append(r)
      
        self.redis.setvalue(mem_key,(results, [start_time, end_time]), 
                           time=self.MEMCACHE_EXPIRY)
        return results, [start_time, end_time]


class SMSHandler(BaseHandler, SMSMixin):
    
    @authenticated
    @check_privileges([PRIVILEGES.SMS_STATISTIC])
    @tornado.web.removeslash
    def prepare(self):

        key = self.get_area_memcache_key(self.current_user.id)
        areas = self.redis.getvalue(key)
        if not areas:
            areas = self.get_privilege_area(self.current_user.id)
            self.redis.setvalue(key, areas)
        self.areas = areas
        #self.provinces = self.db.query("SELECT province_id, province_name FROM T_HLR_PROVINCE")
        #self.groups = self.db.query("SELECT id, name FROM T_XXT_GROUP")
        #self.group_ids = self.db.query("SELECT id, xxt_id FROM T_XXT_GROUP")
        # get privilege groups
        cities = []
        for area in areas:
            cs = area.city
            cities.extend([city.id for city in cs])
        self.groups = self.db.query("SELECT txg.id, txg.name FROM T_XXT_GROUP AS txg"
                                    "  WHERE txg.city_id in %s",
                                    tuple(cities + DUMMY_IDS))
        self.group_ids = [group.id for group in self.groups]
        try:
            self.collection = self.mongodb.sms
        except:
            logging.exception("mongodb connected failed.") 

    @authenticated
    @check_privileges([PRIVILEGES.SMS_STATISTIC])
    @tornado.web.removeslash
    def get(self):

        self.render('report/sms.html',
                    results=[],
                    groups=self.groups,
                    group_ids=self.group_ids,
                    areas=self.areas, 
                    interval=[],
                    cities=[],
                    hash_=None)

    @authenticated
    @check_privileges([PRIVILEGES.SMS_STATISTIC])
    @check_areas()
    @tornado.web.removeslash
    def post(self):

        m = hashlib.md5()
        m.update(self.request.body)
        hash_ = m.hexdigest()
        results, interval = self.prepare_data(hash_)

        self.render('report/sms.html',
                    results=results,
                    groups=self.groups,
                    group_ids=self.group_ids,
                    areas=self.areas, 
                    interval=interval,
                    cities=[],
                    hash_=hash_)


class SMSDownloadHandler(SMSMixin, BaseHandler):

    @authenticated
    @tornado.web.removeslash
    def get(self, hash_):

        mem_key = self.get_memcache_key(hash_)
        r = self.redis.getvalue(mem_key)
        if r:
            results = r[0]
            start_time, end_time = r[1][0], r[1][1]
        else:
            self.render("errors/download.html")
            return

        import xlwt
        from cStringIO import StringIO

        date_style = xlwt.easyxf(num_format_str='YYYY-MM-DD HH:mm:ss')
        
        wb = xlwt.Workbook()
        ws = wb.add_sheet(SMS_SHEET)

        start_line = 0
        for i, head in enumerate(SMS_HEADER):
            ws.write(0, i, head)

        start_line += 1
        for i, result in zip(range(start_line, len(results) + start_line), results):
            ws.write(i, 0, result['province'])
            ws.write(i, 1, result['city'])
            ws.write(i, 2, result['group_name'])
            ws.write(i, 3, result['user_name'])
            ws.write(i, 4, result['mobile'])
            ws.write(i, 5, result['count'])
            ws.col(4).width = 0x0c00
            ws.col(2).width = 0x1c00

        _tmp_file = StringIO()
        wb.save(_tmp_file)
        filename = self.generate_file_name(SMS_FILE_NAME)

        self.set_header('Content-Type', 'application/force-download')
        self.set_header('Content-Disposition', 'attachment; filename=%s.xls' % (filename,))

        # move the the begging. 
        _tmp_file.seek(0, SEEK_SET)
        self.write(_tmp_file.read())
        _tmp_file.close()
        
        
class SMSRegisterHandler(SMSMixin, BaseHandler):
    
    @authenticated
    @tornado.web.removeslash
    def post(self):
        status = ErrorCode.SUCCESS
        try:
#            {"tmobile":18810496308,"pmobile":18810496308}
            data = DotDict(json_decode(self.request.body))
            tmobile = data.tmobile
            pmobile = data.pmobile
            register_sms = SMSCode.SMS_REGISTER % (pmobile, tmobile) 
            ret = SMSHelper.send_to_terminal(tmobile, register_sms)
            ret = DotDict(json_decode(ret))
            if ret.status == ErrorCode.SUCCESS:
                self.db.execute("UPDATE T_TERMINAL_INFO"
                                "  SET msgid = %s"
                                "  WHERE mobile = %s",
                                ret['msgid'], tmobile)
                self.write_ret(status)
            else:
                status = ErrorCode.FAILED
                self.write_ret(status)
            
        except Exception as e:
            logging.exception("SMS register failed. Exception: %s", e.args)
            status = ErrorCode.FAILED
            self.write_ret(status)
