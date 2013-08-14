#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import time
import tornado.web

from tornado.escape import json_decode

from base import BaseHandler,authenticated
from mysql import DBAcbConnection
from codes.errorcode import ErrorCode
from helpers.smshelper import SMSHelper
from helpers.confhelper import ConfHelper
from utils.dotdict import DotDict
from utils.checker import check_phone
from utils.public import clear_data, delete_terminal
from constants import UWEB

class MessageHandler(BaseHandler):

    @authenticated 
    def get(self):
        username = self.get_current_user()
        n_role = self.db.get("select role from T_LOG_ADMIN where name = %s", username)
        domain = ConfHelper.GW_SERVER_CONF.domain
        domain_ip = ConfHelper.GW_SERVER_CONF.domain_ip
        domains = [domain,domain_ip]
        self.render('sms/sms.html',
                    username = username,
                    role = n_role.role,
                    domains = domains)
    
    @authenticated
    @tornado.web.removeslash
    def post(self):
        status = ErrorCode.SUCCESS
        try:
            data = json_decode(self.request.body)
            sms_type = data.get('sms_type')
            tmobile = data.get('tmobile')
            content = ''
            if check_phone(tmobile) is None:
                status = ErrorCode.ILLEGAL_MOBILE
                self.write_ret(status) 
            else:
                if sms_type == 'JH':
                    umobile = data.get('umobile')
                    if check_phone(umobile):
                        content = ':SIM' + ' ' + umobile + ':' + tmobile
                        SMSHelper.send_to_terminal(tmobile,content)
                        self.write_ret(status)
                    else:
                        status=ErrorCode.ILLEGAL_MOBILE
                        self.write_ret(status)
                elif sms_type == 'JB':
                    content = ':' + sms_type
                    is_clear = data.get('is_clear')
                    ret = SMSHelper.send_to_terminal(tmobile,content)
                    ret = json_decode(ret)
                    terminal = self.acbdb.get("SELECT id, tid, owner_mobile, login FROM T_TERMINAL_INFO"
                                               "  WHERE mobile = %s"
                                               "    AND service_status = 1",
                                               tmobile)
                    if not terminal:
                        status = ErrorCode.TERMINAL_NOT_EXISTED
                        logging.error("The terminal with tmobile: %s does not exist!", tmobile)
                        self.write_ret(status)
                        return
                    umobile = terminal.owner_mobile 

                    # record the del action  
                    self.acbdb.execute("UPDATE T_SUBSCRIPTION_LOG SET del_time = %s, op_type = %s" 
                                       " WHERE tmobile = %s ", 
                                       int(time.time()), UWEB.OP_TYPE.DEL, tmobile)

                    if ret['status'] == 0:
                        self.acbdb.execute("UPDATE T_TERMINAL_INFO"
                                            "  SET service_status = 2"
                                            "  WHERE mobile = %s",
                                            tmobile)
                        terminals = self.acbdb.query("SELECT id FROM T_TERMINAL_INFO"
                                                      "  WHERE owner_mobile = %s"
                                                      "    AND service_status = 1",
                                                      umobile)
                        # clear user
                        if len(terminals) == 0:
                            self.acbdb.execute("DELETE FROM T_USER"
                                                "  WHERE mobile = %s",
                                                umobile)
                    if is_clear == 1:
                        clear_data(tmobile,self.acbdb)
                    self.write_ret(status)
             
                elif sms_type == 'CQ':
                    content = ':' + sms_type
                    SMSHelper.send_to_terminal(tmobile,content)
                    self.write_ret(status)              
                                   
                elif sms_type == 'DEL':
                    terminal = self.acbdb.get('SELECT tid FROM T_TERMINAL_INFO WHERE mobile=%s', tmobile)
                    if terminal:
                        delete_terminal(terminal.tid,self.acbdb,self.redis,del_user=False)
                    self.write_ret(status)
                                                         
                elif sms_type == 'DOMAIN':
                    ip = data.get('domain')
                    content = ':DOMAIN '+ip 
                    info = self.acbdb.get('SELECT * FROM T_TERMINAL_INFO WHERE mobile=%s', tmobile)
                    if info:
                        self.acbdb.execute('UPDATE T_TERMINAL_INFO SET domain=%s WHERE mobile=%s', 
                                           content tmobile)                
                        SMSHelper.send_to_terminal(tmobile, content)
                        self.write_ret(status)
                    else:
                        status = ErrorCode.TERMINAL_NOT_EXISTED
                        self.write_ret(status)
        except Exception, e:
            logging.exception("acb-->sms post exception : %s", e)
            self.render('errors/error.html', message=ErrorCode.ERROR_MESSAGE[ErrorCode.FAILED])            
    
