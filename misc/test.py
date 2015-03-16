# -*- coding: utf-8 -*-

import sys
import time

import os.path
import site
TOP_DIR_ = os.path.abspath(os.path.join(__file__, "../.."))
site.addsitedir(os.path.join(TOP_DIR_, "libs"))
import logging

from tornado.options import define, options, parse_command_line

from helpers.confhelper import ConfHelper
from helpers.smshelper import SMSHelper
from helpers.queryhelper import QueryHelper
from utils.checker import check_phone
from db_.mysql import DBConnection
from utils.myredis import MyRedis


def get_location():
    db = DBConnection().db
    redis = MyRedis()

    tid = 'CBBJTEAM01'
    location = QueryHelper.get_location_info(tid, db, redis)
    print 'location', location

def test_distance():
    dis  = get_distance(113.2*3600000, 23.1*3600000, 114.6*3600000, 39.2*3600000)
    print 'dis', dis

def test_location(tid):
    key = 'location:%s' % tid
    dct = "{'name': u'\u5e7f\u4e1c\u7701\u73e0\u6d77\u5e02\u9999\u6d32\u533as111', 'degree': 77.599999999999994, 'timestamp': 1394098543L, 'longitude': 408848760L, 'locate_error': 200000000, 'clongitude': 408890642L, 'type': 0, 'latitude': 80550684L, 'clatitude': 80560235L, 'speed': 3.0, 'id': 413922L}" 
    redis.set(key, dct)
    return redis.getvalue(key)

if __name__ == '__main__':
    ConfHelper.load('../conf/global.conf')
    parse_command_line()
    get_location() 

if __name__ == "__main__": 
    main()
