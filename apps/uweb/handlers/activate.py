# -*- coding: utf-8 -*-

import logging

from tornado.escape import json_decode, json_encode
import tornado.web
import time

from utils.dotdict import DotDict
from codes.errorcode import ErrorCode
from constants import UWEB 

from base import BaseHandler, authenticated

class ActivateHandler(BaseHandler):

    def get_terminal_by_sn(self, sn):
        terminal = self.db.get("SELECT id, service_status, mobile"
                               "  FROM T_TERMINAL_INFO"
                               "  WHERE sn = %s LIMIT 1",
                               sn)
        return terminal

    @tornado.web.removeslash
    def post(self):
        """Activate a YDWQ terminal.
        """
        status = ErrorCode.SUCCESS
        try:
            data = DotDict(json_decode(self.request.body))
            activation_code = data.activation_code.upper()
            sn = data.get('sn','')
            logging.info("[UWEB] activate request: %s", 
                         data)
        except Exception as e:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            logging.exception("[UWEB] Invalid data format. Exception: %s",
                              e.args)
            self.write_ret(status)
            return

        try:
            if not sn: # we assume it's activated by monitor
                terminal = self.db.get("SELECT id, service_status, mobile"
                                       "  FROM T_TERMINAL_INFO"
                                       "  WHERE activation_code = %s"
                                       "  AND sn = '' "
                                       "  AND service_status = %s "
                                       "  AND biz_type = %s LIMIT 1",
                                       activation_code, UWEB.SERVICE_STATUS.TO_BE_ACTIVATED, 
                                       UWEB.BIZ_TYPE.YDWQ)
                if terminal: 
                    self.db.execute("UPDATE T_TERMINAL_INFO"
                                    "  SET service_status = %s"
                                    "  WHERE activation_code = %s",
                                    UWEB.SERVICE_STATUS.ON, activation_code)
                    logging.info("[UWEB] monitored is activated by monitor.  activation_code: %s, sn: %s",
                                 activation_code, sn)
                else: 
                    status = ErrorCode.ILLEGAL_DATA_FORMAT
                    logging.info("[UWEB] Invalid data format. data: %s", data)
                    self.write_ret(status)
                    return
                    
            terminal = self.db.get("SELECT id, service_status, mobile"
                                   "  FROM T_TERMINAL_INFO"
                                   "  WHERE activation_code = %s"
                                   "  AND sn = %s"
                                   "  AND biz_type = %s LIMIT 1",
                                   activation_code, sn,
                                   UWEB.BIZ_TYPE.YDWQ)
            if terminal: # normal login
                logging.info("[UWEB] normal login. activation_code: %s, sn: %s.", 
                             activation_code, sn)
                self.db.execute("UPDATE T_TERMINAL_INFO"
                                "  SET service_status = %s"
                                "  WHERE activation_code = %s",
                                UWEB.SERVICE_STATUS.ON, activation_code)
                self.write_ret(status,
                               dict_=DotDict(mobile=terminal.mobile))
            else: 
                terminal = self.db.get("SELECT id, service_status, mobile, sn"
                                       "  FROM T_TERMINAL_INFO"
                                       "  WHERE activation_code = %s"
                                       "  AND biz_type = %s LIMIT 1",
                                       activation_code, UWEB.BIZ_TYPE.YDWQ)
                if not terminal: # no code 
                    status = ErrorCode.TERMINAL_NOT_EXISTED
                    logging.error("[UWEB] activation_code: %s can not be found.",
                                 activation_code)
                    self.write_ret(status)
                else: # has code 
                    if not terminal['sn']:
                        terminal = self.get_terminal_by_sn(sn)
                        if terminal: # has code, but sn is used 
                            status = ErrorCode.ACCOUNT_NOT_MATCH
                            logging.info("[UWEB] sn: %s has exist.", sn)
                            self.write_ret(status,
                                           dict_=DotDict(mobile=terminal.mobile))
                            return 

                        status = ErrorCode.SUCCESS
                        self.db.execute("UPDATE T_TERMINAL_INFO"
                                        "  SET sn = %s,"
                                        "      service_status = %s"
                                        "  WHERE activation_code = %s",
                                        sn, UWEB.SERVICE_STATUS.ON, activation_code)
                        logging.info("[UWEB] monitored is activated by monitor. now update the sn.  activation_code: %s, sn: %s",
                                     activation_code, sn)
                        self.write_ret(status,
                                       dict_=DotDict(mobile=terminal.mobile))
                        return

                    terminal = self.get_terminal_by_sn(sn)
                    if terminal: # has code, but sn is used 
                        status = ErrorCode.ACCOUNT_NOT_MATCH
                        logging.info("[UWEB] sn: %s has exist.", sn)
                        self.write_ret(status,
                                       dict_=DotDict(mobile=terminal.mobile))
                    else: # has code, sn not exist: a new activate
                        terminal = self.db.get("SELECT id, service_status, mobile"
                                               "  FROM T_TERMINAL_INFO"
                                               "  WHERE activation_code = %s LIMIT 1",
                                               activation_code)
                        if terminal['service_status'] == UWEB.SERVICE_STATUS.ON: # the code is used normal with another sn
                            status = ErrorCode.ACCOUNT_NOT_MATCH
                            logging.info("[UWEB] sn: %s has exist.", sn)
                            self.write_ret(status,
                                           dict_=DotDict(mobile=terminal.mobile))
                        else: # the code is not used normal, now use the new sn
                            logging.info("[UWEB] sn: %s, activation_code: %s activated successfully.", 
                                          sn, activation_code)
                            self.db.execute("UPDATE T_TERMINAL_INFO"
                                            "  SET sn = %s, "
                                            "      service_status = %s"
                                            "  WHERE activation_code = %s",
                                            sn, UWEB.SERVICE_STATUS.ON, activation_code)
                            self.write_ret(status,
                                           dict_=DotDict(mobile=terminal.mobile))
        except Exception as e:
            logging.exception("[UWEB] activate YDWQ termianl failed. Exception: %s",
                              e.args)
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)

