#!/usr/bin/env python
# -*- coding: utf-8 -*-


import os.path
import site
import logging

TOP_DIR_ = os.path.abspath(os.path.join(__file__, "../../../.."))
site.addsitedir(os.path.join(TOP_DIR_, "libs"))
site.addsitedir(os.path.join(TOP_DIR_, "apps/sms"))

from db_.mysql import DBConnection
from net.httpclient import HttpClient
from constants import SMS


class MT(object):
    
    def __init__(self):
        self.db = DBConnection().db
    
    
    def fetch_mt_sms(self):
        try:
            mts = self.db.query("SELECT id, msgid, mobile, content "
                                "  FROM T_SMS "
                                "  WHERE category = %s "
                                "  AND sendstatus != %s"
                                "  ORDER BY id ASC"
                                "  LIMIT 10",
                                SMS.CATEGORY.SEND, 1)
            
            for mt in mts:
                mobile = mt["mobile"]
                content = mt["content"]
                msgid = mt["msgid"]
                id = mt["id"]
                
                status = self.send_mt(msgid, mobile, content)
                
                if status == "100":
                    logging.info("Send mt success mobile = %s, content = %s", mobile, content)
                    self.db.execute("UPDATE T_SMS "
                                   "  SET sendstatus = 1"
                                   "  WHERE id = %s",
                                   id)
                else:
                    if status == "101":
                        logging.error("Send mt failure mobile = %s, content = %s", mobiles, content)
                    elif status == "104":
                        logging.error("Send mt content error! mobile = %s, content = %s", mobile, content)
                    elif status == "105":
                        logging.error("Send mt frequency too fast")
                    elif status == "106":
                        logging.error("Send mt number limited")
                    else:
                        logging.error("Send mt other error")
                        
                    self.db.execute("UPDATE T_SMS "
                                   "  SET sendstatus = 2"
                                   "  WHERE id = %s",
                                   id)
                    
        except Exception, msg:
            logging.exception("Fetch mt sms exception : %s", msg)
    
    
    def send_mt(self, msgid, mobile, content):
        try:
            cmd = "send"
            uid = "2590"
            psw = "CEE712A91DD4D0A8A67CC8E47B645662"
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
            result = HttpClient().send_http_post_request(data)
            return result
        except Exception, msg:
            logging.exception("Send mt sms exception : %s", msg)
        
