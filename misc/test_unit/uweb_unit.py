# -*- coding: utf-8 -*-

import sys
import os.path
import site
import httplib2
TOP_DIR_ = os.path.abspath(os.path.join(__file__, "../../.."))
site.addsitedir(os.path.join(TOP_DIR_, "libs"))
import logging
import time
import thread
import urllib

from tornado.escape import json_decode, json_encode
from tornado.options import define, options, parse_command_line

from helpers.confhelper import ConfHelper
from helpers.smshelper import SMSHelper
from db_.mysql import DBConnection
from utils.myredis import MyRedis

##NOTE: ydcws.com
#alert_mobile = "13693675352" 
#alert_mobile = "18310505991" 
#base_url='http://www.ydcws.com'
#base_url_inner='http://app01:8000'

##NOTE: ichebao.net 
alert_mobile = "18310505991" 
#base_url='http://www.ichebao.net'
#base_url_inner='http://drone-009:6301'
base_url='http://drone-009:6301'
#base_url='http://drone-009:6301'

class Test(object):


    def __init__(self):

        self.db = DBConnection().db 
        self.redis = MyRedis() 
        self.logging = self.initlog() 

    def initlog(self):
        logger = logging.getLogger()
        hdlr = logging.FileHandler("/tmp/uweb_test.log")
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
        hdlr.setFormatter(formatter)
        logger.addHandler(hdlr)
        logger.setLevel(logging.NOTSET)
    
        return logger


    def send(self, content, mobile):
        return
        logging.info("Send %s to %s", content, mobile)
        #NOTE: send encrypt sms to mobile
        #response = SMSHelper.send_to_terminal(mobile, content)
        #NOTE: send general sms to mobile
        response = SMSHelper.send(mobile, content)
        logging.info("Response: %s", response)
    
    def login(self):
        url = base_url + '/logintest'     
        headers = dict()
        http = httplib2.Http(timeout=30)
        response, content = http.request(url, 'POST') 
        if response['status'] in ('200', '302'):
            headers = {'Cookie': response['set-cookie']}
            if content:
                logging.info("[UWEB_TEST] Login nginx request success conent:%s", content)
            else:
                logging.info("[UWEB_TEST] Login nginx request conent is none")
        else:
            logging.exception("[UWEB_TEST] nginx request failed response: %s", response)
            self.end("Login url:%s by nginx failed" % url, 
                 alert_mobile)
    
        logging.info("[UWEB_TEST] Test login cookie header: %s", headers)
        return headers
    
    def check_track_to_nginx(self, headers):
        _start_time = time.time()
        http = httplib2.Http(timeout=30)
        url = base_url + "/track"
        end_time = int(time.time())
        start_time = end_time - 3600*2
        
        try:
            data = dict(start_time=start_time, end_time=end_time, cellid_flag=0, tid="T123SIMULATOR")
            response, content = http.request(url, 'POST', headers=headers, body=json_encode(data))
            _end_time = time.time()
            if response['status'] == '200':
                if content:
                    logging.info("[UWEB_TEST] Track nginx request success conent len: %s, used_time: %s", 
                                 len(content), _end_time - _start_time)
                else:
                    logging.info("[UWEB_TEST] Track nginx request conent is none")
            else:
                logging.info("[UWEB_TEST] Track nginx request failed.")
        except:
            logging.exception("[UWEB_TEST] nginx request failed")
            self.send("Access url:%s by nginx failed" % url, 
                 alert_mobile)
    
    def check_inclastinfo_to_nginx(self, headers):
        _start_time = time.time()
        http = httplib2.Http(timeout=30)
        #url = base_url + "/lastposition"
        url = base_url + "/inclastinfo/corp"
        end_time = int(time.time())
        start_time = end_time - 3600*2
        
        try:
            data = dict(lastinfo_time=-1, cache=0, track_list=[])
            response, content = http.request(url, 'POST', headers=headers, body=json_encode(data))
            _end_time = time.time()
            if response['status'] == '200':
                if content:
                    logging.info("[UWEB_TEST] Lastposition nginx request success conent len: %s, used_time: %s", 
                                 len(content), _end_time - _start_time)
                else:
                    logging.info("[UWEB_TEST] Lastposition nginx request conent is none.")
            else: 
                logging.info("[UWEB_TEST] Lastposition nginx request failed.")
        except:
            logging.exception("[UWEB_TEST] nginx request failed")
            send("Access url:%s by nginx failed" % url,  
                 alert_mobile)
    
    def lastposition(self, headers):
        _start_time = time.time()
        http = httplib2.Http(timeout=30)
        url = base_url + "/lastposition"
        end_time = int(time.time())
        start_time = end_time - 3600*2
        
        try:
            data = dict(lastinfo_time=-1, cache=0, track_list=[],version_type=1)
            #data = dict(lastposition_time=_start_time, cache=0, track_list=[])
            response, content = http.request(url, 'POST', headers=headers, body=json_encode(data))
            _end_time = time.time()
            if response['status'] == '200':
                if content:
                    logging.info("[UWEB_TEST] Lastposition nginx request success conent len: %s, used_time: %s", 
                                 len(content), _end_time - _start_time)
                else:
                    logging.info("[UWEB_TEST] Lastposition nginx request conent is none.")
            else: 
                logging.info("[UWEB_TEST] Lastposition nginx request failed.")
        except:
            logging.exception("[UWEB_TEST] nginx request failed")
            send("Access url:%s by nginx failed" % url,  
                 alert_mobile)
    
    def logintest_android(self, headers):
        _start_time = time.time()
        http = httplib2.Http(timeout=30)
        url = base_url + "/logintest/android"
        end_time = int(time.time())
        start_time = end_time - 3600*2
        
        try:
            data = dict(version_type=1)
            headers['Content-Type'] = 'application/x-www-form-urlencoded'
            response, content = http.request(url, 'POST', headers=headers, body=urllib.urlencode(data))
            #response, content = http.request(url, 'POST', headers=headers, body=json_encode(data))
            _end_time = time.time()
            if response['status'] == '200':
                if content:
                    logging.info("[UWEB_TEST] Lastposition nginx request success conent len: %s, used_time: %s", 
                                 len(content), _end_time - _start_time)
                else:
                    logging.info("[UWEB_TEST] Lastposition nginx request conent is none.")
            else: 
                logging.info("[UWEB_TEST] Lastposition nginx request failed.")
        except Exception as e:
            logging.exception("[UWEB_TEST] nginx request failed")
            send("Access url:%s by nginx failed" % url,  
                 alert_mobile)

    def test(self):
        """
        """
        logging.info("[UWEB_TEST] Test single start.")
    
        cookie = 'bdshare_firstime=1397892175624; USERCURRENTROLE=enterprise; ACBUWEB=Qz0xMzAxMTI5MjIxNzpPPWR1bW15X29pZDpVPTEzMDExMjkyMjE3OlQ9MTMyMTEyOTIyMTg6VFQ9MTMyMTEyOTIyMTg=|1402906411|05e677cb8b0d8ddd89fa5688881ee88fb8022e36'
        headers =  {} 
        headers['Cookie'] = cookie 
        self.lastposition(headers)
        #self.logintest_android(headers)
    
def main():
    """Main method.
    """
    test = Test()
    test.test()

if __name__ == "__main__": 
    ConfHelper.load('../../conf/global.conf')
    parse_command_line()

    main()
