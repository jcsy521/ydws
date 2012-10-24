# -*- coding: utf-8 -*-

import logging
import datetime
import time

from tornado.escape import json_decode, json_encode
import tornado.web

from helpers.seqgenerator import SeqGenerator
from utils.dotdict import DotDict

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
            sms_options = self.db.get("SELECT login, powerlow, illegalshake,"
                                      "       illegalmove, sos, heartbeat_lost, charge"
                                      "  FROM T_SMS_OPTION"
                                      "  WHERE uid = %s"
                                      "  LIMIT 1",
                                      self.current_user.uid) 
            if not sms_options:
                status = ErrorCode.LOGIN_AGAIN
                logging.error("The user with uid: %s does not exist, redirect to login.html", self.current_user.uid)
                self.write_ret(status)
                return
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
            logging.info("[UWEB] smsoption request: %s, uid: %s, tid: %s", 
                         data, self.current_user.uid, self.current_user.tid)
        except Exception as e:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            self.write_ret(status)
            return 

        try:
            fields = DotDict(login="login = %s",
                             powerlow="powerlow = %s",
                             illegalshake="illegalshake = %s",
                             illegalmove="illegalmove = %s",
                             sos="sos = %s",
                             heartbeat_lost="heartbeat_lost = %s",
                             charge="charge = %s")
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
