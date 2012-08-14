# -*- coding: utf-8 -*-

import hashlib
from os import SEEK_SET
import tornado.web
import time

from constants import XXT, AREA
from utils.dotdict import DotDict
from utils.misc import DUMMY_IDS
from utils.checker import check_sql_injection

from excelheaders import USER_HEADER, USER_SHEET, USER_FILE_NAME

from checker import check_areas, check_privileges
from constants import PRIVILEGES
from utils.misc import str_to_list
from myutils import city_list

from mixin import BaseMixin
from base import BaseHandler, authenticated


class UserMixin(BaseMixin):

    KEY_TEMPLATE = "user_query_%s_%s"
    
    def prepare_data(self, hash_):
        """ get result for user-query.

        Workflow:
        mem_key = self.get_memcache_key(hash_)
        data = self.redis.getvalue(mem_key)
        if data:
            return data
        # now, begin the true query    
        category = argument(category)
        terms = []
        if category == parent:
            select_clause = 'select field1,field2...'
            from_table_clause = 'from talbe1, table2...'
            fields = a DotDict,the option provided by front-end
            where_clause = 'where valid=value1'
            USER_BIND_GROUP = a query about group_id 
            USER_BIND_CITY = a query about city 
            for item in fields.iterkeys():
                #do something and rich the fields's values
            user_terms = get value from fields
            terms =  union where_cluse,user_terms,USER_BIND_GROUP,USER_BIND_CITY
            sql = union select_clause, from_table_clause, terms
        else:
           # do the same with parent, except the extra filed 'plan_id'
        self.redis.setvalue(mem_key,data,time_period)
        return data
        """

        mem_key = self.get_memcache_key(hash_)
        
        data = self.redis.getvalue(mem_key)
        if data:
            return data

        counts = DotDict(create=0,
                         suspend=0,
                         cancel=0)
        terms = []
        group_id = int(self.get_argument('group', 0))
        city = int(self.get_argument('cities', 0))
        start_time = int(self.get_argument('start_time'))
        end_time = int(self.get_argument('end_time'))
        interval = [start_time, end_time]
        start_time = time.strftime("%Y%m%d%H%M%S0000", time.localtime(start_time/1000)) 
        end_time = time.strftime("%Y%m%d%H%M%S0000", time.localtime(end_time/1000)) 

        select_clause = "SELECT T_XXT_USER.name AS pname,"\
                      + " T_XXT_USER.optype AS poptype,"\
                      + " T_XXT_USER.status AS jxq_status,"\
                      + " T_XXT_USER.plan_id AS pplan,"\
                      + " T_XXT_USER.timestamp AS ptimestamp,"\
                      + " T_XXT_TARGET.mobile AS tmobile, T_XXT_TARGET.lbmp_status,"\
                      + " T_XXT_TARGET.optype AS toptype,"\
                      + " T_XXT_TARGET.name AS tname,"\
                      + " T_XXT_TARGET.plan_id AS tplan,"\
                      + " T_XXT_TARGET.timestamp AS ttimestamp,"\
                      + " T_HLR_CITY.city_name AS city,"\
                      + " T_XXT_GROUP.name AS group_name,"
        USER_BIND_TARGET = " FROM T_XXT_USER LEFT JOIN T_XXT_TARGET"\
                           " ON (T_XXT_USER.mobile = T_XXT_TARGET.parent_mobile"\
                           " AND T_XXT_USER.service_id = T_XXT_TARGET.service_id),"
        TARGET_BIND_USER = " FROM T_XXT_USER RIGHT JOIN T_XXT_TARGET"\
                           " ON (T_XXT_USER.mobile = T_XXT_TARGET.parent_mobile"\
                           " AND T_XXT_USER.service_id = T_XXT_TARGET.service_id),"
        from_table_clause = "T_HLR_CITY, T_XXT_GROUP"
        where_clause = " WHERE T_XXT_GROUP.xxt_id IN %s "
        if group_id: 
            groups = tuple([group_id,] + DUMMY_IDS) 
            # not query user sql
            #targets = self.db.query("SELECT optype FROM T_XXT_TARGET"
            #                        "  WHERE group_id = %s", group_id)
            #targets = [t.optype for t in targets]
            #counts.create = targets.count(XXT.OPER_TYPE.CREATE)
            #counts.suspend = targets.count(XXT.OPER_TYPE.SUSPEND)
            #counts.cancel = targets.count(XXT.OPER_TYPE.CANCEL)
            ####################
        else:
            if int(self.type) == 1:
                groups = self.db.query("SELECT txg.xxt_id as id"
                                       "  FROM T_XXT_GROUP AS txg,"
                                       "       T_ADMINISTRATOR AS ta"
                                       "  WHERE ta.login = txg.phonenum"
                                       "    AND ta.id = %s",
                                       self.current_user.id)
            else:
                groups = self.db.query("SELECT DISTINCT xxt_id as id"
                                       "  FROM T_XXT_GROUP AS txg,"
                                       "       T_HLR_CITY AS thc"
                                       "  WHERE thc.city_id = %s"
                                       "    AND txg.city_id = thc.region_code",
                                       city)
            group_ids = [int(group.id) for group in groups]
            groups = tuple(group_ids + DUMMY_IDS) 

        terms.append(where_clause)
        target_time_term = "T_XXT_TARGET.timestamp BETWEEN %s AND %s" % (start_time, end_time)
        user_time_term = "T_XXT_USER.timestamp BETWEEN %s AND %s" % (start_time, end_time)

        USER_BIND_GROUP = " T_XXT_USER.group_id = T_XXT_GROUP.xxt_id "
        TARGET_BIND_GROUP = " T_XXT_TARGET.group_id = T_XXT_GROUP.xxt_id "
        GROUP_BIND_CITY = " T_XXT_GROUP.city_id = T_HLR_CITY.region_code"
        terms.append(GROUP_BIND_CITY)
        terms.append(USER_BIND_GROUP)
        select_clause1 = select_clause + " T_XXT_USER.mobile AS pmobile"
        terms.append(user_time_term)
        sql1 = ''.join((select_clause1, USER_BIND_TARGET, from_table_clause, ' AND '.join(terms)))
        terms.remove(USER_BIND_GROUP)
        terms.remove(user_time_term)
        terms.append(TARGET_BIND_GROUP)
        select_clause2 = select_clause + " T_XXT_TARGET.parent_mobile AS pmobile"
        terms.append(target_time_term)
        sql2 = ''.join((select_clause2, TARGET_BIND_USER, from_table_clause, ' AND '.join(terms)))
        sql = sql1 + ' union ' + sql2
                                  
        users = self.db.query(sql, groups, groups)
        plans = self.db.query("SELECT xxt_id, name FROM T_XXT_PLAN")
        d_plan = dict()
        for plan in plans:
            d_plan[plan.xxt_id] = plan.name
        for i, user in enumerate(users):
            user['id'] = i+1
            for key in user:
                if key in ('pplan', 'tplan'):
                    user[key] = d_plan[user[key]] if user[key] else ''
                else:
                    user[key] = user[key] if user[key] else ''

        targets = [user.toptype for user in users]
        counts.create = targets.count(XXT.OPER_TYPE.CREATE)
        counts.suspend = targets.count(XXT.OPER_TYPE.SUSPEND)
        counts.cancel = targets.count(XXT.OPER_TYPE.CANCEL)
        results = dict(users=users,
                       counts=counts)
        self.redis.setvalue(mem_key, (results, interval), time=self.MEMCACHE_EXPIRY)
        return results, interval


