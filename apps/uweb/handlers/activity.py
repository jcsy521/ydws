# -*- coding: utf-8 -*-

import logging

import tornado.web

from utils.dotdict import DotDict
from codes.errorcode import ErrorCode
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
                res = self.db.query("SELECT title, begintime, endtime, filename, html_name"
                                    "  FROM T_ACTIVITY"
                                    "  ORDER BY begintime DESC LIMIT 1")
            else:
                res = self.db.query("SELECT title, begintime, endtime, filename, html_name"
                                    "  FROM T_ACTIVITY"
                                    "  WHERE begintime > %s",
                                    timestamp)
            for r in res:
                if r['filename']:
                    r['filepath'] = self.application.settings['activity_path'] + r['filename']
                else:
                    r['filepath'] = ''
                r['url'] = r['html_name']
                del r['filename']
                del r['html_name']
            self.write_ret(status,
                           dict_=DotDict(res=res))
        except Exception as e:
            logging.exception("[UWEB] get activities failed. Exception: %s",
                              e.args)
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)
