# -*- coding: utf-8 -*-

import hashlib
import logging
import time

import tornado.web
from tornado.escape import json_decode, json_encode

from utils.misc import DUMMY_IDS
from utils.misc import get_terminal_address_key, get_terminal_sessionID_key,\
     get_terminal_info_key, get_lq_sms_key, get_lq_interval_key
from utils.dotdict import DotDict
from base import BaseHandler, authenticated
from checker import check_privileges 
from constants import PRIVILEGES, GATEWAY, SMS, UWEB
from mixin import BaseMixin
from helpers.queryhelper import QueryHelper
from helpers.gfsenderhelper import GFSenderHelper
from codes.smscode import SMSCode 
from helpers.smshelper import SMSHelper
from codes.errorcode import ErrorCode 
from utils.checker import check_sql_injection, check_zs_phone


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

        corp = self.get_argument('corps', 0)
        begintime = int(self.get_argument('begintime',0))
        endtime = int(self.get_argument('endtime',0))
        interval=[begintime, endtime]
        if int(corp) == 0:
            corps = self.db.query("SELECT id FROM T_CORP")
            corps = [str(corp.id) for corp in corps]
        else:
            corps = [str(corp),]
            
        fields = DotDict(ecmobile="mobile LIKE '%%%%%s%%%%'")
                         #begintime="timestamp >= %s",
                         #endtime="timestamp <= %s") 

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

        sql = ("SELECT cid, name as ecname, mobile as ecmobile, address, email" 
               "  FROM T_CORP"
               "  WHERE id IN %s ") % (tuple(corps + DUMMY_IDS),)
        if where_clause:
            sql += " AND " + where_clause
        businesses = self.db.query(sql)
        for i, business in enumerate(businesses):
            business['seq'] = i + 1
            groups = self.db.query("SELECT id FROM T_GROUP WHERE corp_id = %s", business.cid)
            groups = [g.id for g in groups] 
            terminals = self.db.query("SELECT id FROM T_TERMINAL_INFO"
                                      "  WHERE group_id IN %s"
                                      "    AND service_status = %s",
                                      tuple(groups + DUMMY_IDS),
                                      UWEB.SERVICE_STATUS.ON)
            business['total_terminals'] = len(terminals)
            for key in business:
                if business[key] is None:
                    business[key] = ''

        self.redis.setvalue(mem_key,(businesses,interval), 
                            time=self.MEMCACHE_EXPIRY)

        return businesses, interval

    
    def get_ecbusiness_info(self, ecmobile):
        """Get business info in detail throught tmobile.
        """
        business = self.db.get("SELECT cid, name as ecname, mobile as ecmobile,"
                               "       linkman, address, email, timestamp, bizcode, type" 
                               "  FROM T_CORP" 
                               "  WHERE mobile = %s" 
                               "    LIMIT 1",
                               ecmobile)
        return business


class ECBusinessCreateHandler(BaseHandler, ECBusinessMixin):

    @authenticated
    @check_privileges([PRIVILEGES.CREATE_ECBUSINESS])
    @tornado.web.removeslash
    def get(self):
        bizlist = self.db.query("SELECT bizcode, bizname FROM T_BUSINESS")
            
        self.render('ecbusiness/create.html',
                    bizlist=bizlist,
                    status=ErrorCode.SUCCESS,
                    message='')

    @authenticated
    @check_privileges([PRIVILEGES.CREATE_ECBUSINESS])
    @tornado.web.removeslash
    def post(self):
        """Create business for ec user.
        """
        fields = DotDict(ecname="",
                         ecmobile="",
                         password="",
                         linkman="",
                         address="",
                         email="",
                         bizcode="",
                         type="")

        for key in fields.iterkeys():
            fields[key] = self.get_argument(key,'').strip()

        corpid = self.db.execute("INSERT INTO T_CORP(cid, name, mobile, password,"
                                 "  linkman, address, email, timestamp, bizcode, type)"
                                 "  VALUES(%s, %s, %s, password(%s), %s, %s, %s, %s, %s, %s)",
                                 fields.ecmobile, fields.ecname, fields.ecmobile,
                                 fields.password, fields.linkman,
                                 fields.address, fields.email,
                                 int(time.time()), fields.bizcode, fields.type)
        group = self.db.execute("INSERT INTO T_GROUP(corp_id, name, type)"
                                "  VALUES(%s, default, default)",
                                fields.ecmobile)

        self.redirect("/ecbusiness/list/%s" % fields.ecmobile)
        
        
