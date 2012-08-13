#!/usr/bin/env python
# -*- coding: utf-8 -*-


import os.path
import site
import logging
import time

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
        result = ErrorCode.FAILED
        try:
            mts = self.db.query("SELECT id, msgid, mobile, content "
                                "  FROM T_SMS "
                                "  WHERE category = %s "
                                "  AND sendstatus = %s"
                                "  ORDER BY id ASC"
                                "  LIMIT 10",
                                SMS.CATEGORY.MT, SMS.SENDSTATUS.PREPARING)

            for mt in mts:
                mobile = mt["mobile"]
                content = mt["content"]
                msgid = mt["msgid"]
                id = mt["id"]
                
                status = self.send_mt(msgid, mobile, content)
                
                if status:
                    if status == "100":
                        logging.info("sms-->gateway success mobile = %s, content = %s, id = %s ", mobile, content, id)
                        self.db.execute("UPDATE T_SMS "
                                       "  SET sendstatus = %s"
                                       "  WHERE id = %s",
                                       SMS.SENDSTATUS.SUCCESS, id)
                    else:
                        if status == "101":
                            logging.error("sms-->gateway failure errorcode = 101, mobile = %s, content = %s, id = %s ", mobile, content, id)
                        elif status == "104":
                            logging.error("sms-->gateway content error! errorcode = 104, mobile = %s, content = %s, id = %s ", mobile, content, id)
                        elif status == "105":
                            logging.error("sms-->gateway frequency too fast errorcode = 105, mobile = %s, content = %s, id = %s ", mobile, content, id)
                        elif status == "106":
                            logging.error("sms-->gateway number limited errorcode = 106, mobile = %s, content = %s, id = %s ", mobile, content, id)
                        else:
                            logging.error("sms-->gateway other error, errorcode unknown, mobile = %s, content = %s, id = %s ", mobile, content, id)
                            
                        self.db.execute("UPDATE T_SMS "
                                        "  SET sendstatus = %s"
                                        "  WHERE id = %s",
                                        SMS.SENDSTATUS.FAILURE, id)
                    result = ErrorCode.SUCCESS
                else:
                    # http response is None
                    # sleep(60)
                    result = ErrorCode.FAILED
            
        except Exception, msg:
            logging.exception("Fetch mt sms exception : %s", msg)
        finally:
            return result
    
    
    def send_mt(self, msgid, mobile, content):
        result = None
        try:
            url = ConfHelper.SMS_CONF.mt_url
            cmd = "send"
            uid = ConfHelper.SMS_CONF.uid
            psw = ConfHelper.SMS_CONF.psw
            msgid = msgid
            mobiles = mobile
            msg = content.encode('gbk')
            
            data = dict(cmd=cmd,
                        uid=uid,
                        psw=psw,
                        mobiles=mobiles,
                        msgid=msgid,
                        msg=msg
                        )
            result = HttpClient().send_http_post_request(url, data)
            
        except Exception, msg:
            logging.exception("Send mt sms exception : %s", msg)
        finally:
            return result
        
