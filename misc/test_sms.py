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
from helpers.smshelper import SMSHelper
from db_.mysql import DBConnection
from utils.myredis import MyRedis
from utils.misc import get_terminal_info_key

def insert_sms():
    ConfHelper.load('../conf/global.conf')
    parse_command_line()
    db = DBConnection().db
    redis = MyRedis() 

    msgid=str(int(time.time() * 1000))[-9:]
    mobile = '18310505991'
    insert_time = int(time.time() * 1000)
    category = 2 # SMS.CATEGORY.MT
    #send_status = -1 # SMS.SENDSTATUS.PREPARING
    send_status = 0 # SMS.SENDSTATUS.SUCCESS
    count = 3

    for i in xrange(500):
        content= 'test sms'
        content = content + 'seq: %s' % i
        db.execute("INSERT INTO T_SMS(msgid, mobile, content, "
                   " insert_time, category, send_status) "
                   "  VALUES(%s, %s, %s, %s, %s, %s)",
                   msgid, mobile, content, insert_time,
                   category, send_status) 

if __name__ == "__main__": 
    insert_sms()
