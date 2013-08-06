# -*- coding: utf-8 -*-

import os
import sys
DOWNLOAD_DIR_ = os.path.abspath(os.path.join(__file__, "../../static/terminal"))
MESSAGE = None

import logging
import time

import tornado.web
from tornado.escape import json_encode, json_decode

from base import BaseHandler, authenticated
from utils.misc import safe_utf8

class DeleteLuaHandler(BaseHandler):

    @authenticated
    @tornado.web.removeslash
    def get(self):

        username = self.get_current_user()
        delete_time = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
        filename = self.get_argument('filename')
        filepath = os.path.join(DOWNLOAD_DIR_,filename)
        os.remove(filepath)
        self.acbdb.execute("DELETE FROM T_SCRIPT WHERE filename = %s",
                           filename)
        self.redirect("/uploadluascript")
        logging.info("[LOG] %s delete the %s file at the time of : %s ", username, filename, delete_time)

class DownloadLuaHandler(BaseHandler):

    @authenticated
    @tornado.web.removeslash
    def get(self):

        filename = self.get_argument('filename')
        filepath = os.path.join(DOWNLOAD_DIR_,filename)
        instruction = open(filepath)
        self.set_header('Content-Type', 'application/force-download')
        self.set_header('Content-Disposition', 'attachment; filename=%s' % (filename,))
        self.write(instruction.read())
        logging.info("[LOG] Download terminal file success :%s", filename)

class UploadLuaHandler(BaseHandler):

    @authenticated
    @tornado.web.removeslash
    def get(self):

        username = self.get_current_user()
        n_role = self.db.get("SELECT role FROM T_LOG_ADMIN WHERE name = %s", username)
        lst = []
        records = self.acbdb.query("SELECT * FROM T_SCRIPT ORDER BY id DESC")
        for record in records:
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(record.timestamp))
            author = record.author
            filename = record.filename
            version = record.version
            p = {'timestamp':timestamp,
                 'author':author ,
                 'filename':filename,
                 'version':version
                 }
            lst.append(p)
        self.render("fileupload/fileupload.html",
                     username=username,
                     role=n_role.role,
                     files = lst,
                     message = MESSAGE)
        global MESSAGE
        MESSAGE = None

    @authenticated
    @tornado.web.removeslash
    def post(self):

        try:
            upload_file = self.request.files['fileupload'][0]
        except Exception as e:
            logging.info("[LOG] Script upload failed, exception:%s", e.args)
            global MESSAGE
            MESSAGE = '获取不到文件'
            self.redirect("/uploadluascript")
            return

        try:
            author = self.get_current_user()
            versionname = self.get_argument('versionname', '')
            filename = safe_utf8(upload_file['filename'])
            timestamp = int(time.time())
            localtime = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(timestamp))
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
            file_path = os.path.join(DOWNLOAD_DIR_,filename)
            logging.info("[LOG] Upload path: %s", file_path)
            output_file = open(file_path, 'w')
            output_file.write(upload_file['body'])
            output_file.close()

        except Exception as e:
            logging.info("[LOG] %s upload %s file fail at the time of %s Exception:%s", author, filename , localtime, e.args)
        else:
            logging.info("[LOG] %s upload %s file success at the time of %s", author, filename, localtime)
        self.redirect("/uploadluascript")
