# -*- coding: utf-8 -*-

"""This module is designed for activity.
"""

import logging
import time

import tornado.web

from utils.dotdict import DotDict
from codes.errorcode import ErrorCode
from helpers.queryhelper import QueryHelper

from base import BaseHandler


class ActivityHandler(BaseHandler):

    @tornado.web.removeslash
    def get(self):
        """Get activities.
        """
        status = ErrorCode.SUCCESS
        try:
            res = []
            timestamp = self.get_argument('timestamp', None)
            if timestamp is None:
                res = QueryHelper.get_activity_list(self.db)
            elif int(timestamp) == -1:
                res = QueryHelper.get_activity_avaliable(self.db)
            else:
                res = QueryHelper.get_activity_by_begintime(timestamp, self.db)
            for r in res:
                if r['filename']:
                    r['filepath'] = self.application.settings[
                        'activity_path'] + r['filename']
                else:
                    r['filepath'] = ''
                r['url'] = r['html_name']
                del r['filename']
                del r['html_name']
            self.write_ret(status,
                           dict_=DotDict(res=res))
        except Exception as e:
            logging.exception("[UWEB] Get activities failed. Exception: %s",
                              e.args)
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)
