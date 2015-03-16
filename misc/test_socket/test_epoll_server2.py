# -*- coding:utf8 -*-


import socket, logging
import select, errno

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

if __name__ == "__main__":
    InitLog()
    
    try:
        listen_fd = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
    except socket.error, msg:
        logger.error("[SERVER] Create a socket failed")
    
    try:
        listen_fd.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    except socket.error, msg:
        logger.error("[SERVER] setsocketopt error")
    
    try:
        listen_fd.bind(('', 6312))
    except socket.error, msg:
        logger.error("[SERVER] listen file id bind ip error")
    
    try:
        listen_fd.listen(10)
    except socket.error, msg:
        logger.error(msg)
    
    try:
        epoll_fd = select.epoll()
        epoll_fd.register(listen_fd.fileno(), select.EPOLLIN)
    except select.error, msg:
        logger.error(msg)
        
    connections = {}
    addresses = {}
    datalist = {}

    print 'server fd:%s' % listen_fd.fileno()

    def show(fd):
        if connections.has_key(fd):
            print 'show fd:%s, connection:%s, address:%s' % (fd, connections[fd], addresses[fd])
        else:
            print 'nothing can be show fd:%s' % fd

    while True: ## only event 触发才会进入循环。
        epoll_list = epoll_fd.poll()
        print 'epoll_list:%s, type:%s' % (epoll_list, type(epoll_list))
        for fd, events in epoll_list: ###???
            print 'fd: %s, events:%s' % (fd, events)
            print 'listen_fd:%s, listen_fd.fileno():%s' % (listen_fd, listen_fd.fileno())
            if fd == listen_fd.fileno(): # socket server itself.
                print '1.1', show(fd)
                conn, addr = listen_fd.accept()
                logger.debug("[SERVER] accept connection from %s, %d, fd = %d" % (addr[0], addr[1], conn.fileno()))
                conn.setblocking(0) # non block
                # what events?
                epoll_fd.register(conn.fileno(), select.EPOLLIN | select.EPOLLET)
                ## keep the the connections and address of sock's client.
                connections[conn.fileno()] = conn
                addresses[conn.fileno()] = addr
                show(conn.fileno())
            elif select.EPOLLIN & events: # ???               
                print 'readable, ', show(fd)
                datas = ''
                while True:
                    print '1.2.1', show(fd)
                    try:                       
                        data = connections[fd].recv(10)
                        print 'recv data from socket client:%s' % data
                        if not data and not datas:
                            print 'no data from client, colse client:%s', fd
                            epoll_fd.unregister(fd)
                            connections[fd].close()
                            logger.debug("%s, %d closed" % (addresses[fd][0], addresses[fd][1]))
                            break
                        else:
                            datas += data
                        print 'recv the whole data: %s' % datas
                    except socket.error, msg:
                        print 'exect', msg, msg.errno
                        if msg.errno == errno.EAGAIN:
                            print 'exect 1', 'eagain, try it again, the recv it over.'
                            # [Errno 11] Resource temporarily unavailable 11

                            logger.debug("fd: %s receive data: %s" % (fd, datas))
                            datalist[fd] = datas
                            epoll_fd.modify(fd, select.EPOLLET | select.EPOLLOUT)
                            break
                        else:
                            print 'exect 2'
                            epoll_fd.unregister(fd)
                            connections[fd].close() 
                            logger.error(msg)
                            break        
            elif select.EPOLLHUP & events:  ##???
                print 'find close client', show(fd)

                epoll_fd.unregister(fd)
                connections[fd].close()
                logger.debug("[SERVER]  %s, %d closed" % (addresses[fd][0], addresses[fd][1])) 
            elif select.EPOLLOUT & events: ##????
                print 'writable, ', show(fd)
                sendLen = 0             
                while True:
                    print 'send:', datalist[fd][sendLen:]
                    sendLen += connections[fd].send(datalist[fd][sendLen:])
                    if sendLen == len(datalist[fd]):
                        break
                epoll_fd.modify(fd, select.EPOLLIN | select.EPOLLET)                 
            else:                
                print ' continue', show(fd)
                continue