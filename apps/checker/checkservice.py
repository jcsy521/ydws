# -*- coding: utf-8 -*-

import os.path
import site

TOP_DIR_ = os.path.abspath(os.path.join(__file__, "../../.."))
site.addsitedir(os.path.join(TOP_DIR_, "libs"))

import logging
import time

from db_.mysql import DBConnection
from helpers.smshelper import SMSHelper
from helpers.emailhelper import EmailHelper 
from helpers.confhelper import ConfHelper
from codes.smscode import SMSCode


class CheckService(object):

    def __init__(self):
        self.db = DBConnection().db
        self.tid = 'B123SIMULATOR'
        self.mobiles = [13693675352, 18310505991, 13581731204]
        self.emails = ['boliang.guan@dbjtech.com', 'youbo.sun@dbjtech.com', 'xiaolei.jia@dbjtech.com']
        #self.emails = ['boliang.guan@dbjtech.com', 'zhaoxia.guo@dbjtech.com', 'xiaolei.jia@dbjtech.com', 'yuanchanggang@sxt.com.cn']
        
    def check_service(self):
        try:
            base_id = self.get_lid_by_tid(self.tid)
            while True:
                time.sleep(600) # 10 minutes
                new_lid = self.get_lid_by_tid(self.tid) 
                logging.info("[CK] simulator terminal location base_id:%s, new_lid:%s", base_id, new_lid)
                if new_lid > base_id:
                    base_id = new_lid
                else:
                    for mobile in self.mobiles:
                        sms = SMSCode.SMS_SERVICE_EXCEPTION_REPORT % ConfHelper.UWEB_CONF.url_out 
                        SMSHelper.send(mobile, sms)
                        logging.info("[CK] Notify Administrator:%s By SMS, service exception!", mobile)
                    for email in self.emails:
                        content = SMSCode.SMS_SERVICE_EXCEPTION_REPORT % ConfHelper.UWEB_CONF.url_out
                        EmailHelper.send(email, content) 
                        logging.info("[CK] Notify Administrator:%s By EMAIL, service exception!", email)
        except KeyboardInterrupt:
            logging.error("Ctrl-C is pressed.")
        except Exception as e:
            logging.exception("[CK] Check service exception.")

    def get_lid_by_tid(self, tid):
        location = self.db.get("SELECT id"
                               "  FROM T_LOCATION"
                               "  WHERE tid = %s"
                               "  ORDER BY id DESC LIMIT 1", 
                               tid)
        if location: 
            return location.id
        else:
            return 0
