# -*- coding: utf-8 -*-

import os
import datetime, time
ACTIVITY_DIR_ = os.path.abspath(os.path.join(__file__, "../../static/activity"))
import logging

import tornado.web

from utils.dotdict import DotDict
from codes.errorcode import ErrorCode 
from utils.misc import safe_utf8, str_to_list, DUMMY_IDS
from utils.checker import check_filename 

from base import BaseHandler, authenticated

class ActivityHandler(BaseHandler):

    @authenticated
    @tornado.web.removeslash
    def get(self):
        self.render('activity/activity.html',
                    status=ErrorCode.SUCCESS,
                    message='')

    @authenticated
    @tornado.web.removeslash
    def post(self):
        try:
            author = self.get_argument('author', '')
            title = self.get_argument('title', '')
            begintime = self.get_argument('begintime', 0)
            endtime = self.get_argument('endtime', 0)
            upload_file = self.request.files['fileupload'][0]
            filename = safe_utf8(upload_file['filename'])
        except Exception as e:
            logging.info("[ADMIN] Script upload failed, exception:%s", e.args)
            status = ErrorCode.FAILED 
            self.write_ret(status) 
            return

        try:
            status = ErrorCode.SUCCESS 
            # check filename whether contains illegal character
            if not check_filename(filename):
                status = ErrorCode.ACTIVITY_NAME_ILLEGAL
                self.write_ret(status) 
                logging.info("[ADMIN] filename: %s, Message: %s", 
                             filename, ErrorCode.ERROR_MESSAGE[status])
                return

            # check filename whether exists
            files = os.listdir(ACTIVITY_DIR_)
            for file in files:
                if file == filename:
                    status = ErrorCode.ACTIVITY_EXISTED
                    logging.info("[ADMIN] filename: %s, Message: %s", 
                                 filename, ErrorCode.ERROR_MESSAGE[status])
                    self.write_ret(status) 
                    return

            self.db.execute("INSERT INTO T_ACTIVITY(title, filename, begintime, endtime, author)"
                            "VALUES(%s, %s, %s, %s, %s)",
                            title, filename, begintime, endtime, author)
            file_path = os.path.join(ACTIVITY_DIR_, filename)
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
            logging.info("[ADMIN] delete activity: %s", 
                         delete_ids)
        except Exception as e: 
            status = ErrorCode.ILLEGAL_DATA_FORMAT 
            logging.exception("[ADMIN] data format illegal. Exception: %s", 
                               e.args) 
            self.write_ret(status)
            return

        try:
            self.db.execute("DELETE FROM T_ACTIVITY WHERE id IN %s",
                            tuple(delete_ids + DUMMY_IDS))
        except Exception as e: 
            status = ErrorCode.SERVER_BUSY
            logging.exception("[ADMIN] delete activity failed. Exception: %s", 
                              e.args) 
            self.write_ret(status)

class ActivityListHandler(BaseHandler):

    @authenticated
    @tornado.web.removeslash
    def post(self):
        status = ErrorCode.SUCCESS
        try:
            res = self.db.query("SELECT id, title, filename, begintime, endtime, author" 
                                "  FROM T_ACTIVITY ORDER BY begintime ")
            self.write_ret(status=status, 
                           dict_=DotDict(res=res))
        except Exception as e:
            logging.exception("[ADMIN] Get activity list failed.")
            status = ErrorCode.SUCCESS
            self.write_ret(status=status) 
