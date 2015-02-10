#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""This module is designed for mileage-notification-log of terminal.
"""

import logging
import time
import hashlib

import tornado.web

from base import BaseHandler, authenticated
from codes.errorcode import ErrorCode
from mixin import BaseMixin

from checker import check_privileges 
from constants import PRIVILEGES


class NotificationMixin(BaseMixin):
    KEY_TEMPLATE = "notification_report_%s_%s"

class NotificationSearchHandler(BaseHandler, NotificationMixin):

    @authenticated
    @check_privileges([PRIVILEGES.TERMINAL_QUERY])
    @tornado.web.removeslash
    def get(self):
        """Jump to the terminalnotification.html.
        """
        username = self.get_current_user()
        self.render('report/terminalnotification.html',
                    username=username,
                    res={},
                    hash_='')

    @authenticated
    @check_privileges([PRIVILEGES.TERMINAL_QUERY])
    @tornado.web.removeslash
    def post(self):
        """QueryHelper individuals according to the 
        given parameters.
        """
        status = ErrorCode.SUCCESS
        res = {}
        hash_ = ''
        try:
            mobile = self.get_argument('mobile', 0)
            terminal = self.db.get("SELECT tid, owner_mobile, assist_mobile, distance_current"
                                   " FROM T_TERMINAL_INFO WHERE mobile = %s LIMIT 1", mobile)
            tid = terminal.tid if terminal else ''

            if not tid:
                status = ErrorCode.TERMINAL_NOT_EXISTED
                message = ErrorCode.ERROR_MESSAGE[status]
                self.render('report/terminalnotification.html',
                            status=status, res=res, hash_=hash_, message=message)
                return
			
            mileage_cmd = ("SELECT distance_notification, notify_count, left_days, notify_time FROM T_MILEAGE_NOTIFICATION"
                           "  WHERE tid='%s'") % tid

            day_cmd = ("SELECT day_notification, notify_count, left_days, notify_time FROM T_DAY_NOTIFICATION"
                       "  WHERE tid='%s'") % tid

            mileage = self.db.get(mileage_cmd)
            day = self.db.get(day_cmd)

            if mileage:
                mileage['distance_current'] = terminal['distance_current']
            else: 
                mileage = []

            if day:
                day['current_time'] = int(time.time()) 
            else: 
                day = []

            res = dict(tid=tid,
                       owner_mobile=terminal['owner_mobile'],
                       assist_mobile=terminal['assist_mobile'],
                       mileage=mileage,
			           day=day)

            m = hashlib.md5()
            m.update(self.request.body)
            hash_ = m.hexdigest()
            mem_key = self.get_memcache_key(hash_)
            self.redis.setvalue(mem_key, res, time=self.MEMCACHE_EXPIRY)

            self.render('report/terminalnotification.html',
                        status=status, res=res, hash_=hash_)
        except Exception as e:
            logging.exception("Search notification failed. mobile: %s, Exception: %s.", 
                               mobile, e.args)
            self.render('errors/error.html', message=ErrorCode.FAILED)
