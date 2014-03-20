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
import xlwt 

from helpers.confhelper import ConfHelper
from helpers.smshelper import SMSHelper
from utils.checker import check_phone
from db_.mysql import DBConnection

def statistic():
    db = DBConnection().db
    sql = 'select from_unixtime(timestamp), terminal_online, terminal_offline from T_STATISTIC where type=2 and  timestamp between  1378051140  and 1380556741'

    t = db.query(sql)
    sum_on = 0
    sum_off = 0
    for i in t:  
        print 'i', i
        on = i.terminal_online
        off = i.terminal_offline
        sum_on += on
        sum_off += off 
    print 'sum_on: %s, sum_off: %s, sum: %s' % (sum_on, sum_off, sum_on+sum_off)


def usage():
    print "Usage: python handle_excel.py --excel=file_path"

def main():
    ConfHelper.load('../conf/global.conf')
    parse_command_line()
    statistic() 

    #if not 'excel' in options:
    #    usage()
    #    exit(1)

    #fname = options.excel
    #extension = os.path.splitext(fname)[1]
    #if extension not in ['.xlsx', '.xls']:
    #    print 'ivalid excel file.........'
    #else:
    #    batch_import(fname) 

if __name__ == "__main__": 
    main()
