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
from mongodb.mdaily import MDaily, MDailyMixin


class BusinessMixin(BaseMixin):


    def get_sms_status(self, tmobile):
        """
        sms_status: 0,  // failded
                    1,  // sent
                    2,  // reached to terminal
                    3,  // terminal has connected to gataway
        """ 
        sms_status = 0
        terminal = QueryHelper.get_terminal_by_tmobile(tmobile, self.db)
        if terminal.login == GATEWAY.TERMINAL_LOGIN.ONLINE:
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
        business = self.db.get("SELECT tu.name, tu.mobile, tu.address, tu.email, tt.begintime, tt.endtime,"
                               "  tt.mobile as tmobile, tt.service_status, tc.cnum, tc.type, tc.color, tc.brand"
                               "  FROM T_USER as tu, T_TERMINAL_INFO as tt, T_CAR as tc"
                               "  WHERE  tu.mobile = tt.owner_mobile "
                               "    AND tt.tid = tc.tid "
                               "    AND tc.group_id = 0"
                               "    AND tt.mobile = %s"
                               "    LIMIT 1",
                               tmobile)
        if business:
            business['sms_status'] = self.get_sms_status(tmobile)
            for key in business.iterkeys():
                if business[key] is None:
                    business[key] = ''
            return business
        else: 
            return None


