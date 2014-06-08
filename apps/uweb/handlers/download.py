# -*- coding: utf-8 -*-

import os.path
DOWNLOAD_DIR_ = os.path.abspath(os.path.join(__file__, "../../static/download"))

import logging
import hashlib
import random
import string
import time

import tornado.web
from tornado.escape import json_encode, json_decode

from utils.dotdict import DotDict
from codes.errorcode import ErrorCode
from codes.smscode import SMSCode 
from helpers.downloadhelper import get_version_info,\
     update_download_count, get_download_count
from helpers.smshelper import SMSHelper
from helpers.confhelper import ConfHelper
from helpers.queryhelper import QueryHelper
from constants import DOWNLOAD, UWEB

from base import BaseHandler, authenticated

class DownloadHandler(BaseHandler):
    """Download different file throught param."""

    # NOTE: never add authenticated. user may download it by 2-dimensionn code.
    #@authenticated
    @tornado.web.removeslash
    def get(self):
        #"""Download apk for android."""
        #status = ErrorCode.SUCCESS
        #logging.info("Androdid client download request.")
        ## TODO: here, just handle android
        #version_info = get_version_info('android')
        #category = self.get_argument('category', '2')
        #versionname = self.get_argument('versionname', version_info.versionname)
        #update_download_count(category, self.db)

        #url = "/static/download/ACB_"+versionname+".apk#mp.weixin.qq.com"
        #self.redirect(url)

        category = int(self.get_argument('category', 2))
        if category ==2: # ydws
            #version_info = get_version_info('android')
            download_info = get_download_count(category, self.db)
            version_info = QueryHelper.get_version_info_by_category(UWEB.APK_TYPE.YDWS, self.db)
            update_download_count(category, self.db)
            self.render('android_weixin.html',
                        versioncode=version_info.versioncode,
                        versionname=version_info.versionname,
                        versioninfo=version_info.versioninfo,
                        updatetime=version_info.updatetime,
                        filesize=version_info.filesize,
                        count=download_info.count)
        elif category == 3: # ydwq_monitor
            version_info = QueryHelper.get_version_info_by_category(UWEB.APK_TYPE.YDWQ_MONITOR, self.db)
            url = "/static/apk/"+version_info['filename']
            self.redirect(url)
        elif category == 4: # ydwq_monitored
            version_info = QueryHelper.get_version_info_by_category(UWEB.APK_TYPE.YDWQ_MONITORED, self.db)
            url = "/static/apk/"+version_info['filename']
            self.redirect(url)
        elif category == 5: # ydws_anjietong
            version_info = QueryHelper.get_version_info_by_category(UWEB.APK_TYPE.YDWS_ANJIETONG, self.db)
            url = "/static/apk/"+version_info['filename']
            self.redirect(url)

class DownloadTerminalHandler(BaseHandler):

    #@tornado.web.removeslash
    #def get(self):
    #    """
    #    Download script for terminal, and keep the info in T_SCRIPT_DOWNLOAD.
    #    """
    #    status = ErrorCode.SUCCESS
    #    versionname = self.get_argument('v', '')
    #    tid  = self.get_argument('sn', '')
    #    version = self.db.get("SELECT filename FROM T_SCRIPT"
    #                           " WHERE version = %s", versionname)
    #    if not version:
    #        logging.info("[UWEB] versionname: %s is not found, please check it again.", versionname)
    #        url = self.application.settings['terminal_path'] + 'dummy_file'
    #        self.redirect(url)
    #    else:
    #        filename = version['filename'] if version.get('filename', None) is not None else ''
    #        downloadtime = int(time.time())
    #        self.db.execute("INSERT INTO T_SCRIPT_DOWNLOAD(tid, versionname, timestamp)"
    #                        " VALUES(%s, %s, %s)",
    #                        tid, versionname, downloadtime)
    #        url = self.application.settings['terminal_path'] + filename
    #        logging.info("[UWEB] Terminal download path: %s", url)
    #        self.redirect(url)

    @tornado.web.removeslash
    @tornado.web.asynchronous
    def get(self):
        """
        Download script for terminal, and keep the info in T_SCRIPT_DOWNLOAD.
        """
        def _on_finish(db):
            self.db = db
            status = ErrorCode.SUCCESS
            versionname = self.get_argument('v', '')
            tid  = self.get_argument('sn', '')
            version = self.db.get("SELECT filename FROM T_SCRIPT"
                                   " WHERE version = %s", versionname)
            if not version:
                logging.info("[UWEB] Terminal %s versionname: %s is not found, please check it again.", 
                             tid, versionname)
                url = self.application.settings['terminal_path'] + 'dummy_file'
                self.redirect(url)
            else:
                filename = version['filename'] if version.get('filename', None) is not None else ''
                downloadtime = int(time.time())
                self.db.execute("INSERT INTO T_SCRIPT_DOWNLOAD(tid, versionname, timestamp)"
                                " VALUES(%s, %s, %s)",
                                tid, versionname, downloadtime)
                url = self.application.settings['terminal_path'] + filename
                logging.info("[UWEB] Terminal %s download path: %s", 
                             tid, url)
                self.redirect(url)
            return

        self.queue.put((10, _on_finish))

class UploadTerminalHandler(BaseHandler):

    @tornado.web.removeslash
    def get(self):
        """
        Show the upload page for eventer.
        """
        self.render("fileupload.html")

    @tornado.web.removeslash
    def post(self):
        """
        Upload the script for terminal, and keep the info in T_SCRIPT.
        """
        try:
            upload_file = self.request.files['fileUpload'][0]
        except Exception as e:
            logging.info("[UWEB] script upload failed, exception:%s", e.args)
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            self.write_ret(status)
            return

        try:
            status = ErrorCode.SUCCESS
            versionname = self.get_argument('versionname', '')
            filename = 'cloudhawk_'+versionname
            timestamp = int(time.time())
            self.db.execute("INSERT INTO T_SCRIPT(version, filename, timestamp)"
                            "  VALUES(%s, %s, %s)"
                            "    ON DUPLICATE KEY"
                            "    UPDATE version = VALUES(version),"
                            "           filename = VALUES(filename),"
                            "           timestamp = VALUES(timestamp)",
                            versionname, filename, timestamp)
            file_path = self.application.settings['server_path'] +\
                        self.application.settings['terminal_path'] + filename

            logging.info("[UWEB] Upload path: %s", file_path)
            output_file = open(file_path, 'w')
            output_file.write(upload_file['body'])
            output_file.close()
        except Exception as e:
            logging.info("Upload terminal file fail:%s", e.args)
            status = ErrorCode.FAILED
        else:
            logging.info("Upload file %s success!", filename)
        self.write_ret(status)


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

class DownloadManualHandler(BaseHandler):
    """Download different file throught param."""

    @tornado.web.removeslash
    def get(self):
        """Download manual."""
        category = self.get_argument('category', '1')
        filename = "ZJ100_移动卫士使用手册.pdf"
        if category == '1':
            filename = "ZJ100_移动卫士使用手册.pdf"
        elif category == '2':
            filename = "ZJ200_移动卫士使用手册.pdf"
        
        filepath = os.path.join(DOWNLOAD_DIR_, filename)
        instruction = open(filepath)
        self.set_header('Content-Type', 'application/force-download')
        self.set_header('Content-Disposition', 'attachment; filename=%s' % (filename,))
        self.write(instruction.read())
