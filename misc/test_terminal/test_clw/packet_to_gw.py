# -*- coding: utf-8 -*-
import sys
import socket
import select
import time
import thread
import logging
import base64
import random


import os.path
import site
TOP_DIR_ = os.path.abspath(os.path.join(__file__, "../../../.."))
site.addsitedir(os.path.join(TOP_DIR_, "libs"))

from helpers.confhelper import ConfHelper

from tornado.ioloop import IOLoop
from tornado.options import define, options, parse_command_line

from dotdict import DotDict
from base import BaseParser

from utils.myredis import MyRedis

class Terminal(object):
    
    def __init__(self, tid, tmobile, umobile, imsi, imei):

        import redis
        self.redis = redis.Redis(host='192.168.108.43',port=6379)
        #self.redis = MyRedis()

        self.tid = tid
        self.tmobile = tmobile
        self.umobile = umobile
        self.imsi = imsi
        self.imei = imei

        #NOTE: JH
        self.login_mg = "[%s,,D,2.3.0,%s,T1,%s,%s,%s,%s,CLW,2,1,DBJ-3771728252,e3-94-9c-6f-53-9c]"
        #NOTE: normal login 
        self.login_mg = "[%s,,D,2.3.0,%s,T1,%s,%s,%s,%s,CLW,2,0,DBJ-3771728252,e3-94-9c-6f-53-9c]"

        self.redis = MyRedis()

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.connect(('192.168.108.43', 10025))
        self.logging = self.initlog() 

    def login(self):
        t_time = int(time.time())
        #t_time = 1355454637
        login_mg = self.login_mg % (t_time, self.tid, self.tmobile, self.umobile, self.imsi, self.imei)
        self.logging.info("Send login message:\n%s", login_mg) 
        self.socket.send(login_mg)
        time.sleep(1)
  
    def login_response(self, bp):
        info = bp.packet_info 
        self.sessionID = info[3]
        self.logging.info("login success!")
        #t_time = int(time.time())
        #mg = self.config_mg% (t_time, self.sessionID, self.tid)
        #self.socket.send(mg)

    def heartbeat(self):
        time.sleep(10)
        #time.sleep(30)
        while True:
            pbat = random.choice(range(30,100))
            heartbeat_mg = self.heartbeat_mg % (int(time.time()), self.sessionID, self.tid, pbat)
            self.logging.info("Send heartbeat:\n%s", heartbeat_mg)
            print "Send heartbeat:\n%s" %  heartbeat_mg
            self.socket.send(heartbeat_mg)
            time.sleep(10)
            #time.sleep(30)

    def restart(self):
        self.logging.info("Restart terminal...")

    def read_mg(self):
        """Read package from logfile then send them to gateway.
        """
        print 'come into read mg'
        time.sleep(2)
        #NOTE:  
        logfile = '/home/ydcws/3.log'

        count = 0
        f = open(logfile)
        for line in f:
            print 'line', line
            lst = line.split(',')

            old_sessionid = lst[1]
            old_tid = lst[4]

            key = "sessionID:%s" % old_tid
            sessionid = self.redis.get(key)
            if not sessionid:
                continue
            #sessionid = r.get(key)
            #print 'key', key,  'sessionid', sessionid
            if not sessionid:
                sessionid = ''

            line = line.replace(old_sessionid, sessionid)
            line = line.replace(" ", "")
            self.socket.send(line)
            count = count + 1
            if not count % 100:
                print count
            time.sleep(0.01)

    def start_each_thread(self):
        thread.start_new_thread(self.read_mg, ())

    def handle_recv(self, bp, io_loop):
        if bp.type == "S1":
            self.login_response(bp)
            self.start_each_thread()
        else:
            pass
    
    def tcpClient(self, io_loop):
        try:
            self.login()
            while True:
                infds, _, _ = select.select([self.socket], [], [], 1)
                if len(infds) > 0:
                    dat = self.socket.recv(1024)
                    self.logging.info("Recv:%s", dat)
                    print 'recv: ', dat
                    bp = BaseParser(dat)
                    self.handle_recv(bp, io_loop)
        except Exception as e:
            self.logging.exception("What's wrong, reconnect it.")
        finally:
            self.socket.close()

    def initlog(self): 
        logger = logging.getLogger() 
        hdlr = logging.FileHandler("terminal.log") 
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s') 
        hdlr.setFormatter(formatter) 
        logger.addHandler(hdlr) 
        logger.setLevel(logging.NOTSET) 
        return logger


    def start_io_loop(self, io_loop):
        io_loop.start()
       
if __name__ == "__main__":   
    ConfHelper.load('../../../conf/global.conf')
    parse_command_line()

    io_loop = IOLoop.instance()

    args = dict(tid='T123SIMULATOR',
                tmobile='13011292217',
                umobile='18310505991',
                imsi='18310505991',
                imei='')

    terminal = Terminal(args['tid'], args['tmobile'], args['umobile'], args['imsi'], args['imei'])
    thread.start_new_thread(terminal.tcpClient, (io_loop,))
    while True:
        time.sleep(10)