class ECBusinessListHandler(BaseHandler, ECBusinessMixin):

    @authenticated
    @check_privileges([PRIVILEGES.LIST_ECBUSINESS])
    @tornado.web.removeslash
    def get(self, ecmobile):
        """Show the info in detail for the given business.
        #NOTE: in admin, a business is distinguished from others by tmobile.
        """
        business = self.get_ecbusiness_info(ecmobile) 
        self.render('ecbusiness/list.html',
                    ecbusiness=business,
                    status=ErrorCode.SUCCESS,
                    message='')
        
        
class ECBusinessSearchHandler(BaseHandler, ECBusinessMixin):
    @authenticated
    @check_privileges([PRIVILEGES.QUERY_ECBUSINESS])
    @tornado.web.removeslash
    def get(self):
        corplist = self.db.query("SELECT id, name FROM T_CORP")
        self.render('ecbusiness/search.html',
                    interval=[], 
                    corplist=corplist,
                    ecbusinesses=[],
                    status=ErrorCode.SUCCESS,
                    message='')    
        
    @authenticated
    @check_privileges([PRIVILEGES.QUERY_ECBUSINESS])
    @tornado.web.removeslash
    def post(self):
        """Query businesses according to the given params.
        """
        m = hashlib.md5()
        m.update(self.request.body)
        hash_ = m.hexdigest() 
        ecbusinesses, interval = self.prepare_data(hash_)
        corplist = self.db.query("SELECT id, name FROM T_CORP")
        self.render('ecbusiness/search.html',
                    interval=interval, 
                    ecbusinesses=ecbusinesses,
                    corplist=corplist,
                    status=ErrorCode.SUCCESS,
                    message='')
        

class ECBusinessEditHandler(BaseHandler, ECBusinessMixin):

    @authenticated
    @check_privileges([PRIVILEGES.EDIT_ECBUSINESS])
    @tornado.web.removeslash
    def get(self, ecmobile):
        """Jump to edit.html.
        """
        business = self.get_ecbusiness_info(ecmobile) 
        self.render("ecbusiness/edit.html",
                    ecbusiness=business,
                    status=ErrorCode.SUCCESS,
                    message='')
        
    @authenticated
    @check_privileges([PRIVILEGES.EDIT_ECBUSINESS])
    @tornado.web.removeslash
    def post(self, ecmobile):
        """Modify a business.
        """
        fields = DotDict(ecname=" name = '%s'",
                         ecmobile=" mobile = '%s'",
                         linkman="linkman = '%s'",
                         address="address = '%s'",
                         email="email = '%s'",
                         bizcode="bizcode = '%s'",
                         type="type = '%s'")

        for key in fields:
            v = self.get_argument(key, None)
            if v is not None:
                if not check_sql_injection(v):
                   # call get method
                   self.get(tmobile)
                   return
                fields[key] = fields[key] % v 
            else:
                fields[key] = None
        set_cmd = ', '.join([v for v in fields.itervalues()
                             if v is not None])
        
        sql = "UPDATE T_CORP SET " + set_cmd + " WHERE mobile = %s" % ecmobile
        self.db.execute(sql)

        self.redirect("/ecbusiness/list/%s" % ecmobile)
        
        
class ECBusinessDeleteHandler(BaseHandler, ECBusinessMixin):

    @authenticated
    @check_privileges([PRIVILEGES.DELETE_ECBUSINESS])
    @tornado.web.removeslash
    def post(self, ecmobile):
        status = ErrorCode.SUCCESS
        try:
            ec = self.get_ecbusiness_info(ecmobile)
            groups = self.db.query("SELECT id FROM T_GROUP WHERE corp_id = %s", ec.cid)
            groups = [group.id for group in groups]
            terminals = self.db.query("SELECT id, tid, mobile, owner_mobile FROM T_TERMINAL_INFO WHERE group_id IN %s",
                                      tuple(groups + DUMMY_IDS))
            for terminal in terminals:
                # unbind terminal
                seq = str(int(time.time()*1000))[-4:]
                args = DotDict(seq=seq,
                               tid=terminal.tid)
                response = GFSenderHelper.forward(GFSenderHelper.URLS.UNBIND, args)
                response = json_decode(response)
                if response['success'] == ErrorCode.SUCCESS:
                    logging.info("[UWEB] umobile: %s, tid: %s, tmobile:%s GPRS unbind successfully", 
                                 terminal.owner_mobile, terminal.tid,
                                 terminal.mobile)
                else:
                    status = response['success']
                    # unbind failed. clear sessionID for relogin, then unbind it again
                    sessionID_key = get_terminal_sessionID_key(terminal.tid)
                    self.redis.delete(sessionID_key)
                    logging.error('[UWEB] umobile:%s, tid: %s, tmobile:%s GPRS unbind failed, message: %s, send JB sms...', 
                                  terminal.owner_mobile, terminal.tid,
                                  terminal.mobile, ErrorCode.ERROR_MESSAGE[status])
                    unbind_sms = SMSCode.SMS_UNBIND  
                    ret = SMSHelper.send_to_terminal(terminal.mobile, unbind_sms)
                    ret = DotDict(json_decode(ret))
                    status = ret.status
                    if ret.status == ErrorCode.SUCCESS:
                        self.db.execute("UPDATE T_TERMINAL_INFO"
                                        "  SET service_status = %s"
                                        "  WHERE id = %s",
                                        UWEB.SERVICE_STATUS.TO_BE_UNBIND,
                                        terminal.id)
                        logging.info("[UWEB] umobile: %s, tid: %s, tmobile: %s SMS unbind successfully.",
                                     terminal.owner_mobile, terminal.tid,
                                     terminal.mobile)
                    else:
                        logging.error("[UWEB] umobile: %s, tid: %s, tmobile: %s SMS unbind failed. Message: %s",
                                      terminal.owner_mobile, terminal.tid,
                                      terminal.mobile, ErrorCode.ERROR_MESSAGE[status])

            self.db.execute("DELETE FROM T_CORP WHERE cid = %s", ec.cid)
            
        except Exception as e:
            status = ErrorCode.FAILED
            logging.exception("Delete service failed. ecmobile: %s", ecmobile)
        self.write_ret(status)
        

