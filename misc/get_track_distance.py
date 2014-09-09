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
from utils.public import get_terminal_type_by_tid 
from utils.misc import get_terminal_sessionID_key
from db_.mysql import DBConnection
from utils.myredis import MyRedis
from helpers.lbmphelper import get_distance
from constants import UWEB

def block_test():
    db = DBConnection().db
    redis = MyRedis()

    #start_time = int(time.mktime(time.strptime("%s-%s-%s-%s-%s-%s"%(2014,8,26,0,0,0),"%Y-%m-%d-%H-%M-%S")))
    #end_time = int(time.mktime(time.strptime("%s-%s-%s-%s-%s-%s"%(2014,8,27,18,0,0),"%Y-%m-%d-%H-%M-%S")))
    #print time.localtime(start_time)
    #print time.localtime(end_time)

    tid = '3922400068'
    
        
    start_time = 1409222189 
    end_time = 1409223445
    track = db.query("SELECT id, latitude, longitude, clatitude,"
                     "       clongitude, timestamp, name, type, speed, degree, locate_error"
                     "  FROM T_LOCATION"
                     "  WHERE tid = %s"
                     "    AND category = 1"
                     "    AND NOT (latitude = 0 OR longitude = 0)"
                     "    AND (timestamp BETWEEN %s AND %s)"
                     "    AND type = 0"
                     "    GROUP BY timestamp"
                     "    ORDER BY timestamp",
                     tid, start_time, end_time)

    distance = 0
    start_point = None
    for point in track:
        if not start_point: 
            start_point = point
            continue
        else:
            distance += get_distance(start_point["longitude"], start_point["latitude"], 
                                     point["longitude"], point["latitude"])
            start_point = point

    print '---distance',  distance,  tid, start_time, end_time


def usage():
    print "Usage: python milege.py"

def main():
    ConfHelper.load('../conf/global.conf')
    parse_command_line()

    block_test() 

if __name__ == "__main__": 
    main()
