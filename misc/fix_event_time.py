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

from utils.dotdict import DotDict
from helpers.confhelper import ConfHelper
from helpers.smshelper import SMSHelper
from utils.checker import check_phone
from db_.mysql import DBConnection
from utils.myredis import MyRedis

def wash_location():
    db = DBConnection().db
    redis = MyRedis()
    
    sql = 'select id,  timestamp, lid from  T_EVENT where timestamp = 0 order by id desc limit 1000'
    #sql = 'select id,  timestamp, lid from  T_EVENT where timestamp = 0 limit 4'
    l_sql = 'select *, from_unixtime(timestamp) from T_LOCATION where id = %s '
    print 'sql', sql
    events = db.query(sql)
    #print 'len ', len(terminals)
    count = 0
    cnt = 0
    for i, t in enumerate(events):
        count += 1
        lid = t.lid
        eid = t.id
        location = db.get(l_sql, lid) 
        if not location:
            print 'no location', eid, lid
        else:
            cnt += 1
            timestamp = location.timestamp
            if timestamp:
                db.execute("update T_EVENT set timestamp = %s where id = %s",
                           timestamp, eid)
                print '-----', timestamp, eid, lid

    print 'total count:', count
    print 'total hanlded count:', cnt

def usage():
    print "Usage: python wash_location.py "

def main():
    ConfHelper.load('../conf/global.conf')
    parse_command_line()
    wash_location() 

if __name__ == "__main__": 
    main()
