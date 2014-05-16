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

def main():
    ConfHelper.load('../conf/global.conf')
    parse_command_line()

    test_redis() 

if __name__ == "__main__": 
    main()
