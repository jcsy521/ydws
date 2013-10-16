
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
from base import BaseHandler, authenticated

from checker import check_areas, check_privileges 
from codes.errorcode import ErrorCode 
from utils.checker import check_sql_injection, check_zs_phone
from utils.misc import get_terminal_address_key, get_terminal_sessionID_key,\
     get_terminal_info_key, get_lq_sms_key, get_lq_interval_key
from helpers.smshelper import SMSHelper
from helpers.seqgenerator import SeqGenerator
from helpers.gfsenderhelper import GFSenderHelper
from helpers.queryhelper import QueryHelper 
from codes.smscode import SMSCode 
from constants import PRIVILEGES, SMS, UWEB, GATEWAY
from utils.misc import str_to_list, DUMMY_IDS, get_terminal_info_key
from utils.public import record_add_action
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
        business = self.db.get("SELECT tu.name as uname, tu.mobile as umobile, tu.address, tu.email, tt.mobile as tmobile,"
                               "  tt.service_status, tt.begintime, tt.endtime, tc.cnum, tc.type as ctype, tc.color as ccolor,"
                               "  tc.brand as cbrand, tcorp.name as ecname"
                               "  FROM T_TERMINAL_INFO as tt LEFT JOIN T_CAR as tc ON tt.tid = tc.tid"
                               "                             LEFT JOIN T_USER as tu ON tt.owner_mobile = tu.mobile"
                               "                             LEFT JOIN T_GROUP as tg ON tt.group_id = tg.id"
                               "                             LEFT JOIN T_CORP as tcorp ON tg.corp_id = tcorp.cid"
                               "  WHERE tt.mobile = %s", tmobile)
        if business:
            business['sms_status'] = self.get_sms_status(tmobile)
            for key in business.iterkeys():
                if business[key] is None:
                    business[key] = ''
            return business
        else: 
            return None


class BusinessCreateHandler(BaseHandler, BusinessMixin):

    @authenticated
    @check_privileges([PRIVILEGES.CREATE_BUSINESS])
    @tornado.web.removeslash
    def get(self):
        """Just to create.html.
        """
        self.render('business/create.html',
                    status=ErrorCode.SUCCESS,
                    message='')

    @authenticated
    @check_privileges([PRIVILEGES.CREATE_BUSINESS])
    @tornado.web.removeslash
    def post(self):
        """Create business for a couple of users.
        """
        fields = DotDict(group_id="",
                         cnum="",
                         ctype="",
                         ccolor="",
                         cbrand="",
                         tmobile="",
                         begintime="",
                         endtime="",
                         uname="",
                         umobile="",
                         password="",
                         address="",
                         email="",
                         ecmobile="")
        for key in fields.iterkeys():
            fields[key] = self.get_argument(key,'')
            #if not check_sql_injection(fields[key]):
            #    logging.error("Create business condition contain SQL inject. %s : %s", key, fields[key])
            #    self.render('errors/error.html',
            #        message=ErrorCode.ERROR_MESSAGE[ErrorCode.CREATE_CONDITION_ILLEGAL])
            #    return

        white_list = check_zs_phone(fields.tmobile, self.db)
        if not white_list:
            logging.error("Create business error, %s is not whitelist", fields.tmobile)
            self.render('errors/error.html',
                message=ErrorCode.ERROR_MESSAGE[ErrorCode.MOBILE_NOT_ORDERED])
            return

        try:
            # 1: add user
            user = self.db.get("SELECT id FROM T_USER WHERE mobile = %s", fields.umobile)
            if not user:
                self.db.execute("INSERT INTO T_USER(id, uid, password, name, mobile, address, email, remark)"
                                "  VALUES(NULL, %s, password(%s), %s, %s, %s, %s, NULL)",
                                fields.umobile, fields.password,
                                fields.uname, fields.umobile,
                                fields.address, fields.email)
                self.db.execute("INSERT INTO T_SMS_OPTION(uid)"
                                "  VALUES(%s)",
                                fields.umobile)
            
            # record the add action
            record_add_action(fields.tmobile, -1, int(time.time()), self.db)

            # 2: add terminal
            if not fields.umobile:
                user_mobile = fields.ecmobile
            else:
                user_mobile = fields.umobile
            self.db.execute("INSERT INTO T_TERMINAL_INFO(tid, mobile, owner_mobile,"
                            "  begintime, endtime, offline_time)"
                            "  VALUES (%s, %s, %s, %s, %s, %s)",
                            fields.tmobile,
                            fields.tmobile, user_mobile,
                            fields.begintime, fields.endtime, fields.begintime)
    
            # 3: add car tnum --> cnum
            self.db.execute("INSERT INTO T_CAR(tid, cnum, type, color, brand)"
                            "  VALUES(%s, %s, %s, %s, %s)",
                            fields.tmobile, fields.cnum, 
                            fields.ctype, fields.ccolor, fields.cbrand)
            
            # 4: send message to terminal
            register_sms = SMSCode.SMS_REGISTER % (fields.umobile, fields.tmobile) 
            ret = SMSHelper.send_to_terminal(fields.tmobile, register_sms)
            ret = DotDict(json_decode(ret))
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
            logging.exception("Create business failed.")
            self.render('errors/error.html',
                        message=ErrorCode.ERROR_MESSAGE[ErrorCode.CREATE_USER_FAILURE])


