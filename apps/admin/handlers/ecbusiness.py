# -*- coding: utf-8 -*-

import hashlib
import logging

import tornado.web
from tornado.escape import json_decode, json_encode

from utils.dotdict import DotDict
from base import BaseHandler, authenticated
from checker import check_privileges 
from constants import PRIVILEGES, GATEWAY, SMS
from mixin import BaseMixin
from helpers.queryhelper import QueryHelper
from codes.smscode import SMSCode 
from helpers.smshelper import SMSHelper
from codes.errorcode import ErrorCode 
from utils.checker import check_sql_injection


class ECBusinessMixin(BaseMixin):
    KEY_TEMPLATE = "ec_business_report_%s_%s"
    
    def prepare_data(self, hash_):
        """Prepare search results for post.
        """
        mem_key = self.get_memcache_key(hash_)
        data = self.redis.getvalue(mem_key)
        if data:
            if data[0]:
                return data

        begintime = int(self.get_argument('begintime',0))
        endtime = int(self.get_argument('endtime',0))
        interval=[begintime, endtime]

        fields = DotDict(ecname="te.ec_name LIKE '%%%%%s%%%%'",
                         ecmobile="te.mobile LIKE '%%%%%s%%%%'",
                         cnum="tc.cnum LIKE '%%%%%s%%%%'",
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
            sql = ("SELECT te.ec_name as ecname, te.mobile as ecmobile, tu.name, tu.mobile, tu.address, tu.email, tt.begintime, tt.endtime,"
                   "  tt.mobile as tmobile, tt.service_status, tc.cnum"
                   "  FROM T_USER as tu, T_TERMINAL_INFO as tt, T_CAR as tc, T_EC as te, T_EC_GROUP as teg"
                   "  WHERE  tu.mobile = tt.owner_mobile "
                   "    AND tc.group_id = teg.id "
                   "    AND teg.ec_id = te.id "
                   "    AND tt.mobile = tc.tmobile "
                   "    AND tc.group_id != 0"
                   "    AND ") + where_clause
            businesses = self.db.query(sql)
        else:
            sql = ("SELECT te.ec_name as ecname, te.mobile as ecmobile, tu.name, tu.mobile, tu.address, tu.email, tt.begintime, tt.endtime,"
                   "  tt.mobile as tmobile, tt.service_status, tc.cnum"
                   "  FROM T_USER as tu, T_TERMINAL_INFO as tt, T_CAR as tc, T_EC as te, T_EC_GROUP as teg"
                   "  WHERE  tu.mobile = tt.owner_mobile "
                   "    AND tc.group_id = teg.id "
                   "    AND teg.ec_id = te.id "
                   "    AND tc.group_id != 0"
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
        elif terminal.msgid:
            sms_status = 1
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
        business = self.db.get("SELECT te.ec_name as ecname, te.mobile as ecmobile, tu.name, tu.mobile, tu.address, tu.email, tt.begintime, tt.endtime,"
                               "  tt.mobile as tmobile, tt.service_status, tc.cnum, tc.type, tc.color, tc.brand"
                               "  FROM T_USER as tu, T_TERMINAL_INFO as tt, T_CAR as tc, T_EC as te, T_EC_GROUP as teg"
                               "  WHERE  tu.mobile = tt.owner_mobile "
                               "    AND tt.mobile = tc.tmobile "
                               "    AND tc.group_id = teg.id "
                               "    AND teg.ec_id = te.id "
                               "    AND tc.group_id != 0"
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
            DEFAULT_GROUP = "默认组"
            ec_id = ""
            group_id = ""
            ec = self.db.get("SELECT id "
                             "  FROM T_EC "
                             "  WHERE ec_name = %s",
                             fields.ecname)
            if not ec:
                ec_id = self.db.execute("INSERT INTO T_EC(id, ec_name, mobile, password)"
                                        "  VALUES(NULL, %s, %s, password(%s))",
                                        fields.ecname, fields.ecmobile, fields.password)
                
                group_id = self.db.execute("INSERT INTO T_EC_GROUP(id, name, ec_id)"
                                           "  VALUES(NULL, %s, %s)",
                                           DEFAULT_GROUP, ec_id)
            else: 
                ec_id = ec["id"]
                group = self.db.get("SELECT id "
                                    "  FROM T_EC_GROUP "
                                    "  WHERE name = %s"
                                    "  AND ec_id = %s",
                                    DEFAULT_GROUP, ec_id)
                group_id = group["id"]
                
            user_id = self.db.execute("INSERT INTO T_USER(id, uid, password, name, mobile, address, email)"
                                      "  VALUES(NULL, %s, password(%s), %s, %s, %s, %s)"
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
            cid = self.db.execute("INSERT INTO T_CAR(id, cnum, tmobile, type, color, brand, group_id)"
                                  "  VALUES(NULL, %s, %s, %s, %s, %s, %s)"
                                  "  ON DUPLICATE KEY"
                                  "  UPDATE cnum = VALUES(cnum), "
                                  "         tmobile = VALUES(tmobile), "
                                  "         type = VALUES(type), "
                                  "         color = VALUES(color), "
                                  "         brand = VALUES(brand),"
                                  "         group_id = VALUES(group_id)",
                                  fields.cnum, fields.tmobile, fields.type, 
                                  fields.color, fields.brand, group_id)
        else: # modify a user
            user_id = self.db.execute("INSERT INTO T_USER(uid, name, mobile, address, email)"
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
    
            # 3: add car tnum --> cnum, not modify group_id
            cid = self.db.execute("INSERT INTO T_CAR(id, cnum, tmobile, type, color, brand)"
                                  "  VALUES(NULL, %s, %s, %s, %s, %s)"
                                  "  ON DUPLICATE KEY"
                                  "  UPDATE cnum = VALUES(cnum), "
                                  "         tmobile = VALUES(tmobile), "
                                  "         type = VALUES(type), "
                                  "         color = VALUES(color), "
                                  "         brand = VALUES(brand)",
                                  fields.cnum, fields.tmobile, fields.type, 
                                  fields.color, fields.brand)
        
        # 4: send message to terminal
        register_sms = SMSCode.SMS_REGISTER % (fields.mobile, fields.tmobile) 
        ret = SMSHelper.send(fields.tmobile, register_sms)
        ret = DotDict(json_decode(ret))
        if ret.status == ErrorCode.SUCCESS:
            self.db.execute("UPDATE T_TERMINAL_INFO"
                            "  SET msgid = %s"
                            "  WHERE mobile = %s",
                            ret['msgid'], fields.tmobile)
            

class ECBusinessHandler(BaseHandler):
    @authenticated
    @check_privileges([PRIVILEGES.EC_BUSINESS_STATISTIC])
    @tornado.web.removeslash
    def get(self):
        self.render('ecbusiness/create.html',
                    status=ErrorCode.SUCCESS,
                    message='')
    
            
class ECBusinessCreateHandler(BaseHandler, ECBusinessMixin):

    @authenticated
    @check_privileges([PRIVILEGES.EC_BUSINESS_STATISTIC])
    @tornado.web.removeslash
    def post(self):
        """Create business for ec user.
        """
        fields = DotDict(ecname="",
                         ecmobile="",
                         name="",
                         mobile="",
                         tmobile="",
                         password="",
                         cnum="",
                         address="",
                         email="",
                         type="",
                         begintime="",
                         endtime="",
                         color="",
                         brand="")

        for key in fields.iterkeys():
            fields[key] = self.get_argument(key,'').strip()

        self.modify_user_terminal_car(fields)
        self.redirect("/ecbusiness/list/%s" % fields.tmobile)
        
        
class ECBusinessListHandler(BaseHandler, ECBusinessMixin):

    @authenticated
    @check_privileges([PRIVILEGES.EC_BUSINESS_STATISTIC])
    @tornado.web.removeslash
    def get(self, tmobile):
        """Show the info in detail for the given business.
        #NOTE: in admin, a business is distinguished from others by tmobile.
        """
        business = self.get_business_info(tmobile) 
        self.render('ecbusiness/list.html',
                    business=business,
                    status=ErrorCode.SUCCESS,
                    message='')
        
        
class ECBusinessSearchHandler(BaseHandler, ECBusinessMixin):
    @authenticated
    @check_privileges([PRIVILEGES.EC_BUSINESS_STATISTIC])
    @tornado.web.removeslash
    def get(self):
        self.render('ecbusiness/search.html',
                    interval=[], 
                    businesses=[],
                    status=ErrorCode.SUCCESS,
                    message='')    
        
    @authenticated
    @check_privileges([PRIVILEGES.EC_BUSINESS_STATISTIC])
    @tornado.web.removeslash
    def post(self):
        """Query businesses according to the given params.
        """
        m = hashlib.md5()
        m.update(self.request.body)
        hash_ = m.hexdigest() 
        businesses, interval = self.prepare_data(hash_)
        self.render('ecbusiness/search.html',
                    interval=interval, 
                    businesses=businesses,
                    status=ErrorCode.SUCCESS,
                    message='')
        

class ECBusinessEditHandler(BaseHandler, ECBusinessMixin):

    @authenticated
    @check_privileges([PRIVILEGES.EC_BUSINESS_STATISTIC])
    @tornado.web.removeslash
    def get(self, tmobile):
        """Jump to edit.html.
        """
        business = self.get_business_info(tmobile) 
        self.render("ecbusiness/edit.html",
                    business=business,
                    status=ErrorCode.SUCCESS,
                    message='')
        
    @authenticated
    @check_privileges([PRIVILEGES.EC_BUSINESS_STATISTIC])
    @tornado.web.removeslash
    def post(self, tmobile):
        """Modify a business.
        workflow:
        if old_user and old_terminal:
            just update them 
        elif new_user and new_terminal:
            update 
        elif old_user and new_terminal:
            update
        elif new_user and old_terminal:
            update
        """
        print "body : " + self.request.body
        list_inject = ['name', 'mobile', 'type', 'color', 'brand',] 
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

            fields = DotDict(name="",
                             mobile="",
                             tmobile="",
                             cnum="",
                             type="",
                             color="",
                             brand="",
                             address="",
                             email="",
                             begintime="",
                             endtime="")

            for key in fields.iterkeys():
                fields[key] = self.get_argument(key,'')

            self.modify_user_terminal_car(fields)

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

            fields = DotDict(name="",
                             mobile="",
                             cnum="",
                             type="",
                             color="",
                             brand="",
                             address="",
                             email="",
                             begintime="",
                             endtime="")

            for key in fields.iterkeys():
                fields[key] = self.get_argument(key,'')
            fields['tmobile'] = self.get_argument('tmobile','')

            self.modify_user_terminal_car(fields)

        elif mobile_n==mobile_p and tmobile_n!=tmobile_p:
            self.db.execute("UPDATE T_TERMINAL_INFO"
                            "  SET mobile = %s"
                            "  WHERE mobile = %s",
                            tmobile_n, tmobile_p)
            fields = DotDict(name="",
                             mobile="",
                             tmobile="",
                             cnum="",
                             type="",
                             color="",
                             brand="",
                             address="",
                             email="",
                             begintime="",
                             endtime="")
            for key in fields.iterkeys():
                fields[key] = self.get_argument(key,'')
            fields['mobile'] = user.owner_mobile 

            self.modify_user_terminal_car(fields)

        elif mobile_n==mobile_p and tmobile_n==tmobile_p:
            u_fields = DotDict(mobile="mobile=%s",
                               name="name=%s",
                               address="address=%s",
                               email="email=%s")
            c_fields = DotDict(cnum="cnum=%s",
                               type="type=%s",
                               color="color=%s",
                               brand="brand=%s")
            t_fields = DotDict(tmobile="mobile=%s",
                               service_status="service_status=%s",
                               cnum="alias=%s",
                               begintime="begintime=%s",
                               endtime="endtime=%s")


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

            t_data = [self.get_argument(key, '') for key in t_fields.iterkeys()] + [tmobile]
            t_set_clause = ','.join([v for v in t_fields.itervalues()])
            if t_data:
                self.db.execute("UPDATE T_TERMINAL_INFO"
                                "  SET "+t_set_clause+
                                "  WHERE mobile = %s",
                                *t_data)

        self.redirect("/ecbusiness/list/%s" % tmobile_n)
        
        
class ECBusinessStopHandler(BaseHandler, ECBusinessMixin):

    @authenticated
    @check_privileges([PRIVILEGES.EC_BUSINESS_STATISTIC])
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
        
        
class ECBusinessDeleteHandler(BaseHandler, ECBusinessMixin):

    @authenticated
    @check_privileges([PRIVILEGES.EC_BUSINESS_STATISTIC])
    @tornado.web.removeslash
    def post(self, tmobile, pmobile):
        status = ErrorCode.SUCCESS
        try:
            self.db.execute("DELETE FROM T_CAR"
                            "  WHERE tmobile = %s",
                            tmobile)
            terminal = self.db.query("SELECT mobile"
                                     "  FROM T_TERMINAL_INFO "
                                     "  WHERE  owner_mobile = %s ",
                                     pmobile)
            self.db.execute("DELETE FROM T_TERMINAL_INFO"
                            "  WHERE mobile = %s",
                            tmobile)
            
            if len(terminal) == 1:
                self.db.execute("DELETE FROM T_USER"
                                "  WHERE mobile = %s",
                                pmobile)
            else:
                pass
            
        except Exception as e:
            status = ErrorCode.FAILED
            logging.exception("Delete service failed. tmobile: %s, pmobile: %s", tmobile, pmobile)
        self.write_ret(status)
        
# abandon
class ECBusinessCheckMobileHandler(BaseHandler, ECBusinessMixin):

    @authenticated
    @check_privileges([PRIVILEGES.EC_BUSINESS_STATISTIC])
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
        if not res:
            status = False 
        self.write_ret(status)


class ECBusinessCheckTMobileHandler(BaseHandler, ECBusinessMixin):

    @authenticated
    @check_privileges([PRIVILEGES.EC_BUSINESS_STATISTIC])
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
        