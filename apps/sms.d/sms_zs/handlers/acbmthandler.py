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
            mobile = self.get_argument("mobile")

            cm = int(mobile[:3])
            cm_list = (139,138,137,136,135,134,159,150,151,158,157,188,187,152,182,147)
            
            if cm not in cm_list:
                logging.info("%s is not China Mobile, so skip the sms.", mobile)
                self.write({'status' : ErrorCode.SUCCESS, 'msgid' : msgid})
                return
            
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
        
        
