# -*- coding: utf-8 -*-

import sys

import os.path
import site
TOP_DIR_ = os.path.abspath(os.path.join(__file__, "../.."))
site.addsitedir(os.path.join(TOP_DIR_, "libs"))
import logging

from tornado.options import define, options, parse_command_line
define('excel', default="")

import xlrd

from helpers.confhelper import ConfHelper
from helpers.smshelper import SMSHelper
from utils.checker import check_phone
from db_.mysql import DBConnection

def batch_import(file_path):
    db = DBConnection()
    wb = xlrd.open_workbook(file_path)
    sheet = wb.sheets()[0]
    for i in range(sheet.nrows):
        row = sheet.row_values(i)
        tmobile = unicode(row[0])
        tmobile = tmobile[:tmobile.find('.')]
        if not check_phone(tmobile):
            print 'invalid mobile: ', tmobile
            continue

        db.execute("INSERT INTO T_BIZ_WHITELIST(id, mobile)"
                   "  VALUES(NULL, %s)", tmobile)

def usage():
    print "Usage: python2.6 send_sms.py --excel=file_path"

def main():
    ConfHelper.load('../conf/global.conf')
    parse_command_line()
    if not 'excel' in options:
        usage()
        exit(1)

    fname = options.excel
    extension = os.path.splitext(fname)[1]
    print 'extension=', extension
    if extension not in ['.xlsx', '.xls']:
        print 'ivalid excel file.........'
    else:
        batch_import(fname) 

if __name__ == "__main__": 
    main()
