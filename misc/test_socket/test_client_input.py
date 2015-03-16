# -*- coding:utf8 -*-

import socket
import time
import sys

if __name__ == '__main__':
    print 'come into client'
    
    ip = '192.168.1.205'
    #ip = '192.168.1.101'
    port = 7203 
    #port = 6312

     # 建立到 
#      sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((ip, port))    

    body = ' '.join(sys.argv[1:]) or "Hello World!"
    sock.send(body)
 
    response = sock.recv(1024)
    print 'receive',  response
    sock.close()
    time.sleep(3)
