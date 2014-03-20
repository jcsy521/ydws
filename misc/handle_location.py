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
    
    sql_tid = "select tid from V_TERMINAL where  cid = '13600335550' "
    sql_loc = "insert into T_LOCATION_jia select * from T_LOCATION where tid =%s order by timestamp desc limit 1 "
    terminals = db.query(sql_tid)
    #print 'len ', len(terminals)
    for i, t in enumerate(terminals):
        tid = t.tid
        db.execute(sql_loc, tid)

def usage():
    print "Usage: python wash_location.py "

def main():
    ConfHelper.load('../conf/global.conf')
    parse_command_line()
    wash_location() 

if __name__ == "__main__": 
    main()
