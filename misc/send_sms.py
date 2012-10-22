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
    response = SMSHelper.send_to_terminal(mobile, content)
    logging.info("Response: %s", response)

def send_all(content):
    db = DBConnection().db
    terminals = db.query("SELECT mobile FROM T_TERMINAL_INFO")
    for terminal in terminals:
        send(content, terminal.mobile)

def usage():
    print "Usage: python26 send_sms.py --send=[all|one] [--mobile=15942361934]"

def main():
    ConfHelper.load('../conf/global.conf')
    parse_command_line()
    if not 'send' in options:
        usage()
        exit(1)

    content = ':DOMAIN %s' % ConfHelper.GW_SERVER_CONF.domain
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
