# -*- coding: utf-8 -*-

from codes.smscode import SMSCode
from helpers.smshelper import SMSHelper
from helpers.emailhelper import EmailHelper
from helpers.confhelper import ConfHelper

class GWException(Exception):

    def __init__(self):
        Exception.__init__(self)
        self.mobiles = (15982463820, 15882081659, 15800022894)
        self.emails= ('yueyong@supeq.com', 
                      'fengliang@supeq.com', 
                      'liusiming@supeq.com',)
        #self.notify()

    def notify(self):
        content = SMSCode.SMS_GW_ERROR_REPORT % ConfHelper.UWEB_CONF.url_out
        for mobile in self.mobiles:
            SMSHelper.send(mobile, content)

        for email in self.emails:
            EmailHelper.send(email, content)
