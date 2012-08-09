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
from excelheaders import BUSINESS_HEADER, BUSINESS_SHEET, BUSINESS_FILE_NAME
from base import BaseHandler, authenticated

from checker import check_areas, check_privileges 
from codes.errorcode import ErrorCode 
from utils.checker import check_sql_injection
from helpers.smshelper import SMSHelper
from helpers.seqgenerator import SeqGenerator
from helpers.gfsenderhelper import GFSenderHelper
from helpers.queryhelper import QueryHelper 
from codes.smscode import SMSCode 
from constants import PRIVILEGES, SMS, UWEB
from utils.misc import str_to_list, DUMMY_IDS
from myutils import city_list
from mongodb.mdaily import MDaily, MDailyMixin


class BusinessMixin(BaseMixin):

    KEY_TEMPLATE = "business_report_%s_%s"

    def prepare_data(self, hash_):
        """Prepare search results for post.
        """
        mem_key = self.get_memcache_key(hash_)
        
        data = self.memcached.get(mem_key)
        if data:
            return data

        begintime = int(self.get_argument('begintime',0))
        endtime = int(self.get_argument('endtime',0))
        interval=[begintime, endtime]

        fields = DotDict(cnum="tc.cnum LIKE '%%%%%s%%%%'",
                         name="tu.name LIKE '%%%%%s%%%%'",
                         mobile="tu.mobile LIKE '%%%%%s%%%%'",
                         tmobile="tt.mobile LIKE '%%%%%s%%%%'",
                         #service_status="tt.service_status = %s",
                         begintime="tt.begintime >= %s",
                         endtime="tt.endtime <= %s") 

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
            sql = ("SELECT tu.name, tu.mobile, tu.address, tu.email, tu.corporation, tt.begintime, tt.endtime,"
                   "  tt.mobile as tmobile, tt.service_status, tc.cnum"
                   "  FROM T_USER as tu, T_TERMINAL_INFO as tt, T_CAR as tc"
                   "  WHERE  tu.mobile = tt.owner_mobile "
                   "    AND tt.mobile = tc.tmobile "
                   "    AND ") + where_clause
            businesses = self.db.query(sql)
        else:

            sql = ("SELECT tu.name, tu.mobile, tu.address, tu.email, tu.corporation, tt.begintime, tt.endtime,"
                   "  tt.mobile as tmobile, tt.service_status, tc.cnum"
                   "  FROM T_USER as tu, T_TERMINAL_INFO as tt, T_CAR as tc"
                   "  WHERE  tu.mobile = tt.owner_mobile "
                   "    AND tt.mobile = tc.tmobile ")
            businesses = self.db.query(sql)
        for i, business in enumerate(businesses):
            business['seq'] = i + 1
            for key in business:
                if business[key] is None:
                    business[key] = ''

        self.memcached.set(mem_key,(businesses,interval), 
                           time=self.MEMCACHE_EXPIRY)
        return businesses, interval

    def get_business_info(self, tmobile):
        """Get business info in detail throught tmobile.
        """
        business = self.db.get("SELECT tu.name, tu.mobile, tu.address, tu.email, tu.corporation, tt.begintime, tt.endtime,"
                               "  tt.mobile as tmobile, tt.service_status, tc.cnum"
                               "  FROM T_USER as tu, T_TERMINAL_INFO as tt, T_CAR as tc"
                               "  WHERE  tu.mobile = tt.owner_mobile "
                               "    AND tt.mobile = tc.tmobile "
                               "    AND tt.mobile = %s",
                               tmobile)
        if business:
            return business
        else: 
            return None
   
class BusinessCheckMobileHandler(BaseHandler, BusinessMixin):

    @authenticated
    @check_privileges([PRIVILEGES.BUSINESS_STATISTIC])
    @tornado.web.removeslash
    def get(self, mobile):
        """Check whether the mobile exists or not in T_USER. If exists, return True, else False.
        """
        status = False 
        res = self.db.get("SELECT id FROM T_USER"
                          "  WHERE mobile = %s"
                          "  LIMIT 1",
                          mobile)
        if res:
            status = True 
        self.write_ret(status)

