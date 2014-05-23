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
def login():
    url = 'http://www.ydcws.com/logintest'     
    headers = dict()
    http = httplib2.Http(timeout=30)
    response, content = http.request(url, 'POST') 
    if response['status'] in ('200', '302'):
        headers = {'Cookie': response['set-cookie']}
        if content:
            logging.info("Login nginx request success conent:%s", content)
        else:
            logging.info("Login nginx request conent is none")
    else:
        logging.exception("[Login] nginx request failed response: %s", response)
        send("Login www.ydcws.com/logintest by nginx failed", "13693675352")

    logging.exception("[Login] test login cookie header: %s", headers)

    return headers

def check_req_to_nginx(headers):
    a = time.time()
    http = httplib2.Http(timeout=30)
    url = "http://www.ydcws.com/track"
    end_time = int(time.time())
    start_time = end_time - 3600*2
    
    try:
        data = dict(start_time=start_time, end_time=end_time, cellid_flag=0, tid="T123SIMULATOR")
        response, content = http.request(url, 'POST', headers=headers, body=json_encode(data))
        b = time.time()
        if response['status'] == '200':
            if content:
                logging.info("Track nginx request success conent len:%s, used time:%s", len(content), b-a)
            else:
                logging.info("Track nginx request conent is none")
    except:
        logging.exception("[Track] nginx request failed")
        send("Access www.ydcws.com/track by nginx failed", "13693675352")

def check_req_to_uweb(headers):
    a = time.time()
    http = httplib2.Http(timeout=30)
    url = "http://app01:8001/track"
    end_time = int(time.time())
    start_time = end_time - 3600*2

    try:
        data = dict(start_time=start_time, end_time=end_time, cellid_flag=0, tid="T123SIMULATOR")
        response, content = http.request(url, 'POST', headers=headers, body=json_encode(data))
        b = time.time()
        if response['status'] == '200':
            if content:
                logging.info("Track uweb request success conent len:%s, used time:%s", len(content), b-a)
            else:
                logging.info("Track uweb request conent is none")
    except:
        logging.exception("[Track] uweb request failed")
        send("Access http://app01:8000/track by uweb failed", "13693675352")

def main():
    ConfHelper.load('../conf/global.conf')
    parse_command_line()
    
    headers = login()

    while True:
        check_req_to_nginx(headers)
        time.sleep(1)
        check_req_to_uweb(headers)
        time.sleep(30)


if __name__ == "__main__": 
    main()
