# -*- coding: utf-8 -*-
import socket
import select
import time
import thread
import logging
import base64

from tornado.ioloop import IOLoop

from dotdict import DotDict
from base import BaseParser


def send():
    #msg = 'jiaxiaolei'
    #msg = '[1387958150,fzdvrnyu,1,1.0.0,ACB2012777,T10,E,113.252432,N,22.564152,460:0:4489:25196,1]'
    msg = '[1387955485,k347o3aw,3,2.3.10,362E00030D,T10,e,120.93308,n,30.52336,460:0:22322:13215,4]'
    s= socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(('192.168.108.43', 10025))
    s.send(msg)

       
if __name__ == "__main__":   
   send()