class UserHandler(BaseHandler, UserMixin):

    @authenticated
    @check_privileges([PRIVILEGES.QUERY_USER])
    @tornado.web.removeslash
    def prepare(self):

        self.plans = self.db.query("SELECT xxt_id AS id, name FROM T_XXT_PLAN")
        mem_key = self.get_area_memcache_key(self.current_user.id)
        cities = self.redis.getvalue(mem_key)
        if not cities:
            cities = self.get_privilege_area(self.current_user.id)
            self.redis.setvalue(mem_key, cities)
        self.cities = cities
        res  = self.db.get("SELECT type FROM T_ADMINISTRATOR"
                           "  WHERE id = %s", self.current_user.id)
        self.type = res.type


    @authenticated
    @check_privileges([PRIVILEGES.QUERY_GROUP_USER])
    @tornado.web.removeslash
    def get(self):

        self.render("user/search.html",
                    cities=self.cities, 
                    groups=[],
                    users=[],
                    counts=[],
                    interval=[],
                    type=self.type,
                    hash_=None)

    @authenticated
    @check_privileges([PRIVILEGES.QUERY_GROUP_USER])
    #@check_areas()
    @tornado.web.removeslash
    def post(self):

        m = hashlib.md5()
        m.update(self.request.body)
        hash_ = m.hexdigest()
        results, interval = self.prepare_data(hash_)
        self.render("user/search.html",
                    users=results['users'],
                    counts=results['counts'],
                    cities=self.cities, 
                    #groups=self.groups,
                    interval=interval,
                    type=self.type,
                    hash_=hash_)


