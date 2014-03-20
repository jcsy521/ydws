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
    
    #sql = 'select id, mobile, owner_mobile, begintime from T_TERMINAL'
    #sql = 'select id, mobile, owner_mobile, begintime from T_TERMINAL_INFO limit 5'
    #sql = 'select id, mobile, owner_mobile, begintime from T_TERMINAL_INFO  where service_status=1'
    #sql = "select id, mobile, owner_mobile, begintime from T_TERMINAL_INFO  where service_status=1 and mobile like '%%%%14778%%%%' "
    #sql = "select id, mobile, owner_mobile, begintime from T_TERMINAL_INFO  where group_id = 310 "
    sql = "select tid, mobile from V_TERMINAL where cid = '13823936111'"
    terminals  = db.query(sql)
    print 'len ', len(terminals)
    for i, t in enumerate(terminals):
        terminal = db.get("select owner_mobile from T_TERMINAL_INFO where tid = %s", t.tid)
        car= db.get("select cnum from T_CAR where tid = %s", t.tid)
          
        print 't', t
        print 'ter', terminal 
        print 'car', car 
        #reg_time = time.strftime('%Y-%m-%d-%H:%M:%S',time.localtime(t.begintime))
        ws.write(i,0,terminal.owner_mobile)
        ws.write(i,1,t.mobile)
        ws.write(i,2,car.cnum)
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
    wt.save('/tmp/jia_13823936111_corp.xls')

def usage():
    print "Usage: python handle_excel.py --excel=file_path"

def main():
    ConfHelper.load('../conf/global.conf')
    parse_command_line()
    export_excel() 

if __name__ == "__main__": 
    main()
