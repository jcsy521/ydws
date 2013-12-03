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
    keys = ['owner_mobile',]
    terminals = db.query("SELECT tid, owner_mobile FROM T_TERMINAL_INFO")
    #users = db.query("SELECT mobile FROM T_USER")
    #for user in users:
    #    key = 'captcha:%s' % user.mobile
    #    v = redis.getvalue(key)
    #    print '?', v
    for terminal in terminals:
        t_key = get_terminal_info_key(terminal.tid)
        info = redis.getvalue(t_key)
        if info and ('owner_mobile' not in info):
            info['owner_mobile'] = terminal['owner_mobile']
            redis.setvalue(t_key, info)
            print info
        else:
            print 'redis info:', info

if __name__ == "__main__": 
    main()
