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

# 7 days
LOCATION_NAME_EXPIRY = 60 * 60 * 24 *7


class Test(object):

    def __init__(self):
        #self.db = DBConnection().db
        self.redis = MyRedis()

    def test_lk(self):
        #pattern = "lk:4083025:798780"
        pattern = "lk:*"
        keys = self.redis.keys(pattern)
        count = 0
        #print 'len ----', len(keys)
        for k in keys:
            v = self.redis.get(k)
            #print '-----------k', k, v
            self.redis.delete(k)
            count += 1
            #self.redis.set(k, v, LOCATION_NAME_EXPIRY)
            if not (count % 10000):
                print 'count: %s W' %  count

def main():
    ConfHelper.load('../conf/global.conf')
    parse_command_line()

    t = Test()
    t.test_lk() 

if __name__ == "__main__": 
    main()
