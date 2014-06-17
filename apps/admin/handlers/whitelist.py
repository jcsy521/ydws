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
from tornado.escape import json_decode

from base import authenticated,BaseHandler
from helpers.queryhelper import QueryHelper
from codes.errorcode import ErrorCode
from utils.dotdict import DotDict
from utils.checker import check_zs_phone, ZS_PHONE_CHECKER, check_phone

from checker import check_privileges
from constants import PRIVILEGES, UWEB

class WLSearchHandler(BaseHandler):

    @authenticated
    @check_privileges([PRIVILEGES.WHITELIST])
    def get(self):
        username = self.get_current_user()
        self.render('whitelist/whitelist.html',
                    username = username)

    @authenticated
    @check_privileges([PRIVILEGES.WHITELIST])
    @tornado.web.removeslash
    def post(self):   
        status = ErrorCode.SUCCESS
        try:
            data = json_decode(self.request.body)
            mobile = data.get('mobile')
            if check_zs_phone(mobile, self.db):
                biz_type = QueryHelper.get_biz_by_mobile(mobile, self.db)
                if biz_type:
                    biz_type = biz_type.get('biz_type')
                else:
                    r = re.compile(r"^(1477847\d{4})$")
                    if r.match(mobile):
                        biz_type = 1
                    else:
                        biz_type = 0
                whitelist = DotDict(mobile=mobile, biz_type=biz_type)
                self.write_ret(status, dict_=DotDict(whitelist=whitelist)) 
            else:
                status = ErrorCode.MOBILE_NOT_ORDERED
                message = ErrorCode.ERROR_MESSAGE[status] % mobile
                self.write_ret(status=status, message=message)
        except Exception as e:
            logging.exception("Search whitelist failed.Terminal mobile: %s, owner mobile: %s", mobile)
            self.render('errors/error.html',
                        message=ErrorCode.FAILED)

class AddWLHandler(BaseHandler):
    
    @authenticated
    @check_privileges([PRIVILEGES.WHITELIST])
    @tornado.web.removeslash
    def post(self):
        status = ErrorCode.SUCCESS
        try:
            data = json_decode(self.request.body)
            mobile = data.get('mobile')
            biz_type = data.get('biz_type')
            if check_zs_phone(mobile, self.db):
                status=ErrorCode.DATA_EXIST
                self.write_ret(status)
            else:
                self.db.execute("INSERT INTO T_BIZ_WHITELIST VALUES (NULL, %s, %s)", mobile, biz_type)
                self.write_ret(status)
        except Exception as e:
            logging.exception("Add whitelist failed.Terminal mobile: %s, owner mobile: %s", mobile)
            self.render('errors/error.html', message=ErrorCode.FAILED)

    @authenticated
    @check_privileges([PRIVILEGES.WHITELIST])
    @tornado.web.removeslash
    def put(self):
        status = ErrorCode.SUCCESS
        try:
            data = json_decode(self.request.body)
            mobile = data.get('mobile')
            biz_type = data.get('biz_type')
            if check_zs_phone(mobile, self.db):
                white_list = self.db.get("SELECT id FROM T_BIZ_WHITELIST where mobile = %s LIMIT 1", mobile)
                if white_list:
                    self.db.execute("UPDATE T_BIZ_WHITELIST SET biz_type= %s WHERE mobile= %s", biz_type, mobile)
                else:
                    self.db.execute("INSERT INTO T_BIZ_WHITELIST VALUES (NULL, %s, %s)", mobile, biz_type)
                self.write_ret(status)
            else:
                status = ErrorCode.MOBILE_NOT_ORDERED
                message = ErrorCode.ERROR_MESSAGE[status] % mobile 
                self.write_ret(status=status, 
                               message=message)
        except Exception as e:
            logging.exception("Edit whitelist failed.Terminal mobile: %s, owner mobile: %s", mobile)
            self.render('errors/error.html', message=ErrorCode.FAILED)

class WhitelistBatchImportHandler(BaseHandler):
    """Batch add whitelist."""

    @authenticated
    @check_privileges([PRIVILEGES.WHITELIST])
    @tornado.web.removeslash
    def get(self):
        """Render to fileUpload.html 
        """
        self.render('whitelist/fileUpload.html',
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

                    r = DotDict(mobile=mobile,
                                status=ErrorCode.SUCCESS)   

                    if not check_phone(mobile): 
                        r.status = UWEB.TERMINAL_STATUS.INVALID 
                        res.append(r) 
                        continue 

                    ajt = QueryHelper.get_ajt_whitelist_by_mobile(mobile, self.db)
                    if ajt:
                        r.status = UWEB.TERMINAL_STATUS.EXISTED
                    else:
                        pass
                    res.append(r)
            # remove tmp file
            os.remove(file_path)
            self.render("whitelist/fileUpload.html",
                        status=ErrorCode.SUCCESS,
                        res=res)
                  
        except Exception as e:
            logging.exception("[UWEB] Batch import failed. Exception: %s",
                               e.args)
            status = ErrorCode.ILLEGAL_FILE
            self.render("whitelist/fileUpload.html",
                        status=status,
                        message=ErrorCode.ERROR_MESSAGE[status])

class WhitelistBatchAddHandler(BaseHandler):
    """Batch add whitelist."""

    @authenticated
    @check_privileges([PRIVILEGES.WHITELIST])
    @tornado.web.removeslash
    def post(self):
        try:
            data = DotDict(json_decode(self.request.body))
            mobiles = list(data.mobiles)
            logging.info("[UWEB] Batch add whitelist: %s", data)
        except Exception as e:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            self.write_ret(status)
            return

        try:
            status = ErrorCode.SUCCESS
            res = []
            for mobile in mobiles:
                self.db.execute("INSERT INTO T_BIZ_WHITELIST(mobile)"
                                "  VALUES (%s)", 
                                mobile)

                r = DotDict(mobile=mobile,
                            status=ErrorCode.SUCCESS)

                res.append(r)
            self.write_ret(status, 
                           dict_=DotDict(res=res))
        except Exception as e:
            logging.exception("[UWEB] Batch add whitelist failed. Exception: %s",
                              e.args)
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)
