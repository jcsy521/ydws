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

"""
import whitelist 
"""

def batch_import(file_path):
    db = DBConnection().db
    wb = xlrd.open_workbook(file_path)
    sheet = wb.sheets()[0]
    lst = ""
    num = 0
    for i in range(sheet.nrows):
        row = sheet.row_values(i)
        mobile = unicode(row[0])
        mobile = mobile[0:11]
        t = db.get('select id, mobile, login, tid,owner_mobile,domain from T_TERMINAL_INFO where mobile = %s', mobile)
        if not t:
            num += 1
            print 'not: ', mobile
            db.execute("INSERT INTO T_BIZ_WHITELIST(id, mobile)"
                       "  VALUES(NULL, %s)"
                       "  ON DUPLICATE KEY"
                       "  UPDATE mobile = values(mobile)", mobile)
        else:
            print 't', t


        #lst += "'" + mobile + "',"
        #print 'select id, mobile, login, tid,owner_mobile,domain from T_TERMINAL_INFO where mobile = ' + mobile + ';'
        #db.execute("INSERT INTO T_BIZ_WHITELIST(id, mobile)"
        #           "  VALUES(NULL, %s)"
        #           "  ON DUPLICATE KEY"
        #           "  UPDATE mobile = values(mobile)", mobile)
        #content = ':SIM ' + umobile + ':' + mobile
        #print content
        #SMSHelper.send_to_terminal(mobile, content)
        #print '%s sucessfully.' % mobile
    print num 

def usage():
    print "Usage: python import_whitelist_pure.py --excel=file_path"

def main():
    ConfHelper.load('../conf/global.conf')
    parse_command_line()
    if not 'excel' in options:
        usage()
        exit(1)

    fname = options.excel
    extension = os.path.splitext(fname)[1]
    if extension not in ['.xlsx', '.xls']:
        print 'ivalid excel file.........'
    else:
        batch_import(fname) 

if __name__ == "__main__": 
    main()
