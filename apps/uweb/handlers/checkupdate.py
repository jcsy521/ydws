# -*- coding: utf-8 -*-

import logging

import tornado.web

from helpers.downloadhelper import get_version_info 
from utils.dotdict import DotDict
from codes.errorcode import ErrorCode
from base import BaseHandler

class CheckUpdateHandler(BaseHandler):

    @tornado.web.removeslash
    def get(self):
        status = ErrorCode.SUCCESS
        try:
            version_info = get_version_info("android")
            self.write_ret(status,
                           dict_=DotDict(version_info=version_info)) 
        except Exception as e:
            logging.exception("[UWEB] Android check update failed. Exception: %s", e.args) 
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)
