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
from utils.myredis import MyRedis

def wash_location():
    db = DBConnection().db
    redis = MyRedis()
    
    sql = "select tmobile, from_unixtime(add_time) as add_time, from_unixtime(del_time) as del_time from T_BIND_LOG  where group_id in (239, 419)"
    sql_1 = "select tmobile, add_time, del_time from T_BIND_LOG  where op_type = 1 and tmobile = %s"
    sql_2 = "select tmobile, add_time, del_time from T_BIND_LOG  where op_type = 2 and tmobile = %s"
    #print 'sql', sql
    res  = db.query(sql)
    #print 'len ', len(terminals)
    for i, t in enumerate(res):
        tmobile = t.tmobile
        add = db.query(sql_1, tmobile)
        add_num = len(add)

        unbind = db.query(sql_2, tmobile)
        del_num = len(unbind)


        print del_num,  add_num,  t.del_time , t.add_time
        if del_num > add_num:
            print del_num,  add_num,  t.del_time , t.add_time,


def usage():
    print "Usage: python wash_location.py "

def main():
    ConfHelper.load('../conf/global.conf')
    parse_command_line()
    wash_location() 

if __name__ == "__main__": 
    main()
