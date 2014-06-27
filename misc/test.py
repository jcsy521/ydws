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

    
def usage():
    print "Usage: python wash_location.py "

def main():
    ConfHelper.load('../conf/global.conf')
    parse_command_line()
    get_location() 

if __name__ == "__main__": 
    main()
