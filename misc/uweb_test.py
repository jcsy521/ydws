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

##NOTE: ydcws.com
#alert_mobile = "13693675352" 
alert_mobile = "18310505991" 
base_url='http://www.ydcws.com'
base_url_inner='http://app01:8000'

##NOTE: ichebao.net 
#alert_mobile = "18310505991" 
#base_url='http://www.ichebao.net'
#base_url_inner='http://drone-005:8001'

def initlog():
    logger = logging.getLogger()
    hdlr = logging.FileHandler("/tmp/uweb_test.log")
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    hdlr.setFormatter(formatter)
    logger.addHandler(hdlr)
    logger.setLevel(logging.NOTSET)

    return logger

logging = initlog() 

def send(content, mobile):
    logging.info("Send %s to %s", content, mobile)
    #NOTE: send encrypt sms to mobile
    #response = SMSHelper.send_to_terminal(mobile, content)
    #NOTE: send general sms to mobile
    response = SMSHelper.send(mobile, content)
    logging.info("Response: %s", response)

def login():
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
        send("Login url:%s by nginx failed" % url, 
             alert_mobile)

    logging.info("[UWEB_TEST] Test login cookie header: %s", headers)
    return headers

def check_track_to_nginx(headers):
    _start_time = time.time()
    http = httplib2.Http(timeout=30)
    url = base_url + "/track"
    end_time = int(time.time())
    start_time = end_time - 3600*2
    
    try:
        data = dict(start_time=start_time, end_time=end_time, cellid_flag=0, tid="T123SIMULATOR")
        response, content = http.request(url, 'POST', headers=headers, body=json_encode(data))
        #print 'response', response
        #print 'content',  content
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
        send("Access url:%s by nginx failed" % url, 
             alert_mobile)

def check_lastposition_to_nginx(headers):
    _start_time = time.time()
    http = httplib2.Http(timeout=30)
    #url = base_url + "/lastposition"
    url = base_url + "/inclastinfo/corp"
    end_time = int(time.time())
    start_time = end_time - 3600*2
    
    try:
        data = dict(lastinfo_time=-1, cache=0, track_list=[])
        #data = dict(lastposition_time=_start_time, cache=0, track_list=[])
        response, content = http.request(url, 'POST', headers=headers, body=json_encode(data))
        #print 'response', response
        #print 'content',  content
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

def test_single():
    """
    """
    logging.info("[UWEB_TEST] Test single start.")
    #headers = login()
    #NOTE: here, you can set a cookie
    cookie = 'bdshare_firstime=1397896826550; USERCURRENTROLE=enterprise; ACBUWEB="2|1:0|10:1402380632|7:ACBUWEB|92:Qz0xODcwMTYzODQ5NDpPPWR1bW15X29pZDpVPTE4NzAxNjM4NDk0OlQ9Q0JCSlRFQU0wMTpUVD0xNTIxMDAxNjQ2OQ==|678e6a0891f88fdbb22ae21fcfc3978d49ea7523076cb84865cc166dea46193c"'
   
    # 13693675352, 111111
    cookie = 'bdshare_firstime=1397896826550; USERCURRENTROLE=enterprise; ACBUWEB="2|1:0|10:1402478349|7:ACBUWEB|92:Qz0xMzY5MzY3NTM1MjpPPWR1bW15X29pZDpVPTEzNjkzNjc1MzUyOlQ9MTg5MTE0NDM5ODM6VFQ9MTg5MTE0NDM5ODM=|716bb65e7e5436ad35dd4617fec08ce2c317335b0bed4e2df533c23abaf974d7"'

    # ydcws.com
    #cookie = 'bdshare_firstime=1382629354368; USERCURRENTROLE=enterprise; ACBUWEB="Qz0xMzYwMDMzNTU1MDpPPWR1bW15X29pZDpVPTEzNTMxODg3MjMzOlQ9MzY5QTQwMDRBNzpUVD0xNDc3ODc0MzQ3OQ==|1402411014|e586c8fe2d9cd50dd0c906b2a7ff6580892352aa"'

    cookie = 'bdshare_firstime=1382629354368; USERCURRENTROLE=enterprise; ACBUWEB="Qz0xMzcyNjEwMzg4OTpPPWR1bW15X29pZDpVPTEzNzI2MTAzODg5OlQ9MzMwQTAwMDFDOTpUVD0xNDcxNDk4NzU3OQ==|1402413922|d4045caa17f0dc7e1a895db0541a482994f9ebd1"'
    headers =  {} 
    headers['Cookie'] = cookie 
    while True:
        check_lastposition_to_nginx(headers)
        #check_track_to_nginx(headers)
        time.sleep(15)

def test():
    """
    """
    #users=5
    #users=200
    #users=50
    #users=100
    #users=200
    users=300
    #users=1
    try: 
        for i in xrange(users):
            thread.start_new_thread(test_single, ())
            time.sleep(0.1) 
        while True: 
            time.sleep(60) 
    except KeyboardInterrupt as e:
        logging.error("[UWEB_TEST] Ctrl-C is pressed.")
    except Exception as e:
        logging.exception("[UWEB_TEST] Exit Exception")
    finally:
        logging.warn("[UWEB_TEST] Stopped. Bye!") 

if __name__ == "__main__": 
    ConfHelper.load('../conf/global.conf')
    parse_command_line()
    test()
