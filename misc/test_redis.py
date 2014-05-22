# -*- coding: utf-8 -*-

import sys

import os.path
import site
TOP_DIR_ = os.path.abspath(os.path.join(__file__, "../.."))
site.addsitedir(os.path.join(TOP_DIR_, "libs"))
import logging

from tornado.options import define, options, parse_command_line

from helpers.confhelper import ConfHelper
from utils.public import get_terminal_type_by_tid 
from utils.misc import get_terminal_sessionID_key
from db_.mysql import DBConnection
from utils.myredis import MyRedis

def test_redis():
    db = DBConnection().db
    redis = MyRedis()
    tid = 'T123SIMULATOR'
    sessionID_key = get_terminal_sessionID_key(tid)
    old_sessionid = redis.get(sessionID_key)
    print  'session_id: %s' % old_sessionid

def test_mileage():
    db = DBConnection().db
    redis = MyRedis()
    tid = 'CBBJTEAM01'
    #tid = '361A000066'
    mileage_key = 'mileage:%s'  % tid
    #mileage = redis.getvalue(mileage_key)

    # for hmy
    #mileage = dict(lat=80547804,
    #               lon=408846024,
    #               dis=530, 
    #               gps_time=1400733148)

    # for lp 
    mileage = dict(lat=144089748,
                   lon=418702032,
                   dis=561, 
                   gps_time=1400732859)
    print  'mileage: %s' % mileage 
    #mileage['dis'] = 530
    redis.setvalue(mileage_key, mileage)


def main():
    ConfHelper.load('../conf/global.conf')
    parse_command_line()

    test_mileage() 

if __name__ == "__main__": 
    main()
