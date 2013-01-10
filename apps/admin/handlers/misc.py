# -*- coding: utf-8 -*-

import tornado.web
from tornado.escape import json_encode, json_decode

from utils.dotdict import DotDict
from utils.misc import safe_unicode, DUMMY_IDS
from codes.errorcode import ErrorCode

from base import BaseHandler, authenticated
from mixin import BaseMixin


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

class CorpListHandler(BaseHandler):

    @authenticated
    @tornado.web.removeslash
    def get(self):
        """
        """

        corps = self.db.query("SELECT id, name FROM T_CORP")
            
        self.set_header(*self.JSON_HEADER)
        self.write(json_encode(corps))
        
class CheckTMobileHandler(BaseHandler):

    @authenticated
    @tornado.web.removeslash
    def get(self, mobile):
        """
        """

        ret = DotDict(status=ErrorCode.SUCCESS,
                      message=None)
        corp = self.db.get("SELECT id"
                           "  FROM T_TERMINAL_INFO"
                           "  WHERE mobile = %s"
                           "   LIMIT 1",
                           mobile)
        if corp:
            ret.status = ErrorCode.TERMINAL_ORDERED
            ret.message = ErrorCode.ERROR_MESSAGE[ret.status]
            
        self.set_header(*self.JSON_HEADER)
        self.write(json_encode(ret))
        

class CheckECMobileHandler(BaseHandler):

    @authenticated
    @tornado.web.removeslash
    def get(self, mobile):
        """
        """

        ret = DotDict(status=ErrorCode.SUCCESS,
                      message=None)
        corp = self.db.get("SELECT id"
                           "  FROM T_CORP"
                           "  WHERE mobile = %s"
                           "   LIMIT 1",
                           mobile)
        if corp:
            ret.status = ErrorCode.EC_MOBILE_EXISTED
            ret.message = ErrorCode.ERROR_MESSAGE[ret.status]
            
        self.set_header(*self.JSON_HEADER)
        self.write(json_encode(ret))
        
class CheckECNameHandler(BaseHandler):

    @authenticated
    @tornado.web.removeslash
    def get(self, name):
        """
        """

        ret = DotDict(status=ErrorCode.SUCCESS,
                      message=None)
        corp = self.db.get("SELECT id"
                           "  FROM T_CORP"
                           "  WHERE name = %s"
                           "   LIMIT 1",
                           name)
        if corp:
            ret.status = ErrorCode.EC_NAME_EXISTED
            ret.message = ErrorCode.ERROR_MESSAGE[ret.status]
            
        self.set_header(*self.JSON_HEADER)
        self.write(json_encode(ret))
        


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
