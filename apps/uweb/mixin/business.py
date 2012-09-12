# -*- coding: utf-8 -*-

import logging
import time
from tornado.escape import json_decode, json_encode

from utils.dotdict import DotDict
from helpers.confhelper import ConfHelper
from helpers.smshelper import SMSHelper
from helpers.queryhelper import QueryHelper 
from constants import UWEB, SMS, GATEWAY 
from codes.errorcode import ErrorCode
from codes.smscode import SMSCode
from base import BaseMixin


class BusinessMixin(BaseMixin):

    def get_sms_status(self, tmobile):
        """
        sms_status: 0,  // failded. not reached T_SMS
                    1,  // be sent to smsproxy
                    2,  // reached to terminal
                    3,  // terminal has connected to gataway
        """ 
        sms_status = 0
        terminal = QueryHelper.get_terminal_by_tmobile(tmobile, self.db)
        if terminal.login == GATEWAY.TERMINAL_LOGIN.LOGIN:
            sms_status = 3
        elif not terminal.msgid:
            sms_status = 0
        else:
            sms = self.db.get("SELECT send_status, recv_status"
                              "  FROM T_SMS"
                              "  WHERE msgid = %s"
                              "  AND category = %s"
                              "  LIMIT 1",
                              terminal.msgid, SMS.CATEGORY.MT)
            if not sms:
                pass
            elif sms.recv_status == 0:
                sms_status = 2
            elif sms.send_status == 0:
                sms_status = 1
        return sms_status
           
    def get_business_info(self, tmobile):
        """Get business info in detail throught tmobile.
        """
        business = self.db.get("SELECT tu.name, tu.mobile, tu.address, tu.email, tt.begintime, tt.endtime,"
                               "  tt.mobile as tmobile, tt.service_status, tc.cnum"
                               "  FROM T_USER as tu, T_TERMINAL_INFO as tt, T_CAR as tc"
                               "  WHERE  tu.mobile = tt.owner_mobile "
                               "    AND tt.mobile = tc.tmobile "
                               "    AND tt.mobile = %s"
                               "    LIMIT 1",
                               tmobile)
        if business:
            business['sms_status'] = self.get_sms_status(tmobile)
            return business
        else: 
            return None

    def modify_user_terminal_car(self, fields):
        # 1: add user
        if fields.has_key('password'): # create a new user
            uid = self.db.execute("INSERT INTO T_USER(uid, password, name, mobile, address, email)"
                                  "  VALUES(%s, password(%s), %s, %s, %s, %s)"
                                  "  ON DUPLICATE KEY"
                                  "  UPDATE uid = VALUES(uid),"
                                  "         password = VALUES(password),"
                                  "         name = VALUES(name), "
                                  "         mobile = VALUES(mobile), "
                                  "         address = VALUES(address), "
                                  "         email = VALUES(email)",
                                  fields.mobile, fields.password,
                                  fields.name, fields.mobile,
                                  fields.address, fields.email) 
        else: # modify a user
             uid = self.db.execute("INSERT INTO T_USER(uid, name, mobile, address, email)"
                                   "  VALUES(%s, %s, %s, %s, %s)"
                                   "  ON DUPLICATE KEY"
                                   "  UPDATE uid = VALUES(uid),"
                                   "         name = VALUES(name), "
                                   "         mobile = VALUES(mobile), "
                                   "         address = VALUES(address), "
                                   "         email = VALUES(email)",
                                   fields.mobile, fields.name, fields.mobile,
                                   fields.address, fields.email) 
        # 2: add terminal
        tid = self.db.execute("INSERT INTO T_TERMINAL_INFO(tid, mobile, owner_mobile,"
                              "  alias, begintime, endtime)"
                              "  VALUES (%s, %s, %s, %s, %s, %s)"
                              "  ON DUPLICATE KEY"
                              "  UPDATE tid=values(tid),"
                              "         mobile=values(mobile),"
                              "         owner_mobile=values(owner_mobile),"
                              "         alias=values(alias),"
                              "         begintime=values(begintime),"
                              "         begintime=values(begintime),"
                              "         endtime=values(endtime)",
                              fields.tmobile, fields.tmobile,
                              fields.mobile, fields.cnum, 
                              fields.begintime, fields.endtime)

        # 3: add car tnum --> cnum
        cid = self.db.execute("INSERT INTO T_CAR(cnum, tmobile)"
                              "  VALUES(%s, %s)"
                              "  ON DUPLICATE KEY"
                              "  UPDATE cnum = VALUES(cnum),"
                              "         tmobile = VALUES(tmobile)",
                              fields.cnum, fields.tmobile)
        
        # 4: send message to terminal
        #NOTE: here, not send message actually. if need, remove the annotations velow. 
        register_sms = SMSCode.SMS_REGISTER % (fields.mobile, fields.tmobile) 
        ret = SMSHelper.send_to_terminal(fields.tmobile, register_sms)
        ret = DotDict(json_decode(ret))
        if ret.status == ErrorCode.SUCCESS:
            self.db.execute("UPDATE T_TERMINAL_INFO"
                            "  SET msgid = %s"
                            "  WHERE mobile = %s",
                            ret['msgid'], fields.tmobile)
