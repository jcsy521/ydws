# -*- coding: utf-8 -*-
import sys
import socket
import select
import time
import logging

import os.path
import site
TOP_DIR_ = os.path.abspath(os.path.join(__file__, "../../../.."))
site.addsitedir(os.path.join(TOP_DIR_, "libs"))

from helpers.confhelper import ConfHelper

from tornado.options import define, options, parse_command_line

from utils.myredis import MyRedis

class Terminal(object):
    
    def __init__(self):

        self.redis = MyRedis()

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        #NOTE: connect the gateway
        self.socket.connect(('192.168.1.105', 10025))
        self.logging = self.initlog() 

    def __send__(self, packet):
        """Send packet to gateway and receive the response.
        """
        logging.info('send: %s', packet.strip())
        self.socket.send(packet)
        recv = self.socket.recv(1024)
        logging.info('recv: %s', recv)

    def read_mg(self):
        """Read package from logfile then send them to gateway.
        """
        logging.info('come into read mg')
        time.sleep(5)
        #NOTE: the gateway log has been pre-handled 
        logfile = '/home/pabb/0703.log'

        f = open(logfile)
        for line in f:
            lst = line.split(',')

            old_sessionid = lst[1]
            old_tid = lst[4]

            key = "sessionID:%s" % old_tid
            sessionid = self.redis.get(key)
            logging.info('key:%s, sessionid: %s', key, sessionid)
            if not sessionid:
                sessionid = ''

            line = line.replace(old_sessionid, sessionid)
            line = line.replace(" ", "")

            self.__send__(line)
            time.sleep(5)

    def initlog(self): 
        logger = logging.getLogger() 
        hdlr = logging.FileHandler("terminal.log") 
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s') 
        hdlr.setFormatter(formatter) 
        logger.addHandler(hdlr) 
        logger.setLevel(logging.NOTSET) 
        return logger
       
if __name__ == "__main__":   
    ConfHelper.load('../../../conf/global.conf')
    parse_command_line()

    terminal = Terminal()
    terminal.read_mg()
