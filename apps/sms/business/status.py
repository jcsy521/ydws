#!/usr/bin/env python
# -*- coding: utf-8 -*-


import os.path
import site
import logging

TOP_DIR_ = os.path.abspath(os.path.join(__file__, "../../../.."))
site.addsitedir(os.path.join(TOP_DIR_, "apps/sms"))

from net.httpclient import HttpClient
from db_.mysql import DBConnection


class Status(object):
    
    
    def __init__(self):
        self.db = DBConnection().db
        
        
    def get_user_receive_status(self):
        try:
            cmd = "getstatus"
            uid = "2590"
            psw = "CEE712A91DD4D0A8A67CC8E47B645662"
            
            data = dict(cmd=cmd,
                        uid=uid,
                        psw=psw,
                        )
            result = HttpClient().send_http_post_request(data)
            print result
            self.save_user_receive_status(result)
        except Exception, msg:
            logging.exception("Get user receive status exception : %s", msg)
        
    
    def save_user_receive_status(self, result):
        try:
#        result = '''100
#567848895#15012345678#0
#567816375#18842476170#0'''
            
            # result_list = ['100', '567848895#15012345678#0', '567816375#18842476170#0']
            result_list = result.strip().splitlines()
            if result_list[0] == "101":
                logging.info("No user receive status")
            # result_list[0] == "100"
            else:
                logging.info("Obtain user receive status")
                result_list.remove(result_list[0])
                for info in result_list:
                    info_list = info.split("#")
                    msgid = info_list[0]
                    mobile = info_list[1]
                    status = info_list[2]
                    if status == '1':
                        logging.warn("User %s does not recieve sms, msgid = %s ", mobile, msgid)
                    
                    self.db.execute("UPDATE T_SMS "
                                    "  SET userstatus = %s"
                                    "  WHERE msgid = %s"
                                    "  AND mobile = %s",
                                    status, msgid, mobile)
        except Exception, msg:
            logging.exception("Save user receive status exception : %s", msg)
                
        
if __name__ == "__main__":
    print Status().get_user_receive_status()