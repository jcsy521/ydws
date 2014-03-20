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
from utils.misc import get_terminal_sessionID_key
from utils.myredis import MyRedis
from db_.mysql import DBConnection

def batch_import(file_path):
    db = DBConnection().db
    redis = MyRedis()

    online_style = xlwt.easyxf('font: colour_index green, bold off; align: wrap on, vert centre, horiz center;')
    offline_style = xlwt.easyxf('font: colour_index brown, bold off; align: wrap on, vert centre, horiz center;')

    wt = xlwt.Workbook()   
    ws = wt.add_sheet(u'jia') 

    wb = xlrd.open_workbook(file_path)
    sheet = wb.sheets()[0]
    lst = ""
    num = 0
    for i in range(0,sheet.nrows):
        row = sheet.row_values(i)
        print 'row', row
        mobile = unicode(row[0])
        mobile = mobile[0:11] 
        #mobile = unicode(row[0])[0:-2]
        print 'mobile', repr(mobile)

        sql_t = 'select tid, test, login, service_status from T_TERMINAL_INFO where mobile =' + mobile
        terminal = db.get(sql_t)
        print 'terminal', terminal
        tid = terminal.get('tid','') if terminal else ''
        sql = 'UPDATE T_TERMINAL_INFO set test=0 where mobile =' + mobile
        print 'sql', sql
        #db.execute('UPDATE T_TERMINAL_INFO set test=0 where mobile = %s', int(mobile))
        #db.execute(sql)
        sessionID_key = get_terminal_sessionID_key(tid)
        print 'sessionID_key', sessionID_key
        old_sessionid = redis.get(sessionID_key)
        if old_sessionid:
            redis.delete(sessionID_key)
            logging.info("[UWEB] Termianl %s delete session in redis.", tid)
        #if i == 3:
        #    break
    
    print num 

def usage():
    print "Usage: python handle_sos.py --excel=file_path"

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
