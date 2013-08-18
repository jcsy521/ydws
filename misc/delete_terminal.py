# -*- coding: utf-8 -*-

import sys

import os.path
import site
TOP_DIR_ = os.path.abspath(os.path.join(__file__, "../.."))
site.addsitedir(os.path.join(TOP_DIR_, "libs"))
import logging

from tornado.options import define, options, parse_command_line
define('tid', default="")

from helpers.confhelper import ConfHelper
from helpers.smshelper import SMSHelper
from helpers.queryhelper import QueryHelper
from db_.mysql import DBConnection
from utils.myredis import MyRedis
from utils.public import delete_terminal
from utils.misc import *


def execute(mobile):
    db = DBConnection().db
    redis = MyRedis()
    terminal = db.get("SELECT tid, mobile FROM T_TERMINAL_INFO WHERE mobile = %s LIMIT 1", mobile)
    if terminal:
        delete_terminal(terminal.tid, db, redis, del_user=True)

def main():
    ConfHelper.load('../conf/global.conf')
    parse_command_line()
    if not options.mobile:
        usage()
        exit(1)
    execute(options.mobile)
    

def usage():
    print "Usage: python delete_terminal.py --mobile=15919176710"

if __name__ == "__main__": 
    main()
