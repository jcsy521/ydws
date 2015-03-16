# -*- coding: utf-8 -*-
import socket
import select
import time
import thread
import logging
import base64
import random
import logging

import os.path
import site
TOP_DIR_ = os.path.abspath(os.path.join(__file__, "../../../.."))
site.addsitedir(os.path.join(TOP_DIR_, "libs"))

from helpers.confhelper import ConfHelper

from tornado.options import define, options, parse_command_line

from utils.myredis import MyRedis

class Terminal(object):
#TODO:
    
    def __init__(self, tid, tmobile, umobile, imsi, imei):

        self.redis = MyRedis()

        self.tid = tid
        self.tmobile = tmobile
        self.umobile = umobile
        self.imsi = imsi
        self.imei = imei

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.connect(('192.168.1.105', 10025))
        self.logging = self.initlog() 

    def __send__(self, packet):
        """Send packet to gateway and receive the response.
        """
        logging.info('send: %s', packet.strip())
        self.socket.send(packet)
        recv = self.socket.recv(1024)
        logging.info('recv: %s', recv)

    def initlog(self): 
        logger = logging.getLogger() 
        hdlr = logging.FileHandler("terminal.log") 
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s') 
        hdlr.setFormatter(formatter) 
        logger.addHandler(hdlr) 
        logger.setLevel(logging.NOTSET) 
        return logger
       

    def test_T11(self):
        """

        """

        key = "sessionID:%s" % self.tid
        sessionid = self.redis.get(key)
        logging.info('key:%s, sessionid: %s', key, sessionid)
        if not sessionid:
            sessionid = ''

        t_time = int(time.time())
        mg = "[%s,%s,1,1.0.0,%s,T11,{E,113.252432,N,22.564152,133.3,270.5,1351492202}]"
        mg = mg % (t_time, sessionid, self.tid)

        self.__send__(mg)


def main():

    args = dict(tid='T123SIMULATOR',
                tmobile='13011292217',
                umobile='18310505991',
                imsi='18310505991',
                imei='18310505991')

    terminal = Terminal(args['tid'], args['tmobile'], args['umobile'], args['imsi'], args['imei'])
    terminal.test_T11()

if __name__ == "__main__":   

    ConfHelper.load('../../../conf/global.conf')
    parse_command_line()

    main()

