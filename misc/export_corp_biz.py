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

def export_excel():
    db = DBConnection().db
    online_style = xlwt.easyxf('font: colour_index green, bold off; align: wrap on, vert centre, horiz center;')
    offline_style = xlwt.easyxf('font: colour_index brown, bold off; align: wrap on, vert centre, horiz center;')

    wt = xlwt.Workbook()   
    ws = wt.add_sheet(u'jia') 
    
    sql = "select id, mobile, owner_mobile, begintime from T_TERMINAL_INFO  where service_status=1 and begintime<1396281600 order by begintime "
    terminals  = db.query(sql)

    print 'len ', len(terminals)
    for i, t in enumerate(terminals):
        #terminal = db.get("select owner_mobile from T_TERMINAL_INFO where tid = %s", t.tid)
        #car= db.get("select cnum from T_CAR where tid = %s", t.tid)

        biz= db.get("select biz_type from T_BIZ_WHITELIST where mobile = %s limit 1", t.mobile)
        biz_type = 10
        if biz:
            if biz['biz_type'] == 1:
                biz_type = 20
         
        print 't', t
        reg_time = time.strftime('%Y-%m-%d-%H:%M:%S',time.localtime(t.begintime))
        #reg_time = time.strftime('%Y-%m-%d-%H:%M:%S',time.localtime(t.begintime))
        ws.write(i,0,t.owner_mobile)
        ws.write(i,1,t.mobile)
        ws.write(i,2,reg_time)
        ws.write(i,3,biz_type)
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
    wt.save('/tmp/jia_biz_type.xls')

def usage():
    print "Usage: python handle_excel.py --excel=file_path"

def main():
    ConfHelper.load('../conf/global.conf')
    parse_command_line()
    export_excel() 

if __name__ == "__main__": 
    main()