class UserDownloadHandler(BaseHandler, UserMixin):

    @authenticated
    @tornado.web.removeslash
    def get(self, hash_):

        mem_key = self.get_memcache_key(hash_)
        r = self.redis.getvalue(mem_key)
        if not r:
            self.render("errors/download.html")
            return
        else:
            results = r[0]
        users = results.get('users', [])

        import xlwt
        from cStringIO import StringIO

        wb = xlwt.Workbook(encoding='utf-8')
        ws = wb.add_sheet(USER_SHEET)

        start_line = 0
        for i, head in enumerate(USER_HEADER):
            ws.write(0, i, head)

        start_line += 1
        for i, user in zip(range(start_line, len(users) + start_line), users):
            ws.write(i, 0, user.pname)
            ws.write(i, 1, user.tname)
            ws.write(i, 2, user.pmobile)
            ws.write(i, 3, user.tmobile)
            ws.write(i, 4, user.group_name)
            ws.write(i, 5, user.pplan)
            ws.write(i, 6, user.tplan)

            if user.jxq_status:
                if int(user.jxq_status) == 0:
                    user.jxq_status = u"未同步"
                elif int(user.jxq_status) == 1:
                    user.jxq_status = u"已同步"
            ws.write(i, 7, user.jxq_status)

            if user.lbmp_status:
                if int(user.lbmp_status) == 0:
                    user.lbmp_status = u"未同步"
                elif int(user.lbmp_status) == 1:
                    user.lbmp_status = u"已同步"
                else:
                    user.lbmp_status = u"同步失败"
            ws.write(i, 8, user.lbmp_status)

            for key in ['poptype', 'toptype']:
                if user[key]:
                    if int(user[key]) == 1:
                        user[key] = u"订购"
                    elif int(user[key]) == 2:
                        user[key] = u"暂停"
                    elif int(user[key]) == 5:
                        user[key] = u"退订"
                else:
                    user[key] = u"未订购"
            ws.write(i, 9, user.poptype)
            ws.write(i, 10, user.toptype)

            for key in ['ptimestamp', 'ttimestamp']:
                if user[key]:
                    #user[key] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(user[key]/1000))
                    timestamp = str(user[key])
                    user[key] = timestamp[0:4] + '-' + timestamp[4:6] + '-' +\
                                timestamp[6:8] + ' ' + timestamp[8:10] + ':' +\
                                timestamp[10:12] + ':' + timestamp[12:14]
            ws.write(i, 11, user.ptimestamp)
            ws.write(i, 12, user.ttimestamp)
            ws.col(2).width = 0x0c00
            ws.col(3).width = 0x0c00
            ws.col(11).width = 0x1200
            ws.col(12).width = 0x1200

        _tmp_file = StringIO()
        wb.save(_tmp_file)
        filename = self.generate_file_name(USER_FILE_NAME)

        self.set_header('Content-Type', 'application/force-download')
        self.set_header('Content-Disposition', 'attachment; filename=%s.xls' % (filename,))

        # move to the begin
        _tmp_file.seek(0, SEEK_SET)
        self.write(_tmp_file.read())
        _tmp_file.close()
