#!/usr/bin/env python
# -*- coding: utf-8 -*-


import os.path
import site
import logging
import time
from exceptions import UnicodeEncodeError

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
from util.smscomposer import SMSComposer
from util.smsparser import SMSParser

class MT(object):
    
    def __init__(self):
        ConfHelper.load(options.conf)
        self.db = DBConnection().db
    
    
    def fetch_mt_sms(self):
        status = ErrorCode.SUCCESS
        result = {'status': ErrorCode.FAILED, 'response' : None}
        try:
            mts = self.db.query("SELECT id, msgid, mobile, content "
                                "  FROM T_SMS "
                                "  WHERE category = %s "
                                "  AND send_status = %s"
                                "  ORDER BY id ASC"
                                "  LIMIT 10",
                                SMS.CATEGORY.MT, SMS.SENDSTATUS.PREPARING)

            for mt in mts:
                mobile = mt["mobile"]
                content = mt["content"]
                msgid = mt["msgid"]
                id = mt["id"]
                
                pack_result = SMSComposer(mobile, content).result
                url = ConfHelper.SMS_CONF.mt_url
                HttpClient().async_send_http_post_request(url, pack_result, _on_finish)

                def _on_finish(db):
                
                    if result["status"] == ErrorCode.SUCCESS:
                        
                        parser_result = SMSParser(result["response"])
                        response_code = parser_result.response_code
                        response_text = parser_result.response_text
                        
                        if response_code == "0":
                            logging.info("SMS-->Gateway success mobile = %s, content = %s, id = %s ", mobile, content, id)
                            self.db.execute("UPDATE T_SMS "
                                           "  SET send_status = %s"
                                           "  WHERE id = %s",
                                           SMS.SENDSTATUS.SUCCESS, id)
                            status = ErrorCode.SUCCESS
                        else:
                            if response_code == "5":
                                logging.error("SMS-->Gateway failure, gateway fault, errorcode = 5, mobile = %s, content = %s, id = %s ", mobile, content, id)
                            else:
                                logging.error("SMS-->Gateway other error, errorcode = %s errortext = %s, mobile = %s, content = %s, id = %s ", response_code, response_text, mobile, content, id)
                                
                                self.db.execute("UPDATE T_SMS "
                                                "  SET send_status = %s"
                                                "  WHERE id = %s",
                                                SMS.SENDSTATUS.FAILURE, id)
                            status = ErrorCode.FAILED
                    else:
                        status = ErrorCode.FAILED
                        self.db.execute("UPDATE T_SMS "
                                        "  SET send_status = %s"
                                        "  WHERE id = %s",
                                        SMS.SENDSTATUS.FAILURE, id)
                        logging.error("SMS execute send_http_post_request() failure, mobile = %s, content = %s, id = %s ", mobile, content, id)
                    self.finish()
                    
        except UnicodeEncodeError, msg:
            self.db.execute("UPDATE T_SMS "
                            "  SET send_status = %s, "
                            "  retry_status = %s "
                            "  WHERE id = %s",
                            SMS.SENDSTATUS.FAILURE,
                            SMS.RETRYSTATUS.YES, id)
            logging.exception("MT sms encode exception : %s, msgid:%s, id:%s", msg, msgid, id)
        except Exception, msg:
            status = ErrorCode.FAILED
            logging.exception("Fetch mt sms exception : %s", msg)
        finally:
            return status
        
    
    def fetch_failed_mt_sms(self):
        status = ErrorCode.SUCCESS
        result = {'status': ErrorCode.FAILED, 'response' : None}
        try:
            mts = self.db.query("SELECT id, msgid, mobile, content, insert_time "
                                "  FROM T_SMS "
                                "  WHERE category = %s "
                                "  AND send_status = %s"
                                "  AND retry_status = %s"
                                "  ORDER BY id ASC"
                                "  LIMIT 10",
                                SMS.CATEGORY.MT, SMS.SENDSTATUS.FAILURE, SMS.RETRYSTATUS.NO)
            
            for mt in mts:
                mobile = mt["mobile"]
                content = mt["content"]
                msgid = mt["msgid"]
                id = mt["id"]
                insert_time = mt["insert_time"]
                
                pack_result = SMSComposer(mobile, content).result
                url = ConfHelper.SMS_CONF.mt_url
                result = HttpClient().send_http_post_request(url, pack_result)
                
                if result["status"] == ErrorCode.SUCCESS:
                    parser_result = SMSParser(result["response"])
                    response_code = parser_result.response_code
                    response_text = parser_result.response_text
                    
                    if response_code == "0":
                        logging.info("SMS-->Gateway retry success mobile = %s, content = %s, id = %s ", mobile, content, id)
                        self.db.execute("UPDATE T_SMS "
                                       "  SET send_status = %s,"
                                       "  retry_status = %s"
                                       "  WHERE id = %s",
                                       SMS.SENDSTATUS.SUCCESS, SMS.RETRYSTATUS.YES, id)
                        status = ErrorCode.SUCCESS
                    else:
                        logging.error("SMS-->Gateway retry error, errorcode = %s errortext = %s, mobile = %s, content = %s, id = %s ", response_code, response_text, mobile, content, id)
                        self.db.execute("UPDATE T_SMS "
                                        "  SET send_status = %s,"
                                        "  retry_status = %s"
                                        "  WHERE id = %s",
                                        SMS.SENDSTATUS.FAILURE, SMS.RETRYSTATUS.YES, id)
                        status = ErrorCode.FAILED
                else:
                    status = ErrorCode.FAILED
                    self.db.execute("UPDATE T_SMS "
                                    "  SET send_status = %s,"
                                    "  retry_status = %s"
                                    "  WHERE id = %s",
                                    SMS.SENDSTATUS.FAILURE, SMS.RETRYSTATUS.YES, id)
                    logging.error("SMS retry execute send_http_post_request() failure, mobile = %s, content = %s, id = %s ", mobile, content, id)
        except UnicodeEncodeError, msg:
            self.db.execute("UPDATE T_SMS "
                            "  SET send_status = %s, "
                            "  retry_status = %s "
                            "  WHERE id = %s",
                            SMS.SENDSTATUS.FAILURE,
                            SMS.RETRYSTATUS.YES, id)
            logging.exception("MT sms encode exception : %s, msgid:%s, id:%s", msg, msgid, id)
        except Exception, msg:
            status = ErrorCode.FAILED
            logging.exception("Fetch failed mt sms exception : %s", msg)
        finally:
            return status
        
        
