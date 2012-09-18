# -*- coding: utf-8 -*-

import os.path
DOWNLOAD_DIR_ = os.path.abspath(os.path.join(__file__, "../../static/download"))

import logging
import hashlib

import tornado.web
from tornado.escape import json_encode, json_decode

from utils.dotdict import DotDict
from utils.checker import check_sql_injection, check_phone
from codes.errorcode import ErrorCode
from codes.smscode import SMSCode 
from helpers.downloadhelper import get_version_info,\
     get_download_count, update_download_count
from helpers.smshelper import SMSHelper
from constants import DOWNLOAD
from errors.updateerror import UpdateException, DataBaseException
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
        data = DotDict(json_decode(self.request.body))

        mobile = data.mobile 
        captcha_sms = data.captcha_sms 
        captchahash_sms = data.captchahash_sms 
        category = data.category 

        m = hashlib.md5()
        m.update(captcha_sms.lower())
        hash_ = m.hexdigest()
        if  hash_.lower() != captchahash_sms.lower():
            status = ErrorCode.WRONG_CAPTCHA
        else:
            version_info = get_version_info('android')
            downloadurl = DOWNLOAD.URL.ANDROID % version_info.versionname
            download_remind = SMSCode.SMS_DOWNLOAD_REMIND % downloadurl 
            SMSHelper.send(mobile, download_remind)
   
        self.write_ret(status)