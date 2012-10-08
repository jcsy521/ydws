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


class MO(object):
    
    
    def __init__(self):
        ConfHelper.load(options.conf)
        self.db = DBConnection().db
        
        
    def get_mo_sms_from_gateway(self):
        result = None
        status = ErrorCode.SUCCESS
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
            if result["status"] == ErrorCode.SUCCESS:
                result_list = result["ret"].strip().splitlines()
                # 101 means get mo connection success, but no mo data
                if result_list[0] == "101":
                    pass
                else:
                    result_list.remove(result_list[0])
                    for info in result_list:
                        info_list = info.split("#")
                        msgid = info_list[0]
                        time = info_list[1]
                        mobile = info_list[2]
                        uid = info_list[3]
                        content = info_list[4]
                        
                        self.save(msgid, mobile, content)
                status = ErrorCode.SUCCESS
            else:
                # http response is None
                status = ErrorCode.FAILED
                    
        except Exception, msg:
            status = ErrorCode.FAILED
            logging.exception("Get mo sms exception : %s", msg)
        finally:
            return status
            
            
    def save(self, msgid, mobile, content):
        try:
            insert_time = int(time.time() * 1000)
            user = self.db.get("SELECT mobile "
                               "  FROM T_USER "
                               "  WHERE mobile = %s ",
                               mobile)
            if user:
                self.db.execute("INSERT INTO T_SMS(msgid, mobile, content, "
                                " insert_time, category, send_status) "
                                "  VALUES(%s, %s, %s, %s, %s, %s)",
                                msgid, mobile, content, insert_time,
                                SMS.CATEGORY.MO, SMS.SENDSTATUS.PREPARING)
                logging.info("Gateway-->SMS: save mo success msgid = %s, mobile = %s, content = %s", msgid, mobile, content)
            else:
                logging.error("Gateway-->SMS: mobile no order, give up it mobile = %s, content = %s", mobile, content)
        except Exception, msg:
            logging.exception("Gateway-->SMS save exception : %s", msg)
        
        
        