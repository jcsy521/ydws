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
    ws = wt.add_sheet(u'jia') 

    wb = xlrd.open_workbook(file_path)
    sheet = wb.sheets()[0]
    lst = ""
    num = 0
    #for i in range(1,sheet.nrows):
    for i in range(0,sheet.nrows):
        row = sheet.row_values(i)
        print 'roe', row
        #mobile = unicode(row[0])[0:-2]
        mobile = unicode(row[0])[0:11] # is recommend
        print 'mobile', mobile

        t = db.get("select id, mobile, login, tid, owner_mobile, from_unixtime(begintime) as begin_time,"
                   " from_unixtime(login_time) as login_time, domain from T_TERMINAL_INFO where mobile = %s and service_status=1", 
                   mobile)
    
        print 't', t
        if not t:
            label= u'未激活'
            b = db.query('select * from T_BIND_LOG where tmobile=%s', mobile)
            if b:
                label= u'已解绑'
            umobile=''
            print 'not: ', mobile
        else:
            label = u'已激活'
            print 't: ', t
            umobile=t.owner_mobile
            num += 1
        print 'label', label
        ws.write(i,0,mobile)
        ws.write(i,1,umobile)

        if label == u'未激活':
            ws.write(i,2,label, offline_style)
        else:
            ws.write(i,2,label, online_style)

        if t:
            begin_time = t.begin_time
            login_time = t.login_time
            #reg_time = time.strftime('%Y-%m-%d-%H:%M:%S',time.localtime(t.begintime))
            begintime = str(begin_time.year)+'-'+str(begin_time.month)+'-' +str(begin_time.day) +'-'+str(begin_time.hour)+':'+str(begin_time.minute)+':'+str(begin_time.second)
            logintime = str(login_time.year)+'-'+str(login_time.month)+'-'+ str(login_time.day) +'-'+str(login_time.hour)+':'+str(login_time.minute)+':'+str(login_time.second)

            ws.write(i,3,begintime)
            ws.write(i,4,logintime)
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
    wt.save('/tmp/jia_new.xls')

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
