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

def add_timestamp():
    db = DBConnection().db
    redis = MyRedis()
    
    e_sql = 'select id, tid, timestamp, lid from T_EVENT where timestamp = 0 order by id desc  limit 3000000'
    #e_sql = 'select id, tid, timestamp, lid from T_EVENT where timestamp = 0 '
    #e_sql = 'select id, tid, timestamp, lid from T_EVENT where timestamp = 0 limit 1000000'
    l_sql = 'select id, tid, timestamp from T_LOCATION where id = %s'
    print 'e_sql', e_sql
    event = db.query(e_sql)
    print 'len ', len(event)
    for i, e in enumerate(event):
        if not (i % 10000):
            print 'now, it is ', i
            time.sleep(2)

        print '-----i: %s, e: %s' % (i, e)

        lid = e.lid
        eid = e.id
         
        location = db.get(l_sql, lid)
        if location:
            gps_time = location.get('timestamp', 0)  
            if gps_time:
                print 'update time', gps_time
                db.execute('UPDATE T_EVENT SET timestamp = %s WHERE id = %s',
                           gps_time, eid)
             
def usage():
    print "Usage: python wash_location.py "

def main():
    ConfHelper.load('../conf/global.conf')
    parse_command_line()
    add_timestamp() 

if __name__ == "__main__": 
    main()
