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
                    SMSHelper.send_to_terminal(tmobile,content)
                    if is_clear == 1:
                        clear_data(tmobile,self.acbdb)
                    self.write_ret(status)
             
                elif sms_type == 'CQ':
                    content = ':' + sms_type
                    SMSHelper.send_to_terminal(tmobile,content)
                    self.write_ret(status)              
                                   
                elif sms_type == 'DEL':
                    delete_terminal(tmobile,self.acbdb,self.redis,del_user=True)
                    self.write_ret(status)
                                                         
                elif sms_type == 'DOMAIN':
                    ip = data.get('domain')
                    info = self.acbdb.get('SELECT * FROM T_TERMINAL_INFO WHERE mobile=%s', tmobile)
                    if info:
                        self.acbdb.execute('UPDATE T_TERMINAL_INFO SET domain=%s WHERE mobile=%s', ip, tmobile)                
                        self.write_ret(status)
                    else:
                        status = ErrorCode.TERMINAL_NOT_EXISTED
                        self.write_ret(status)
        except Exception, e:
            logging.exception("acb-->sms post exception : %s", e)
            self.render('errors/error.html', message=ErrorCode.ERROR_MESSAGE[ErrorCode.FAILED])            
    
