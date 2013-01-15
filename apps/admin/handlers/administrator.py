# -*- coding: utf-8 -*-

from urllib import quote

import tornado.web
from tornado.escape import json_decode, json_encode

from utils.dotdict import DotDict
from utils.misc import DUMMY_IDS, safe_utf8
from constants import AREA
from utils.misc import str_to_list
from utils.checker import check_sql_injection

from errors import ErrorCode
from base import BaseHandler, authenticated 
from mixin import BaseMixin
from checker import check_privileges
from constants import PRIVILEGES


class AdministratorSearchHandler(BaseHandler):

    @authenticated
    @tornado.web.removeslash
    def prepare(self):
        self.sources = self.db.query("SELECT * FROM T_ADMINISTRATOR_SOURCE")
        
    @authenticated
    @check_privileges([PRIVILEGES.QUERY_ADMINISTRATOR])
    @tornado.web.removeslash
    def get(self):
        self.render("administrator/search.html",
                    sources=self.sources,
                    administrators=[])


    @authenticated
    @check_privileges([PRIVILEGES.QUERY_ADMINISTRATOR])
    @tornado.web.removeslash
    def post(self):
        # TODO: this is ugly!
        fields = DotDict(corporation="corporation LIKE '%%%%%s%%%%'",
                         name="name LIKE '%%%%%s%%%%'",
                         mobile="mobile LIKE '%%%%%s%%%%'",
                         phone="phone LIKE '%%%%%s%%%%'",
                         login="login LIKE '%%%%%s%%%%'",
                         valid="valid = %s",
                         source_id="source_id = %s")
        for key in fields.iterkeys():
            v = self.get_argument(key, None)
            if v:
                if not check_sql_injection(v):
                    self.get()
                    return  
                fields[key] = fields[key] % (v,)
            else:
                 fields[key] = None

        where_clause = ' AND '.join([v for v in fields.itervalues()
                                     if v is not None])
        if where_clause:
            sql = ("SELECT id, corporation, name, mobile,"
                   "       phone, login, valid, type"
                   "  FROM T_ADMINISTRATOR"
                   "  WHERE ") + where_clause
            administrators = self.db.query(sql)
        else:
            administrators = []
        for i, administrator in enumerate(administrators):
            administrator['seq'] = i + 1
            for key in administrator:
                if administrator[key] is None:
                    administrator[key] = ''
        self.render("administrator/search.html",
                    sources=self.sources,
                    administrators=administrators)


class AdministratorMixin(BaseMixin):
    def get_administrator_info(self, administrator_id):
        administrator = self.db.get("SELECT id, corporation, name, mobile,"
                                    "       phone, login, valid,"
                                    "       email, source_id, type"
                                    "  FROM T_ADMINISTRATOR"
                                    "  WHERE id = %s",
                                    administrator_id)
        if administrator:
            for key in administrator:
                if administrator[key] is None:
                    administrator[key] = ''
            administrator = DotDict(administrator)
            
            privileges = self.db.query("SELECT tpg.id"
                                       "  FROM T_PRIVILEGE AS tp, T_PRIVILEGE_GROUP AS tpg"
                                       "  WHERE tp.privilege_group_id = tpg.id"
                                       "    AND tp.administrator_id = %s",
                                       administrator_id)
            privilege_list = [p.id for p in privileges]
            privilege_groups = self.db.query("SELECT id, name, builtin AS valid FROM T_PRIVILEGE_GROUP")
            for p in privilege_groups:
                if p['id'] in privilege_list:
                    p['valid'] = 1
                else:
                    p['valid'] = 0
            administrator.privileges = privilege_groups
            
            key = self.get_area_memcache_key(administrator_id)
            areas = self.redis.getvalue(key)
            if not areas:
                areas = self.get_privilege_area(administrator_id)
                self.redis.setvalue(key, areas)
            administrator.cities = areas 
            return administrator

        
class AdministratorListHandler(BaseHandler, AdministratorMixin):

    @authenticated
    @check_privileges([PRIVILEGES.LIST_ADMINISTRATOR])
    @tornado.web.removeslash
    def get(self, administrator_id):
        success = True
        message = None

        administrator = self.get_administrator_info(administrator_id)
        if not administrator:
            success = False
            message = ErrorCode.USER_NOT_FOUND

        self.render("administrator/list.html",
                    administrator=administrator,
                    success=success,
                    message=message)


class AdministratorSelfEditHandler(BaseHandler):

    @authenticated
    @tornado.web.removeslash
    def get(self):
        self.redirect("/administrator/list/" + self.current_user.id)

