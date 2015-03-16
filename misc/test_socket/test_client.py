# -*- coding:utf8 -*-

import socket
import time

if __name__ == '__main__':
    
    
    #NOTE: server's info
    print 'come into client'
    
    ip = '192.168.1.101'
#    ip = '192.168.1.7'
#    ip = ''
#    ip = '0.0.0.1'
    #port = 10025 
    port = 6312
#    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#    sock.connect((ip, port))    
#    #sock.connect(('localhost', 8001))  
    #sock.connect(('211.137.45.80',13002))
    
##    sock.send('jia')
#    sock.send('jia')    
#    response = sock.recv(1024)
#    print response
#    
#    sock.send('jia')    
#    response = sock.recv(1024)
#    print response
#    
#    sock.send('jia')    
#    response = sock.recv(1024)
#    print response
#    
#    sock.send('jia')    
#    response = sock.recv(1024)
#    print response
#    
    
#    #NOTE：Test client
    for k in range(10):  
        # 建立到 
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((ip, port))    
#        sock.connect(ip, port)   

        print 'send', 'jia' 
        sock.send('jia')
    
#        response = sock.recv(2)
        response = sock.recv(1024)
        print 'receive',  response
        sock.close()
        time.sleep(3)
