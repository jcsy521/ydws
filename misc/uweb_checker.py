# -*- coding: utf-8 -*-

import sys
import os.path
import site
import httplib2
TOP_DIR_ = os.path.abspath(os.path.join(__file__, "../.."))
site.addsitedir(os.path.join(TOP_DIR_, "libs"))
import logging
import time

from tornado.escape import json_decode, json_encode
from tornado.options import define, options, parse_command_line
define('send', default="one")
define('mobile', default="")

from helpers.confhelper import ConfHelper
from helpers.smshelper import SMSHelper
from db_.mysql import DBConnection

def send(content, mobile):
    logging.info("Send %s to %s", content, mobile)
    #NOTE: send encrypt sms to mobile
    response = SMSHelper.send_to_terminal(mobile, content)
    #NOTE: send general sms to mobile
    #response = SMSHelper.send(mobile, content)
    logging.info("Response: %s", response)

def send_all(content):
    db = DBConnection().db
    terminals = db.query("SELECT mobile FROM T_TERMINAL_INFO where login=0")
    for terminal in terminals:
        send(content, terminal.mobile)

def check_req_to_nginx():
    http = httplib2.Http(timeout=30)
    url = "http://www.ydcws.com/zfjsyncer"
    data = dict()
    response, content = http.request(url, 'POST', json_encode(data))
    if response['status'] == '200':
        if content:
            logging.info("ZFJSyncer nginx request success conent:%s", content)
        else:
            logging.info("ZFJSyncer nginx request conent is none")
    else:
        logging.exception("[ZFJSyncer] nginx request failed response: %s", response)
        send("Access www.ydcws.com by nginx failed", "13693675352")

def check_req_to_uweb():
    http = httplib2.Http(timeout=30)
    url = "http://APP01:8000/zfjsyncer"
    data = dict()
    response, content = http.request(url, 'POST', json_encode(data))
    if response['status'] == '200':
        if content:
            logging.info("ZFJSyncer uweb request success conent:%s", content)
        else:
            logging.info("ZFJSyncer uweb request conent is none")
    else:
        logging.exception("[ZFJSyncer] uweb request failed response: %s", response)
        send("Access http://APP01:8000/zfjsyncer by uweb failed", "13693675352")

def main():
    ConfHelper.load('../conf/global.conf')
    parse_command_line()

    while True:
        check_req_to_nginx()
        time.sleep(1)
        check_req_to_uweb()
        time.sleep(30)


if __name__ == "__main__": 
    main()
