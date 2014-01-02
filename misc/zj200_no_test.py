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
from db_.mysql import DBConnection

def block_test():
    db = DBConnection().db
    terminals = db.query("SELECT tid, mobile, group_id, cid FROM V_TERMINAL WHERE group_id != '-1'")
    for terminal in terminals: 
        tid = terminal.tid
        ttype = get_terminal_type_by_tid(tid) 
        print 'ttype', ttype
        if ttype == 'zj200':
            db.execute("UPDATE T_TERMINAL_INFO SET test=0 WHERE tid = %s", 
                       tid)
            print 'tid: %s test is closed.' % tid

def usage():
    print "Usage: python zj200_no_test.py"

def main():
    ConfHelper.load('../conf/global.conf')
    parse_command_line()

    block_test() 

if __name__ == "__main__": 
    main()
