# -*- coding: utf-8 -*-

import os.path
DOWNLOAD_DIR_ = os.path.abspath(os.path.join(__file__, "../../static/download"))

import logging
import hashlib

import tornado.web
from tornado.escape import json_encode, json_decode

from utils.dotdict import DotDict
from codes.errorcode import ErrorCode
from codes.smscode import SMSCode 
from helpers.downloadhelper import get_version_info,\
     update_download_count
from helpers.smshelper import SMSHelper
from helpers.confhelper import ConfHelper
from constants import DOWNLOAD

from base import BaseHandler, authenticated

class DownloadHandler(BaseHandler):
    """Download different file throught param."""

    # NOTE: never add authenticated. user may download it by 2-dimensionn code.
    #@authenticated
    @tornado.web.removeslash
    def get(self):
        """Delete existing items."""
        status = ErrorCode.SUCCESS
        # TODO: here, just handle android
        version_info = get_version_info('android')
        category = self.get_argument('category', '2')
        versionname = self.get_argument('versionname', version_info.versionname)
        update_download_count(category, self.db)

        url = "/static/download/ACB_"+versionname+".apk"
        self.redirect(url)

class DownloadSmsHandler(BaseHandler):
    """Send download_url to user's mobile."""

    @tornado.web.removeslash
    def post(self):
        """Send sms to user's mobile."""
        status = ErrorCode.SUCCESS
        try:
            data = DotDict(json_decode(self.request.body))
            logging.info("[UWEB] downloadsms request: %s", data)

            mobile = data.mobile 
            captcha_sms = data.captcha_sms 
            captchahash_sms = data.captchahash_sms 
            category = data.category 
        except Exception as e:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            self.write_ret(status)
            return 

        try:
            m = hashlib.md5()
            m.update(captcha_sms.lower())
            hash_ = m.hexdigest()
            if  hash_.lower() != captchahash_sms.lower():
                status = ErrorCode.WRONG_CAPTCHA
                logging.info("[UWEB] downloadsms failed. Message: %s", ErrorCode.ERROR_MESSAGE[status])
            else:
                version_info = get_version_info('android')
                # downloadurl = DOWNLOAD.URL.ANDROID % ConfHelper.UWEB_CONF.url_out
                download_remind = SMSCode.SMS_DOWNLOAD_REMIND 
                SMSHelper.send(mobile, download_remind)
       
            self.write_ret(status)
        except Exception as e:
            logging.exception("[UWEB] smsdownload failed. Exception: %s. ", 
                              e.args)
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)
