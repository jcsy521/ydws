# -*- coding: utf-8 -*-

"""This module is designed for alarm-management.
"""

import logging
import datetime
import time

from tornado.escape import json_decode
import tornado.web

from utils.dotdict import DotDict

from base import BaseHandler, authenticated
from codes.errorcode import ErrorCode


class AlarmOptionHandler(BaseHandler):

    """Options about alarm info.:

    Key options of alarm info are as follows:

    1, # login 
    2, # powerlow
    3, # illegalshake
    4, # illegalmove
    5, # sos 
    6, # hearbeat lost
    7, # region enter
    8, # retion out
    9, # power off
    10, # stop
    11, # speed_limit 

    The alarmoption is associate with user(administrator or operator in corp). 

    If alarmoption is inexistence for the user, initialize it.  
    If user's infomation changed, the alarmoption is should be changed with it.

    """
    @authenticated
    @tornado.web.removeslash
    def get(self):
        """Display smsoption of current user.

        workflow:
        if alarmoption is exist:
            return alarmoption 
        else:
            initialize the alarmoption
            return alarmoption 
        """
        status = ErrorCode.SUCCESS
        try:
            umobile = self.get_argument('umobile')
            logging.info(
                "[UWEB] Alarmoption request: %s", self.request.arguments)
        except Exception as e:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            logging.exception(
                "[UWEB] Invalid data format. Exception: %s", e.args)
            self.write_ret(status)
            return

        try:
            alarm_options = QueryHelper.get_alarm_options(mobile, self.db)
            self.write_ret(status,
                           dict_=dict(res=alarm_options))
        except Exception as e:
            logging.exception("[UWEB] Get alarmoption failed. umobile: %s, Exception: %s",
                              umobile, e.args)
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)

    @authenticated
    @tornado.web.removeslash
    def put(self):
        """Modify alarmoptions for current user.
        """
        status = ErrorCode.SUCCESS
        try:
            data = DotDict(json_decode(self.request.body))
            umobile = data.umobile
            logging.info("[UWEB] Alarmoption request: %s, uid: %s",
                         data, umobile)
        except Exception as e:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            self.write_ret(status)
            return

        try:
            del data['umobile']            
            update_alarm_option(data, umobile, self.db, self.redis)
            self.write_ret(status)

        except Exception as e:
            logging.exception("[UWEB] Update Alarmoption failed. umobile: %s, Exception: %s",
                              umobile, e.args)
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)
