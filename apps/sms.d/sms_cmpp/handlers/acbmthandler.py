#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import time

import tornado.web

from basehandler import BaseHandler
from constants import SMS
from codes.errorcode import ErrorCode


class ACBMTHandler(BaseHandler):
    
    @tornado.web.removeslash
    def post(self):
        insert_time = int(time.time() * 1000)
        msgid = str(insert_time)[-9:]
        try:
            content = self.get_argument("content")
            logging.info("content = %s", content)
            mobile = self.get_argument("mobile")
            
            self.db.execute("INSERT INTO T_SMS(msgid, mobile, content, "
                            " insert_time, category, send_status) "
                            "  VALUES(%s, %s, %s, %s, %s, %s)",
                            msgid, mobile, content, insert_time,
                            SMS.CATEGORY.MT, SMS.SENDSTATUS.PREPARING)
            logging.info("acb-->sms save success! mobile = %s, content = %s", mobile, content)
            self.write({'status' : ErrorCode.SUCCESS, 'msgid' : msgid})
        except Exception, msg:  
            logging.exception("acb-->sms post exception : %s", msg)
            self.write({'status' : ErrorCode.FAILED, 'msgid' : msgid})
        
        
