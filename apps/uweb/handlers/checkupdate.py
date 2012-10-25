# -*- coding: utf-8 -*-

import logging

import tornado.web

from helpers.downloadhelper import get_version_info 
from helpers.queryhelper import QueryHelper
from utils.dotdict import DotDict
from codes.errorcode import ErrorCode
from base import BaseHandler, authenticated

class CheckUpdateHandler(BaseHandler):

    @authenticated
    @tornado.web.removeslash
    def get(self):
        status = ErrorCode.SUCCESS
        try:
            version_info = None
            terminal = QueryHelper.get_terminal_by_tid(self.current_user.tid, self.db)
            if terminal:
                version_info = get_version_info("android")
            else:
                status = ErrorCode.LOGIN_AGAIN
            self.write_ret(status,
                           dict_=DotDict(version_info=version_info)) 
        except Exception as e:
            logging.exception("[UWEB] Android check update failed. uid: %s, tid: %s. Exception: %s", 
                              self.current_user.uid, self.current_user.tid, e.args) 
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)
