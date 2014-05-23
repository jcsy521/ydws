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

def batch_import(file_path):
    db = DBConnection().db
    online_style = xlwt.easyxf('font: colour_index green, bold off; align: wrap on, vert centre, horiz center;')
    offline_style = xlwt.easyxf('font: colour_index brown, bold off; align: wrap on, vert centre, horiz center;')

    wt = xlwt.Workbook()   
    ws = wt.add_sheet(u'polly') 

    wb = xlrd.open_workbook(file_path)
    sheet = wb.sheets()[0]
    lst = ""
    num = 0
    ws.write(0,0,u"终端号码")
    ws.write(0,1,u"绑定时间")
    #for i in range(1,sheet.nrows):
    for i in range(0,sheet.nrows):
        row = sheet.row_values(i)
        print 'roe', row
        #mobile = unicode(row[0])[0:-2]
        #mobile = unicode(row[0])[0:11] # is recommend
        mobile = int(row[0])
        print 'mobile', mobile

        sql = "SELECT tmobile,FROM_UNIXTIME(add_time) as add_time,FROM_UNIXTIME(del_time) as del_time from T_BIND_LOG where tmobile = '%s' HAVING MIN(FROM_UNIXTIME(add_time))" % mobile
       # print"sql:", sql
        t = db.get(sql)
        if not t:
            i = i+1
            print "ttttttttttttt:", t
        add_time = ''
        del_time = ''
        if t:   
            tmobile = t.tmobile
            add_time = t.add_time
            del_time = t.del_time
            add_time = str(add_time.year)+'-'+str(add_time.month)+'-' +str(add_time.day) +'-'+str(add_time.hour)+':'+str(add_time.minute)+':'+str(add_time.second)           
            del_time = str(del_time.year)+'-'+str(del_time.month)+'-' +str(del_time.day) +'-'+str(del_time.hour)+':'+str(del_time.minute)+':'+str(del_time.second)

        ws.write(i+1,0,mobile)
        ws.write(i+1,1,add_time)
        
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
    print "iiiiiiiiiiiiiiiii",i
    wt.save('/home/ydcws/polly_new.xls')

def usage():
    print "Usage: python handle_excel.py --excel=file_path"

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
