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

def sms_corp():
    db = DBConnection().db
    
    #sql = 'select id, mobile, owner_mobile, begintime from T_TERMINAL'
    #sql = 'select id, mobile, owner_mobile, begintime from T_TERMINAL_INFO limit 5'
    #sql = 'select id, mobile, owner_mobile, begintime from T_TERMINAL_INFO  where service_status=1'
    #sql = "select id, mobile, owner_mobile, begintime from T_TERMINAL_INFO  where service_status=1 and mobile like '%%%%14778%%%%' "
    #sql = "select id, mobile, owner_mobile, begintime from T_TERMINAL_INFO  where group_id = 310 "

    sql = "select tid, mobile from V_TERMINAL where cid = %s"
    #cid = '15913418063' # huoju
    cid = '13726103889' #zhonghe 
    terminals = db.query(sql, cid)
    print 'len ', len(terminals)
    for i, t in enumerate(terminals):
        tid = t.tid
        mobile = t.mobile 
        terminal = db.get("select trace_para, owner_mobile, mobile from T_TERMINAL_INFO where tid = %s", t.tid)
        print 'ter', terminal 
        #db.execute("update T_TERMINAL_INFO set trace_para = '300:10' where tid = %s", t.tid)
        db.execute("update T_TERMINAL_INFO set trace_para = '0:1' where tid = %s", t.tid)
        SMSHelper.send_to_terminal(mobile, ':CQ')


def usage():
    print "Usage: python handle_excel.py --excel=file_path"

def main():
    ConfHelper.load('../conf/global.conf')
    parse_command_line()
    sms_corp() 

if __name__ == "__main__": 
    main()
