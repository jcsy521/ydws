# -*- coding:utf8 -*-

import socket
import time

if __name__ == '__main__':
    
    
    #NOTE: server's info
    print 'come into client'
    
    ip = '192.168.1.205'
    #ip = '192.168.1.101'
    port = 10025 
    body = '[1343278839,tmum1lwf,A,5.0.0,T123SIMULATOR,T2,23:${gms}:96,0,0]'

#    #NOTE：Test client
    # 建立到 
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#     sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((ip, port))    

    for k in range(1000):  
        time.sleep(10)
        print 'send', body 
        sock.send(body)

    #     response = sock.recv(2)
        response = sock.recv(1024)
        print 'receive',  response

    sock.close()
