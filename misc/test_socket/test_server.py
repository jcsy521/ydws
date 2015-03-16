import socket
import time

if __name__ == '__main__':
    print 'come into main'
    
    #NOTE: server's info
    
    ip = '192.168.1.101'
#    ip = '0.0.0.1'
    port = 6312
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((ip, port))
    
    while True:
        response, address = sock.recvfrom(1024)
        print 'response:%s, address:%s' % (response, address)
        time.sleep(3)
        sock.sendto('receive it:%s' % response, address )   
