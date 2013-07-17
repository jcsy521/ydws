# -*- coding: utf-8 -*-

import logging
import time

import tornado.web
from tornado.escape import json_encode, json_decode

from utils.dotdict import DotDict
from utils.checker import check_sql_injection
from helpers.confhelper import ConfHelper
from codes.errorcode import ErrorCode
from base import BaseHandler

class FeedBackHandler(BaseHandler):
    """Accept feedbacks from various devices.
    NOTE: One can add feedback when he is not login, so authenticated is no need.
    """

    @tornado.web.removeslash
    def get(self):
        """Jump to feedback.html."""
        self.render('feedback.html',
                    map_type=ConfHelper.LBMP_CONF.map_type)

    @tornado.web.removeslash
    def post(self):
        """Insert new items."""
        status = ErrorCode.SUCCESS
        try:
            data = DotDict(json_decode(self.request.body))
            logging.info("[UWEB] feedback request: %s", data)
        except Exception as e:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            self.write_ret(status)
            return 

        try:

            #if data.has_key('contact') and not check_sql_injection(data.contact):
            #    status = ErrorCode.ILLEGAL_NAME
            #    logging.info("[UWEB] feedback failed, Message: %s", ErrorCode.ERROR_MESSAGE[status])
            #    self.write_ret(status)
            #    return

            #if data.has_key('email')  and not check_sql_injection(data.email):
            #    status = ErrorCode.ILLEGAL_EMAIL
            #    logging.info("[UWEB] feedback failed, Message: %s", ErrorCode.ERROR_MESSAGE[status])
            #    self.write_ret(status)
            #    return

            self.db.execute("INSERT into T_FEEDBACK(contact,email,content,timestamp,category)"
                            "  VALUES(%s, %s, %s, %s, %s)",
                            data.contact, data.email, data.content,
                            int(time.time()), data.category)
            self.write_ret(status)
        except Exception as e:
            status = ErrorCode.FEEDBACK_FAILED
            logging.exception("[UWEB] add feedback failed, Exception: %s, content:\n%s", 
                              e.args, data.content)
            self.write_ret(status)
