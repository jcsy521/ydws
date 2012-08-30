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
from constants import PRIVILEGES, SMS, UWEB, GATEWAY
from utils.misc import str_to_list, DUMMY_IDS
from myutils import city_list
from mongodb.mdaily import MDaily, MDailyMixin


class BusinessMixin(BaseMixin):

    KEY_TEMPLATE = "business_report_%s_%s"

    def prepare_data(self, hash_):
        """Prepare search results for post.
        """
        mem_key = self.get_memcache_key(hash_)

        data = self.redis.getvalue(mem_key)
        if data:
            return data

        begintime = int(self.get_argument('begintime',0))
        endtime = int(self.get_argument('endtime',0))
        interval=[begintime, endtime]

        fields = DotDict(cnum="tc.cnum LIKE '%%%%%s%%%%'",
                         name="tu.name LIKE '%%%%%s%%%%'",
                         mobile="tu.mobile LIKE '%%%%%s%%%%'",
                         tmobile="tt.mobile LIKE '%%%%%s%%%%'",
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
            sql = ("SELECT tu.name, tu.mobile, tu.address, tu.email, tt.begintime, tt.endtime,"
                   "  tt.mobile as tmobile, tt.service_status, tc.cnum"
                   "  FROM T_USER as tu, T_TERMINAL_INFO as tt, T_CAR as tc"
                   "  WHERE  tu.mobile = tt.owner_mobile "
                   "    AND tt.mobile = tc.tmobile "
                   "    AND ") + where_clause
            businesses = self.db.query(sql)
        else:
            sql = ("SELECT tu.name, tu.mobile, tu.address, tu.email, tt.begintime, tt.endtime,"
                   "  tt.mobile as tmobile, tt.service_status, tc.cnum"
                   "  FROM T_USER as tu, T_TERMINAL_INFO as tt, T_CAR as tc"
                   "  WHERE  tu.mobile = tt.owner_mobile "
                   "    AND tt.mobile = tc.tmobile ")
            businesses = self.db.query(sql)
        for i, business in enumerate(businesses):
            business['seq'] = i + 1
            business['sms_status'] = self.get_sms_status(business['tmobile'])
            for key in business:
                if business[key] is None:
                    business[key] = ''

        self.redis.setvalue(mem_key,(businesses,interval), 
                            time=self.MEMCACHE_EXPIRY)
        return businesses, interval

    def get_sms_status(self, tmobile):
        """
        sms_status: 0,  // failded
                    1,  // sent
                    2,  // reached to terminal
                    3,  // terminal has connected to gataway
        """ 
        sms_status = 0
        terminal = QueryHelper.get_terminal_by_tmobile(tmobile, self.db)
        if terminal.login == GATEWAY.TERMINAL_LOGIN.LOGIN:
            sms_status = 3
        elif not terminal.msgid:
            sms_status = 0
        else:
            sms = self.db.get("SELECT send_status, recv_status"
                              "  FROM T_SMS"
                              "  WHERE msgid = %s"
                              "  AND category = %s"
                              "  LIMIT 1",
                              terminal.msgid, SMS.CATEGORY.MT)
            if not sms:
                pass
            elif sms.recv_status == 0:
                sms_status = 2
            elif sms.send_status == 0:
                sms_status = 1
        return sms_status
           
    def get_business_info(self, tmobile):
        """Get business info in detail throught tmobile.
        """
        business = self.db.get("SELECT tu.name, tu.mobile, tu.address, tu.email, tt.begintime, tt.endtime,"
                               "  tt.mobile as tmobile, tt.service_status, tc.cnum"
                               "  FROM T_USER as tu, T_TERMINAL_INFO as tt, T_CAR as tc"
                               "  WHERE  tu.mobile = tt.owner_mobile "
                               "    AND tt.mobile = tc.tmobile "
                               "    AND tt.mobile = %s"
                               "    LIMIT 1",
                               tmobile)
        if business:
            business['sms_status'] = self.get_sms_status(tmobile)
            return business
        else: 
            return None

    def modify_user_terminal_car(self, fields):
        # 1: add user
        if fields.has_key('password'): # create a new user
            uid = self.db.execute("INSERT INTO T_USER(uid, password, name, mobile, address, email)"
                                  "  VALUES(%s, password(%s), %s, %s, %s, %s)"
                                  "  ON DUPLICATE KEY"
                                  "  UPDATE uid = VALUES(uid),"
                                  "         password = VALUES(password),"
                                  "         name = VALUES(name), "
                                  "         mobile = VALUES(mobile), "
                                  "         address = VALUES(address), "
                                  "         email = VALUES(email)",
                                  fields.mobile, fields.password,
                                  fields.name, fields.mobile,
                                  fields.address, fields.email) 
        else: # modify a user
             uid = self.db.execute("INSERT INTO T_USER(uid, name, mobile, address, email)"
                                   "  VALUES(%s, %s, %s, %s, %s)"
                                   "  ON DUPLICATE KEY"
                                   "  UPDATE uid = VALUES(uid),"
                                   "         name = VALUES(name), "
                                   "         mobile = VALUES(mobile), "
                                   "         address = VALUES(address), "
                                   "         email = VALUES(email)",
                                   fields.mobile, fields.name, fields.mobile,
                                   fields.address, fields.email) 
        # 2: add terminal
        tid = self.db.execute("INSERT INTO T_TERMINAL_INFO(tid, mobile, owner_mobile,"
                              "  alias, begintime, endtime)"
                              "  VALUES (%s, %s, %s, %s, %s, %s)"
                              "  ON DUPLICATE KEY"
                              "  UPDATE tid=values(tid),"
                              "         mobile=values(mobile),"
                              "         owner_mobile=values(owner_mobile),"
                              "         alias=values(alias),"
                              "         begintime=values(begintime),"
                              "         begintime=values(begintime),"
                              "         endtime=values(endtime)",
                              fields.tmobile, fields.tmobile,
                              fields.mobile, fields.cnum, 
                              fields.begintime, fields.endtime)

        # 3: add car tnum --> cnum
        cid = self.db.execute("INSERT INTO T_CAR(cnum, tmobile)"
                              "  VALUES(%s, %s)"
                              "  ON DUPLICATE KEY"
                              "  UPDATE cnum = VALUES(cnum),"
                              "         tmobile = VALUES(tmobile)",
                              fields.cnum, fields.tmobile)
        
        # 4: send message to terminal
        #NOTE: here, not send message actually. if need, remove the annotations velow. 
        register_sms = SMSCode.SMS_REGISTER % (fields.mobile, fields.tmobile) 
        ret = SMSHelper.send(fields.tmobile, register_sms)
        ret = DotDict(json_decode(ret))
        if ret.status == ErrorCode.SUCCESS:
            self.db.execute("UPDATE T_TERMINAL_INFO"
                            "  SET msgid = %s"
                            "  WHERE mobile = %s",
                            ret['msgid'], fields.tmobile)


class BusinessCheckMobileHandler(BaseHandler, BusinessMixin):

    @authenticated
    @check_privileges([PRIVILEGES.BUSINESS_STATISTIC])
    @tornado.web.removeslash
    def get(self, mobile):
        """Check whether the owner_mobile can order a new terminal.     
        if the ower has two terminal, retrun True, give a message and do not allow continue.
        if not, return False, let the business go ahead.
        """
        status = True 
        res = self.db.query("SELECT id FROM T_TERMINAL_INFO"
                            "  WHERE owner_mobile = %s",
                            mobile)
        if len(res) < 2:
            status = False 
        self.write_ret(status)

class BusinessCheckTMobileHandler(BaseHandler, BusinessMixin):

    @authenticated
    @check_privileges([PRIVILEGES.BUSINESS_STATISTIC])
    @tornado.web.removeslash
    def get(self, tmobile):
        """Check whether the terminal can be ordered by a new owner.
        if terminal exist, return True, give a message and do not allow continue. 
        if not, return False, let the business go ahead.
        """
        status = True 
        res = self.db.get("SELECT id FROM T_TERMINAL_INFO"
                          "  WHERE mobile = %s"
                          "  LIMIT 1",
                          tmobile)
        if not res:
            status = False 
        self.write_ret(status)

class BusinessCreateHandler(BaseHandler, BusinessMixin):

    @authenticated
    @check_privileges([PRIVILEGES.BUSINESS_STATISTIC])
    @tornado.web.removeslash
    def get(self):
        """Just to create.html.
        """
        self.render('business/create.html',
                    status=ErrorCode.SUCCESS,
                    message='')

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
                         begintime="",
                         endtime="")

        for key in fields.iterkeys():
            fields[key] = self.get_argument(key,'')

        self.modify_user_terminal_car(fields)
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
                    businesses=[],
                    status=ErrorCode.SUCCESS,
                    message='')

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
                    businesses=businesses,
                    status=ErrorCode.SUCCESS,
                    message='')

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
                    business=business,
                    status=ErrorCode.SUCCESS,
                    message='')

