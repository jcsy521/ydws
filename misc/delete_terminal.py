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
from utils.misc import *

def delete_terminal(tid, db, redis):
    user = QueryHelper.get_user_by_tid(tid, db)
    terminal = db.get("SELECT mobile FROM T_TERMINAL_INFO"
                      "  WHERE tid = %s", tid)
    for item in [tid,]:
        sessionID_key = get_terminal_sessionID_key(item)
        address_key = get_terminal_address_key(item)
        info_key = get_terminal_info_key(item)
        lq_sms_key = get_lq_sms_key(item)
        lq_interval_key = get_lq_interval_key(item)
        location_key = get_location_key(item)
        del_data_key = get_del_data_key(item)
        keys = [sessionID_key, address_key, info_key, lq_sms_key, lq_interval_key,
                location_key, del_data_key]
        redis.delete(*keys)
    # clear db
    db.execute("DELETE FROM T_TERMINAL_INFO"
               "  WHERE tid = %s", 
               tid) 
    logging.info("[GW] Delete Terminal: %s, umobile: %s",
                 tid, (user.owner_mobile if user else None))

def execute(tid):
    db = DBConnection().db
    redis = MyRedis()
    delete_terminal(tid, db, redis)
    


def main():
    ConfHelper.load('../conf/global.conf')
    parse_command_line()
    if not options.tid:
        usage()
        exit(1)
    execute(options.tid)
    

def usage():
    print "Usage: python delete_terminal.py --tid=1111"

if __name__ == "__main__": 
    main()
