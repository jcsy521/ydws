# -*- coding: utf-8 -*-

"""This module is designed for owner-service, one activity in YDWS.

#NOTE：deprecated.
"""

import logging
import time

import tornado.web

from base import BaseHandler
from codes.errorcode import ErrorCode
from tornado.escape import json_decode

class OwnerserviceHandler(BaseHandler):

    @tornado.web.removeslash
    def get(self):
        username = self.get_current_user()
        self.render("html/ownerservice.html", 
                    username=username)

    @tornado.web.removeslash
    def post(self):
        status = ErrorCode.SUCCESS
        try:
            data = json_decode(self.request.body)
            umobile = data['umobile']
            cars = data['cars']
            add_time = int(time.time())
            for car in cars:
                cnum = car['car_num']
                car_type = car['car_type']
                if umobile and cnum:
                    self.db.execute("INSERT INTO T_OWNERSERVICE(umobile, "
                                    "  cnum, add_time, car_type)"
                                    "  VALUES(%s,%s,%s,%s)", 
                                    umobile, cnum, add_time, car_type)

            self.write_ret(status=status)
        except Exception as e:
            status = ErrorCode.CREATE_USER_FAILURE
            messeage = ErrorCode.ERROR_MESSAGE[status]
            logging.exception("[UWEB] Ownerservice failed. Exception: %s",
                              e.args)
            self.write_ret(status=status, 
                           message=messeage)