class BusinessCheckTMobileHandler(BaseHandler, BusinessMixin):

    @authenticated
    @check_privileges([PRIVILEGES.BUSINESS_STATISTIC])
    @tornado.web.removeslash
    def get(self, tmobile):
        """Check whether the mobile exists or not in T_TERMINAL_INFO. If exists, return True, else False.
        """
        status = False 
        res = self.db.get("SELECT id FROM T_TERMINAL_INFO"
                          "  WHERE mobile = %s"
                          "  LIMIT 1",
                          tmobile)
        if res:
            status = True 
        self.write_ret(status)

class BusinessCreateHandler(BaseHandler, BusinessMixin):

    @authenticated
    @check_privileges([PRIVILEGES.BUSINESS_STATISTIC])
    @tornado.web.removeslash
    def get(self):
        """Just to create.html.
        """
        self.render('business/create.html')

    @authenticated
    @check_privileges([PRIVILEGES.BUSINESS_STATISTIC])
    @tornado.web.removeslash
    def post(self):
        """Create business for a couple of users.
        """
        fields = DotDict(name="",
                         mobile="",
                         tmobile="",
                         password="",
                         cnum="",
                         address="",
                         email="",
                         corporation="",
                         begintime="",
                         endtime="")

        for key in fields.iterkeys():
            fields[key] = self.get_argument(key,'')

        # 1: add user
        uid = self.db.execute("INSERT INTO T_USER(uid, password, name, mobile, address,"
                              "  email, corporation)"
                              "  VALUES (%s, password(%s), %s, %s, %s, %s, %s)",
                              fields.mobile, fields.password,
                              fields.name, fields.mobile,
                              fields.address, fields.email, 
                              fields.corporation)

        # 2: add terminal
        tid = self.db.execute("INSERT INTO T_TERMINAL_INFO(tid, mobile, owner_mobile,"
                              "  begintime, endtime)"
                              "  VALUES (%s, %s, %s, %s, %s)",
                              fields.tmobile, fields.tmobile,
                              fields.mobile, fields.begintime, 
                              fields.endtime)

        # 3: add car tnum --> cnum
        cid = self.db.execute("INSERT INTO T_CAR"
                              "  VALUES(NULL, %s, %s)"
                              "  ON DUPLICATE KEY"
                              "  UPDATE cnum = VALUES(cnum),"
                              "         tmobile = VALUES(tmobile)",
                              fields.cnum, fields.tmobile)
        
        # 4: send message to terminal
        register_sms = SMSCode.SMS_REGISTER % (fields.mobile, fields.tmobile) 
        ret = SMSHelper.send(fields.tmobile, register_sms)
        ret = DotDict(json_decode(ret))
        if ret.status == ErrorCode.SUCCESS:
            self.db.execute("UPDATE T_TERMINAL_INFO"
                            "  SET msgid = %s"
                            "  WHERE mobile = %s",
                            ret['msgid'], fields.tmobile)
        self.redirect("/business/list/%s" % fields.tmobile)
        

class BusinessSearchHandler(BaseHandler, BusinessMixin):

    @authenticated
    @check_privileges([PRIVILEGES.BUSINESS_STATISTIC])
    @tornado.web.removeslash
    def prepare(self):
        # TODO: if any nees, prepare can be invoked before the actual handler method.
        pass

    @authenticated
    @check_privileges([PRIVILEGES.BUSINESS_STATISTIC])
    @tornado.web.removeslash
    def get(self):
        self.render('business/search.html',
                    interval=[], 
                    businesses=[])

    @authenticated
    @check_privileges([PRIVILEGES.BUSINESS_STATISTIC])
    #@check_areas()
    @tornado.web.removeslash
    def post(self):
        """Query bsinesses according to the given params.
        """
        m = hashlib.md5()
        m.update(self.request.body)
        hash_ = m.hexdigest() 
        businesses, interval = self.prepare_data(hash_)
        self.render('business/search.html',
                    interval=interval, 
                    businesses=businesses)

class BusinessListHandler(BaseHandler, BusinessMixin):

    @authenticated
    @check_privileges([PRIVILEGES.BUSINESS_STATISTIC])
    @tornado.web.removeslash
    def get(self, tmobile):
        """Show the info in detail for the given business.
        #NOTE: in admin, a business is distinguished from others by tmobile.
        """
        business = self.get_business_info(tmobile) 
        self.render('business/list.html',
                    success=True,
                    business=business)

