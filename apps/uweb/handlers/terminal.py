# -*- coding: utf-8 -*-

import logging
import time
import datetime
from dateutil.relativedelta import relativedelta

import tornado.web
from tornado.escape import json_decode, json_encode
from tornado.ioloop import IOLoop

from utils.misc import get_terminal_sessionID_key, get_terminal_address_key,\
    get_terminal_info_key, get_lq_sms_key, get_lq_interval_key, get_del_data_key
from utils.dotdict import DotDict
from utils.checker import check_sql_injection, check_zs_phone, check_cnum
from utils.public import record_add_action, delete_terminal
from base import BaseHandler, authenticated
from codes.errorcode import ErrorCode
from codes.smscode import SMSCode 
from constants import UWEB, SMS, GATEWAY

from helpers.queryhelper import QueryHelper  
from helpers.seqgenerator import SeqGenerator
from helpers.gfsenderhelper import GFSenderHelper
from helpers.smshelper import SMSHelper

from mixin.terminal import TerminalMixin 


class TerminalHandler(BaseHandler, TerminalMixin):

    @authenticated
    @tornado.web.removeslash
    def get(self):
        """Get terminal info.
        """
        status = ErrorCode.SUCCESS
        try:
            tid = self.get_argument('tid',None) 
            # check tid whether exist in request and update current_user
            self.check_tid(tid)
          
            car_sets = DotDict() 
            # 1: terminal 
            terminal = self.db.get("SELECT freq, alias, trace, cellid_status,"
                                   "       vibchk, tid as sn, mobile, vibl,"
                                   "       white_pop, push_status, icon_type, owner_mobile, login_permit"
                                   "  FROM T_TERMINAL_INFO"
                                   "  WHERE tid = %s"
                                   "    AND service_status = %s"
                                   "  LIMIT 1",
                                   self.current_user.tid,
                                   UWEB.SERVICE_STATUS.ON)
            if not terminal:
                status = ErrorCode.LOGIN_AGAIN
                logging.error("The terminal with tid: %s does not exist, redirect to login.html", self.current_user.tid)
                self.write_ret(status)
                return

            # 2: whitelist
            user = QueryHelper.get_user_by_mobile(terminal.owner_mobile, self.db)
            if not user:
                logging.error("The user with uid: %s does not exist, redirect to login.html", self.current_user.uid)
                self.clear_cookie(self.app_name)
                self.write_ret(ErrorCode.LOGIN_AGAIN)
                return

            whitelist = self.db.query("SELECT mobile"
                                      "  FROM T_WHITELIST"
                                      "  WHERE tid = %s",
                                      self.current_user.tid)

            # 3: car
            car = self.db.get("SELECT cnum corp_cnum FROM T_CAR"
                              "  WHERE tid = %s",
                              self.current_user.tid)

            # add tow dict: terminal, car. add two value: whitelist_1, whitelist_2 
            car_sets.update(terminal)
            car_sets.update(car)
            white_list = [terminal.owner_mobile]
            for item in whitelist: 
                white_list.append(item['mobile'])
            car_sets.update(DotDict(white_list=white_list))
            self.write_ret(status,
                           dict_=dict(car_sets=car_sets))
        except Exception as e: 
            status = ErrorCode.SERVER_BUSY
            logging.exception("[UWEB] uid: %s tid: %s get terminal failed. Exception: %s", 
                              self.current_user.uid, self.current_user.tid, e.args) 
            self.write_ret(status)

    @authenticated
    @tornado.web.removeslash
    def put(self):
        """Update the params of terminal.
        """
        status = ErrorCode.SUCCESS
        try:
            data = DotDict(json_decode(self.request.body))
            tid = data.get('tid',None) 
            # check tid whether exist in request and update current_user
            self.check_tid(tid)
            logging.info("[UWEB] terminal request: %s, uid: %s, tid: %s", 
                         data, self.current_user.uid, self.current_user.tid)
        except Exception as e:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            self.write_ret(status)
            return 
        
        try:
            #seq = str(int(time.time()*1000))[-4:]
            #args = DotDict(seq=seq,
            #               tid=self.current_user.tid)

            # check the data. some be sent to terminal, some just be modified in db 
            terminal = self.db.get("SELECT id FROM T_TERMINAL_INFO"
                                   "  WHERE tid = %s"
                                   "    AND service_status = %s",
                                   self.current_user.tid,
                                   UWEB.SERVICE_STATUS.ON)
            if not terminal:
                status = ErrorCode.LOGIN_AGAIN
                logging.error("The terminal with tid: %s does not exist, redirect to login.html", self.current_user.tid)
                self.write_ret(status)
                return

            user = QueryHelper.get_user_by_uid(self.current_user.uid, self.db)
            if not user:
                status = ErrorCode.LOGIN_AGAIN
                logging.error("The user with uid: %s does not exist, redirect to login.html", self.current_user.uid)
                self.write_ret(status)
                return

            # sql injection 
            if data.has_key('corp_cnum') and not check_cnum(data.corp_cnum):
                status = ErrorCode.ILLEGAL_CNUM 
                self.write_ret(status)
                return

            #if data.has_key('alias') and not check_sql_injection(data.alias):
            #    status = ErrorCode.ILLEGAL_ALIAS 
            #    self.write_ret(status)
            #    return

            #if data.has_key('corp_cnum') and not check_sql_injection(data.corp_cnum):
            #    status = ErrorCode.ILLEGAL_CNUM 
            #    self.write_ret(status)
            #    return

            #if data.has_key('owner_mobile') and not check_sql_injection(data.owner_mobile):
            #    status = ErrorCode.ILLEGAL_MOBILE
            #    self.write_ret(status)
            #    return

            if data.has_key('white_list'):
                white_list = ":".join(data.white_list)
                if not check_sql_injection(white_list):
                    status = ErrorCode.ILLEGAL_WHITELIST 
                    self.write_ret(status)
                    return

            #gf_params = DotDict()
            #db_params = DotDict()
            #DB_FIELDS = ['alias', 'cnum', 'cellid_status', 'white_pop', 'push_status']
            #for key, value in data.iteritems():
            #    if key in DB_FIELDS:
            #        db_params[key] = value
            #    else:
            #        if key == 'white_list':
            #            gf_params[key]=":".join(value)
            #        else:
            #            gf_params[key]=value
            #       
            self.update_terminal_db(data) 
            #args.params = gf_params 

            #def _on_finish(response):
            #    status = ErrorCode.SUCCESS
            #    response = json_decode(response)
            #    if response['success'] == ErrorCode.SUCCESS:
            #        for key, value in response['params'].iteritems():
            #            if value != "0":
            #                status = ErrorCode.TERMINAL_SET_FAILED
            #                logging.error("[UWEB] uid:%s, tid:%s set terminal %s faileds",
            #                              self.current_user.uid, self.current_user.tid, key) 
            #                break
            #        self.update_terminal_info(gf_params, response['params'])
            #    else:
            #        if response['success'] in (ErrorCode.TERMINAL_OFFLINE, ErrorCode.TERMINAL_TIME_OUT): 
            #            self.send_lq_sms(self.current_user.sim, self.current_user.tid, SMS.LQ.WEB)
            #        status = response['success'] 
            #        logging.error("[UWEB] uid:%s tid: %s set terminal failed, message: %s", 
            #                       self.current_user.uid, self.current_user.tid, ErrorCode.ERROR_MESSAGE[status] )
            #    self.write_ret(status)
            #    IOLoop.instance().add_callback(self.finish)

            #if args.params:
            #    self.keep_waking(self.current_user.sim, self.current_user.tid)
            #    GFSenderHelper.async_forward(GFSenderHelper.URLS.TERMINAL, args,
            #                                 _on_finish)
            #else: 
            #    self.write_ret(status)
            #    IOLoop.instance().add_callback(self.finish)

            self.write_ret(status)
        except Exception as e:
            logging.exception("[UWEB] uid:%s, tid:%s update terminal info failed. Exception: %s", 
                              self.current_user.uid, self.current_user.tid, e.args)
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)