class BusinessEditHandler(BaseHandler, BusinessMixin):

    @authenticated
    @check_privileges([PRIVILEGES.BUSINESS_STATISTIC])
    @tornado.web.removeslash
    def get(self, tmobile):
        """Jump to editer.html.
        """
        business = self.get_business_info(tmobile) 
        self.render("business/edit.html",
                    business=business,
                    status=ErrorCode.SUCCESS,
                    message='')

    @authenticated
    @check_privileges([PRIVILEGES.EDIT_ADMINISTRATOR])
    @tornado.web.removeslash
    def post(self, tmobile):
        """Modify a business.
        workflow:
        if new_user and new_terminal:
            update mobile of new user
            update owner_mobile and mobile of terminal
            update owner_mobile of other mobiles, whose owner_mobile is old owner_mobile
        elif new_user and old_terminal:
            update mobile of new user
            update owner_mobile of terminal
            update owner_mobile of other mobiles, whose owner_mobile is old owner_mobile
        elif old_user and new_terminal:
            update mobile of terminal
        elif old_user and old_terminal:
             pass
        update other info 
        """
        
        list_inject = ['name','mobile'] 
        for key in list_inject:
            v = self.get_argument(key, '')
            if not check_sql_injection(v):
               # call get method
               self.get(tmobile) 
               return

        user = QueryHelper.get_user_by_tmobile(tmobile, self.db)
        mobile_p = self.get_argument('mobile_p', '')
        tmobile_p = self.get_argument('tmobile_p', '')
        mobile_n = self.get_argument('mobile', '')
        tmobile_n = self.get_argument('tmobile', '')

        if mobile_n!=mobile_p and tmobile_n!=tmobile_p:
            self.db.execute("UPDATE T_TERMINAL_INFO"
                            "  SET mobile = %s,"
                            "      owner_mobile = %s"
                            "  WHERE mobile = %s",
                            tmobile_n, mobile_n, tmobile_p)

            self.db.execute("UPDATE T_USER"
                            "  SET mobile = %s"
                            "  WHERE mobile = %s",
                            mobile_n, mobile_p)

            # modify owner_mobile of other terminals of the owner.
            self.db.execute("UPDATE T_TERMINAL_INFO"
                            "  SET owner_mobile = %s"
                            "  WHERE owner_mobile = %s",
                            mobile_n, mobile_p)

        elif mobile_n!=mobile_p and tmobile_n==tmobile_p:
            self.db.execute("UPDATE T_TERMINAL_INFO"
                            "  SET owner_mobile = %s"
                            "  WHERE mobile = %s",
                            mobile_n, tmobile_p)

            self.db.execute("UPDATE T_USER"
                            "  SET mobile = %s"
                            "  WHERE mobile = %s",
                            mobile_n, mobile_p)

            # modify owner_mobile of other terminals of the owner.
            self.db.execute("UPDATE T_TERMINAL_INFO"
                            "  SET owner_mobile = %s"
                            "  WHERE owner_mobile = %s",
                            mobile_n, mobile_p)

        elif mobile_n==mobile_p and tmobile_n!=tmobile_p:
            self.db.execute("UPDATE T_TERMINAL_INFO"
                            "  SET mobile = %s"
                            "  WHERE mobile = %s",
                            tmobile_n, tmobile_p)

        elif mobile_n==mobile_p and tmobile_n==tmobile_p:
            pass

        fields = DotDict(name="",
                         mobile="",
                         tmobile="",
                         cnum="",
                         address="",
                         email="",
                         begintime="",
                         endtime="")
        for key in fields.iterkeys():
            fields[key] = self.get_argument(key,'')

        self.modify_user_terminal_car(fields)

        self.redirect("/business/list/%s" % tmobile_n)

class BusinessDeleteHandler(BaseHandler, BusinessMixin):

    @authenticated
    @check_privileges([PRIVILEGES.BUSINESS_STATISTIC])
    @tornado.web.removeslash
    def post(self, tmobile, service_status):
        status = ErrorCode.SUCCESS
        try: 
            self.db.execute("UPDATE T_TERMINAL_INFO"
                            "  SET service_status = %s"
                            "  WHERE mobile = %s",
                            service_status, tmobile)
        except Exception as e:
            status = ErrorCode.FAILED
            logging.exception("Stop service failed. tmobile: %s", mobile)

        self.write_ret(status)
