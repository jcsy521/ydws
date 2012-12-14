# -*- coding: utf-8 -*-

import socket
import errno
import select
import struct
import logging
import json
import pika
from pika.adapters import *
from pika.exceptions import AMQPConnectionError
from functools import partial
import time

from constants import GF 
from constants.GATEWAY import DUMMY_FD, TERMINAL_LOGIN
from codes.gfcode import GFCode
from utils.dotdict import DotDict
from utils.repeatedtimer import RepeatedTimer
from db_.mysql import get_connection
from utils.misc import get_terminal_address_key, get_terminal_sessionID_key,\
                       get_terminal_info_key

from helpers.seqgenerator import SeqGenerator
from helpers.confhelper import ConfHelper

from gf.packet.composer.bindcomposer import BindRespComposer, UNBindRespComposer
from gf.packet.composer.sendcomposer import SendRespComposer
from gf.packet.composer.activetestcomposer import ActiveTestComposer

from gf.packet.parser.codecheck import GFCheck
from gf.packet.parser.bindparser import BindParser
from gf.packet.parser.sendparser import SendParser

from clw.packet.parser.codecheck import S_CLWCheck

class MySIServer():
    """
    SIServer
    It receives requests from SI and sends these requests to GWServer,
    then gives responses to SI.
    """
    def __init__(self, conf_file):
        ConfHelper.load(conf_file)
        for i in ('port', 'count'):
            ConfHelper.SI_SERVER_CONF[i] = int(ConfHelper.SI_SERVER_CONF[i])
        self.db = None 
        self.redis = None
        # RabbitMQ
        self.rabbitmq_connection = None
        self.rabbitmq_channel = None
        self.exchange = 'acb_exchange'
        self.gw_queue = 'gw_requests_queue@' +\
                        ConfHelper.GW_SERVER_CONF.host + ':' +\
                        str(ConfHelper.GW_SERVER_CONF.port)
        self.si_queue = 'si_requests_queue@' +\
                        ConfHelper.SI_SERVER_CONF.host + ':' +\
                        str(ConfHelper.SI_SERVER_CONF.port)
        self.gw_binding = 'gw_requests_binding@' +\
                          ConfHelper.GW_SERVER_CONF.host + ':' +\
                          str(ConfHelper.GW_SERVER_CONF.port)
        self.si_binding = 'si_requests_binding@' +\
                          ConfHelper.SI_SERVER_CONF.host + ':' +\
                          str(ConfHelper.SI_SERVER_CONF.port)

        self.heart_beat_queues = {} 
        self.heartbeat_threads = {} 

        self.connections = {}
        self.addresses = {}
        self.listen_fd, self.epoll_fd = self.get_socket()
        self.rabbitmq_connection, self.rabbitmq_channel = self.__connect_rabbitmq(ConfHelper.RABBITMQ_CONF.host)

    def __connect_rabbitmq(self, host):
        connection = None
        channel = None
        try:
            parameters = pika.ConnectionParameters(host=host)
            connection = BlockingConnection(parameters)
            # Write buffer exceeded warning threshold
            reconnect_rabbitmq = partial(self.__reconnect_rabbitmq, (host,))
            connection.add_backpressure_callback(reconnect_rabbitmq)
            channel = connection.channel()
            channel.exchange_declare(exchange=self.exchange,
                                     durable=False,
                                     auto_delete=True)
            channel.queue_declare(queue=self.si_queue,
                                  durable=False,
                                  exclusive=False,
                                  auto_delete=True)
            channel.queue_bind(exchange=self.exchange,
                               queue=self.si_queue,
                               routing_key=self.si_binding)
            logging.info("[SI] Create SI request queue: %s, binding: %s",
                         self.si_queue, self.si_binding)

        except:
            logging.exception("[SI] Connect Rabbitmq-server Error!")

        return connection, channel

    def __reconnect_rabbitmq(self, host=None):
        """
        This is for catching any unpredictable AMQPConnectionError.
        Release resource for reconnect. 
        """
        logging.debug("[SI] Reconnect rabbitmq...") 
        if not host:
            host = ConfHelper.RABBITMQ_CONF.host

        if self.rabbitmq_connection and self.rabbitmq_connection.is_open:
            self.rabbitmq_connection.close()

        try:
            self.rabbitmq_connection, self.rabbitmq_channel = self.__connect_rabbitmq(host)
            logging.info("[SI] Rabbitmq reconnected!")
        except:
            logging.exception("[SI] Connect rabbitmq error.")

    def get_socket(self):
        listen_fd = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        listen_fd.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listen_fd.bind((ConfHelper.SI_SERVER_CONF.host, ConfHelper.SI_SERVER_CONF.port))
        listen_fd.listen(ConfHelper.SI_SERVER_CONF.count)
        epoll_fd = None

        try:
            epoll_fd = select.epoll()
            epoll_fd.register(listen_fd.fileno(), select.EPOLLIN)
        except:
            logging.error("[SI]epoll error")
        
        return listen_fd, epoll_fd

    def activetest(self, fd, connection, channel):
        seq = str(int(time.time()*1000))[-4:]
        args = DotDict(seq=seq,
                       status=GFCode.SUCCESS)
        atc = ActiveTestComposer(args)
        logging.debug("[SI]-->%s:%s Active_test: %r",
                      self.addresses[fd][0], self.addresses[fd][1], atc.buf)
        request = DotDict(packet=atc.buf,
                          category='H')
        self.append_si_request(request)

    def __start_heartbeat_thread(self, fd):
        try:
            connection, channel = self.__connect_rabbitmq(host=ConfHelper.RABBITMQ_CONF.host)
        except AMQPConnectionError as e:
            logging.exception("[SI] Rabbitmq publish error: %s", e.args)

        heartbeat_thread = RepeatedTimer(15, self.activetest,
                                         args=(fd, connection, channel))
        self.heartbeat_threads[fd] = heartbeat_thread
        heartbeat_thread.start()
        logging.info("[SI]%s:%s Heartbeat thread is running...",
                     self.addresses[fd][0], self.addresses[fd][1])

    def __stop_heartbeat_thread(self, fd):
        heartbeat_thread = self.heartbeat_threads.get(fd)
        if heartbeat_thread is not None:
            heartbeat_thread.cancel()
            heartbeat_thread.join()
            logging.info("[SI]%s:%s STOP heartbeat thread.",
                         self.addresses[fd][0], self.addresses[fd][1])
            self.heartbeat_threads.pop(fd)

    def get_terminal_status(self, terminal_id):
        status = GFCode.SUCCESS 
        terminal_fd = None
        
        address_key = get_terminal_address_key(terminal_id)
        terminal_fd = self.redis.getvalue(address_key)
        if (not terminal_fd or terminal_fd == DUMMY_FD):
            terminal = self.db.get("SELECT id FROM T_TERMINAL_INFO"
                                   "  WHERE tid = %s",
                                   terminal_id) 
            if terminal:
                status = GFCode.TERMINAL_OFFLINE 
                self.db.execute("UPDATE T_TERMINAL_INFO"
                                "  SET login = %s"
                                "  WHERE id = %s",
                                TERMINAL_LOGIN.OFFLINE, terminal.id)
                terminal_sessionID_key = get_terminal_sessionID_key(terminal_id)
                terminal_status_key = get_terminal_address_key(terminal_id)
                keys = [terminal_sessionID_key, terminal_status_key]
                self.redis.delete(*keys)
                terminal_info_key = get_terminal_info_key(terminal_id)
                terminal_info = self.redis.getvalue(terminal_info_key)
                if terminal_info:
                    terminal_info['login'] = TERMINAL_LOGIN.OFFLINE
            else:
                status = GFCode.GF_NOT_ORDERED 
                    
        return terminal_fd, status
                        
    def recv_all(self, length, fd):
        """
        Circulation receiving packet until len(packet) == length
        avoid receiving half packet once.
        """
        ret_buf = ""

        try:
            while length:
                tmp_buf = self.connections[fd].recv(length)
                if not tmp_buf:
                    logging.warn("[SI]<--%s:%s Recv empty response of socket!",
                                 self.addresses[fd][0], self.addresses[fd][1])
                    raise socket.error(errno.EPIPE, "the pipe might be broken.") 
                ret_buf += tmp_buf 
                length -= len(tmp_buf)
        except socket.error as e:
            logging.exception("[SI]<--%s:%s sock recv error:%s",
                              self.addresses[fd][0], self.addresses[fd][1],
                              e.args)
            if isinstance(e.args, tuple):
                if e[0] != errno.EAGAIN: 
                    self.__close_fd(fd)
            raise
        except Exception as e:
            logging.exception("[SI]<--%s:%s unknown recv error:%s",
                              self.addresses[fd][0], self.addresses[fd][1],
                              e.args)

        return ret_buf

    def recv_response(self, fd):
        """ Get request from SI.
            workflow:
                get the length of packet first
                then recv left data of this packet
        """
        packet = ""

        header_len = GF.len[GF.gftype['packet_len']]

        header = self.recv_all(header_len, fd)
        if header:
            packet_len = int(struct.unpack('!' + GF.fmt[GF.gftype['packet_len']], header)[0])
            body = self.recv_all(packet_len - header_len, fd)
            packet = header + body 

        return packet 

    def send_request(self, fd, request):
        """
        @param fd: address of SI
               request: whole gf request
        """
        try:
            while len(request['packet']) > 0:
                logging.info("[SI]-->%s:%s Send:\n%r",
                             self.addresses[fd][0], self.addresses[fd][1],
                             request['packet'])
                str_len = self.connections[fd].send(request['packet'])
                request['packet'] = request['packet'][str_len:]
        except socket.error as e:
            logging.exception("[SI]-->%s:%s sock send error:%s",
                              self.addresses[fd][0], self.addresses[fd][1],
                              e.args)
            self.__close_fd(fd)
            raise 
        except Exception as e:
            logging.exception("[SI]-->%s:%s unknown send error:%s",
                              self.addresses[fd][0], self.addresses[fd][1],
                              e.args)
            self.__close_fd(fd)

        return len(request['packet'])

    def handle_response_from_si(self, fd, response):
        """
        @param fd: readable fd
               response: whole packet recv from SI.
        workflow:
            if recv login:
                start heart_beat thread for this fd
                start regist terminals to fd thread
            elif recv logout:
                unregist fd, and stop all threads, clear data
            elif recv send_data:
                send data to terminal
        """

        gf = GFCheck(response)
        gfheads = gf.heads
        gfdatas = gf.datas
        for gfhead, gfdata in zip(gfheads, gfdatas):
            if gfhead.command == '0001': # bind
                bp = BindParser(gfdata)
                success = bp.check(bp.gfbody)
                if success:
                    logging.info("[SI]<--%s:%s Bind success!",
                                 self.addresses[fd][0], self.addresses[fd][1])
                    args = DotDict(seq=gfhead.seq,
                                   status=GFCode.SUCCESS)
                    brc = BindRespComposer(args)
                    logging.debug("[SI]-->%s:%s Bind resp: %r",
                                  self.addresses[fd][0], self.addresses[fd][1],
                                  brc.buf)
                    request = DotDict(packet=brc.buf)
                    self.append_si_request(request)
                    self.__start_heartbeat_thread(fd)
                    fds = self.redis.getvalue('fds')
                    if fds:
                        fds = fds.append(fd)
                    else:
                        fds = [fd,]
                    self.redis.setvalue('fds', fds)
            elif gfhead.command == '0002': # unbind
                logging.debug("[SI]<--%s:%s UNBind: %r",
                              self.addresses[fd][0], self.addresses[fd][1],
                              response)
                args = DotDict(seq=gfhead.seq,
                               status=GFCode.SUCCESS)
                nbrc = UNBindRespComposer(args)
                logging.debug("[SI]-->%s:%s UNBind resp: %r",
                              self.addresses[fd][0], self.addresses[fd][1],
                              nbrc.buf)
                request = DotDict(packet=nbrc.buf,
                                  category='C')
                self.append_si_request(request)
            elif gfhead.command == '0010': # senddata
                sp = SendParser(gfdata)
                logging.debug("[SI]<--%s:%s SendData:\n %r",
                              self.addresses[fd][0], self.addresses[fd][1],
                              response)
                # check terminal_id, status
                terminal_id = sp.gfbody.Terminal_id.strip()
                clwc = S_CLWCheck(sp.gfbody.Content)
                terminal_type = clwc.head.command
                t_address, t_status = self.get_terminal_status(terminal_id)
                if (t_address and t_address != DUMMY_FD): 
                    request = DotDict(packet=sp.gfbody.Content,
                                      address=t_address)
                    self.append_gw_request(request)
                
                # response it.
                args = DotDict(seq=gfhead.seq,
                               status=t_status,
                               terminal_id=terminal_id,
                               type=terminal_type)
                src = SendRespComposer(args)
                logging.debug("[SI]-->%s:%s SendData_resp: %r",
                              self.addresses[fd][0], self.addresses[fd][1],
                              src.buf)
                request = DotDict(packet=src.buf)
                self.append_si_request(request)
            elif gfhead.command == '0012': # query_terminal
                qtp = QueryTerminalParser(gfdata)
                logging.debug("[SI]<--%s:%s QueryTerminal: %r",
                              self.addresses[fd][0], self.addresses[fd][1],
                              response)
                terminal_count = qtp.gfbody.terminal_count
                terminal_id = qtp.gfbody.terminal_id
                terminal_status = []
                for tid in terminal_id:
                    t_fd, t_status = self.get_terminal_status(tid)
                    terminal_status.append(t_status)
                args = DotDict(seq=gfhead.seq,
                               status=GFCode.SUCCESS,
                               terminal_count=terminal_count,
                               terminal_status=terminal_status)
                qtrc = QueryTerminalRespComposer(args)
                logging.debug("[SI]-->%s:%s QueryTerminal_resp: %s",
                              self.addresses[fd][0], self.addresses[fd][1],
                              qtrc.buf)
                request = DotDict(packet=qtrc.buf)
                self.append_si_request(request)
            elif gfhead.command == '1011': # upload_data_resp
                logging.debug("[SI]<--%s:%s Upload_data_resp:%r",
                              self.addresses[fd][0], self.addresses[fd][1],
                              response)
            elif gfhead.command == '1020': # active_test_response
                logging.debug("[SI]<--%s:%s Active_test_resp:%r",
                              self.addresses[fd][0], self.addresses[fd][1],
                              response)
                self.heart_beat_queues[fd] = []
            else:
                logging.exception("[SI]<--%s:%s unknown command:%r",
                                  self.addresses[fd][0], self.addresses[fd][1],
                                  response)

    def handle_requests_to_si(self, fd):
        """
        heartbeat: stop fd if have no response to heartbeat for 3 times.
        unbind: unregister fd
        other: send to SI 
        """
        try:
            method, header, body = self.rabbitmq_channel.basic_get(queue=self.si_queue)
            if method.NAME == 'Basic.GetEmpty':
                #print "demo_get: Empty Basic.Get Response (Basic.GetEmpty)"
                return
            self.rabbitmq_channel.basic_ack(delivery_tag=method.delivery_tag)
            request = json.loads(body)
            if request.get('category') == 'H': # heart_beat
                # send 3 times at most
                if not self.heart_beat_queues.has_key(fd):
                    self.heart_beat_queues[fd] = [request,]
                elif len(self.heart_beat_queues[fd]) < 3:
                    self.heart_beat_queues[fd].append(request)
                else: 
                    logging.warn("[SI]-->%s:%s heart_beat_queue is full, quit.", 
                                 self.addresses[fd][0], self.addresses[fd][1])
                    self.__stop_client(fd)
                    return 
            elif request.get('category') == 'C': # si unbind
                logging.warn("[SI]<--%s:%s UNBind.",
                             self.addresses[fd][0], self.addresses[fd][1])
            else:
                pass

            try:
                left_len = self.send_request(fd, request)
                if (request.get('category') == 'C' and left_len == 0):
                    # unbind, stop client fd
                    self.__stop_client(fd)
            except socket.error as e:
                logging.exception("[SI]-->%s:%s sock send error:%s",
                                  self.addresses[fd][0], self.addresses[fd][1],
                                  e.args)
                self.__stop_client(fd)

        except AMQPConnectionError as e:
            logging.exception("[SI] Rabbitmq consume error: %s", e.args)
            self.__reconnect_rabbitmq()
        except Exception as e:
            logging.exception("[SI] Unkown error: %s", e.args)

    def handle_si_connections(self):
        """
        main process
        all operations about socket: register fd, send request and recv
        response
        """
        while True:
            try:
                if not self.epoll_fd:
                    logging.error("[SI] epoll_fd is None.")
                    return
                epoll_list = self.epoll_fd.poll()
                for fd, events in epoll_list:
                    if fd == self.listen_fd.fileno():
                        conn, addr = self.listen_fd.accept()
                        logging.info("[SI] Accept connection from %s:%s, fd = %d",
                                     addr[0], addr[1], conn.fileno())
                        conn.setblocking(0)
                        self.epoll_fd.register(conn.fileno(), select.EPOLLIN | select.EPOLLET)
                        self.connections[conn.fileno()] = conn
                        self.addresses[conn.fileno()] = addr
                    elif select.EPOLLIN & events:
                        try:
                            response = self.recv_response(fd)
                        except socket.error, msg:
                            if msg.errno == errno.EAGAIN:
                                logging.warn("[SI]<--%s:%s Recv empty.",
                                             self.addresses[fd][0], self.addresses[fd][1])
                                self.epoll_fd.modify(fd, select.EPOLLET | select.EPOLLIN | select.EPOLLOUT) 
                            else:
                                self.__stop_client(fd)
                        else:
                            logging.info("[SI]<--%s:%s Recv:\n %r",
                                         self.addresses[fd][0], self.addresses[fd][1],
                                         response)
                            self.handle_response_from_si(fd, response)
                            self.epoll_fd.modify(fd, select.EPOLLET | select.EPOLLIN | select.EPOLLOUT) 
                    elif select.EPOLLOUT & events:
                        self.handle_requests_to_si(fd)
                        try:
                            self.epoll_fd.modify(fd, select.EPOLLET | select.EPOLLIN | select.EPOLLOUT) 
                        except:
                            # may si unbind or other error.
                            logging.error("[SI] the pipe might be broken.")
                                
                    elif select.EPOLLHUP & events:
                        self.__stop_client(fd)
                    else:
                        continue
            except select.error as e:
                logging.exception("[SI] select error: %s", e.args)
            except Exception as e:
                logging.exception("[SI] unknown error: %s", e.args)

    def append_gw_request(self, request):
        message = json.dumps(request)
        try:
            # make message not persistent
            properties = pika.BasicProperties(delivery_mode=1,)
            self.rabbitmq_channel.basic_publish(exchange=self.exchange,
                                                routing_key=self.gw_binding,
                                                body=message,
                                                properties=properties)
        except AMQPConnectionError as e:
            logging.exception("[SI] Rabbitmq publish error: %s", e.args)
            self.__reconnect_rabbitmq()

    def append_si_request(self, request):
        #si_fds = self.redis.getvalue('fds')
        #if si_fds:
        #    si_fd = si_fds[0]
        message = json.dumps(request)
        try:
            # make message not persistent
            properties = pika.BasicProperties(delivery_mode=1,)
            self.rabbitmq_channel.basic_publish(exchange=self.exchange,
                                                routing_key=self.si_binding,
                                                body=message,
                                                properties=properties)
        except AMQPConnectionError as e:
            logging.exception("[SI] Rabbitmq publish error: %s", e.args)
            self.__reconnect_rabbitmq()

    def __close_thread_by_fd(self, fd):
        if fd:
            self.__stop_heartbeat_thread(fd)
            if self.heart_beat_queues and self.heart_beat_queues.get(fd):
                self.heart_beat_queues.pop(fd)

    def __clear_mem_by_fd(self, fd):
        pass

    def __close_fd(self, fd):
        if fd and fd in self.connections:
            self.epoll_fd.unregister(fd)
            self.connections[fd].close()
            self.connections.pop(fd)

    def __close_main_socket(self):
        try:
            if self.epoll_fd:
                self.epoll_fd.unregister(self.listen_fd.fileno())
                self.epoll_fd.close()
                self.epoll_fd = None
            if self.listen_fd:
                self.listen_fd.close()
                self.listen_fd = None
        except:
            pass

    def __close_database(self):
        #TODO: should i do this? process db or gateway_server db is closed
        if self.db:
            self.db.close()

    def __stop_client(self, fd):
        self.__clear_mem_by_fd(fd) 
        self.__close_thread_by_fd(fd)
        self.__close_fd(fd)

    def __close_rabbitmq(self):
        if self.rabbitmq_connection and self.rabbitmq_connection.is_open:
            self.rabbitmq_channel.queue_delete(queue=self.si_queue)
            self.rabbitmq_connection.close()

    def stop(self):
        for fd in self.connections.keys():
            self.__stop_client(fd)
        self.redis.delete('fds')
        self.__close_main_socket()
        #self.__close_database()
        self.__close_rabbitmq()

    def __del__(self):
        self.stop()
