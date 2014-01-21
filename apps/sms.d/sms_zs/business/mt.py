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
    
    def __init__(self, queue):
        ConfHelper.load(options.conf)
        self.db = DBConnection().db
        self.queue = queue 

    def add_sms_to_queue(self):
        status = ErrorCode.SUCCESS
        try:
            mts = self.db.query("SELECT id, msgid, mobile, content "
                                "  FROM T_SMS "
                                "  WHERE category = %s "
                                "  AND send_status = %s"
                                "  ORDER BY id ASC"
                                "  LIMIT 50",
                                SMS.CATEGORY.MT, SMS.SENDSTATUS.PREPARING)

            for mt in mts:
                mobile = mt["mobile"]
                content = mt["content"]
                msgid = mt["msgid"]
                id = mt["id"]
                packet = SMSComposer(mobile, content).result
                url = ConfHelper.SMS_CONF.mt_url
                sms = {"url":url,
                       "packet":packet,
                       "msgid":msgid,
                       "mobile":mobile,
                       "content":content,
                       "id":id}
                self.queue.put(sms)
                self.db.execute("UPDATE T_SMS"
                                "  SET send_status = %s"
                                "  WHERE id = %s",
                                SMS.SENDSTATUS.SENDING, id)
        except Exception as e:
            status = ErrorCode.FAILED
            logging.exception("[SMS] add sms to queue exception: %s", e.args)
        finally:
            return status

    def send_sms(self, sms):
        try:
            status = ErrorCode.SUCCESS
            result = HttpClient().send_http_post_request(sms['url'], sms['packet'])
            if result["status"] == ErrorCode.SUCCESS:
                parser_result = SMSParser(result["response"])
                response_code = parser_result.response_code
                response_text = parser_result.response_text
                if response_code == "0":
                    logging.info("[SMS] SMS-->Gateway success mobile = %s, content = %s, id= %s ", 
                                 sms['mobile'], sms['content'], sms['id'])
                    self.db.execute("UPDATE T_SMS "
                                   "  SET send_status = %s"
                                   "  WHERE id = %s",
                                   SMS.SENDSTATUS.SUCCESS, sms['id'])
                else:
                    status = ErrorCode.FAILED
                    if response_code == "5":
                        logging.error("[SMS] SMS-->Gateway failure, gateway fault, errorcode = 5, mobile = %s, content = %s, id = %s ", 
                                      sms['mobile'], sms['content'], sms['id'])
                    else:
                        logging.error("[SMS] SMS-->Gateway other error, errorcode = %s errortext = %s, mobile = %s, content = %s, id = %s ", 
                                      response_code, response_text,
                                      sms['mobile'], sms['content'], sms['id'])
                        
                        self.db.execute("UPDATE T_SMS "
                                        "  SET send_status = %s"
                                        "  WHERE id = %s",
                                        SMS.SENDSTATUS.FAILURE, sms['id'])
            else:
                status = ErrorCode.FAILED
                self.db.execute("UPDATE T_SMS "
                                "  SET send_status = %s"
                                "  WHERE id = %s",
                                SMS.SENDSTATUS.FAILURE, sms['id'])
                logging.error("[SMS] SMS execute send_http_post_request() failure, mobile = %s, content = %s, id = %s ", 
                              sms['mobile'], sms['content'], sms['id'])
                
        except UnicodeEncodeError as e:
            self.db.execute("UPDATE T_SMS"
                            "  SET send_status = %s, "
                            "  retry_status = %s "
                            "  WHERE id = %s",
                            SMS.SENDSTATUS.FAILURE,
                            SMS.RETRYSTATUS.YES, sms['id'])
            logging.exception("[SMS] Send sms encode exception : %s, msgid:%s, id:%s", 
                              e.args, sms['msgid'], sms['id'])
        except Exception as e:
            status = ErrorCode.FAILED
            logging.exception("[SMS] Send sms exception : %s", e.args)
        finally:
            return status
