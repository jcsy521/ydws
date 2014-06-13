# -*- coding: utf-8 -*-

import sys
import time

import os.path
import site
TOP_DIR_ = os.path.abspath(os.path.join(__file__, "../.."))
site.addsitedir(os.path.join(TOP_DIR_, "libs"))
import logging

from tornado.options import define, options, parse_command_line


from utils.dotdict import DotDict
from helpers.confhelper import ConfHelper
from helpers.smshelper import SMSHelper
from utils.checker import check_phone
from db_.mysql import DBConnection
from utils.myredis import MyRedis
from utils.misc import get_terminal_info_key, get_terminal_sessionID_key

def modify_terminal():

    db = DBConnection().db
    redis = MyRedis()
    
    mobile='14778746907'
    #mobile='14778741845'
    #mobile='14778749172'
    #mobile='14778746786'
    #mobile='14778740942'
    #mobile='14778745985'
    #mobile='14778744628'
    #mobile='14778744861'
    #mobile='14778742261'
    #mobile='14778744473'
    #mobile='14778747112'
    #mobile='14778745219'
    #mobile='14778742290'
    #mobile='14778749137'
    #mobile='14778742587'
    #mobile='14778745073'
    #mobile='14778747467'
    #mobile='14778741340'
    #mobile='14778748943'
    #mobile='14778743681'
    sql = "select id, tid, mobile, owner_mobile, begintime, login_time from T_TERMINAL_INFO where mobile= %s"
    
    terminals  = db.query(sql, mobile)
    #print 'len ', len(terminals)
    count = 0
    cnt = 0
    no_loc = 0
    for i, t in enumerate(terminals):
        tid = t.tid
        mobile = t.mobile
        owner_mobile = t.owner_mobile
        terminal_info_key = get_terminal_info_key(tid) 
        terminal_info = redis.getvalue(terminal_info_key) 
        if terminal_info: 
            print 'umobile in redis:%s, umobile in db:%s' % (terminal_info['owner_mobile'], owner_mobile)
            if terminal_info['owner_mobile'] != owner_mobile:
                print 'mobile: %s, umobile in redis:%s, umobile in db:%s' % (mobile, terminal_info['owner_mobile'], owner_mobile)
                cnt = cnt + 1    
                terminal_info['owner_mobile'] = owner_mobile 
                redis.setvalue(terminal_info_key, terminal_info)
        else:
            pass

    print 'count:', count
    print 'cnt:', cnt

def usage():
    print "Usage: python update_owner_mobile_in_redis.py"

def main():
    ConfHelper.load('../conf/global.conf')
    parse_command_line()
    modify_terminal() 

if __name__ == "__main__": 
    main()
