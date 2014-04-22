#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import re
import time
import os
import random
import string
import xlrd

import tornado.web
from tornado.escape import json_decode, json_encode

from base import authenticated,BaseHandler
from helpers.queryhelper import QueryHelper
from codes.errorcode import ErrorCode
from utils.dotdict import DotDict
from utils.checker import check_zs_phone, ZS_PHONE_CHECKER

from checker import check_privileges
from constants import PRIVILEGES, UWEB

class WhitelistAJTHandler(BaseHandler):

    @authenticated
    @check_privileges([PRIVILEGES.WHITELIST])
    def get(self):
        """Jump to whitelist.html.
        """
        username = self.get_current_user()
        self.render('whitelist/whitelist_ajt.html',
                    username = username)
    @authenticated
    @check_privileges([PRIVILEGES.WHITELIST])
    @tornado.web.removeslash
    def post(self):
        """Add a whitelist.
        """
        status = ErrorCode.SUCCESS
        try:
            data = json_decode(self.request.body)
            mobile = data.get('mobile')
            ajt = QueryHelper.get_ajt_whitelist_by_mobile(mobile, self.db)
            if ajt:
                status = ErrorCode.AJT_ORDERED
                message = ErrorCode.ERROR_MESSAGE[status] % mobile
                self.write_ret(status, 
                               message=message)
            else:
                self.db.execute("INSERT INTO T_AJT_WHITELIST(mobile, timestamp)"
                                "  VALUES (%s, %s)"
                                "  ON DUPLICATE KEY"
                                "  UPDATE mobile = VALUES(mobile),"
                                "         timestamp = VALUES(timestamp)", 
                                mobile, int(time.time()))
                self.write_ret(status)
        except Exception as e:
            logging.exception("[ADMIN] Add whitelist failed. Terminal mobile: %s.", 
                              mobile)
            self.render('errors/error.html', 
                        message=ErrorCode.FAILED)

class WhitelistAJTSearchHandler(BaseHandler):
    
    @authenticated
    @check_privileges([PRIVILEGES.WHITELIST])
    @tornado.web.removeslash
    def post(self):   
        """Check whitelist whether exist.
        """
        status = ErrorCode.SUCCESS
        try:
            data = json_decode(self.request.body)
            mobile = data.get('mobile', '')
            ajt = QueryHelper.get_ajt_whitelist_by_mobile(mobile, self.db)
            if ajt:
                self.write_ret(status, 
                               dict_=DotDict(res=ajt)) 
            else:
                status = ErrorCode.AJT_NOT_ORDERED
                message = ErrorCode.ERROR_MESSAGE[status] % mobile
                self.write_ret(status=status, 
                               message=message)
        except Exception as e:
            logging.exception("[ADMIN] Search whitelist failed. Terminal mobile: %s, owner mobile: %s", 
                              mobile)
            self.render('errors/error.html',
                        message=ErrorCode.FAILED)

class WhitelistAJTBatchImportHandler(BaseHandler):
    """Batch add whitelist."""

    @authenticated
    @check_privileges([PRIVILEGES.WHITELIST])
    @tornado.web.removeslash
    def get(self):
        """Render to fileUpload.html 
        """
        self.render('whitelist/fileUpload_ajt.html',
                    status=None)

    @authenticated
    @check_privileges([PRIVILEGES.WHITELIST])
    @tornado.web.removeslash
    def post(self):
        """Read excel.
        """
        try:
            upload_file = self.request.files['upload_file'][0]
            logging.info("[UWEB] batch import.")
        except Exception as e:
            logging.info("[ADMIN] Invalid data format, Exception: %s",
                          e.args) 
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            self.write_ret(status)
            return

        try:
            status = ErrorCode.SUCCESS
            original_fname = upload_file['filename']
            extension = os.path.splitext(original_fname)[1]
            if extension not in ['.xlsx', '.xls']:
                status = ErrorCode.ILLEGAL_EXCEL_FILE
                self.write_ret(status)
                return

            # write into tmp file
            fname = ''.join(random.choice(string.ascii_lowercase + string.digits) for x in range(6))
            final_filename= fname + extension
            file_path = final_filename
            output_file = open(file_path, 'w')
            output_file.write(upload_file['body'])
            output_file.close()

            res = []
            # read from tmp file
            wb = xlrd.open_workbook(file_path)
            for sheet in wb.sheets():
                #NOTE: first line is title, and it should be ignored
                for j in range(1, sheet.nrows): 
                    row = sheet.row_values(j)
                    mobile = unicode(row[0])
                    mobile = mobile[0:11]

                    ajt = QueryHelper.get_ajt_whitelist_by_mobile(mobile, self.db)
                    if ajt:
                        status = ErrorCode.AJT_ORDERED
                    else:
                        pass
                    r = DotDict(mobile=mobile,
                                status=ErrorCode.SUCCESS)   
                    res.append(r)
            # remove tmp file
            #print 'res', res, type(res)
            #res = json_encode(res)
            #print 'res', res, type(res)
            os.remove(file_path)
            self.render("whitelist/fileUpload_ajt.html",
                        status=ErrorCode.SUCCESS,
                        res=res)
                  
        except Exception as e:
            logging.exception("[UWEB] batch import failed. Exception: %s",
                               e.args)
            status = ErrorCode.ILLEGAL_FILE
            self.render("whitelist/fileUpload_ajt.html",
                        status=status,
                        message=ErrorCode.ERROR_MESSAGE[status])

class WhitelistAJTBatchAddHandler(BaseHandler):
    """Batch add whitelist."""

    @authenticated
    @check_privileges([PRIVILEGES.WHITELIST])
    @tornado.web.removeslash
    def post(self):
        try:
            data = DotDict(json_decode(self.request.body))
            mobiles = list(data.mobiles)
            logging.info("[UWEB] batch add: %s", data)
        except Exception as e:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            self.write_ret(status)
            return

        try:
            status = ErrorCode.SUCCESS
            res = []
            for mobile in mobiles:
                self.db.execute("INSERT INTO T_AJT_WHITELIST(mobile, timestamp)"
                                "  VALUES (%s, %s)"
                                "  ON DUPLICATE KEY"
                                "  UPDATE mobile = VALUES(mobile),"
                                "         timestamp = VALUES(timestamp)", 
                                mobile, int(time.time()))

                r = DotDict(mobile=mobile,
                            status=ErrorCode.SUCCESS)

                res.append(r)
            self.write_ret(status, 
                           dict_=DotDict(res=res))
        except Exception as e:
            logging.exception("[UWEB] batch jh failed. Exception: %s",
                              e.args)
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)
