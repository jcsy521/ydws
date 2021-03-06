# -*- coding: utf-8 -*-

import os
DOWNLOAD_DIR_ = os.path.abspath(os.path.join(__file__, "../../static/terminal"))
MESSAGE = None

import logging
import time

import tornado.web
from tornado.escape import json_decode

from codes.errorcode import ErrorCode
from base import BaseHandler, authenticated
from utils.misc import safe_utf8
from utils.checker import check_filename


class DeleteLuaHandler(BaseHandler):

    @authenticated
    @tornado.web.removeslash
    def get(self):

        username = self.get_current_user()
        delete_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
        filename = self.get_argument('filename')
        filepath = os.path.join(DOWNLOAD_DIR_, filename)

        if os.path.isfile(filepath):
            os.remove(filepath)
        else:
            logging.warn("[LOG] filename: %s can not be found in platform.", 
                         filename)

        self.acbdb.execute("DELETE FROM T_SCRIPT"
                           "  WHERE filename = %s",
                           filename)
        self.redirect("/uploadluascript")
        logging.info("[LOG] %s delete the %s file at the time of : %s ", 
                     username, filename, delete_time)


class DownloadLuaHandler(BaseHandler):

    @authenticated
    @tornado.web.removeslash
    def get(self):

        filename = self.get_argument('filename')
        filepath = os.path.join(DOWNLOAD_DIR_, filename)
        instruction = open(filepath)
        self.set_header('Content-Type', 'application/force-download')
        self.set_header('Content-Disposition', 'attachment; filename=%s' % (filename,))
        self.write(instruction.read())
        logging.info("[LOG] Download terminal file success :%s", 
                     filename)


class UploadLuaHandler(BaseHandler):

    @authenticated
    @tornado.web.removeslash
    def get(self):
        username = self.get_current_user()
        n_role = self.db.get("SELECT role "
                             "  FROM T_LOG_ADMIN"
                             "  WHERE name = %s", 
                             username)
        lst = []
        records = self.acbdb.query("SELECT *"
                                   "  FROM T_SCRIPT "
                                   "  ORDER BY id DESC")
        for record in records:
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(record.timestamp))
            author = record.author
            filename = record.filename
            version = record.version
            islocked = record.islocked
            id = record.id
            p = {'timestamp': timestamp,
                 'author': author,
                 'filename': filename,
                 'version': version,
                 'islocked': islocked,
                 'id': id,
                 }
            lst.append(p)
        self.render("fileupload/fileupload.html",
                    username=username,
                    role=n_role.role,
                    files=lst,
                    message=MESSAGE)
        global MESSAGE
        MESSAGE = None

    @authenticated
    @tornado.web.removeslash
    def put(self):
        status = ErrorCode.SUCCESS
        try:
            data = json_decode(self.request.body)
            logging.info("data: %s", data)
            id = data.get("id", -1)
            islocked = data.get("islocked", 0)
        except Exception as e:
            logging.info("[LOG] islocked illegal data format. Exception: %s", 
                         e.args)
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            self.write_ret(status)

        try:
            self.acbdb.execute("UPDATE T_SCRIPT"
                               " SET islocked = %s WHERE id = %s", 
                               islocked, id)
            self.write_ret(status)
        except Exception as e:
            logging.exception("[LOG] set islocked failed. Exception: %s", 
                              e.args)
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)

    @authenticated
    @tornado.web.removeslash
    def post(self):

        try:
            upload_file = self.request.files['fileupload'][0]
        except Exception as e:
            logging.info("[LOG] Script upload failed, exception:%s", 
                         e.args)
            global MESSAGE
            MESSAGE = '获取不到文件'
            self.redirect("/uploadluascript")
            return

        try:
            author = self.get_current_user()

            # check version
            records = self.acbdb.query("SELECT * "
                                       "  FROM T_SCRIPT"
                                       "  ORDER BY id DESC")
            version_list = [record.version for record in records]
            versionname = self.get_argument('versionname', '')
            if versionname in version_list:
                global MESSAGE
                MESSAGE = '该版本号已存在'
                logging.info("[LOG] Message: %s", MESSAGE)
                self.redirect("/uploadluascript")
                return

            # check filename whether contains illegal character
            filename = safe_utf8(upload_file['filename'])
            if not check_filename(filename):
                global MESSAGE
                MESSAGE = '文件名只能包含字母、数字、下划线、点'
                logging.info("[LOG] Message: %s", MESSAGE)
                self.redirect("/uploadluascript")
                return

            # check filename whether exists
            timestamp = int(time.time())
            localtime = time.strftime(
                '%Y-%m-%d %H:%M:%S', time.localtime(timestamp))
            files = os.listdir(DOWNLOAD_DIR_)
            for file in files:
                if file == filename:
                    global MESSAGE
                    MESSAGE = '文件已经存在，请先删除'
                    self.redirect("/uploadluascript")
                    return

            self.acbdb.execute("INSERT INTO T_SCRIPT(version, filename, timestamp, author)"
                               "VALUES(%s, %s, %s, %s)",
                               versionname, filename, timestamp, author)
            file_path = os.path.join(DOWNLOAD_DIR_, filename)
            logging.info("[LOG] Upload path: %s", file_path)
            output_file = open(file_path, 'w')
            output_file.write(upload_file['body'])
            output_file.close()

        except Exception as e:
            logging.info("[LOG] %s upload %s file fail at the time of %s Exception:%s", 
                         author, filename, localtime, e.args)
        else:
            logging.info("[LOG] %s upload %s file success at the time of %s", 
                         author, filename, localtime)
        self.redirect("/uploadluascript")
