# -*- coding: utf-8 -*-

import logging
import datetime
import time
from dateutil.relativedelta import relativedelta

from tornado.escape import json_decode, json_encode
import tornado.web

from helpers.seqgenerator import SeqGenerator
from utils.misc import get_today_last_month
from utils.dotdict import DotDict

from base import BaseHandler, authenticated
from codes.errorcode import ErrorCode


class DetailHandler(BaseHandler):
    """Browse location fixes from Web."""

    @authenticated
    @tornado.web.removeslash
    def get(self):
        user = self.db.get("SELECT name, mobile, address, email, corporation, remark"
                           "  FROM T_USER"
                           "  WHERE uid = %s"
                           "  limit 1",
                           self.current_user.uid) 

        details = DotDict()
        details.update(user)
        self.write_ret(ErrorCode.SUCCESS,
                       dict_=dict(details=details))

    @authenticated
    @tornado.web.removeslash
    def put(self):
        try:
            data = DotDict(json_decode(self.request.body))
            name = data.name
            mobile = data.mobile
            address= data.address
            email = data.email
            corporation = data.corporation
            remark = data.remark
			
            self.db.execute("UPDATE T_USER"
                            "  SET mobile = %s,"
                            "      name = %s,"
                            "      address = %s,"
                            "      email = %s,"
                            "      corporation = %s,"
                            "      remark = %s"
                            "  WHERE uid = %s",
                            mobile, name, address, email, 
                            corporation, remark, self.current_user.uid)

            self.write_ret(ErrorCode.SUCCESS)

        except Exception as e:
            logging.exception("Update detail failed. Exception: %s", e.args)
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)

