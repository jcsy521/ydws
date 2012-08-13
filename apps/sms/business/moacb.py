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
from constants import SMS
from codes.errorcode import ErrorCode
from net.httpclient import HttpClient


class MOACB(object):
    
    
    def __init__(self):
        ConfHelper.load(options.conf)
        self.db = DBConnection().db
    
    
    def fetch_mo_sms(self):
        status = ErrorCode.FAILED
        try:
            mos = self.db.query("SELECT id, mobile, content "
                                "  FROM T_SMS "
                                "  WHERE category = %s "
                                "  AND sendstatus = %s"
                                "  ORDER BY id ASC"
                                "  LIMIT 10",
                                SMS.CATEGORY.MO, SMS.SENDSTATUS.PREPARING)
            
            for mo in mos:
                mobile = mo["mobile"]
                content = mo["content"]
                id = mo["id"]
                
                status = self.send_mo_to_acb(mobile, content)
                if status:
                    if status == str(ErrorCode.SUCCESS):
                        logging.info("sms-->acb success mobile = %s, content = %s", mobile, content)
                        self.db.execute("UPDATE T_SMS "
                                       "  SET sendstatus = %s"
                                       "  WHERE id = %s",
                                       SMS.SENDSTATUS.SUCCESS, id)
                    elif status == str(ErrorCode.FAILED):
                        logging.info("sms-->acb failure mobile = %s, content = %s", mobile, content)
                        self.db.execute("UPDATE T_SMS "
                                       "  SET sendstatus = %s"
                                       "  WHERE id = %s",
                                       SMS.SENDSTATUS.FAILURE, id)
                    else:
                        #sms-->acb reponse error result
                        pass
                else:
                    # http response is None
                    pass
            
        except Exception, msg:
            logging.exception("Fetch mo sms exception : %s", msg)
            
            
    def send_mo_to_acb(self, mobile, content):
        result = None
        try:
            url = ConfHelper.UWEB_CONF.url_in + "/sms/mo"
            mobile = mobile
            content = content.encode('utf-8')
            
            data = dict(mobile=mobile,
                        content=content
                        )
            result = HttpClient().send_http_post_request(url, data)
        except Exception, msg:
            logging.exception("Send mo sms to acb exception : %s", msg)
        finally:
            return result
            
            
            
            
            
            