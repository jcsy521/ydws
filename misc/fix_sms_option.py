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

def block_test():
    db = DBConnection().db
    redis = MyRedis()

    sms = db.query("SELECT uid FROM T_SMS_OPTION")
    count = 0
    for s in sms: 
        uid = s.uid
        user = db.get("select * from T_USER where uid = %s", uid)
        if user:
            pass
            #print 'pass'
        else:
            db.execute("DELETE FROM T_SMS_OPTION WHERE uid = %s", uid)
            print 'delete ....', uid
            count += 1
    print '-------count: %s' % count

def usage():
    print "Usage: python zj200_no_test.py"

def main():
    ConfHelper.load('../conf/global.conf')
    parse_command_line()

    block_test() 

if __name__ == "__main__": 
    main()
