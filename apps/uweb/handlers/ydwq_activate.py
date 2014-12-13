# -*- coding: utf-8 -*-

"""This module is designed for YDWQ.
"""

import logging

from tornado.escape import json_decode, json_encode
import tornado.web
import time

from utils.dotdict import DotDict
from codes.errorcode import ErrorCode
from constants import UWEB 

from base import BaseHandler, authenticated

class YDWQActivateHandler(BaseHandler):

    def get_terminal_by_sn(self, sn):
        terminal = self.db.get("SELECT id, service_status, mobile"
                               "  FROM T_TERMINAL_INFO"
                               "  WHERE sn = %s LIMIT 1",
                               sn)
        return terminal

    @tornado.web.removeslash
    def post(self):
        """Activate a YDWQ terminal.

        workflow:
        mobile, activation --> activated by monitor
        mobile, activation, sn --> activated by monitored itself
        """
        status = ErrorCode.SUCCESS
        try:
            data = DotDict(json_decode(self.request.body))
            activation_code = data.activation_code.upper()
            sn = data.get('sn','')
            mobile = data.get('mobile','')
            logging.info("[UWEB] Activate request: %s", data)
        except Exception as e:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            logging.exception("[UWEB] Invalid data format. Exception: %s",
                              e.args)
            self.write_ret(status)
            return

        try:
            # check mobile & activation_code
            terminal = self.db.get("SELECT id, service_status, mobile, sn"
                                   "  FROM T_TERMINAL_INFO"
                                   "  WHERE mobile = %s"
                                   "  AND activation_code = %s"
                                   "  AND (service_status = %s"
                                   "    or service_status = %s)"
                                   "  AND biz_type = %s LIMIT 1",
                                   mobile, activation_code,
                                   UWEB.SERVICE_STATUS.TO_BE_ACTIVATED, 
                                   UWEB.SERVICE_STATUS.ON, 
                                   UWEB.BIZ_TYPE.YDWQ)
            if not terminal:
                status = ErrorCode.ACCOUNT_INVALID
                logging.info("[UWEB] Monitored is activated by monitor failed. Account is invalid."
                             "mobile: %s, activation_code: %s, sn: %s",
                             mobile, activation_code, sn)
            else:
                if not sn: # it's activated by monitor
                    self.db.execute("UPDATE T_TERMINAL_INFO"
                                    "  SET service_status = %s"
                                    "  WHERE activation_code = %s",
                                    UWEB.SERVICE_STATUS.ON, activation_code)
                    logging.info("[UWEB] Monitored is activated by monitor successful. mobile: %s, activation_code: %s, sn: %s",
                                 mobile, activation_code, sn)
                else:
                    if sn != terminal['sn']:  # sn is changed, 
                        t = self.get_terminal_by_sn(sn)
                        if t: # has activation_code, but sn is used 
                            status = ErrorCode.SN_USED
                            logging.info("[UWEB] Monitored is activated by monitor failed. sn is used by others."
                                         " mobile: %s, activation_code: %s, sn: %s",
                                         mobile, activation_code, sn)
                        else:
                            self.db.execute("UPDATE T_TERMINAL_INFO"
                                            "  SET service_status = %s, "
                                            "      sn = %s"
                                            "  WHERE activation_code = %s",
                                            UWEB.SERVICE_STATUS.ON, sn, activation_code)
                            logging.info("[UWEB] Monitored is activated by monitor successful. sn is changed to a new sn not used by others ."
                                         " mobile: %s, activation_code: %s, sn: %s",
                                         mobile, activation_code, sn)
                    else: 
                        self.db.execute("UPDATE T_TERMINAL_INFO"
                                        "  SET service_status = %s"
                                        "  WHERE activation_code = %s",
                                        UWEB.SERVICE_STATUS.ON, activation_code)
                        status = ErrorCode.SUCCESS
                        logging.info("[UWEB] Monitored normal login. mobile: %s, activation_code: %s, sn: %s.", 
                                     mobile, activation_code, sn)

            self.write_ret(status)
        except Exception as e:
            logging.exception("[UWEB] Activate YDWQ termianl failed. Exception: %s",
                              e.args)
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)