# -*- coding: utf-8 -*-

import os.path
DOWNLOAD_DIR_ = os.path.abspath(os.path.join(__file__, "../../static/download"))

import logging
import hashlib
import random
import string

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
        """Download apk for android."""
        status = ErrorCode.SUCCESS
        # TODO: here, just handle android
        version_info = get_version_info('android')
        category = self.get_argument('category', '2')
        versionname = self.get_argument('versionname', version_info.versionname)
        update_download_count(category, self.db)

        url = "/static/download/ACB_"+versionname+".apk"
        self.redirect(url)

class DownloadTerminalHandler(BaseHandler):

    @tornado.web.removeslash
    def get(self):
        """Download test.apk for terminal."""
        url = "/static/terminal/script.luac"
        self.redirect(url)

class UploadTerminalHandler(BaseHandler):

    @tornado.web.removeslash
    def post(self):
        try:
            upload_file = self.request.files['fileUpload'][0]
        except Exception as e:
            logging.info("exception:%s", e.args)
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            self.write_ret(status)
            return

        try:
            status = ErrorCode.SUCCESS
            filename = upload_file['filename']

            # write into tmp file
            if filename == "script.luac":
                file_path = "/home/ydcws/acb/trunk/apps/uweb/static/terminal/" + filename
                output_file = open(file_path, 'w')
                output_file.write(upload_file['body'])
                output_file.close()
            else:
                logging.error("Upload file %s not assign file type.", filename)
                self.write("上传的非指定文件类型")
                return
        except Exception as e:
            logging.info("Upload terminal file fail:%s", e.args)
        else:
            logging.info("Upload file %s success!", filename)
            self.write("上传成功!")
            return



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