class AdministratorEditHandler(BaseHandler, AdministratorMixin):

    @authenticated
    @check_privileges([PRIVILEGES.EDIT_ADMINISTRATOR])
    @tornado.web.removeslash
    def get(self, administrator_id):
        success = True
        message = None

        administrator = self.get_administrator_info(administrator_id)
        if not administrator:
            success = False
            message = ErrorCode.USER_NOT_FOUND

        sources = self.db.query("SELECT * FROM T_ADMINISTRATOR_SOURCE")
        area = self.db.get("SELECT area_id FROM T_AREA_PRIVILEGE"
                           "  WHERE administrator_id = %s"
                           "    AND category = %s",
                           self.current_user.id, AREA.CATEGORY.PROVINCE)
        if area:
            cities = self.db.query("SELECT city_id, city_name"
                                   "  FROM T_HLR_CITY"
                                   "  WHERE province_id = %s",
                                   area.area_id)
        else:
            area = self.db.query("SELECT area_id FROM T_AREA_PRIVILEGE"
                                 "  WHERE administrator_id = %s"
                                 "    AND category = %s",
                                 self.current_user.id, AREA.CATEGORY.CITY)
            region_codes = [a.area_id for a in area]
            cities = self.db.query("SELECT city_id, city_name"
                                   "  FROM T_HLR_CITY"
                                   "  WHERE region_code IN %s",
                                   tuple(region_codes + DUMMY_IDS))

        self.render("administrator/edit.html",
                    administrator=administrator,
                    sources=sources,
                    cities=cities,
                    success=success,
                    message=message,
                    is_self=administrator_id == self.current_user.id)
        
    @authenticated
    @check_privileges([PRIVILEGES.EDIT_ADMINISTRATOR])
    @tornado.web.removeslash
    def post(self, administrator_id):
        is_self = (administrator_id == self.current_user.id)

        # update basic info
        fields = DotDict(corporation="corporation = %s",
                         name="name = %s",
                         mobile="mobile = %s",
                         phone="phone = %s",
                         email="email = %s",
                         valid="valid = %s",
                         source_id="source_id = %s"
                         )
        list_inject = ['corporation','name','mobile','phone'] 
        for key in list_inject:
            v = self.get_argument(key, '')
            if not check_sql_injection(v):
               self.get(administrator_id) 
               return
        if is_self:
            del fields['valid']
            del fields['source_id']

            self.bookkeep(dict(id=self.current_user.id, 
                           session_id=self.current_user.session_id),
                      quote(safe_utf8(self.get_argument('name', u""))))

        data = [self.get_argument(key, '') for key in fields.iterkeys()] + [administrator_id]

        set_clause = ','.join([v for v in fields.itervalues()])

        self.db.execute("UPDATE T_ADMINISTRATOR"
                        " SET " + set_clause +
                        "  WHERE id = %s",
                        *data)

        if not is_self:
            # update privilege
            privileges = map(int, self.get_arguments('privileges'))
            if privileges:
                rs = self.db.query("SELECT privilege_group_id FROM T_PRIVILEGE"
                                   "  WHERE administrator_id = %s",
                                   administrator_id)
                ids = [r.privilege_group_id for r in rs]
                new_ids = list(set(privileges) - set(ids))
                old_ids = list(set(ids) - set(privileges))
                # clean up old ids
                self.db.execute("DELETE FROM T_PRIVILEGE"
                                "  WHERE administrator_id = %s"
                                "    AND privilege_group_id in %s",
                                administrator_id, tuple(old_ids + DUMMY_IDS))
                # insert new ids
                self.db.executemany("INSERT INTO T_PRIVILEGE"
                                    "  VALUES (%s, %s)",
                                    [(administrator_id, priv)
                                     for priv in new_ids])

            key = self.get_area_memcache_key(administrator_id)
            cities = [int(i) for i in str_to_list(self.get_argument('cities', ''))]
            if len(cities) == 1 and int(cities[0]) == 0:
                self.db.execute("DELETE FROM T_AREA_PRIVILEGE"
                                "  WHERE administrator_id = %s",
                                administrator_id)
                self.db.execute("INSERT INTO T_AREA_PRIVILEGE"
                                "  VALUES(NULL, %s, %s, %s)",
                                administrator_id, AREA.CATEGORY.PROVINCE,
                                AREA.PROVINCE.LIAONING) 
                cities = self.db.query("SELECT city_id, city_name FROM T_HLR_CITY"
                                       "  WHERE province_id = %s",
                                       AREA.PROVINCE.LIAONING)
                self.redis.setvalue(key, cities)
            else:
                if cities:
                    areas = self.get_area(cities)
                    self.redis.setvalue(key, areas)

                    cities = self.db.query("SELECT region_code FROM T_HLR_CITY"
                                           "  WHERE city_id IN %s",
                                           tuple(cities + DUMMY_IDS))
                    cids = [c.region_code for c in cities]
                    rs = self.db.query("SELECT area_id FROM T_AREA_PRIVILEGE"
                                       "  WHERE category = %s"
                                       "    AND administrator_id = %s",
                                       AREA.CATEGORY.CITY, administrator_id)
                    ids = [r.area_id for r in rs]
                    new_ids = list(set(cids) - set(ids))
                    old_ids = list(set(ids) - set(cids))
                    # clean up old ids
                    self.db.execute("DELETE FROM T_AREA_PRIVILEGE"
                                    "  WHERE administrator_id = %s"
                                    "    AND category = %s"
                                    "    AND area_id in %s",
                                    administrator_id, AREA.CATEGORY.CITY,
                                    tuple(old_ids + DUMMY_IDS))
                    self.db.execute("DELETE FROM T_AREA_PRIVILEGE"
                                    "  WHERE administrator_id = %s"
                                    "    AND category = %s",
                                    administrator_id, AREA.CATEGORY.PROVINCE)
                    # insert new ids
                    self.db.executemany("INSERT INTO T_AREA_PRIVILEGE"
                                        "  VALUES (NULL, %s, %s, %s)",
                                        [(administrator_id, AREA.CATEGORY.CITY, id)
                                         for id in new_ids])
                else:
                    self.db.execute("DELETE FROM T_AREA_PRIVILEGE"
                                    "  WHERE administrator_id = %s",
                                    administrator_id)
                    self.redis.delete(key)


        self.redirect("/administrator/list/%s" % administrator_id)

        
