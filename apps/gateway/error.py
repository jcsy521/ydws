# -*- coding: utf-8 -*-

from codes.smscode import SMSCode
from helpers.smshelper import SMSHelper
from helpers.emailhelper import EmailHelper
from helpers.confhelper import ConfHelper

class GWException(Exception):

    def __init__(self):
        Exception.__init__(self)
        self.mobiles = (13693675352, 15901258591, 18310505991)
        self.emails= ('boliang.guan@dbjtech.com', 
                      'zhaoxia.guo@dbjtech.com', 
                      'xiaolei.jia@dbjtech.com',)
        self.notify()

    def notify(self):
        content = SMSCode.SMS_GW_ERROR_REPORT % ConfHelper.UWEB_CONF.url_out
        for mobile in self.mobiles:
            SMSHelper.send(mobile, content)

        for email in self.emails:
            EmailHelper.send(email, content)
