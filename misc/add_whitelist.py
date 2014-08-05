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

def add_whitelist():
    db = DBConnection().db
    begin = 20000000000
    num = 100
    for mobile  in xrange(begin, begin+num+1):
        print 'mobile', mobile
        db.execute("INSERT INTO T_BIZ_WHITELIST(id, mobile)"
                   "  VALUES(NULL, %s)"
                   "  ON DUPLICATE KEY"
                   "  UPDATE mobile = values(mobile)", mobile)

def usage():
    print "Usage: python import_whitelist.py --excel=file_path"

def main():
    ConfHelper.load('../conf/global.conf')
    parse_command_line()
    add_whitelist()

if __name__ == "__main__": 
    main()
