#register!/usr/bin/env python
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
from helpers.queryhelper import QueryHelper
from utils.misc import safe_unicode, get_terminal_sessionID_key
from utils.dotdict import DotDict

from checker import check_privileges 
from constants import PRIVILEGES

class SettingHandler(BaseHandler):

    @authenticated
    @check_privileges([PRIVILEGES.TERMINAL_QUERY])
    @tornado.web.removeslash
    def get(self):
        username = self.get_current_user()
        self.render('report/terminalsetting.html',
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
            tmobile = self.get_argument('tmobile', '')
            key = self.get_argument('key', '')

            sql_cmd = "SELECT %(key)s FROM T_TERMINAL_INFO WHERE mobile = %(tmobile)s LIMIT 1 " % locals()
            res = self.db.get(sql_cmd)
            if res:
                res = dict(tmobile=tmobile,
                           key=key,
                           value=res.get(key,'') if res else '')
            self.render('report/terminalsetting.html',
                        status=status, res=res, hash_=hash_)
        except Exception as e:
            logging.exception("Search register for %s,it is does'\nt exists", tmobile)
            self.render('errors/error.html', message=ErrorCode.FAILED)

    @authenticated
    @check_privileges([PRIVILEGES.TERMINAL_QUERY])
    @tornado.web.removeslash
    def put(self):

        status = ErrorCode.SUCCESS
        res = {}
        hash_ = ''
        try:
            data = DotDict(json_decode(self.request.body))
            logging.info("[UWEB] Setting modify request: %s", self.request.body) 
            tmobile = data.tmobile 
            key = data.key
            value = data.value 
            logging.info("[UWEB] Setting modify request: %s", data) 
        except Exception as e: 
            status = ErrorCode.ILLEGAL_DATA_FORMAT 
            logging.exception("[UWEB] Invalid data format. Exception: %s", e.args) 
            self.write_ret(status) 
            return

        try:
            clear_session = False
            terminal = QueryHelper.get_terminal_by_tmobile(tmobile, self.db)
            if not terminal:
                status = ErrorCode.TERMINAL_NOT_EXISTED 
            else:
                tid = terminal.tid
                sql_cmd = "UPDATE T_TERMINAL_INFO SET %(key)s = %(value)s WHERE tid='%(tid)s' LIMIT 1 " % locals()
                if key in ['tracking_interval']: 
                    clear_session = True

                if clear_session:
                    sessionID_key = get_terminal_sessionID_key(tid)
                    self.redis.delete(sessionID_key)
                self.db.execute(sql_cmd)

            self.write_ret(status)
        except Exception as e:
            logging.exception("Modify setting failed. Exception: %s", e.args)
            self.render('errors/error.html', message=ErrorCode.FAILED)
