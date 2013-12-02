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


class Status(object):
    
    
    def __init__(self):
        ConfHelper.load(options.conf)
        self.db = DBConnection().db
        
        
    def get_user_receive_status(self):
        result = None
        status = ErrorCode.SUCCESS
        try:
            url = ConfHelper.SMS_CONF.mt_url
            cmd = "getstatus"
            uid = ConfHelper.SMS_CONF.uid
            psw = ConfHelper.SMS_CONF.psw
            
            data = dict(cmd=cmd,
                        uid=uid,
                        psw=psw,
                        )
            result = HttpClient().send_http_post_request(url, data)
            if result["status"] == ErrorCode.SUCCESS:
                self.save_user_receive_status(result["ret"])
                status = ErrorCode.SUCCESS
            else:
                # http response is None
                status = ErrorCode.FAILED
            
        except Exception, msg:
            status = ErrorCode.FAILED
            logging.exception("Get user receive status exception : %s", msg)
        finally:
            return status
        
    
    def save_user_receive_status(self, result):
        try:
#        result = '''100
#567848895#15012345678#0
#567816375#18842476170#0'''
            
            # result_list = ['100', '567848895#15012345678#0', '567816375#18842476170#0']
            result_list = result.strip().splitlines()
            # 101 means get status connection success, but no status data
            if result_list[0] == "101":
                pass
            # result_list[0] == "100"
            else:
                result_list.remove(result_list[0])
                for info in result_list:
                    info_list = info.split("#")
                    msgid = info_list[0]
                    mobile = info_list[1]
                    status = info_list[2]
                    if status == str(SMS.USERSTATUS.FAILURE):
                        logging.warn("User %s does not recieve sms, msgid = %s ", mobile, msgid)
                        self.db.execute("UPDATE T_SMS "
                                        "  SET recv_status = %s"
                                        "  WHERE msgid = %s"
                                        "  AND category = %s"
                                        "  AND mobile = %s",
                                        SMS.USERSTATUS.FAILURE, msgid, SMS.CATEGORY.MT, mobile)
                    elif status == str(SMS.USERSTATUS.SUCCESS):
                        self.db.execute("UPDATE T_SMS "
                                        "  SET recv_status = %s"
                                        "  WHERE msgid = %s"
                                        "  AND category = %s"
                                        "  AND mobile = %s",
                                        SMS.USERSTATUS.SUCCESS, msgid, SMS.CATEGORY.MT, mobile)
                    else:
                        logging.error("User %s recieve sms status error, msgid = %s, status = %s ", mobile, msgid, status)
        except Exception, msg:
            logging.exception("Save user receive status exception : %s", msg)
                
        