class ActivationcodeHandler(BaseHandler):

    @tornado.web.removeslash
    def get(self):
        """Get activation_code according to tid or mobile.
        """
        status = ErrorCode.SUCCESS
        try:
            tid = self.get_argument('tid','')
            mobile = self.get_argument('mobile','')
            logging.info("[ACTIVATIONCODE] Activation_code query, tid: %s, mobile: %s.",
                         tid, mobile)
        except Exception as e:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            logging.exception("[ACTIVATIONCODE] Illegal format, body: %s.",
                              self.request.body)
            self.write_ret(status)
            return 

        try:
            terminal = None
            if tid:
                terminal = self.db.get("SELECT activation_code, mobile, tid, biz_type FROM T_TERMINAL_INFO"
                                       "  WHERE tid = %s", 
                                       tid)
            if not terminal:
                if mobile:
                    terminal = self.db.get("SELECT activation_code, mobile, tid, biz_type FROM T_TERMINAL_INFO"
                                           "  WHERE mobile = %s", 
                                           mobile)


            activation_code = terminal.get('activation_code', '') if terminal else ''
            tid = terminal.get('tid', '') if terminal else ''
            mobile = terminal.get('mobile', '') if terminal else ''
            biz_type = terminal.get('biz_type', UWEB.BIZ_TYPE.YDWS) if terminal else UWEB.BIZ_TYPE.YDWS

            self.write_ret(status,
                           dict_=DotDict(activation_code=activation_code,
                                         tid=tid,
                                         mobile=mobile,
                                         biz_type=biz_type))
        except Exception as e:
            status = ErrorCode.SERVER_BUSY
            logging.exception("[ACTIVATIONCODE] get activation_code failed, body: %s. Exception: %s", 
                              self.request.body, e.args)
            self.write_ret(status)

