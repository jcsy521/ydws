# -*- coding: utf-8 -*-

import os
import datetime, time
APK_DIR_ = os.path.abspath(os.path.join(__file__, "../../static/apk"))
import logging

import tornado.web

from utils.dotdict import DotDict
from codes.errorcode import ErrorCode 
from utils.misc import safe_utf8, str_to_list, DUMMY_IDS
from utils.checker import check_filename 

from constants import UWEB

from base import BaseHandler, authenticated

class ApkHandler(BaseHandler):

    @authenticated
    @tornado.web.removeslash
    def get(self):
        self.render('apk/apkManage.html',
                    status=ErrorCode.SUCCESS,
                    message='')

    @authenticated
    @tornado.web.removeslash
    def post(self):
        try:
            author = self.get_argument('author', '')
            versioncode = self.get_argument('versioncode', '')
            versionname = self.get_argument('versionname', '')
            versioninfo = self.get_argument('versioninfo', '')
            updatetime = self.get_argument('updatetime', '')
            category = int(self.get_argument('category', ''))
            filesize = self.get_argument('filesize', '')
            upload_file = self.request.files['fileupload'][0]
            filename = safe_utf8(upload_file['filename'])
        except Exception as e:
            logging.info("[ADMIN] Apk upload failed, exception:%s", e.args)
            status = ErrorCode.FAILED 
            self.write_ret(status) 
            return

        try:
            status = ErrorCode.SUCCESS 
            if not check_filename(filename):
                status = ErrorCode.ACTIVITY_NAME_ILLEGAL
                self.write_ret(status) 
                logging.info("[ADMIN] filename: %s, Message: %s", 
                             filename, ErrorCode.ERROR_MESSAGE[status])
                return

            if category == UWEB.APK_TYPE.YDWS: # 1
                filename_ = 'ACB_%s.apk' 
            elif category == UWEB.APK_TYPE.YDWQ_MONITOR: # 2
                filename_ = 'YDWQ_monitor_%s.apk' 
            elif category == UWEB.APK_TYPE.YDWQ_MONITORED: # 3
                filename_ = 'YDWQ_monitored_%s.apk' 
            elif category == UWEB.APK_TYPE.YDWS_ANJIETONG: # 4
                filename_ = 'YDWS_anjietong_%s.apk' 

            filename = filename_ % versionname

            self.db.execute("INSERT INTO T_APK(versioncode, versionname, versioninfo,"
                            "  updatetime, filesize, author, category, filename) "
                            "  VALUES(%s, %s, %s, %s, %s, %s, %s, %s)",
                            versioncode, versionname, versioninfo, updatetime, 
                            filesize, author, category, filename)

            file_path = os.path.join(APK_DIR_, filename)
            logging.info("[ADMIN] Upload path: %s", file_path)
            output_file = open(file_path, 'w')
            output_file.write(upload_file['body'])
            output_file.close()
            logging.info("[ADMIN] %s upload %s file success.", author, filename)
            self.write_ret(status) 
        except Exception as e:
            status = ErrorCode.SERVER_BUSY
            logging.exception("[ADMIN] %s upload %s file failed. Exception:%s", 
                              author, filename, e.args)
            self.write_ret(status) 

    @authenticated
    @tornado.web.removeslash
    def delete(self):
        """Delete activity.  
        """
        try: 
            delete_ids = map(int, str_to_list(self.get_argument('ids', None))) 
            logging.info("[ADMIN] delete apk: %s", 
                         delete_ids)
        except Exception as e: 
            status = ErrorCode.ILLEGAL_DATA_FORMAT 
            logging.exception("[ADMIN] data format illegal. Exception: %s", 
                               e.args) 
            self.write_ret(status)
            return

        try:
            status = ErrorCode.SUCCESS
            self.db.execute("DELETE FROM T_APK WHERE id IN %s",
                            tuple(delete_ids + DUMMY_IDS))
            self.write_ret(status)
        except Exception as e: 
            status = ErrorCode.SERVER_BUSY
            logging.exception("[ADMIN] delete apk failed. Exception: %s", 
                              e.args) 
            self.write_ret(status)

class ApkListHandler(BaseHandler):

    @authenticated
    @tornado.web.removeslash
    def post(self):
        status = ErrorCode.SUCCESS
        try:
            res = self.db.query("SELECT id, versioncode, versionname, versioninfo,"
                                "  updatetime, filesize, author, category" 
                                "  FROM T_APK ORDER BY updatetime ")
            self.write_ret(status=status, 
                           dict_=DotDict(res=res))
        except Exception as e:
            logging.exception("[ADMIN] Get apk list failed.")
            status = ErrorCode.SUCCESS
            self.write_ret(status=status) 
