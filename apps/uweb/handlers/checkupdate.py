# -*- coding: utf-8 -*-

import logging

import tornado.web

from helpers.downloadhelper import get_version_info 
from helpers.queryhelper import QueryHelper 
from utils.dotdict import DotDict
from codes.errorcode import ErrorCode
from constants import UWEB
from base import BaseHandler

class CheckUpdateAndroidHandler(BaseHandler):

    @tornado.web.removeslash
    def get(self):
        status = ErrorCode.SUCCESS
        try:
            category = int(self.get_argument('category', UWEB.APK_TYPE.YDWS))
            if category == UWEB.APK_TYPE.YDWS: # 1
                version_info = get_version_info("android")
                #version_info = QueryHelper.get_version_info_by_category(category, self.db)
            elif category == UWEB.APK_TYPE.YDWQ_MONITOR: # 2
                version_info = QueryHelper.get_version_info_by_category(category, self.db)
            elif category == UWEB.APK_TYPE.YDWQ_MONITORED: # 3
                version_info = QueryHelper.get_version_info_by_category(category, self.db)
            elif category == UWEB.APK_TYPE.YDWS_ANJIETONG: # 4
                version_info = QueryHelper.get_version_info_by_category(category, self.db)
            else:
                logging.info("[UWEB] Invalid category: %s",
                             category)

            self.write_ret(status,
                           dict_=DotDict(version_info=version_info)) 
        except Exception as e:
            logging.exception("[UWEB] Android check update failed. Exception: %s", e.args) 
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)

class CheckUpdateIOSHandler(BaseHandler):

    @tornado.web.removeslash
    def get(self):
        status = ErrorCode.SUCCESS
        try:
            version_info = get_version_info("ios")
            self.write_ret(status,
                           dict_=DotDict(version_info=version_info)) 
        except Exception as e:
            logging.exception("[UWEB] IOS check update failed. Exception: %s", e.args) 
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)
