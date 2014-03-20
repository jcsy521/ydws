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

    terminals = db.query("SELECT tid, mobile, group_id, cid FROM V_TERMINAL WHERE group_id != '-1'")
    for terminal in terminals: 
        tid = terminal.tid
        ttype = get_terminal_type_by_tid(tid) 
        print 'ttype', ttype
        if ttype == 'zj200':
            t = db.query("SELECT tid from T_TERMINAL_INFO where test !=0 and tid=%s", tid)  
            if not t:
                continue
            db.execute("UPDATE T_TERMINAL_INFO SET test=0 WHERE tid = %s", 
                       tid)
            print 'tid: %s test is closed.' % tid
            sessionID_key = get_terminal_sessionID_key(tid)
            old_sessionid = redis.get(sessionID_key)
            if old_sessionid:
                redis.delete(sessionID_key)
                print "Termianl %s delete session in redis." % tid

def usage():
    print "Usage: python zj200_no_test.py"

def main():
    ConfHelper.load('../conf/global.conf')
    parse_command_line()

    block_test() 

if __name__ == "__main__": 
    main()