class BusinessEditHandler(BaseHandler, BusinessMixin):

    @authenticated
    @check_privileges([PRIVILEGES.BUSINESS_STATISTIC])
    @tornado.web.removeslash
    def get(self, tmobile):
        """Jump to editer.html.
        """
        business = self.get_business_info(tmobile) 
        self.render("business/edit.html",
                    business=business)

    @authenticated
    @check_privileges([PRIVILEGES.EDIT_ADMINISTRATOR])
    @tornado.web.removeslash
    def post(self, tmobile):
        """Modify a business.
        """
        # for user
        u_fields = DotDict(name="name=%s",
                           address="address=%s",
                           email="email=%s",
                           corporation="corporation=%s")
        # for car
        c_fields = DotDict(cnum="cnum=%s")
        # for terminal
        t_fields = DotDict(service_status="service_status=%s",
                           begintime="begintime=%s",
                           endtime="endtime=%s")

        list_inject = ['corporation','name','mobile'] 
        for key in list_inject:
            v = self.get_argument(key, '')
            if not check_sql_injection(v):
               self.get(administrator_id) 
               return
        user = QueryHelper.get_user_by_tmobile(tmobile, self.db) 
        u_data = [self.get_argument(key, '') for key in u_fields.iterkeys()] + [user.owner_mobile]
        u_set_clause = ','.join([v for v in u_fields.itervalues()])
        if u_data:
            self.db.execute("UPDATE T_USER"
                            "  SET "+u_set_clause+
                            "  WHERE mobile = %s",
                            *u_data)
        
        c_data = [self.get_argument(key, '') for key in c_fields.iterkeys()] + [tmobile]
        c_set_clause = ','.join([v for v in c_fields.itervalues()])
        if c_data:
            self.db.execute("UPDATE T_CAR"
                            "  SET "+c_set_clause+
                            "  WHERE tmobile = %s",
                            *c_data)

        # TODO: ...
        t_data = [self.get_argument(key, '') for key in t_fields.iterkeys()] + [tmobile]
        t_set_clause = ','.join([v for v in t_fields.itervalues()])
        if t_data:
            self.db.execute("UPDATE T_TERMINAL_INFO"
                            "  SET "+t_set_clause+
                            "  WHERE mobile = %s",
                            *t_data)
        self.redirect("/business/list/%s" % tmobile)

class BusinessDeleteHandler(BaseHandler, BusinessMixin):

    @authenticated
    @check_privileges([PRIVILEGES.BUSINESS_STATISTIC])
    @tornado.web.removeslash
    #@tornado.web.asynchronous  
    def post(self, tmobile, service_status):
        status = ErrorCode.SUCCESS
        try: 
            self.db.execute("UPDATE T_TERMINAL_INFO"
                            "  SET service_status = %s"
                            "  WHERE mobile = %s",
                            service_status, tmobile)
        except Exception as e:
            status = ErrorCode.SUCCESS
            logging.exception("Stop service failed. tmobile: %s", mobile)

        #NOTE: here just modify database.
        #terminal = QueryHelper.get_terminal_by_tmobile(tmobile, self.db)
        #args = DotDict(seq=SeqGenerator.next(self.db),
        #               tid=terminal.tid)
        #args.params = DotDict(service_status=service_status) 
        #def _on_finish(response):
        #    status = ErrorCode.SUCCESS
        #    response = json_decode(response)
        #    if response['success'] == 0:
        #        self.update_terminal_info(response['params'], data, self.current_user.tid)
        #    else:
        #        status = response['success'] 
        #        logging.error("[UWEB] Set terminal failed. status: %s, message: %s", 
        #                       status, ErrorCode.ERROR_MESSAGE[status] )
        #    self.write_ret(status)
        #    IOLoop.instance().add_callback(self.finish)       
        #if args.params:
        #    GFSenderHelper.async_forward(GFSenderHelper.URLS.TERMINAL, args,
        #                                      _on_finish)
        #else: 
        #    self.write_ret(status)
        #    IOLoop.instance().add_callback(self.finish)

        self.write_ret(status)
