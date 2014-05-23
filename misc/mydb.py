# -*- coding: utf-8 -*-

import sys

import os.path
import site
TOP_DIR_ = os.path.abspath(os.path.join(__file__, "../.."))
site.addsitedir(os.path.join(TOP_DIR_, "libs"))
import logging

from tornado.options import define, options, parse_command_line

from helpers.confhelper import ConfHelper
from helpers.smshelper import SMSHelper
from db_.mysql import DBConnection
from utils.myredis import MyRedis
from utils.misc import get_terminal_info_key

def main():
    ConfHelper.load('../conf/global.conf')
    parse_command_line()
    db = DBConnection().db
    redis = MyRedis() 

    #tid = '35A60002B3'
    tid = '36E24006A6'
    location = db.get("SELECT id, speed, timestamp, category, name,"
                      "  degree, type, latitude, longitude, clatitude, clongitude,"
                      "  timestamp, locate_error"
                      "  FROM T_LOCATION"
                      "  WHERE tid = %s"
                      "    AND type = 0"
                      "    AND NOT (latitude = 0 AND longitude = 0)"
                      "    ORDER BY timestamp DESC"
                      "    LIMIT 1",
                      tid)
    print 'location:', location


if __name__ == "__main__": 
    main()
