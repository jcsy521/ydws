#!/usr/bin/env python
# -*- coding: utf-8 -*-


import os.path
import site
import logging

TOP_DIR_ = os.path.abspath(os.path.join(__file__, "../../../.."))
site.addsitedir(os.path.join(TOP_DIR_, "libs"))
site.addsitedir(os.path.join(TOP_DIR_, "apps/sms"))

from tornado.options import define, options
if 'conf' not in options:
    define('conf', default=os.path.join(TOP_DIR_, "conf/global.conf"))

from helpers.confhelper import ConfHelper
from db_.mysql import DBConnection
from net.httpclient import HttpClient
from constants import SMS


class MOACB(object):
    
    
    def __init__(self):
        self.db = DBConnection().db
        ConfHelper.load(options.conf)
    
    
    def fetch_mo_sms(self):
        try:
            mos = self.db.query("SELECT id, mobile, content "
                                "  FROM T_SMS "
                                "  WHERE category = %s "
                                "  AND sendstatus = %s"
                                "  ORDER BY id ASC"
                                "  LIMIT 10",
                                SMS.CATEGORY.RECEIVE, 0)
            
            for mo in mos:
                mobile = mo["mobile"]
                content = mo["content"]
                id = mo["id"]
                
                status = self.send_mo_to_acb(mobile, content)
                if status == '0':
                    logging.info("Send mo success mobile = %s, content = %s", mobile, content)
                    self.db.execute("UPDATE T_SMS "
                                   "  SET sendstatus = 1"
                                   "  WHERE id = %s",
                                   id)
                else:
                    logging.info("Send mo failed mobile = %s, content = %s", mobile, content)
                    self.db.execute("UPDATE T_SMS "
                                   "  SET sendstatus = 2"
                                   "  WHERE id = %s",
                                   id)
            
        except Exception, msg:
            logging.exception("Fetch mo sms exception : %s", msg)
            self.db.execute("UPDATE T_SMS "
                            "  SET sendstatus = 2"
                            "  WHERE id = %s",
                            id)
            
            
    def send_mo_to_acb(self, mobile, content):
        try:
#            url = "http://drone-004:8600/sms/mo" 
#            url = "http://drone-009:6301/sms/mo" 
            url = ConfHelper.UWEB_CONF.url_in + "/sms/mo"
            mobile = mobile
            content = content.encode('utf-8')
            
            data = dict(mobile=mobile,
                        content=content
                        )
            result = HttpClient().send_http_post_request(url, data)
            return result
        except Exception, msg:
            logging.exception("Send mo sms to acb exception : %s", msg)
            
            
            
            
            
            
            