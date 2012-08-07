#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import time

import tornado.web

from basehandler import BaseHandler
from constants import SMS


class ACBMTHandler(BaseHandler):
    
    @tornado.web.removeslash
    def post(self):
        status = "1"
        try:
            mobile = self.get_argument("mobile")
            content = self.get_argument("content")
            status = self.save(mobile, content)
        except Exception, msg:  
            logging.exception("acb-->sms post exception : %s", msg)
        finally:
            self.write(status)
        
        
    def save(self, mobile, content):
        try:
            insert_time = int(time.time() * 1000)
            msgid = mobile[-4:] + str(insert_time)[-5:]
            self.db.execute("INSERT INTO T_SMS(msgid, mobile, content, "
                            " inserttime, category, sendstatus) "
                            "  VALUES(%s, %s, %s, %s, %s, %s)",
                            msgid, mobile, content, insert_time,
                            SMS.CATEGORY.SEND, SMS.SENDSTATUS.PENDING)
            logging.info("acb-->sms save success! mobile = %s, content = %s", mobile, content)
            return "0"
        except Exception, msg:
            logging.exception("acb-->sms save exception : %s", msg)
            return "1"
            
            
            