class BusinessSearchHandler(BaseHandler, BusinessMixin):

    @authenticated
    @check_privileges([PRIVILEGES.QUERY_BUSINESS])
    @tornado.web.removeslash
    def get(self):
        corplist = self.db.query("SELECT id, name FROM T_CORP")
        self.render('business/search.html',
                    interval=[], 
                    businesses=[],
                    corplist=corplist,
                    status=ErrorCode.SUCCESS,
                    message='')


    @authenticated
    @check_privileges([PRIVILEGES.QUERY_BUSINESS])
    @tornado.web.removeslash
    def post(self):
        """Query businesses according to the given params.
        """
        corplist = self.db.query("SELECT id, name FROM T_CORP")
        corps = self.get_argument('corps', 0)
        begintime = int(self.get_argument('begintime',0))
        endtime = int(self.get_argument('endtime',0))
        interval=[begintime, endtime]
        if int(corps) == 0:
            corps = self.db.query("SELECT cid FROM T_CORP")
            corps = [str(corp.cid) for corp in corps]
            sql = "SELECT id FROM T_GROUP WHERE corp_id IN %s" % (tuple(corps + DUMMY_IDS),)
            groups = self.db.query(sql)
            groups = [str(group.id) for group in groups] + [-1,]
        else:
            corps = self.db.get("SELECT cid FROM T_CORP"
                                "  WHERE id = %s", corps)
            groups = self.db.query("SELECT id FROM T_GROUP WHERE corp_id = %s", corps.cid) 
            groups = [str(group.id) for group in groups]

        fields = DotDict(umobile="tu.mobile LIKE '%%%%%s%%%%'",
                         tmobile="tt.mobile LIKE '%%%%%s%%%%'",
                         begintime="tt.begintime >= %s",
                         endtime="tt.begintime <= %s",
                         login="tt.login = %s")
        
        for key in fields.iterkeys():
            #BIG NOTE: if online is to be got, "tt.login != 0" is good
            if key == 'login' and self.get_argument(key, None) == '1':
                fields[key] = "tt.login != 0"
                continue

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
            sql = ("SELECT tt.tid, tt.login, tu.name as uname, tu.mobile as umobile, tt.mobile as tmobile, tt.begintime, tt.endtime,"
                   "  tt.service_status, tc.cnum, tcorp.name as ecname"
                   "  FROM T_TERMINAL_INFO as tt LEFT JOIN T_CAR as tc ON tt.tid = tc.tid"
                   "                             LEFT JOIN T_USER as tu ON tt.owner_mobile = tu.mobile"
                   "                             LEFT JOIN T_GROUP as tg ON tt.group_id = tg.id"
                   "                             LEFT JOIN T_CORP as tcorp ON tg.corp_id = tcorp.cid"
                   "  WHERE tt.service_status=1 AND tt.group_id IN %s ") % (tuple(groups + DUMMY_IDS),)
            if where_clause:
                sql += ' AND ' + where_clause

            businesses = self.db.query(sql)

            for i, business in enumerate(businesses):
                business['seq'] = i + 1
                business['sms_status'] = self.get_sms_status(business['tmobile'])
                business['corp_name'] = ''
                #NOTE: if login !=0(offline), set login as 1(online)
                business['login'] = business['login'] if business['login']==0 else 1
                biz = QueryHelper.get_biz_by_mobile(business['tmobile'], self.db)
                business['biz_type'] = biz['biz_type'] if biz else 1
                terminal = QueryHelper.get_terminal_info(business['tid'], self.db, self.redis)
                business['pbat'] = terminal['pbat'] if terminal.get('pbat', None) is not None else 0 
                

                for key in business:
                    if business[key] is None:
                        business[key] = ''

            self.render('business/search.html',
                        interval=interval, 
                        businesses=businesses,
                        corplist=corplist,
                        status=ErrorCode.SUCCESS,
                        message='')
        except Exception as e:
            logging.exception("Search business failed.")
            self.render('errors/error.html',
                        message=ErrorCode.ERROR_MESSAGE[ErrorCode.SEARCH_BUSINESS_FAILURE])


