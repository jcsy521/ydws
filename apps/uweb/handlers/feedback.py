# -*- coding: utf-8 -*-

"""This module is designed for feedback.
"""

import logging
import time

import tornado.web
from tornado.escape import json_decode

from utils.dotdict import DotDict
from utils.misc import safe_unicode
from helpers.confhelper import ConfHelper
from codes.errorcode import ErrorCode
from base import BaseHandler

class FeedBackWeixinHandler(BaseHandler):
    """Accept feedbacks from various devices.
    """
    @tornado.web.removeslash
    def get(self):
        """Jump to feedback_weixin.html."""
        self.render('feedback_weixin.html',
                    map_type=ConfHelper.LBMP_CONF.map_type)

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
            mobile = data.get('mobile', '')
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

            self.db.execute("INSERT INTO T_FEEDBACK(contact, mobile,"
                            "  email, content, timestamp, category)"
                            "  VALUES(%s, %s, %s, %s, %s, %s)",
                            data.contact, mobile, data.email, 
                            safe_unicode(data.content),
                            int(time.time()), data.category)
            self.write_ret(status)
        except Exception as e:
            status = ErrorCode.FEEDBACK_FAILED
            logging.exception("[UWEB] add feedback failed, Exception: %s, content:\n%s", 
                              e.args, data.content)
            self.write_ret(status)
