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

mobiles = ["13928181902","13928109033","13823931771"]

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

def check_ncdl():
    http = httplib2.Http(timeout=30)
    url = "http://ncdl.zs.gov.cn"

    try:
        response, content = http.request(url, 'GET')
        b = time.time()
        if response['status'] == '200':
            logging.info("%s request success", url)
        else:
            logging.info("%s request failed", url)
            for mobile in mobiles:
                send("%s 访问异常，请检查！" % url, mobile)
    except:
        logging.exception("ncdl request failed")
        for mobile in mobiles:
            send("%s 访问异常，请检查！" % url, mobile)

def check_zsonline():
    http = httplib2.Http(timeout=30)
    url = "http://www.zsonline.gov.cn"

    try:
        response, content = http.request(url, 'GET')
        b = time.time()
        if response['status'] == '200':
            logging.info("%s request success", url)
        else:
            logging.info("%s request failed", url)
            for mobile in mobiles:
                send("%s 访问异常，请检查！" % url, mobile)
    except:
        logging.exception("zsonlie request failed")
        for mobile in mobiles:
            send("%s 访问异常，请检查！" % url, mobile)

def main():
    ConfHelper.load('../conf/global.conf')
    parse_command_line()
    
    while True:
        check_ncdl()
        time.sleep(1)
        check_zsonline()
        time.sleep(300)


if __name__ == "__main__": 
    main()
