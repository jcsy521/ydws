# -*- coding: utf-8 -*-


import sys

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

def send(content, mobile):
    logging.info("Send %s to %s", content, mobile)
    response = SMSHelper.send(mobile, content)
    logging.info("Response: %s", response)

def send_all(content):
    db = DBConnection().db
    terminals = db.query("SELECT mobile FROM T_TERMINAL_INFO")
    for terminal in terminals:
        send(content, terminal.mobile)

def usage():
    print "Usage: python2.6 send_sms.py --send=[all|one] [--mobile=15942361934]"

def main():
    ConfHelper.load('../conf/global.conf')
    parse_command_line()
    if not 'send' in options:
        usage()
        exit(1)

    #content = 'SET GROUP 10657061123235'
    #content = 'SET SIM 13841915426'
    #content = 'SET SMS 10657'
    #content = 'BIND 18642537770:13842168880'
    #content = 'HFCC'
    content = 'LQ 30'
    #content = 'SSDW'
    #content = 'RELOGIN'
    #content = 'SET TIME 20140625133814'
    #content = 'SET QQ 1*爸爸*13693675352 2*妈妈*13693675352'

    if options.send.lower() == 'all':
        send_all(content)
    elif options.send.lower() == 'one':
        if not 'mobile' in options:
            usage()
            exit(1)
        elif not options.mobile:
            usage()
            exit(1)
        send(content, options.mobile)
    else:
        usage()
        exit(1)


if __name__ == "__main__":
    main()
