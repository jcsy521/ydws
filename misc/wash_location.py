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
    
    #sql = "select id, tid,  mobile, owner_mobile, begintime, login_time from T_TERMINAL_INFO where tid = '36E2400480' "
    sql = "select id, tid,  mobile, owner_mobile, begintime, login_time from T_TERMINAL_INFO"
    #sql = "select id, tid,  mobile, owner_mobile, begintime, login_time from T_TERMINAL_INFO where login = 0"
    #print 'sql', sql
    terminals  = db.query(sql)
    print 'len ', len(terminals)
    count = 0
    cnt = 0
    for i, t in enumerate(terminals):
        tid = t.tid
        key = 'location:%s' % tid
        location = redis.get(key) 
        if not location:
        #if True:
            print 'tid', tid

            location = db.get("SELECT timestamp, MAX(timestamp) as maxtime"
                              "  FROM T_LOCATION"
                              "  WHERE tid = %s"
                              "    AND type = 0"
                              "    AND latitude != 0",
                              tid)
            
            if location:
                if location.timestamp != location.maxtime:
                    print 'timestamp != maxtime, tid', tid
                    location = db.get("SELECT * FROM T_LOCATION where timestamp = %s AND tid = %s limit 1", location.maxtime, tid)
                else:
                    continue
                mem_location = DotDict({'id':location.id,
                                        'latitude':location.latitude,
                                        'longitude':location.longitude,
                                        'type':location.type,
                                        'clatitude':location.clatitude,
                                        'clongitude':location.clongitude,
                                        'timestamp':location.timestamp,
                                        'name':location.name,
                                        'degree':float(location.degree),
                                        'speed':float(location.speed),
                                        'locate_error':int(location.locate_error)})

                redis.setvalue(key, mem_location, 86400*356*2)
                count = count +1 
                print 'handled tid:', tid
            else:
                cnt = cnt + 1    
    print 'total hanlded count:', count
    print 'total not hanlded count:', cnt

def usage():
    print "Usage: python wash_location.py "

def main():
    ConfHelper.load('../conf/global.conf')
    parse_command_line()
    wash_location() 

if __name__ == "__main__": 
    main()
