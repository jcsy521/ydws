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
from helpers.queryhelper import QueryHelper
from db_.mysql import DBConnection
from utils.myredis import MyRedis
from utils.public import delete_terminal
from utils.misc import *


def execute():
    db = DBConnection().db
    redis = MyRedis()
    terminals = db.query("SELECT tid, mobile FROM T_TERMINAL_INFO ")
    print 'len ', len(terminals)
    for t in terminals:
        tid = t.tid
        print 'tid', tid
        car = db.get("select * from T_CAR where tid = %s", tid)
        if car:
            print 'has car '
            pass
        else:
            print 'insert car'
            #db.execute("insert into T_CAR(tid) values(%s) ", tid)

def main():
    ConfHelper.load('../conf/global.conf')
    parse_command_line()
    execute()
    

if __name__ == "__main__": 
    main()