# abandon
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
        if not res:
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
                         type="",
                         begintime="",
                         endtime="",
                         color="",
                         brand="")
        for key in fields.iterkeys():
                fields[key] = self.get_argument(key,'')
                if not check_sql_injection(fields[key]):
                    logging.error("Create business condition contain SQL inject. %s : %s", key, fields[key])
                    self.render('errors/error.html',
                        message=ErrorCode.ERROR_MESSAGE[ErrorCode.CREATE_CONDITION_ILLEGAL])
                    return
                
        try:
            # 1: add user
            self.db.execute("INSERT INTO T_USER(id, uid, password, name, mobile, address, email, remark)"
                            "  VALUES(NULL, %s, password(%s), %s, %s, %s, %s, NULL)"
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
            self.db.execute("INSERT INTO T_TERMINAL_INFO(tid, mobile, owner_mobile,"
                            "  alias, begintime, endtime)"
                            "  VALUES (%s, %s, %s, %s, %s, %s)",
                            fields.tmobile, fields.tmobile,
                            fields.mobile, fields.cnum, 
                            fields.begintime, fields.endtime)
    
            # 3: add car tnum --> cnum
            self.db.execute("INSERT INTO T_CAR(tid, cnum, type, color, brand, group_id)"
                            "  VALUES(%s, %s, %s, %s, %s, DEFAULT)",
                            fields.tmobile, fields.cnum, 
                            fields.type, fields.color, fields.brand)
            
            # 4: add default sms report value
            sms_option = self.db.get("SELECT id FROM T_SMS_OPTION WHERE uid = %s", fields.mobile)
            if not sms_option:
                self.db.execute("INSERT INTO T_SMS_OPTION(uid)"
                                "  VALUES(%s)",
                                fields.mobile)
            
            # 5: send message to terminal
            register_sms = SMSCode.SMS_REGISTER % (fields.mobile, fields.tmobile) 
            ret = SMSHelper.send_to_terminal(fields.tmobile, register_sms)
            ret = DotDict(json_decode(ret))
            #ret = DotDict(status=0, msgid=1111)
            sms_status = 0
            if ret.status == ErrorCode.SUCCESS:
                self.db.execute("UPDATE T_TERMINAL_INFO"
                                "  SET msgid = %s"
                                "  WHERE mobile = %s",
                                ret['msgid'], fields.tmobile)
            #convert front desk need format 
                sms_status = 1
            else:
                
                sms_status = 0
                logging.error("Create business sms send failure. terminal mobile: %s, owner mobile: %s", fields.tmobile, fields.mobile)
            fields.sms_status = sms_status
            fields.service_status = 1
            self.render('business/list.html',
                        business=fields,
                        status=ErrorCode.SUCCESS,
                        message='')
        except Exception as e:
            logging.exception("Create business failed. terminal mobile: %s, owner mobile: %s", fields.tmobile, fields.mobile)
            self.render('errors/error.html',
                        message=ErrorCode.ERROR_MESSAGE[ErrorCode.CREATE_USER_FAILURE])


class BusinessSearchHandler(BaseHandler, BusinessMixin):

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
    @tornado.web.removeslash
    def post(self):
        """Query businesses according to the given params.
        """
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
                    logging.error("Search business condition contain SQL inject. %s : %s", key, v)
                    self.render('errors/error.html',
                        message=ErrorCode.ERROR_MESSAGE[ErrorCode.SELECT_CONDITION_ILLEGAL])
                    return
                else:
                    fields[key] = fields[key] % (v,)
            else:
                fields[key] = None

        where_clause = ' AND '.join([v for v in fields.itervalues()
                                     if v is not None])
        try:
            if where_clause:
                sql = ("SELECT tu.name, tu.mobile, tu.address, tu.email, tt.begintime, tt.endtime,"
                       "  tt.mobile as tmobile, tt.service_status, tc.cnum"
                       "  FROM T_USER as tu, T_TERMINAL_INFO as tt, T_CAR as tc"
                       "  WHERE  tu.mobile = tt.owner_mobile "
                       "    AND tt.tid = tc.tid "
                       "    AND tc.group_id = 0"
                       "    AND ") + where_clause
                businesses = self.db.query(sql)
            else:
                sql = ("SELECT tu.name, tu.mobile, tu.address, tu.email, tt.begintime, tt.endtime,"
                       "  tt.mobile as tmobile, tt.service_status, tc.cnum"
                       "  FROM T_USER as tu, T_TERMINAL_INFO as tt, T_CAR as tc"
                       "  WHERE  tu.mobile = tt.owner_mobile "
                       "    AND tc.group_id = 0"
                       "    AND tt.tid = tc.tid ")
                businesses = self.db.query(sql)
            for i, business in enumerate(businesses):
                business['seq'] = i + 1
                business['sms_status'] = self.get_sms_status(business['tmobile'])
                for key in business:
                    if business[key] is None:
                        business[key] = ''
            self.render('business/search.html',
                        interval=interval, 
                        businesses=businesses,
                        status=ErrorCode.SUCCESS,
                        message='')
        except Exception as e:
            logging.exception("Search business failed.")
            self.render('errors/error.html',
                        message=ErrorCode.ERROR_MESSAGE[ErrorCode.SEARCH_BUSINESS_FAILURE])


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
        """Jump to edit.html.
        """
        business = self.get_business_info(tmobile)
        self.render("business/edit.html",
                    business=business,
                    status=ErrorCode.SUCCESS,
                    message='')

    @authenticated
    @check_privileges([PRIVILEGES.BUSINESS_STATISTIC])
    @tornado.web.removeslash
    def post(self, tmobile):
        """Modify a business."""
        
        fields = DotDict(name="",
                         mobile="",
                         tmobile="",
                         cnum="",
                         color="",
                         brand="",
                         address="",
                         email="")
        
        for key in fields.iterkeys():
            fields[key] = self.get_argument(key, "")
            if fields[key]:
                if not check_sql_injection(fields[key]):
                    logging.error("Edit business condition contain SQL inject. %s : %s", key, fields[key])
                    self.render('errors/error.html',
                        message=ErrorCode.ERROR_MESSAGE[ErrorCode.EDIT_CONDITION_ILLEGAL])
                    return
                
        fields.begintime = int(self.get_argument('begintime',0))
        fields.endtime = int(self.get_argument('endtime',0))
        fields.type = int(self.get_argument('type',0))
        fields.service_status = int(self.get_argument('service_status',0))
        try:
            self.db.execute("UPDATE T_USER"
                            "  SET name = %s,"
                            "  address = %s,"
                            "  email = %s "
                            "  WHERE mobile = %s",
                            fields.name, fields.address, 
                            fields.email, fields.mobile)
            
            self.db.execute("UPDATE T_TERMINAL_INFO"
                            "  SET begintime = %s,"
                            "  endtime = %s,"
                            "  service_status = %s "
                            "  WHERE mobile = %s",
                            fields.begintime, fields.endtime, 
                            fields.service_status, fields.tmobile)
            
            terminal = self.db.get("SELECT tid "
                                   "  FROM T_TERMINAL_INFO"
                                   "  WHERE mobile = %s",
                                   fields.tmobile)
            
            self.db.execute("UPDATE T_CAR"
                            "  SET cnum = %s,"
                            "  type = %s,"
                            "  color = %s,"
                            "  brand = %s "
                            "  WHERE tid = %s",
                            fields.cnum, fields.type, 
                            fields.color, fields.brand, terminal.tid)
            t = QueryHelper.get_terminal_by_tid(terminal.tid, self.db)
            if not t.alias:
                terminal_info_key = get_terminal_info_key(terminal.tid)
                terminal_info = self.redis.getvalue(terminal_info_key)
                terminal_info['alias'] = fields.cnum if fields.cnum else fields.tmobile
                self.redis.setvalue(terminal_info_key, terminal_info)
            
            fields.sms_status = self.get_sms_status(fields.tmobile)
            self.render('business/list.html',
                        business=fields,
                        status=ErrorCode.SUCCESS,
                        message='')
        except Exception as e:
            logging.exception("Edit business failed.Terminal mobile: %s, owner mobile: %s", fields.tmobile, fields.mobile)
            self.render('errors/error.html',
                        message=ErrorCode.ERROR_MESSAGE[ErrorCode.EDIT_USER_FAILURE])
        
        
class BusinessStopHandler(BaseHandler, BusinessMixin):

    @authenticated
    @check_privileges([PRIVILEGES.BUSINESS_STATISTIC])
    @tornado.web.removeslash
    #@tornado.web.asynchronous  
    def post(self, tmobile, service_status):
        status = ErrorCode.SUCCESS
        try: 
            terminal = self.db.get("SELECT id, tid FROM T_TERMINAL_INFO"
                                   "  WHERE mobile = %s",
                                   tmobile)
            self.db.execute("UPDATE T_TERMINAL_INFO"
                            "  SET service_status = %s"
                            "  WHERE id = %s",
                            service_status, terminal.id)
            sessionID_key = get_terminal_sessionID_key(terminal.tid)
            address_key = get_terminal_address_key(terminal.tid)
            info_key = get_terminal_info_key(terminal.tid)
            lq_sms_key = get_lq_sms_key(terminal.tid)
            lq_interval_key = get_lq_interval_key(terminal.tid)
            keys = [sessionID_key, address_key, info_key, lq_sms_key, lq_interval_key]
            self.redis.delete(*keys)
        except Exception as e:
            status = ErrorCode.FAILED
            logging.exception("Set service status to %s failed. tmobile: %s", service_status, mobile)

        self.write_ret(status)
        
        
class BusinessDeleteHandler(BaseHandler, BusinessMixin):

    @authenticated
    @check_privileges([PRIVILEGES.BUSINESS_STATISTIC])
    @tornado.web.removeslash
    def post(self, tmobile, pmobile):
        status = ErrorCode.SUCCESS
        try:
            terminal = self.db.get("SELECT id, tid FROM T_TERMINAL_INFO"
                                   "  WHERE mobile = %s",
                                   tmobile)
            self.db.execute("DELETE FROM T_TERMINAL_INFO"
                            "  WHERE id = %s",
                            terminal.id)
            # unbind terminal
            seq = str(int(time.time()*1000))[-4:]
            args = DotDict(seq=seq,
                           tid=terminal.tid)
            response = GFSenderHelper.forward(GFSenderHelper.URLS.UNBIND, args) 
            logging.info("UNBind terminal: %s, response: %s", terminal.tid, response)

            # clear redis
            sessionID_key = get_terminal_sessionID_key(terminal.tid)
            address_key = get_terminal_address_key(terminal.tid)
            info_key = get_terminal_info_key(terminal.tid)
            lq_sms_key = get_lq_sms_key(terminal.tid)
            lq_interval_key = get_lq_interval_key(terminal.tid)
            keys = [sessionID_key, address_key, info_key, lq_sms_key, lq_interval_key]
            self.redis.delete(*keys)
            terminals = self.db.query("SELECT mobile"
                                      "  FROM T_TERMINAL_INFO"
                                      "  WHERE owner_mobile = %s",
                                      pmobile)
            if len(terminals) == 0:
                self.db.execute("DELETE FROM T_USER"
                                "  WHERE mobile = %s",
                                pmobile)

            
        except Exception as e:
            status = ErrorCode.FAILED
            logging.exception("Delete service failed. tmobile: %s, owner mobile: %s", tmobile, pmobile)
        self.write_ret(status)
            
