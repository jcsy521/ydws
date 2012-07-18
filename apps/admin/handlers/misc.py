# -*- coding: utf-8 -*-

import tornado.web
from tornado.escape import json_encode, json_decode

from utils.dotdict import DotDict
from utils.misc import safe_unicode, DUMMY_IDS

from base import BaseHandler, authenticated
from mixin import BaseMixin
from constants import XXT


class AreaHandler(BaseHandler, BaseMixin):

    @authenticated
    @tornado.web.removeslash
    def get(self):
       """
       return privilege_area include provinces and cities
       """
       key = self.get_area_memcache_key(self.current_user.id)
       areas = self.memcached.get(key)
       if not areas:
           areas = self.get_privilege_area(self.current_user.id)
           self.memcached.set(key, areas)

       self.set_header(*self.JSON_HEADER)
       self.write(json_encode(areas))


class ProvinceListHandler(BaseHandler, BaseMixin):

    @authenticated
    @tornado.web.removeslash
    def get(self):
        """
        return the list of provinces.
        """

        #provinces = self.db.query("SELECT * FROM T_HLR_PROVINCE")
        provinces = []
        key = self.get_area_memcache_key(self.current_user.id)
        areas = self.memcached.get(key)
        if not areas:
            areas = self.get_privilege_area(self.current_user.id)
            self.memcached.set(key, areas)
        for area in areas:
            province = DotDict(id=area.pid,
                               name=area.pname)
            provinces.append(province)

        self.set_header(*self.JSON_HEADER)
        self.write(json_encode(provinces))


class ProvinceHandler(BaseHandler, BaseMixin):

    @authenticated
    @tornado.web.removeslash
    def get(self, province_id):
        """
        return cities of the province.
        """
        
        #rs = self.db.query("SELECT region_code, city_name"
        #                   "  FROM T_HLR_CITY"
        #                   "  WHERE province_id = %s",
        #                   province_id)
        key = self.get_area_memcache_key(self.current_user.id)
        areas = self.memcached.get(key)
        if not areas:
            areas = self.get_privilege_area(self.current_user.id)
            self.memcached.set(key, areas)
        for area in areas:
            if area.pid == int(province_id):
                rs = area.city
                break

        self.set_header(*self.JSON_HEADER)
        self.write(json_encode(rs))


class GroupListHandler(BaseHandler):
    
    @authenticated
    @tornado.web.removeslash
    def post(self):
        """
        return groups of city.
        """

        data = json_decode(self.request.body)
        cities = data['city']
        if int(data['type']) == 1:
            groups = self.db.query("SELECT txg.xxt_id as id, txg.name"
                                   "  FROM T_XXT_GROUP AS txg,"
                                   "       T_ADMINISTRATOR AS ta"
                                   "  WHERE ta.login = txg.phonenum"
                                   "    AND ta.id = %s",
                                   self.current_user.id)
        else:
            groups = self.db.query("SELECT DISTINCT xxt_id as id, txg.name"
                                   "  FROM T_XXT_GROUP AS txg,"
                                   "       T_HLR_CITY AS thc"
                                   "  WHERE thc.city_id in %s"
                                   "    AND txg.city_id = thc.region_code",
                                   [item for item in cities] + DUMMY_IDS)

        self.set_header(*self.JSON_HEADER)
        self.write(json_encode(groups))
    

class AdministratorStatusHandler(BaseHandler):
    
    @authenticated
    @tornado.web.removeslash
    def post(self, administrator_id):
        """
        change administrator's status.
        """

        valid = DotDict(json_decode(self.request.body)).valid
        
        self.db.execute("UPDATE T_ADMINISTRATOR"
                        "  SET valid = %s"
                        "  WHERE id = %s",
                        valid, administrator_id)
        
        self.set_header(*self.JSON_HEADER)
        # TODO: always return true...
        self.write(json_encode(dict(success=0)))


class AdministratorLoginnameHandler(BaseHandler):
    
    @authenticated
    @tornado.web.removeslash
    def get(self, login):
        """
        check if the login has been used.
        """

        r = self.db.query("SELECT * FROM T_ADMINISTRATOR"
                          "  WHERE login = %s",
                          login)
        ret = dict(success=True if r else False)
        self.set_header(*self.JSON_HEADER)
        self.write(json_encode(ret))

class PrivilegeGroupNameHandler(BaseHandler):

    @authenticated
    @tornado.web.removeslash
    def get(self, privilegegroupname):
        """
        check whether the privilegegroupname already exists.
        """

        r = self.db.query("SELECT id FROM T_PRIVILEGE_GROUP"
                          " WHERE name = %s",safe_unicode(privilegegroupname))
        ret = dict(success=True if r else False)
        self.set_header(*self.JSON_HEADER)
        self.write(json_encode(ret))

        
class AreaPrivilegeHandler(BaseHandler):
    
    @authenticated
    @tornado.web.removeslash
    def get(self, administrator_id):
        """
        return area privileges of administrator.
        """

        from constants import AREA
        
        provinces = self.db.query("SELECT category, area_id, thp.province_name"
                                  "  FROM T_AREA_PRIVILEGE AS tap, T_HLR_PROVINCE AS thp"
                                  "  WHERE tap.administrator_id = %s"
                                  "    AND category = %s",
                                  administrator_id, AREA.CATEGORY.PROVINCE)

        cities = self.db.query("SELECT category, area_id, thc.city_name"
                               "  FROM T_AREA_PRIVILEGE AS tap, T_HLR_CITY AS thc"
                               "  WHERE tap.administrator_id = %s"
                               "    AND category = %s",
                               administrator_id, AREA.CATEGORY.CITY)

        areas = provinces.extend(cities)
        
        self.set_header(*self.JSON_HEADER)
        self.write(json_encode(areas))


class UserInfoHandler(BaseHandler):

    @authenticated
    @tornado.web.removeslash
    def get(self, mobile):
        """
        return user info according to the mobile, either user or target.
        """

        r = self.db.get("SELECT name"
                        "  FROM T_XXT_USER"
                        "  WHERE mobile = %s"
                        "   AND optype != %s"
                        "   LIMIT 1",
                        mobile,XXT.OPER_TYPE.CANCEL)
                    
        user = dict(user=r if r else None)
            
        self.set_header(*self.JSON_HEADER)
        self.write(json_encode(user))
        

class MonitorHandler(BaseHandler):

    @authenticated
    @tornado.web.removeslash
    def get(self, parent_mobile, child_mobile):
        """
        check whether these two mobiles are matching.
        """

        from helpers.queryhelper import QueryHelper

        r = QueryHelper.get_monitor_relation(parent_mobile, child_mobile, self.db)
        ret = dict(success=True if r else False)
        
        self.set_header(*self.JSON_HEADER)
        self.write(json_encode(ret))


class PrivilegeListHandler(BaseHandler): 

    @authenticated
    @tornado.web.removeslash
    def get(self):
        ret = self.db.query("SELECT * FROM T_META_PRIVILEGE")
        
        self.set_header(*self.JSON_HEADER)
        self.write(json_encode(ret))


class PrivilegeSetHandler(BaseHandler):

    @authenticated
    @tornado.web.removeslash
    def get(self, privilege_group_id):

        ret = self.db.query("SELECT tmp.id, tmp.name"
                            " FROM T_PRIVILEGE_GROUP_DATA AS tpgd, T_META_PRIVILEGE AS tmp"
                            " WHERE tpgd.privilege_group_id = %s"
                            " AND tpgd.privilege_id = tmp.id",
                            privilege_group_id)
        self.set_header(*self.JSON_HEADER)
        self.write(json_encode(ret))
