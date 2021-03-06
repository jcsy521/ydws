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


class MT(object):
    
    def __init__(self):
        ConfHelper.load(options.conf)
        self.db = DBConnection().db
    
    
    def fetch_mt_sms(self):
        status = ErrorCode.SUCCESS
        result = None
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
                
                result = self.send_mt(id, msgid, mobile, content)
                
                if result["status"] == ErrorCode.SUCCESS:
                    logging.info("SMS-->Gateway success mobile = %s, content = %s, id = %s ", mobile, content, id)
                    self.db.execute("UPDATE T_SMS "
                                   "  SET send_status = %s"
                                   "  WHERE id = %s",
                                   SMS.SENDSTATUS.SUCCESS, id)
                    status = ErrorCode.SUCCESS
                else:
                    logging.info("SMS-->Gateway failed. mobile = %s, content = %s, id = %s ", mobile, content, id)
                    # http response is None
                    status = ErrorCode.FAILED
                    self.db.execute("UPDATE T_SMS "
                                    "  SET send_status = %s"
                                    "  WHERE id = %s",
                                    SMS.SENDSTATUS.FAILURE, id)
            
        except Exception, msg:
            status = ErrorCode.FAILED
            logging.exception("Fetch mt sms exception : %s", msg)
        finally:
            return status
    
    
    def send_mt(self, id, msgid, mobile, content):
        try:
            url = ConfHelper.SMS_CONF.mt_url
            cmd = "send"
            #uid = ConfHelper.SMS_CONF.uid
            #psw = ConfHelper.SMS_CONF.psw
            uid = ''
            psw = ''
            msgid = msgid
            mobiles = mobile
            msg = content.encode('gbk')
            
            data = dict(cmd=cmd,
                        uid=uid,
                        psw=psw,
                        mobile=mobiles,
                        msgid=msgid,
                        content=content,
                        )

            result = HttpClient().send_http_post_request(url, data)
            
        except UnicodeEncodeError, msg:
            self.db.execute("UPDATE T_SMS "
                            "  SET send_status = %s, "
                            "  recv_status = %s, "
                            "  retry_status = %s "
                            "  WHERE id = %s",
                            SMS.SENDSTATUS.FAILURE, SMS.USERSTATUS.FAILURE, 
                            SMS.RETRYSTATUS.YES, id)
            logging.exception("MT sms encode exception : %s, msgid:%s, id:%s", msg, msgid, id)
        except Exception, msg:
            logging.exception("Send mt sms exception : %s, msgid:%s, id:%s", msg, msgid, id)
        finally:
            return result
        
    
    def fetch_failed_mt_sms(self):
        status = ErrorCode.SUCCESS
        try:
            mts = self.db.query("SELECT id, msgid, mobile, content, insert_time "
                                "  FROM T_SMS "
                                "  WHERE category = %s "
                                "  AND send_status = %s"
                                "  OR recv_status != %s"
                                "  AND retry_status = %s"
                                "  ORDER BY id ASC"
                                "  LIMIT 10",
                                SMS.CATEGORY.MT, SMS.SENDSTATUS.FAILURE, 
                                SMS.USERSTATUS.SUCCESS, SMS.RETRYSTATUS.NO)
            for mt in mts:
                mobile = mt["mobile"]
                content = mt["content"]
                msgid = mt["msgid"]
                id = mt["id"]
                insert_time = mt["insert_time"]
                
                current_time = int(time.time() * 1000)
                ONE_MIN = 60 * 1000 # millisecond
                
                if current_time - int(insert_time) > ONE_MIN:
                    result = self.send_mt(id, msgid, mobile, content)
                    
                    if result["status"] == ErrorCode.SUCCESS:
                        logging.info("SMS-->Gateway retry success mobile = %s, content = %s, id = %s ", mobile, content, id)
                        self.db.execute("UPDATE T_SMS "
                                       "  SET send_status = %s"
                                       "  WHERE id = %s",
                                       SMS.SENDSTATUS.SUCCESS, id)
                        status = ErrorCode.SUCCESS
                    else:
                        # http response is None
                        status = ErrorCode.FAILED
                        self.db.execute("UPDATE T_SMS "
                                        "  SET send_status = %s"
                                        "  WHERE id = %s",
                                        SMS.SENDSTATUS.FAILURE, id)
                    self.db.execute("UPDATE T_SMS "
                                    "  SET retry_status = %s"
                                    "  WHERE id = %s",
                                    SMS.RETRYSTATUS.YES, id)
                else:
                    pass
        except Exception, msg:
            status = ErrorCode.FAILED
            logging.exception("Fetch failed mt sms exception : %s", msg)
        finally:
            return status
