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
from excelheaders import BUSINESS_FILE_NAME, BUSINESS_SHEET, BUSINESS_HEADER  
from base import BaseHandler, authenticated

from checker import check_areas, check_privileges 
from codes.errorcode import ErrorCode 
from utils.checker import check_sql_injection, check_zs_phone
from utils.misc import get_terminal_address_key, get_terminal_sessionID_key,\
     get_terminal_info_key, get_lq_sms_key, get_lq_interval_key, safe_unicode
from helpers.smshelper import SMSHelper
from helpers.seqgenerator import SeqGenerator
from helpers.gfsenderhelper import GFSenderHelper
from helpers.queryhelper import QueryHelper 
from codes.smscode import SMSCode 
from constants import PRIVILEGES, SMS, UWEB, GATEWAY
from utils.misc import str_to_list, DUMMY_IDS, get_terminal_info_key
from utils.public import record_add_action, delete_terminal, add_user, add_terminal
from myutils import city_list
from mongodb.mdaily import MDaily, MDailyMixin


class BusinessMixin(BaseMixin):

    KEY_TEMPLATE = "business_mixin_%s_%s"

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
    @check_privileges([PRIVILEGES.BUSINESS_HANDLE])
    @tornado.web.removeslash
    def get(self):
        """Just to create.html.
        """
        self.render('business/create.html',
                    status=ErrorCode.SUCCESS,
                    message='')

    @authenticated
    @check_privileges([PRIVILEGES.BUSINESS_HANDLE])
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
            user_info = dict(umobile=fields.umobile,
                             password=fields.password,
                             uname=fields.uname,
                             address=fields.address,
                             email=fields.email)
            add_user(user_info, self.db, self.redis)

            # record the add action
            record_add_action(fields.tmobile, -1, int(time.time()), self.db)

            # 2: add terminal
            if not fields.umobile:
                user_mobile = fields.ecmobile
            else:
                user_mobile = fields.umobile


            terminal_info = dict(tmobile=fields.tmobile,
                                 owner_mobile=user_mobile,
                                 begintime=fields.begintime,
                                 endtime=4733481600, # 2120.1.1
                                 cnum=fields.cnum,
                                 ctype=fields.ctype,
                                 ccolor=fields.ccolor,
                                 cbrand=fields.cbrand)
            add_terminal(terminal_info, self.db, self.redis)

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
    @check_privileges([PRIVILEGES.BUSINESS_QUERY])
    @tornado.web.removeslash
    def get(self):
        corplist = self.db.query("SELECT id, cid, name FROM T_CORP")
        self.render('business/search.html',
                    hash_='',
                    interval=[], 
                    businesses=[],
                    corplist=corplist,
                    status=ErrorCode.SUCCESS,
                    message='')


    @authenticated
    @check_privileges([PRIVILEGES.BUSINESS_QUERY])
    @tornado.web.removeslash
    def post(self):
        """Query businesses according to the given params.
        """
        corplist = self.db.query("SELECT id, cid, name FROM T_CORP")
        corps = self.get_argument('corps', None)
        begintime = int(self.get_argument('begintime',0))
        endtime = int(self.get_argument('endtime',0))
        interval=[begintime, endtime]
        if not corps:
            corps = self.db.query("SELECT cid FROM T_CORP")
            corps = [str(corp.cid) for corp in corps]
            sql = "SELECT id FROM T_GROUP WHERE corp_id IN %s" % (tuple(corps + DUMMY_IDS),)
            groups = self.db.query(sql)
            groups = [str(group.id) for group in groups] + [-1,]
        else:
            groups = self.db.query("SELECT id FROM T_GROUP WHERE corp_id = %s", corps) 
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
            sql = ("SELECT tt.tid, tt.login, tu.name as uname, tu.mobile as umobile, tt.mobile as tmobile,"
                   "  tt.softversion, tt.begintime, tt.endtime, tt.move_val, tt.static_val,"
                   "  tt.service_status, tc.cnum, tcorp.name as ecname, tt.biz_type"
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
                #business['sms_status'] = self.get_sms_status(business['tmobile'])
                business['corp_name'] = ''
                #NOTE: if login !=0(offline), set login as 1(online)
                business['login'] = business['login'] if business['login']==0 else 1
                #biz = QueryHelper.get_biz_by_mobile(business['tmobile'], self.db)
                #business['biz_type'] = biz['biz_type'] if biz else 1
                terminal = QueryHelper.get_terminal_info(business['tid'], self.db, self.redis)
                business['pbat'] = terminal['pbat'] if terminal.get('pbat', None) is not None else 0 
                business['alias'] = business['cnum'] if business['cnum'] else business['tmobile']  

                for key in business:
                    if business[key] is None:
                        business[key] = ''

            # keep data in redis
            m = hashlib.md5()
            m.update(self.request.body)
            hash_ = m.hexdigest()
            mem_key = self.get_memcache_key(hash_)
            self.redis.setvalue(mem_key, businesses,
                                time=self.MEMCACHE_EXPIRY)
            
            self.render('business/search.html',
                        status=ErrorCode.SUCCESS,
                        message='',
                        interval=interval, 
                        businesses=businesses,
                        corplist=corplist,
                        hash_=hash_)
        except Exception as e:
            logging.exception("Search business failed.")
            self.render('errors/error.html',
                        message=ErrorCode.ERROR_MESSAGE[ErrorCode.SEARCH_BUSINESS_FAILURE])


class BusinessSearchDownloadHandler(BaseHandler, BusinessMixin):

    @authenticated
    @check_privileges([PRIVILEGES.BUSINESS_QUERY])
    @tornado.web.removeslash
    def get(self, hash_):

        mem_key = self.get_memcache_key(hash_)

        results = self.redis.getvalue(mem_key)

        if not results:
            self.render("errors/download.html")
            return

        import xlwt
        from cStringIO import StringIO

        filename = BUSINESS_FILE_NAME 
        online_style = xlwt.easyxf('font: colour_index green, bold off; align: wrap on, vert centre, horiz center;') 
        offline_style = xlwt.easyxf('font: colour_index brown, bold off; align: wrap on, vert centre, horiz center;')

        date_style = xlwt.easyxf(num_format_str='YYYY-MM-DD HH:mm:ss')
        wb = xlwt.Workbook()
        ws = wb.add_sheet(BUSINESS_SHEET)

        start_line = 0
        for i, head in enumerate(BUSINESS_HEADER): 
            ws.write(0, i, head)

        start_line += 1
        for i, result in zip(range(start_line, len(results) + start_line), results):
            ws.write(i, 0, i)
            ws.write(i, 1, safe_unicode(result['ecname']) if result['ecname'] else u'')
            ws.write(i, 2, result['umobile'])
            ws.write(i, 3, result['tmobile'])
            ws.write(i, 4, result['tid'])
            ws.write(i, 5, result['softversion'])
            ws.write(i, 6, result['alias'])
            ws.write(i, 7, u'移动卫士' if int(result['biz_type']) == 0 else u'移动外勤')
            if int(result['login']) == 0:
                ws.write(i, 8, u'离线', offline_style)
            else:
                ws.write(i, 8, u'在线', online_style)
            ws.write(i, 9, '%s%%' % result['pbat'])
            ws.write(i, 10, time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(result['begintime'])))

        _tmp_file = StringIO()
        wb.save(_tmp_file)
        
        filename = self.generate_file_name(filename)

        self.set_header('Content-Type', 'application/force-download')
        self.set_header('Content-Disposition', 'attachment; filename=%s.xls' % (filename,))

        # move the the begging. 
        _tmp_file.seek(0, SEEK_SET)
        self.write(_tmp_file.read())
        _tmp_file.close()


