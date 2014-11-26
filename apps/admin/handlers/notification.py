#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import time
from os import SEEK_SET
import hashlib
import xlwt
from cStringIO import StringIO

import tornado.web
from tornado.escape import json_decode

from base import BaseHandler, authenticated
from codes.errorcode import ErrorCode
from mixin import BaseMixin
from excelheaders import MANUALLOG_FILE_NAME, MANUALLOG_SHEET, MANUALLOG_HEADER
from utils.misc import safe_unicode

from checker import check_privileges 
from constants import PRIVILEGES

class NotificationMixin(BaseMixin):
    KEY_TEMPLATE = "notification_report_%s_%s"

    def prepare_data(self, hash_):
        mem_key = self.get_memcache_key(hash_)
        data = self.getvalue(mem_key)

        if data:
            return data

class NotificationSearchHandler(BaseHandler, NotificationMixin):

    @authenticated
    @check_privileges([PRIVILEGES.TERMINAL_QUERY])
    @tornado.web.removeslash
    def get(self):
        username = self.get_current_user()
        self.render('report/terminalnotification.html',
                    username=username,
                    res={},
                    hash_='')

    @authenticated
    @check_privileges([PRIVILEGES.TERMINAL_QUERY])
    @tornado.web.removeslash
    def post(self):

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

            mileage=mileage if mileage else {} 
            day=day if day else {}
            mileage['distance_current'] = terminal['distance_current']
            day['current_time'] = int(time.time()) 

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
            logging.exception("Search manual log for %s,it is does'\nt exists", mobile)
            self.render('errors/error.html', message=ErrorCode.FAILED)


       _tmp_file.close()