class TerminalCorpHandler(BaseHandler, TerminalMixin):

    @authenticated
    @tornado.web.removeslash
    def get(self):
        """Show information of a terminal.
        """
        status = ErrorCode.SUCCESS
        try:
            terminals = QueryHelper.get_terminals_by_cid(self.current_user.cid, self.db)
            res=[]
            for terminal in terminals:
                res.append(dict(tid=terminal.tid,
                                tmobile=terminal.mobile))

            self.write_ret(status,
                           dict_=dict(res=res))
        except Exception as e:
            logging.exception("[UWEB] cid:%s, tid:%s get terminal info failed. Exception: %s", 
                              self.current_user.cid, tid, e.args)
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)

    @authenticated
    @tornado.web.removeslash
    def post(self):
        """Add a terminal.
        """
        status = ErrorCode.SUCCESS
        try:
            data = DotDict(json_decode(self.request.body))
            logging.info("[UWEB] corp add terminal request: %s, cid: %s", 
                         data, self.current_user.cid)
        except Exception as e:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            self.write_ret(status)
            return 
        
        try:
            if data.has_key('cnum') and not check_cnum(data.cnum):
                status = ErrorCode.ILLEGAL_CNUM 
                self.write_ret(status)
                return
            
            # 1 year
            begintime = int(time.time())
            now_ = datetime.datetime.now()
            endtime = now_ + relativedelta(years=1)
            endtime = int(time.mktime(endtime.timetuple()))

            ## 0. check tmobile is whitelist or not
            #white_list = check_zs_phone(data.tmobile, self.db) 
            #if not white_list:
            #    logging.error("[UWEB] mobile: %s is not whitelist.", data.tmobile)
            #    status = ErrorCode.MOBILE_NOT_ORDERED
            #    message = ErrorCode.ERROR_MESSAGE[status] % data.tmobile
            #    self.write_ret(status, message=message)
            #    return

            # 1: add terminal
            umobile = data.umobile if data.umobile else self.current_user.cid
            terminal = self.db.get("SELECT id, tid, service_status FROM T_TERMINAL_INFO WHERE mobile = %s",
                                   data.tmobile)
            if terminal:
                if terminal.service_status == UWEB.SERVICE_STATUS.TO_BE_UNBIND:
                    delete_terminal(terminal.tid, self.db, self.redis)
                else:
                    logging.error("[UWEB] mobile: %s already existed.", data.tmobile)
                    status = ErrorCode.TERMINAL_ORDERED
                    self.write_ret(status)
                    return

            # record the add action
            record_add_action(data.tmobile, data.group_id, int(time.time()), self.db)

            self.db.execute("INSERT INTO T_TERMINAL_INFO(tid, group_id, mobile, owner_mobile,"
                            "  defend_status, mannual_status, begintime, endtime, offline_time, icon_type, login_permit)"
                            "  VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                            data.tmobile, data.group_id,
                            data.tmobile, umobile, UWEB.DEFEND_STATUS.NO,
                            UWEB.DEFEND_STATUS.NO, begintime, endtime, begintime, data.icon_type, 0)
    
            # 1: add user
            user = self.db.get("SELECT id FROM T_USER WHERE mobile = %s", umobile)
            if not user:
                self.db.execute("INSERT INTO T_USER(id, uid, password, name, mobile)"
                                "  VALUES(NULL, %s, password(%s), %s, %s )",
                                umobile, '111111',
                                u'', umobile)
                self.db.execute("INSERT INTO T_SMS_OPTION(uid)"
                                "  VALUES(%s)",
                                umobile) 
            # 3: add car 
            self.db.execute("INSERT INTO T_CAR(tid, cnum)"
                            "  VALUES(%s, %s)",
                            data.tmobile, data.cnum )
            
            # 4: send message to terminal
            register_sms = SMSCode.SMS_REGISTER % (umobile, data.tmobile) 
            ret = SMSHelper.send_to_terminal(data.tmobile, register_sms)
            ret = DotDict(json_decode(ret))
            sms_status = 0
            if ret.status == ErrorCode.SUCCESS:
                self.db.execute("UPDATE T_TERMINAL_INFO"
                                "  SET msgid = %s"
                                "  WHERE mobile = %s",
                                ret['msgid'], data.tmobile)
                sms_status = 1
            else:
                sms_status = 0
                logging.error("[UWEB] Send %s to terminal %s failed.", register_sms, data.tmobile)
            self.write_ret(status)
        except Exception as e:
            logging.exception("[UWEB] cid:%s update terminal info failed. Exception: %s", 
                              self.current_user.cid, e.args)
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)

    #@authenticated
    #@tornado.web.removeslash
    #def put(self):
    #    """modify a terminal.
    #    """
    #    status = ErrorCode.SUCCESS
    #    try:
    #        data = DotDict(json_decode(self.request.body))
    #        logging.info("[UWEB] corp modify terminal request: %s, cid: %s", 
    #                     data, self.current_user.cid)
    #    except Exception as e:
    #        status = ErrorCode.ILLEGAL_DATA_FORMAT
    #        self.write_ret(status)
    #        return 
    #    
    #    try:
    #        tid = data.tid

    #        fields_car = DotDict()
    #        fields_terminal = DotDict()

    #        FIELDS_CAR = DotDict(cnum="cnum = '%s'",
    #                             ctype="type = '%s'",
    #                             ccolor="color = '%s'",
    #                             cbrand="brand = '%s'")

    #        FIELDS_TERMINAL = DotDict(begintime="begintime = '%s'",
    #                                  endtime="endtime = '%s'",
    #                                  owner_mobile="owner_mobile = '%s'")

    #        for key, value in data.iteritems():
    #            if key == u'tid':
    #                pass
    #            elif key in ['begintime', 'endtime']:
    #                fields_terminal.setdefault(key, FIELDS_TERMINAL[key] % value) 
    #            elif key == u'cnum':
    #                self.db.execute("UPDATE T_CAR"
    #                                "  SET cnum = %s"
    #                                "  WHERE tid = %s",
    #                                value, self.current_user.tid)
    #                terminal_info_key = get_terminal_info_key(self.current_user.tid)
    #                terminal_info = self.redis.getvalue(terminal_info_key)
    #                if terminal_info:
    #                    terminal_info['alias'] = value if value else self.current_user.sim 
    #                    self.redis.setvalue(terminal_info_key, terminal_info)
    #            elif key == u'owner_mobile':
    #                if not data['owner_mobile']:
    #                    umobile = self.current_user.cid
    #                else:
    #                    umobile = value 
    #                    user = self.db.get("SELECT id FROM T_USER WHERE mobile = %s", umobile)
    #                    if not user:
    #                        self.db.execute("INSERT INTO T_USER(id, uid, password, name, mobile)"
    #                                        "  VALUES(NULL, %s, password(%s), %s, %s )",
    #                                        umobile, '111111',
    #                                        u'', umobile)
    #                        self.db.execute("INSERT INTO T_SMS_OPTION(uid)"
    #                                        "  VALUES(%s)",
    #                                        umobile) 
    #                fields_terminal.setdefault(key, FIELDS_TERMINAL[key] % umobile)
    #                # TODO:need to send JH SMS?
    #                #register_sms = SMSCode.SMS_REGISTER % (umobile, tmobile)
    #                #SMSHelper.send_to_terminal(tmobile, register_sms)
    #                # clear redis, terminal login again
    #                sessionID_key = get_terminal_sessionID_key(tid)
    #                self.redis.delete(sessionID_key)
    #            else:
    #                fields_car.setdefault(key, FIELDS_CAR[key] % value) 

    #        set_clause_car = ','.join([v for v in fields_car.itervalues() if v is not None])
    #        if set_clause_car:
    #            self.db.execute("UPDATE T_CAR SET " + set_clause_car +
    #                            "  WHERE tid = %s",
    #                            tid)

    #        set_clause_terminal = ','.join([v for v in fields_terminal.itervalues() if v is not None])
    #        if set_clause_terminal:
    #            self.db.execute("UPDATE T_TERMINAL_INFO SET " + set_clause_terminal +
    #                            "  WHERE tid = %s",
    #                            tid)
    #        self.send_lq_sms(self.current_user.sim, self.current_user.tid, SMS.LQ.WEB)
    #        self.write_ret(status)
    #    except Exception as e:
    #        logging.exception("[UWEB] cid:%s update terminal info failed. Exception: %s", 
    #                          self.current_user.cid, e.args)
    #        status = ErrorCode.SERVER_BUSY
    #        self.write_ret(status)

    @authenticated
    @tornado.web.removeslash
    def delete(self):
        """Delete a terminal.
        """
        try:
            status = ErrorCode.SUCCESS
            tid = self.get_argument('tid', None)
            flag = self.get_argument('flag', 0)
            logging.info("[UWEB] corp delete terminal tid: %s, flag: %s, cid: %s", 
                         tid, flag, self.current_user.cid)
            terminal = self.db.get("SELECT id, mobile, owner_mobile, login FROM T_TERMINAL_INFO"
                                   "  WHERE tid = %s"
                                   "    AND service_status = %s",
                                   tid, 
                                   UWEB.SERVICE_STATUS.ON)
            if not terminal:
                logging.error("The terminal with tid: %s does not exist!", tid)
                status = ErrorCode.TERMINAL_NOT_EXISTED
                self.write_ret(status)
                return

            key = get_del_data_key(tid)
            self.redis.set(key, flag)
            if terminal.login != GATEWAY.TERMINAL_LOGIN.ONLINE:
                if terminal.mobile == tid:
                    delete_terminal(tid, self.db, self.redis)
                else:
                    status = self.send_jb_sms(terminal.mobile, terminal.owner_mobile, tid)
                self.write_ret(status)
                return

            # unbind terminal
            seq = str(int(time.time()*1000))[-4:]
            args = DotDict(seq=seq,
                           tid=tid)
            response = GFSenderHelper.forward(GFSenderHelper.URLS.UNBIND, args) 
            response = json_decode(response)
            logging.info("UNBind terminal: %s, response: %s", tid, response)
            if response['success'] == ErrorCode.SUCCESS:
                logging.info("[UWEB] uid:%s, tid: %s, tmobile:%s GPRS unbind successfully", 
                             self.current_user.uid, tid, terminal.mobile)

            else:
                status = response['success']
                # unbind failed. clear sessionID for relogin, then unbind it again
                sessionID_key = get_terminal_sessionID_key(tid)
                self.redis.delete(sessionID_key)
                logging.error('[UWEB] uid:%s, tid: %s, tmobile:%s GPRS unbind failed, message: %s, send JB sms...', 
                              self.current_user.uid, tid, terminal.mobile, ErrorCode.ERROR_MESSAGE[status])
                status = self.send_jb_sms(terminal.mobile, terminal.owner_mobile, tid)


            self.write_ret(status)
        except Exception as e:
            logging.exception("[UWEB] cid: %s delete terminal failed. Exception: %s", 
                              self.current_user.cid, e.args) 
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)

