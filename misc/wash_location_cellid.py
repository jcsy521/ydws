# -*- coding: utf-8 -*-

import sys
import time

import os.path
import site
TOP_DIR_ = os.path.abspath(os.path.join(__file__, "../.."))
site.addsitedir(os.path.join(TOP_DIR_, "libs"))
import logging

from tornado.options import define, options, parse_command_line

from utils.dotdict import DotDict
from helpers.confhelper import ConfHelper
from utils.checker import check_phone
from db_.mysql import DBConnection
from utils.myredis import MyRedis

def wash_location():
    db = DBConnection().db
    redis = MyRedis()
    
    sql = "select id, tid,  mobile, owner_mobile, begintime, login_time from T_TERMINAL_INFO "
    #print 'sql', sql
    terminals = db.query(sql)
    #print 'len ', len(terminals)
    count = 0
    cnt = 0
    for i, t in enumerate(terminals):
        tid = t.tid
        key = 'location:%s' % tid
        location = redis.getvalue(key) 
        #print 'location', location, type(location) 
        if location and int(location.locate_error) > 500: 
            print '------1 tid', tid, location
            location['locate_error'] = 500
            print '------2 tid', tid, location
            #mem_location = DotDict({'id':location.id,
            #                        'latitude':location.latitude,
            #                        'longitude':location.longitude,
            #                        'type':location.type,
            #                        'clatitude':location.clatitude,
            #                        'clongitude':location.clongitude,
            #                        'timestamp':location.timestamp,
            #                        'name':location.name,
            #                        'degree':float(location.degree),
            #                        'speed':float(location.speed),
            #                        'locate_error':location['locate_error']})

            #redis.setvalue(key, mem_location, 86400*356*2)
            count = count +1 
            print 'handled tid:', tid
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