class AdministratorCreateHandler(BaseHandler, BaseMixin):

    @authenticated
    @check_privileges([PRIVILEGES.CREATE_ADMINISTRATOR])
    @tornado.web.removeslash
    def get(self):
        self.privilege_groups = self.db.query("SELECT * FROM T_PRIVILEGE_GROUP")
        self.sources = self.db.query("SELECT * FROM T_ADMINISTRATOR_SOURCE order by id")
        key = self.get_area_memcache_key(self.current_user.id)
        areas = self.redis.getvalue(key)
        if not areas:
            areas = self.get_privilege_area(self.current_user.id)
            self.redis.setvalue(key, areas)
        self.render("administrator/create.html",
                    sources=self.sources,
                    cities=areas,
                    privilege_groups=self.privilege_groups)

    @authenticated
    @check_privileges([PRIVILEGES.CREATE_ADMINISTRATOR])
    @tornado.web.removeslash
    def post(self):
        # create
        fields = DotDict(corporation="",
                         name="",
                         login="",
                         password="",
                         mobile="",
                         phone="",
                         email="",
                         valid="",
                         source_id="")

        list_inject = ['name','password','mobile','phone']
        for key in list_inject:
            v = self.get_argument(key,'')
            if not check_sql_injection(v):
                self.get()
                return
        for key in fields.iterkeys():
            fields[key] = self.get_argument(key,'')

        fields.source_id = fields.source_id if fields.source_id else 5
        administrator_id = self.db.execute("INSERT INTO T_ADMINISTRATOR (login, password, name, mobile, phone, email, "
                                           "corporation, source_id, valid, type)"
                                           "  VALUES (%s, password(%s), %s, %s, %s, %s, %s, %s, %s, %s)",
                                           fields.login, fields.password,
                                           fields.name, fields.mobile,
                                           fields.phone, fields.email,
                                           fields.corporation,
                                           fields.source_id, fields.valid, 2)
        # insert privilege
        privileges = map(int, self.get_arguments('privileges'))
        if privileges:
            self.db.executemany("INSERT INTO T_PRIVILEGE"
                                "  VALUES (%s, %s)",
                                [(administrator_id, id)
                                 for id in privileges])

        cities = map(int, str_to_list(self.get_argument('cities', '')))
        key = self.get_area_memcache_key(administrator_id)
        if len(cities) == 1 and cities[0] == 0:
            self.db.execute("INSERT INTO T_AREA_PRIVILEGE"
                            "  VALUES(NULL, %s, %s, %s)",
                            administrator_id, AREA.CATEGORY.PROVINCE,
                            AREA.PROVINCE.LIAONING) 
            cities = self.db.query("SELECT city_id, city_name FROM T_HLR_CITY"
                                   "  WHERE province_id = %s",
                                   AREA.PROVINCE.LIAONING)
            self.redis.setvalue(key, cities)
        else:
            # put privilege_areas into memcached
            areas = self.get_area(cities)
            self.redis.setvalue(key, areas)

            cities = self.db.query("SELECT region_code FROM T_HLR_CITY"
                                   "  WHERE city_id IN %s",
                                   tuple(cities + DUMMY_IDS))
            cids = [c.region_code for c in cities]

            for cid in cids:
                self.db.execute("INSERT INTO T_AREA_PRIVILEGE"
                                "  VALUES (NULL, %s, %s, %s)",
                                administrator_id, AREA.CATEGORY.CITY, cid)

        self.redirect("/administrator/list/%s" % administrator_id)


class AdministratorDeleteHandler(BaseHandler, BaseMixin):

    @authenticated
    @check_privileges([PRIVILEGES.DELETE_ADMINISTRATOR])
    @tornado.web.removeslash
    def post(self, administrator_id):
        if administrator_id == self.current_user.id:
            ret = dict(success=1)
        else:
            self.db.execute("DELETE FROM T_ADMINISTRATOR"
                            "  WHERE id = %s",
                            administrator_id)
            ret = dict(success=0)
            key = self.get_area_memcache_key(administrator_id) 
            self.redis.delete(key)
        self.set_header(*self.JSON_HEADER)
        self.write(json_encode(ret))


