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
        status = ErrorCode.SUCCESS
        result = None
        try:
            mos = self.db.query("SELECT id, mobile, content "
                                "  FROM T_SMS "
                                "  WHERE category = %s "
                                "  AND send_status = %s"
                                "  ORDER BY id ASC"
                                "  LIMIT 10",
                                SMS.CATEGORY.MO, SMS.SENDSTATUS.PREPARING)
            
            for mo in mos:
                mobile = mo["mobile"]
                content = mo["content"]
                id = mo["id"]
                
                result = self.send_mo_to_acb(mobile, content)
                if result["status"] == ErrorCode.SUCCESS:
                    if int(result["ret"]) == ErrorCode.SUCCESS:
                        logging.info("SMS-->ACB success mobile = %s, content = %s", mobile, content)
                        self.db.execute("UPDATE T_SMS "
                                       "  SET send_status = %s"
                                       "  WHERE id = %s",
                                       SMS.SENDSTATUS.SUCCESS, id)
                        status = ErrorCode.SUCCESS
                    elif int(result["ret"]) == ErrorCode.FAILED:
                        logging.info("SMS-->ACB failure mobile = %s, content = %s", mobile, content)
                        self.db.execute("UPDATE T_SMS "
                                       "  SET send_status = %s"
                                       "  WHERE id = %s",
                                       SMS.SENDSTATUS.FAILURE, id)
                        status = ErrorCode.FAILURE
                    else:
                        #sms-->acb reponse error result
                        status = ErrorCode.FAILURE
                else:
                    # http response is None
                    status = ErrorCode.FAILURE
            
        except Exception, msg:
            status = ErrorCode.FAILURE
            logging.exception("Fetch mo sms exception : %s", msg)
        finally:
            return status
            
            
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
            
            
            
            
            
            