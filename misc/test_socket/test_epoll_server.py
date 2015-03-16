# -*- coding:utf8 -*-

import logging
import socket
import errno
import select
import time

"""
参考：
http://www.cnblogs.com/dkblog/archive/2011/03/25/1995755.html

https://pypi.python.org/pypi/python-epoll

http://www.360doc.com/content/11/1119/15/2660674_165748138.shtml


"""

logger = logging.getLogger("network-server")

def InitLog():
    logger.setLevel(logging.DEBUG)

    fh = logging.FileHandler("network-server.log")
    fh.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.ERROR)
    
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    ch.setFormatter(formatter)
    fh.setFormatter(formatter)
    
    logger.addHandler(fh)
    logger.addHandler(ch)


if __name__ == '__main__':
    print 'come into main'
    InitLog()
    
    #NOTE: server's info
    
    ip = '192.168.1.101'
#    ip = '0.0.0.1'
    port = 6312
    # tcp socket server
    listen_fd = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listen_fd.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listen_fd.bind((ip, port))

    #listen_fd.bind(('', port))
    epoll_fd = select.epoll()
    # epoll in
    epoll_fd.register(listen_fd.fileno(), select.EPOLLIN)


    connections = {}
    addresses = {}
    datalist = {}
    while True:
        epoll_list = epoll_fd.poll()
        for fd, events in epoll_list:
            if fd == listen_fd.fileno():
                conn, addr = listen_fd.accept()
                logger.debug("accept connection from %s, %d, fd = %d" % (addr[0], addr[1], conn.fileno()))
                conn.setblocking(0)
                epoll_fd.register(conn.fileno(), select.EPOLLIN | select.EPOLLET)
                connections[conn.fileno()] = conn
                addresses[conn.fileno()] = addr
            elif select.EPOLLIN & events:
                datas = ''
                while True:
                    try:
                        data = connections[fd].recv(10)
                        if not data and not datas:
                            epoll_fd.unregister(fd)
                            connections[fd].close()
                            logger.debug("%s, %d closed" % (addresses[fd][0], addresses[fd][1]))
                            break
                        else:
                            datas += data
                    except socket.error, msg:
                        if msg.errno == errno.EAGAIN:
                            logger.debug("%s receive %s" % (fd, datas))
                            datalist[fd] = datas
                            epoll_fd.modify(fd, select.EPOLLET | select.EPOLLOUT)
                            break
                        else:
                            epoll_fd.unregister(fd)
                            connections[fd].close() 
                            logger.error(msg)
                            break        
            elif select.EPOLLHUP & events:
                epoll_fd.unregister(fd)
                connections[fd].close()
                logger.debug("%s, %d closed" % (addresses[fd][0], addresses[fd][1])) 
            elif select.EPOLLOUT & events:
                sendLen = 0             
                while True:
                    sendLen += connections[fd].send(datalist[fd][sendLen:])
                    if sendLen == len(datalist[fd]):
                        break
                epoll_fd.modify(fd, select.EPOLLIN | select.EPOLLET)                 
            else:
                continue

