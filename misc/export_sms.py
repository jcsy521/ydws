# -*- coding: utf-8 -*-

import sys
import time

import os.path
import site
TOP_DIR_ = os.path.abspath(os.path.join(__file__, "../.."))
site.addsitedir(os.path.join(TOP_DIR_, "libs"))
import logging

from tornado.options import define, options, parse_command_line

import xlrd 
import xlwt 

from helpers.confhelper import ConfHelper
from helpers.smshelper import SMSHelper
from utils.checker import check_phone
from db_.mysql import DBConnection

def export_sms():
    db = DBConnection().db
    online_style = xlwt.easyxf('font: colour_index green, bold off; align: wrap on, vert centre, horiz center;')
    offline_style = xlwt.easyxf('font: colour_index brown, bold off; align: wrap on, vert centre, horiz center;')

    wt = xlwt.Workbook()   
    ws = wt.add_sheet(u'jia') 
    
    sql = "select insert_time, mobile, content from T_SMS where insert_time > 1393603200000 limit 5000" 
    #sql = "select insert_time, mobile, content from T_SMS where insert_time between  1391184000000 and 1393603200000 limit 5000" 
    #sql = "select insert_time, mobile, content from T_SMS where insert_time > 1388505600000 limit 5000" 

    #sql = "select insert_time, mobile, content from T_SMS where insert_time > 1388505600000" 
    #sql = "select insert_time, mobile, content from T_SMS where content like '%%激活成功%%' " 
    print 'sql', sql
    sms  = db.query(sql)
    print 'len ', len(sms)
    for i, s in enumerate(sms):
        #print 's', s
        reg_time = time.strftime('%Y-%m-%d-%H:%M:%S',time.localtime(s.insert_time/1000))
        ws.write(i,0,str(s.mobile))
        ws.write(i,1,reg_time)
        ws.write(i,2,s.content)
    wt.save('./sms_3.xls')

def usage():
    print "Usage: python handle_excel.py --excel=file_path"

def main():
    ConfHelper.load('../conf/global.conf')
    parse_command_line()
    export_sms() 

if __name__ == "__main__": 
    main()
