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
    
    sql = "select id, tid,  mobile, owner_mobile, begintime from T_TERMINAL_INFO "
    #print 'sql', sql
    terminals  = db.query(sql)
    #print 'len ', len(terminals)
    for i, t in enumerate(terminals):
        tid = t.tid
        key = 'location:%s' % tid
        location = redis.get(key) 
        if location:
            print 'key', key
            print 'location', location

def usage():
    print "Usage: python wash_location.py "

def main():
    ConfHelper.load('../conf/global.conf')
    parse_command_line()
    wash_location() 

if __name__ == "__main__": 
    main()
