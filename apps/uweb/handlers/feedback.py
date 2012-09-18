# -*- coding: utf-8 -*-

import logging
import time

import tornado.web
from tornado.escape import json_encode, json_decode

from utils.dotdict import DotDict
from codes.errorcode import ErrorCode
from base import BaseHandler

class FeedBackHandler(BaseHandler):
    """Accept feedbacks from various devices.
    NOTE: One can add feedback when he is not login, so authenticated is no need.
    """

    @tornado.web.removeslash
    def get(self):
        """Jump to feedback.html."""
        self.render('feedback.html')

    @tornado.web.removeslash
    def post(self):
        """Insert new items."""
        status = ErrorCode.SUCCESS
        try:
            data = DotDict(json_decode(self.request.body))
        except Exception as e:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            self.write_ret(status)
            return 

        try:
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
