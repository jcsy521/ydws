#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os.path
import site
import logging
import time

TOP_DIR_ = os.path.abspath(os.path.join(__file__, "../../../.."))
site.addsitedir(os.path.join(TOP_DIR_, "apps/sms"))

from tornado.options import define, options
if 'conf' not in options:
    define('conf', default=os.path.join(TOP_DIR_, "conf/global.conf"))

from helpers.confhelper import ConfHelper
from db_.mysql import DBConnection
from constants import SMS
from net.httpclient import HttpClient


class MO(object):
    
    
    def __init__(self):
        ConfHelper.load(options.conf)
        self.db = DBConnection().db
        
        
    def get_mo_sms(self):
        try:
            url = ConfHelper.SMS_CONF.mt_url
            cmd = "getmo"
            uid = ConfHelper.SMS_CONF.uid
            psw = ConfHelper.SMS_CONF.psw
            
            data = dict(cmd=cmd,
                        uid=uid,
                        psw=psw,
                        )
            result = HttpClient().send_http_post_request(url, data)
            if result:
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
            else:
                # http response is None
                pass
                    
        except Exception, msg:
            logging.exception("Get mo sms exception : %s", msg)
            
            
    def save(self, msgid, mobile, content):
        try:
            insert_time = int(time.time() * 1000)
            self.db.execute("INSERT INTO T_SMS(msgid, mobile, content, "
                            " inserttime, category, sendstatus) "
                            "  VALUES(%s, %s, %s, %s, %s, %s)",
                            msgid, mobile, content, insert_time,
                            SMS.CATEGORY.RECEIVE, SMS.SENDSTATUS.PENDING)
            logging.info("Gateway-->sms save success! mobile = %s, content = %s", mobile, content)
        except Exception, msg:
            logging.exception("Gateway-->sms save exception : %s", msg)
        
        
        