class ECBusinessAddTerminalHandler(BaseHandler, ECBusinessMixin):

    @authenticated
    @check_privileges([PRIVILEGES.CREATE_BUSINESS])
    @tornado.web.removeslash
    def get(self):
        """Just to create.html.
        """
        corplist = self.db.query("SELECT id, name FROM T_CORP")
        self.render('ecbusiness/addterminal.html',
                    corplist=corplist,
                    status=ErrorCode.SUCCESS,
                    message='')

    @authenticated
    @check_privileges([PRIVILEGES.CREATE_BUSINESS])
    @tornado.web.removeslash
    def post(self):
        """Create business for a couple of users.
        """
        fields = DotDict(ecid="",
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
                         email="")
        for key in fields.iterkeys():
            fields[key] = self.get_argument(key,'')
            if not check_sql_injection(fields[key]):
                logging.error("Create business condition contain SQL inject. %s : %s", key, fields[key])
                self.render('errors/error.html',
                    message=ErrorCode.ERROR_MESSAGE[ErrorCode.CREATE_CONDITION_ILLEGAL])
                return

        white_list = check_zs_phone(fields.tmobile, self.db)
        if not white_list:
            logging.error("Create business error, %s is not whitelist", fields.tmobile)
            self.render('errors/error.html',
                message=ErrorCode.ERROR_MESSAGE[ErrorCode.MOBILE_NOT_ORDERED])
            return

        try:
            # 1: add user
            if fields.umobile:
                user = self.db.get("SELECT id FROM T_USER WHERE mobile = %s", fields.umobile)
                if not user:
                    self.db.execute("INSERT INTO T_USER(id, uid, password, name, mobile, address, email, remark)"
                                    "  VALUES(NULL, %s, password(%s), %s, %s, %s, %s, NULL)",
                                    fields.umobile, '111111',
                                    fields.uname, fields.umobile,
                                    fields.address, fields.email)
                    self.db.execute("INSERT INTO T_SMS_OPTION(uid)"
                                    "  VALUES(%s)",
                                    fields.umobile)
            
            # 2: add terminal
            corp = self.db.get("SELECT cid FROM T_CORP WHERE id = %s", fields.ecid)
            group = self.db.get("SELECT id FROM T_GROUP WHERE corp_id = %s AND type = 0 LIMIT 1", corp.cid) 
            if not group:
                gid= self.db.execute("INSERT INTO T_GROUP(corp_id, name, type)"
                                     "  VALUES(%s, default, default)",
                                     corp.cid)
            else:
                gid = group.id

            self.db.execute("INSERT INTO T_TERMINAL_INFO(tid, group_id, mobile, owner_mobile,"
                            "  begintime, endtime)"
                            "  VALUES (%s, %s, %s, %s, %s, %s)",
                            fields.tmobile, gid,
                            fields.tmobile, fields.umobile, 
                            fields.begintime, fields.endtime)
    
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
                logging.error("Create business sms send failure. terminal mobile: %s, owner mobile: %s", fields.tmobile, fields.umobile)
            fields.sms_status = sms_status
            fields.service_status = 1
            self.render('business/list.html',
                        business=fields,
                        status=ErrorCode.SUCCESS,
                        message='')
        except Exception as e:
            logging.exception("Add terminal failed.")
            self.render('errors/error.html',
                        message=ErrorCode.ERROR_MESSAGE[ErrorCode.CREATE_USER_FAILURE])

 
