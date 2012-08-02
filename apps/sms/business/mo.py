#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os.path
import site
import logging
import time

TOP_DIR_ = os.path.abspath(os.path.join(__file__, "../../../.."))
site.addsitedir(os.path.join(TOP_DIR_, "apps/sms"))

from net.httpclient import HttpClient
from db_.mysql import DBConnection
from constants import SMS


class MO(object):
    
    
    def __init__(self):
        self.db = DBConnection().db
        
        
    def get_mo_sms(self):
        try:
            url = "http://kltx.sms10000.com.cn/sdk/SMS"
            cmd = "getmo"
            uid = "2590"
            psw = "CEE712A91DD4D0A8A67CC8E47B645662"
            
            data = dict(cmd=cmd,
                        uid=uid,
                        psw=psw,
                        )
            result = HttpClient().send_http_post_request(url, data)
            result_list = result.strip().splitlines()
            if result_list[0] == "101":
                logging.info("No mo sms")
            else:
                logging.info("Obtain mo sms")
                result_list.remove(result_list[0])
                for info in result_list:
                    info_list = info.split("#")
                    msgid = info_list[0]
                    time = info_list[1]
                    mobile = info_list[2]
                    uid = info_list[3]
                    content = info_list[4]
                    
                    self.save(msgid, mobile, content)
                    
        except Exception, msg:
            logging.exception("Get mo sms exception : %s", msg)
            
            
    def save(self, msgid, mobile, content):
        try:
            insert_time = int(time.time() * 1000)
            self.db.execute("INSERT INTO T_SMS(msgid, mobile, content, "
                            " inserttime, category, sendstatus) "
                            "  VALUES(%s, %s, %s, %s, %s, %s)",
                            msgid, mobile, content, insert_time,
                            SMS.CATEGORY.RECEIVE, 0)
            logging.info("Gateway-->sms save success! mobile = %s, content = %s", mobile, content)
        except Exception, msg:
            logging.exception("Save mo sms exception : %s", msg)
        
        
        