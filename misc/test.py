# -*- coding: utf-8 -*-

import sys
import os.path
import site
import httplib2
TOP_DIR_ = os.path.abspath(os.path.join(__file__, "../.."))
site.addsitedir(os.path.join(TOP_DIR_, "libs"))
import logging
import time
import thread

from tornado.escape import json_decode, json_encode
from tornado.options import define, options, parse_command_line

from helpers.confhelper import ConfHelper
from helpers.smshelper import SMSHelper
from db_.mysql import DBConnection

def test():
    """
    """
    url = 'http://tcc.taobao.com/cc/json/mobile_tel_segment.htm?tel=15850781443'
    #url = 'http://tcc.taobao.com/cc/json/mobile_tel_segment.htm?tel=15014903707'
    http = httplib2.Http(timeout=30)
    response, content = http.request(url, 'GET')
    print 'r', response, 'c', content
    print '---', content.decode('gbk')
    cont =  content.decode('gbk')
    cont = cont[cont.find('{'):]
    print 'cont', cont
    #print '---', dict(cont)
    print cont.find(u'江苏')
    print cont.find(u'河南')
    if  cont.find(u'广东')>0:
        print 'guandong'
    else:
        print 'no guandong'
    

if __name__ == "__main__": 
    ConfHelper.load('../conf/global.conf')
    parse_command_line()
    test()