class BusinessListHandler(BaseHandler, BusinessMixin):

    @authenticated
    @check_privileges([PRIVILEGES.BUSINESS_QUERY])
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
    @check_privileges([PRIVILEGES.BUSINESS_QUERY])
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
    @check_privileges([PRIVILEGES.BUSINESS_QUERY])
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
    @check_privileges([PRIVILEGES.BUSINESS_QUERY])
    @tornado.web.removeslash
    def post(self, tmobile, pmobile):
        status = ErrorCode.SUCCESS
        try:
            terminal = self.db.get("SELECT id, login, mobile, tid FROM T_TERMINAL_INFO"
                                   "  WHERE mobile = %s",
                                   tmobile)
            tid = terminal.tid
            biz_type = QueryHelper.get_biz_type_by_tmobile(tmobile, self.db) 
            if int(biz_type) == UWEB.BIZ_TYPE.YDWS:
                if terminal.login != GATEWAY.TERMINAL_LOGIN.ONLINE: # offline
                    if terminal.mobile == tid:
                        delete_terminal(tid, self.db, self.redis)
                        logging.info('[ADMIN] Delete terminal. umobile:%s, tid: %s, tmobile:%s.', 
                                     pmobile, tid, tmobile)
                    else:
                        delete_terminal(tid, self.db, self.redis)
                        unbind_sms = SMSCode.SMS_UNBIND  
                        ret = SMSHelper.send_to_terminal(tmobile, unbind_sms)
                        ret = DotDict(json_decode(ret))
                        logging.info('[ADMIN] Send JB sms. umobile:%s, tid: %s, tmobile:%s.', 
                                     pmobile, tid, tmobile)
                    self.write_ret(status)
                    return
            else: 
                delete_terminal(tid, self.db, self.redis)
                self.write_ret(status)
                return

            # unbind terminal
            seq = str(int(time.time()*1000))[-4:]
            args = DotDict(seq=seq,
                           tid=terminal.tid)
            response = GFSenderHelper.forward(GFSenderHelper.URLS.UNBIND, args)
            response = json_decode(response)
            if response['success'] == ErrorCode.SUCCESS:
                logging.info("[ADMIN] Umobile: %s, tid: %s, tmobile:%s GPRS unbind successfully", 
                             pmobile, terminal.tid, tmobile)
            else:
                status = response['success']
                # unbind failed. clear sessionID for relogin, then unbind it again
                sessionID_key = get_terminal_sessionID_key(terminal.tid)
                self.redis.delete(sessionID_key)
                logging.error("[ADMIN] Umobile:%s, tid: %s, tmobile:%s GPRS unbind failed, message: %s, send JB sms...", 
                              pmobile, terminal.tid, tmobile, ErrorCode.ERROR_MESSAGE[status])
                unbind_sms = SMSCode.SMS_UNBIND  
                biz_type = QueryHelper.get_biz_type_by_tmobile(tmobile, self.db)
                if biz_type != UWEB.BIZ_TYPE.YDWS:
                    ret = DotDict(status=ErrorCode.SUCCESS)
                else:
                    ret = SMSHelper.send_to_terminal(tmobile, unbind_sms)
                    ret = DotDict(json_decode(ret))
                status = ret.status
                if ret.status == ErrorCode.SUCCESS:
                    self.db.execute("UPDATE T_TERMINAL_INFO"
                                    "  SET service_status = %s"
                                    "  WHERE id = %s",
                                    UWEB.SERVICE_STATUS.TO_BE_UNBIND,
                                    terminal.id)
                    logging.info("[ADMIN] umobile: %s, tid: %s, tmobile: %s SMS unbind successfully.",
                                 pmobile, terminal.tid, tmobile)
                else:
                    logging.error("[ADMIN] umobile: %s, tid: %s, tmobile: %s SMS unbind failed. Message: %s",
                                  pmobile, terminal.tid, tmobile, ErrorCode.ERROR_MESSAGE[status])

        except Exception as e:
            status = ErrorCode.FAILED
            logging.exception("[ADMIN] Delete service failed. tmobile: %s, owner mobile: %s", tmobile, pmobile)
        self.write_ret(status)
            
class BusinessServiceHandler(BaseHandler, BusinessMixin):

    @authenticated
    @check_privileges([PRIVILEGES.BUSINESS_QUERY])
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
            logging.exception("[ADMIN] Update service_status to %s failed. tmobile: %s", service_status, tmobile)
        self.write_ret(status)
            
