# -*- coding: utf-8 -*-

import sys
import re

import os.path
import site
TOP_DIR_ = os.path.abspath(os.path.join(__file__, "../.."))
site.addsitedir(os.path.join(TOP_DIR_, "libs"))
import logging

from tornado.options import define, options, parse_command_line
define('send', default="one")
define('mobile', default="")

from helpers.confhelper import ConfHelper
from helpers.smshelper import SMSHelper
from db_.mysql import DBConnection

def main():
    for i in xrange(1,101):
    #for i in xrange(64,65):
        file_path = '/var/log/supervisor/gateway/error.log.'+str(i)
        log = open(file_path)
        #p0 = re.compile("130708", re.I)
        p1 = re.compile("36E24002F2", re.I)
        p2 = re.compile("recv", re.I)
        p3 = re.compile("send", re.I)
        for line in log:
            if p1.search(line) and p2.search(line): # and p0.search(line):
                print line
                index = line.find('from') + 4
                addr = line[index:][1:-1]
                p4 = re.compile(addr, re.I)
                for line in log: 
                    if p3.search(line) and p4.search(line): # and p0.search(line):
                        print line
                        break
        

if __name__ == "__main__": 
    main()