class BusinessListHandler(BaseHandler, BusinessMixin):

    @authenticated
    @check_privileges([PRIVILEGES.LIST_BUSINESS])
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
    @check_privileges([PRIVILEGES.EDIT_BUSINESS])
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
    @check_privileges([PRIVILEGES.EDIT_BUSINESS])
    @tornado.web.removeslash
    def post(self, tmobile):
        """Modify a business."""
        
        fields = DotDict(cnum="",
                         ctype="",
                         ccolor="",
                         cbrand="",
                         uname="",
                         umobile="",
                         tmobile="",
                         service_status="",
                         begintime="",
                         endtime="",
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
                
        try:
            self.db.execute("UPDATE T_USER"
                            "  SET name = %s,"
                            "      address = %s,"
                            "      email = %s "
                            "  WHERE mobile = %s",
                            fields.uname, fields.address, 
                            fields.email, fields.umobile)
            
            self.db.execute("UPDATE T_TERMINAL_INFO"
                            "  SET begintime = %s,"
                            "      endtime = %s,"
                            "      service_status = %s "
                            "  WHERE mobile = %s",
                            fields.begintime, fields.endtime, 
                            fields.service_status, fields.tmobile)
            
            terminal = self.db.get("SELECT tid "
                                   "  FROM T_TERMINAL_INFO"
                                   "  WHERE mobile = %s",
                                   fields.tmobile)
            
            self.db.execute("UPDATE T_CAR"
                            "  SET cnum = %s,"
                            "      type = %s,"
                            "      color = %s,"
                            "      brand = %s "
                            "  WHERE tid = %s",
                            fields.cnum, fields.ctype, 
                            fields.ccolor, fields.cbrand, terminal.tid)
            terminal_info_key = get_terminal_info_key(terminal.tid)
            terminal_info = self.redis.getvalue(terminal_info_key)
            if terminal_info:
                terminal_info['alias'] = fields.cnum if fields.cnum else fields.tmobile
                self.redis.setvalue(terminal_info_key, terminal_info)
            
            fields.sms_status = self.get_sms_status(fields.tmobile)
            self.render('business/list.html',
                        business=fields,
                        status=ErrorCode.SUCCESS,
                        message='')
        except Exception as e:
            logging.exception("Edit business failed.Terminal mobile: %s, owner mobile: %s",
                              tmobile)
            self.render('errors/error.html',
                        message=ErrorCode.ERROR_MESSAGE[ErrorCode.EDIT_USER_FAILURE])
        
        
        
class BusinessDeleteHandler(BaseHandler, BusinessMixin):

    @authenticated
    @check_privileges([PRIVILEGES.DELETE_BUSINESS])
    @tornado.web.removeslash
    def post(self, tmobile, pmobile):
        status = ErrorCode.SUCCESS
        try:
            terminal = self.db.get("SELECT id, tid FROM T_TERMINAL_INFO"
                                   "  WHERE mobile = %s",
                                   tmobile)
            # unbind terminal
            seq = str(int(time.time()*1000))[-4:]
            args = DotDict(seq=seq,
                           tid=terminal.tid)
            response = GFSenderHelper.forward(GFSenderHelper.URLS.UNBIND, args)
            response = json_decode(response)
            if response['success'] == ErrorCode.SUCCESS:
                logging.info("[UWEB] umobile: %s, tid: %s, tmobile:%s GPRS unbind successfully", 
                             pmobile, terminal.tid, tmobile)
            else:
                status = response['success']
                # unbind failed. clear sessionID for relogin, then unbind it again
                sessionID_key = get_terminal_sessionID_key(terminal.tid)
                self.redis.delete(sessionID_key)
                logging.error('[UWEB] umobile:%s, tid: %s, tmobile:%s GPRS unbind failed, message: %s, send JB sms...', 
                              pmobile, terminal.tid, tmobile, ErrorCode.ERROR_MESSAGE[status])
                unbind_sms = SMSCode.SMS_UNBIND  
                ret = SMSHelper.send_to_terminal(tmobile, unbind_sms)
                ret = DotDict(json_decode(ret))
                status = ret.status
                if ret.status == ErrorCode.SUCCESS:
                    self.db.execute("UPDATE T_TERMINAL_INFO"
                                    "  SET service_status = %s"
                                    "  WHERE id = %s",
                                    UWEB.SERVICE_STATUS.TO_BE_UNBIND,
                                    terminal.id)
                    logging.info("[UWEB] umobile: %s, tid: %s, tmobile: %s SMS unbind successfully.",
                                 pmobile, terminal.tid, tmobile)
                else:
                    logging.error("[UWEB] umobile: %s, tid: %s, tmobile: %s SMS unbind failed. Message: %s",
                                  pmobile, terminal.tid, tmobile, ErrorCode.ERROR_MESSAGE[status])

        except Exception as e:
            status = ErrorCode.FAILED
            logging.exception("Delete service failed. tmobile: %s, owner mobile: %s", tmobile, pmobile)
        self.write_ret(status)
            
class BusinessServiceHandler(BaseHandler, BusinessMixin):

    @authenticated
    @check_privileges([PRIVILEGES.EDIT_BUSINESS])
    @tornado.web.removeslash
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
            # clear redis
            sessionID_key = get_terminal_sessionID_key(terminal.tid)
            address_key = get_terminal_address_key(terminal.tid)
            info_key = get_terminal_info_key(terminal.tid)
            lq_sms_key = get_lq_sms_key(terminal.tid)
            lq_interval_key = get_lq_interval_key(terminal.tid)
            keys = [sessionID_key, address_key, info_key, lq_sms_key, lq_interval_key]
            self.redis.delete(*keys)
        except Exception as e:
            status = ErrorCode.FAILED
            logging.exception("Update service_status to %s failed. tmobile: %s", service_status, tmobile)
        self.write_ret(status)
            
