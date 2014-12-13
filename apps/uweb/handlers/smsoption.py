# -*- coding: utf-8 -*-

"""This module is designed for the querying and modifying of sms-option.
"""

import logging

from tornado.escape import json_decode, json_encode
import tornado.web

from helpers.queryhelper import QueryHelper

from base import BaseHandler, authenticated
from codes.errorcode import ErrorCode


class SMSOptionHandler(BaseHandler):
    """SMSOption:
       login/powerlow/poweroff/illegalmove/sos/heartbeat_lost
       1: send
       0: not send
    """

    @authenticated
    @tornado.web.removeslash
    def get(self):
        """Display smsoption of current user.
        """
        status = ErrorCode.SUCCESS
        try: 
            sms_option = QueryHelper.get_sms_option(self.current_user.uid, db) 
            self.write_ret(status,
                           dict_=dict(sms_options=sms_options))
        except Exception as e:
            logging.exception("[UWEB] uid:%s tid:%s get SMS Options failed. Exception: %s", e.args) 
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)

    @authenticated
    @tornado.web.removeslash
    def put(self):
        """Modify smsoptions for current user.
        """
        status = ErrorCode.SUCCESS
        try:
            data = DotDict(json_decode(self.request.body))
            logging.info("[UWEB] smsoption request: %s, uid: %s", 
                         data, self.current_user.uid)
        except Exception as e:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            self.write_ret(status)
            return 

        try:
            fields = DotDict(login="login = %s",
                             powerlow="powerlow = %s",
                             powerdown="powerdown = %s",
                             illegalshake="illegalshake = %s",
                             illegalmove="illegalmove = %s",
                             sos="sos = %s",
                             heartbeat_lost="heartbeat_lost = %s",
                             charge="charge = %s",
                             region_enter="region_enter = %s",
                             region_out="region_out = %s")
            for key, value in data.iteritems():
                data[key] = fields[key] % data[key] 
            set_clause = ','.join([v for v in data.itervalues() if v is not None])
            if set_clause:
                self.db.execute("UPDATE T_SMS_OPTION SET " + set_clause +
                                "  WHERE uid = %s",
                                self.current_user.uid)
            self.write_ret(status)
        except Exception as e:
            logging.exception("[UWEB] uid:%s tid:%s update SMS Options failed.  Exception: %s", 
                              self.current_user.uid,self.current_user.tid, e.args)
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)

class SMSOptionCorpHandler(BaseHandler):
    """SMSOption:
       login/powerlow/poweroff/illegalmove/sos/heartbeat_lost/region_enter/region_out
       1: send
       0: not send
    """

    @authenticated
    @tornado.web.removeslash
    def get(self):
        """Display smsoption of current user.
        """
        status = ErrorCode.SUCCESS
        try: 
            terminals = self.db.query("SELECT tt.mobile, tt.owner_mobile FROM T_TERMINAL_INFO as tt, "
                                      "  T_GROUP as tg, T_CORP as tc" 
                                      "  WHERE tt.service_status = 1 AND tc.cid = %s "
                                      "  AND tc.cid = tg.corp_id AND tt.group_id = tg.id",
                                      self.current_user.cid)
            mobiles = []
            for terminal in terminals:
                if terminal.owner_mobile not in mobiles:
                    mobiles.append(terminal.owner_mobile)

            sms_options = {} 
            for mobile in mobiles:              
                sms_option = QueryHelper.get_sms_option(self.current_user.uid, db) 
                sms_options[mobile] = sms_option
            self.write_ret(status,
                           dict_=dict(sms_options=sms_options))
        except Exception as e:
            logging.exception("[UWEB] uid:%s tid:%s get SMS Options failed. Exception: %s", e.args) 
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)

    @authenticated
    @tornado.web.removeslash
    def put(self):
        """Modify smsoptions for the given owner_mobile.
        """
        status = ErrorCode.SUCCESS
        try:
            data = DotDict(json_decode(self.request.body))
            owner_mobile = data['owner_mobile']
            logging.info("[UWEB] smsoption request: %s, uid: %s", 
                         data, self.current_user.uid)
        except Exception as e:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            self.write_ret(status)
            return 

        try:
            del data['owner_mobile']
            fields = DotDict(login="login = %s",
                             powerlow="powerlow = %s",
                             powerdown="powerdown = %s",
                             illegalshake="illegalshake = %s",
                             illegalmove="illegalmove = %s",
                             sos="sos = %s",
                             heartbeat_lost="heartbeat_lost = %s",
                             charge="charge = %s",
                             region_enter="region_enter = %s",
                             region_out="region_out = %s",
                             stop="stop = %s",
                             speed_limit="speed_limit = %s")
            for key, value in data.iteritems():
                data[key] = fields[key] % data[key] 
            set_clause = ','.join([v for v in data.itervalues() if v is not None])
            if set_clause:
                self.db.execute("UPDATE T_SMS_OPTION SET " + set_clause +
                                "  WHERE uid = %s",
                                owner_mobile)
            self.write_ret(status)
        except Exception as e:
            logging.exception("[UWEB] uid:%s tid:%s update SMS Options failed.  Exception: %s", 
                              self.current_user.uid,self.current_user.tid, e.args)
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)
