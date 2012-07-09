# -*- coding: utf-8 -*-

import socket, select, errno 
import logging
import time

from utils.dotdict import DotDict
from utils.repeatedtimer import RepeatedTimer
from utils.misc import get_gw_fd_key, get_gw_requests_key, get_alarm_status_key,\
     get_terminal_time
from constants.GATEWAY import T_MESSAGE_TYPE, S_MESSAGE_TYPE, HEARTBEAT_INTERVAL,\
     LOGIN_SUCCESS, LOGIN_FAILD, SLEEP_HEARTBEAT_INTERVAL, DUMMY_FD
from constants.MEMCACHED import ALIVED
from constants import EVENTER
from codes.smscode import SMSCode

from helpers.seqgenerator import SeqGenerator
from helpers.confhelper import ConfHelper
from helpers.queryhelper import QueryHelper
from helpers.smshelper import SMSHelper
  
from clw.packet.parser.codecheck import T_CLWCheck 
from clw.packet.parser.login import LoginParser
from clw.packet.parser.heartbeat import HeartbeatParser 
from clw.packet.parser.async import AsyncParser
from clw.packet.composer.login import LoginRespComposer
from clw.packet.composer.heartbeat import HeartbeatRespComposer
from clw.packet.composer.position import PositionRespComposer
from gf.packet.composer.uploaddatacomposer import UploadDataComposer

class GatewayServer(object):

    def __init__(self, conf_file):
        ConfHelper.load(conf_file)
        for i in ('port', 'count', 'check_heartbeat_interval'):
            ConfHelper.GW_SERVER_CONF[i] = int(ConfHelper.GW_SERVER_CONF[i])
        self.check_heartbeat_thread = None
        self.connections = {}
        self.online_terminals = [] 
        self.epoll_fd = None
        self.memcached = None 
        self.db = None

    def handle_terminal_connections(self, si_requests_queue):
        try:
            listen_fd = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
            listen_fd.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            listen_fd.bind((ConfHelper.GW_SERVER_CONF.host, ConfHelper.GW_SERVER_CONF.port))
            listen_fd.listen(ConfHelper.GW_SERVER_CONF.count)
            self.epoll_fd = select.epoll()
            self.epoll_fd.register(listen_fd.fileno(), select.EPOLLIN | select.EPOLLET)
            self.__start_check_heartbeat_thread()

            while True:
                epoll_list = self.epoll_fd.poll()
                for fd, events in epoll_list:
                    if fd == listen_fd.fileno():
                        conn, addr = listen_fd.accept()
                        conn.setblocking(0)
                        self.epoll_fd.register(conn.fileno(), select.EPOLLIN | select.EPOLLET)
                        self.connections[conn.fileno()] = conn
                    elif select.EPOLLIN & events:
                        responses = ''
                        while True:
                            try:
                                response = self.connections[fd].recv(1024)
                                if not response and not responses:
                                    self.__close_socket(fd)
                                    break
                                else:
                                    responses += response
                            except socket.error, msg:
                                if msg.errno == errno.EAGAIN:
                                    if responses:
                                        self.handle_response_from_terminal(responses, fd, si_requests_queue)

                                    if fd in self.connections.keys():
                                        self.epoll_fd.modify(fd, select.EPOLLET | select.EPOLLOUT | select.EPOLLIN)
                                    else:
                                        logging.warn("[GW] socket has been closed, fd:%s", fd)
                                    break
                                else:
                                    self.__close_socket(fd)
                                    break 
                    elif select.EPOLLOUT & events:
                         self.handle_request_to_terminal(fd)
                    elif select.EPOLLHUP & events:
                        self.__close_socket(fd)
                    else:
                        continue
        except KeyboardInterrupt:
            logging.warn("[GW] Ctrl-C is pressed")
        except Exception as e:
            logging.exception("[GW] Main socket Exception:%s", e.args)
        finally:
            self.stop()

    def handle_request_to_terminal(self, fd):
        try:
            request = ""
            fd_request_key = get_gw_requests_key(fd)
            requests = self.memcached.get(fd_request_key) 
            conn = self.connections[fd]
            try:
                if conn and requests:
                    for request in requests:
                        logging.info("[GW] Send data:%s", request)
                        conn.send(request) 
                    self.memcached.delete(fd_request_key)
                self.epoll_fd.modify(fd, select.EPOLLIN | select.EPOLLET | select.EPOLLOUT)
            except:
                self.__close_socket(fd)
        except:
            logging.exception("[GW] Send Exception.") 

    def handle_response_from_terminal(self, response, fd, si_requests_queue):
         try:
             clw = T_CLWCheck(response)
             for packet_info in clw.packets_info:
                 if packet_info.head.type == T_MESSAGE_TYPE.LOGIN:
                     logging.info("[GW] Recv login message:\n%s", packet_info.message)
                     self.handle_login(packet_info.head, packet_info.body, fd) 
                 elif packet_info.head.type == T_MESSAGE_TYPE.HEARTBEAT:
                     logging.info("[GW] Recv heartbeat message:\n%s", packet_info.message)
                     self.handle_heartbeat(packet_info.head, packet_info.body, fd)
                 else:
                     logging.info("[GW] Recv message from terminal:\n%s", packet_info.message)
                     self.foward_packet_to_si(packet_info, packet_info.message, fd, si_requests_queue)
         except:
             logging.exception("[GW] Recv Exception.")

    def handle_login(self, t_info, content, fd):
        try:
            args = DotDict(success=LOGIN_SUCCESS,
                           info="0")
            lp = LoginParser(content)
            t_info.update(lp.ret) 
                    
            try:
                self.db.execute("INSERT INTO T_TERMINAL_INFO_W"
                                "  (id, tid, mobile, owner_mobile, psw)"
                                "  VALUES(NULL, %s, %s, %s, %s)"
                                "  ON DUPLICATE KEY"
                                "    UPDATE tid = VALUES(tid),"
                                "    mobile = VALUES(mobile),"
                                "    owner_mobile = VALUES(owner_mobile),"
                                "    psw = VALUES(psw)",
                                t_info["dev_id"], t_info["t_msisdn"],
                                t_info["u_msisdn"], t_info["passwd"])

                self.db.execute("INSERT INTO T_TERMINAL_INFO_R"
                                "  VALUES(NULL, %s, %s, %s, %s,"
                                "         NULL, NULL, NULL, NULL, NULL,"
                                "         DEFAULT, NULL)"
                                "  ON DUPLICATE KEY"
                                "    UPDATE tid = VALUES(tid),"
                                "           imsi = VALUES(imsi),"
                                "           imei = VALUES(imei),"
                                "           factory_name = VALUES(factory_name)",
                                t_info["dev_id"], t_info["imsi"],
                                t_info["imei"], t_info["factory_name"])
            except:
                args.success = LOGIN_FAILD
                args.info = "1"
                logging.exception("[GW] %s login Faild.", t_info["dev_id"])

            if args.success == LOGIN_SUCCESS:
                self.update_terminal_status(t_info["dev_id"], fd)
                self.update_login_status(t_info["dev_id"], LOGIN_SUCCESS)
                if not t_info["dev_id"] in self.online_terminals:
                    self.online_terminals.append(t_info["dev_id"])
                logging.info("[GW] %s login success!", t_info['dev_id'])

            lc = LoginRespComposer(args)
            request = lc.buf
            self.append_gw_request(request, fd)
        except:
            logging.exception("[GW] Hand login exception.")
        
    def handle_heartbeat(self, heartbeat_info, content, fd):
        try:
            terminal_status = self.get_terminal_status(heartbeat_info.dev_id)
            if terminal_status:
                hp = HeartbeatParser(content)
                heartbeat_info.update(hp.ret) 
                hc = HeartbeatRespComposer()
                request = hc.buf
                self.update_terminal_status(heartbeat_info.dev_id, fd)
                self.append_gw_request(request, fd)
            else:
                self.__close_socket(fd)
        except:
            logging.exception("[GW] Hand heartbeat exception.")

    def foward_packet_to_si(self, packet, response, fd, si_requests_queue):
        try:
            terminal_status = self.get_terminal_status(packet.head.dev_id)
            if terminal_status:
                dev_id = packet.head.dev_id
                args = DotDict(seq=SeqGenerator.next(self.db),
                               dev_id=dev_id,
                               content=response)
                content = UploadDataComposer(args).buf
                logging.info("[GW] Forward message to SI:\n%s", content)
                self.append_si_request(content, si_requests_queue)
                self.update_terminal_status(dev_id, fd)
                if packet.head.type == T_MESSAGE_TYPE.POSITION:
                    rc = PositionRespComposer()
                    request = rc.buf
                    self.append_gw_request(request, fd)
                    ap = AsyncParser(packet.body, packet.head)
                    position = ap.ret
                    if position['status'] in ('4', '5'):
                        self.update_terminal_status(dev_id, DUMMY_FD, False)
            else:
                self.__close_socket(fd)
        except:
            logging.exception("[GW] Handle SI message exception.")

    def append_gw_request(self, request, fd):
        fd_request_key = get_gw_requests_key(fd)
        requests = self.memcached.get(fd_request_key)
        if not requests:
            requests = [request,]
        else:
            requests.append(request)
        self.memcached.set(fd_request_key, requests)
 
    def append_si_request(self, request, si_requests_queue):
        si_fds = self.memcached.get('fds')
        if si_fds:
            si_fd = si_fds[0]
            request = dict({"packet":request})
            si_requests_queue.put(request, False)

        # si_key = get_si_fd_key(dev_id)
        # si_fd = self.memcached.get(si_key) 
        # if si_fd:
        #     si_request_key = get_si_requests_key(si_fd)
        #     requests = self.memcached.get(si_request_key)
        #     request = dict({"packet":request})
        #     if not requests:
        #         requests = [request,]
        #     else:
        #         requests.append(request)
        #     self.memcached.set(si_request_key, requests)

    def update_terminal_status(self, dev_id, fd, flag=True):
        terminal_status_key = get_gw_fd_key(dev_id)
        if flag:
            self.memcached.set(terminal_status_key, fd, 2*HEARTBEAT_INTERVAL)
        else:
            self.memcached.set(terminal_status_key, fd, 2*SLEEP_HEARTBEAT_INTERVAL)
 
    def get_terminal_status(self, dev_id):
        terminal_status_key = get_gw_fd_key(dev_id)
        return self.memcached.get(terminal_status_key)

    def update_login_status(self, dev_id, login):
        try:
            self.db.execute("UPDATE T_TERMINAL_INFO_R"
                            "  SET login = %s"
                            "  WHERE tid = %s",
                            login, dev_id)
        except:
            logging.exception("[GW] Update login status exception")

    def check_heartbeat(self):
        try:
            is_alived = self.memcached.get("is_alived")
            if is_alived == ALIVED:
                for dev_id in self.online_terminals:
                    terminal_status_key = get_gw_fd_key(dev_id)
                    status = self.memcached.get(terminal_status_key)
                    if not status:
                        self.heartbeat_lost_report(dev_id)
                        self.update_login_status(dev_id, LOGIN_FAILD)
        except:
            logging.exception("[GW] Check gateway heartbeat exception.")
                
    def heartbeat_lost_report(self, dev_id):
        timestamp = int(time.time() * 1000)
        rname = EVENTER.RNAME.HEARTBEAT_LOST
        category = EVENTER.CATEGORY[rname]
        lid = self.db.execute("INSERT INTO T_LOCATION(tid, timestamp, category, type)"
                              "  VALUES(%s, %s, %s, %s)",
                              dev_id, timestamp, category, 1)
        self.db.execute("INSERT INTO T_EVENT"
                        "  VALUES (NULL, %s, %s, %s)",
                        dev_id, lid, category)
        alarm_key = get_alarm_status_key(dev_id)
        alarm_status = self.memcached.get(alarm_key)
        if alarm_status != rname: 
            self.memcached.set(alarm_key, category) 
        user = QueryHelper.get_umobile_by_dev_id(dev_id, self.db)
        current_time = get_terminal_time(timestamp) 
        sms = SMSCode.SMS_HEARTBEAT_LOST % (dev_id, current_time)
        if user:
            SMSHelper.send(user.owner_mobile, sms)
            logging.warn("[GW] Terminal %s Heartbeat lost report:\n%s", dev_id, sms)
        self.online_terminals.remove(dev_id)

    def __start_check_heartbeat_thread(self):
        self.check_heartbeat_thread = RepeatedTimer(ConfHelper.GW_SERVER_CONF.check_heartbeat_interval,
                                                    self.check_heartbeat)
        self.check_heartbeat_thread.start()
        logging.info("[GW] Check heartbeat thread is running...")

    def __stop_check_heartbeat_thread(self):
        if self.check_heartbeat_thread is not None:
            self.check_heartbeat_thread.cancel()
            self.check_heartbeat_thread.join()
            logging.info("[GW] Check heartbeat stop.")
            self.check_heartbeat_thread = None

    def __close_socket(self, fd):
        try:
            self.epoll_fd.unregister(fd)
            self.connections[fd].close()
            del self.connections[fd]
            self.__clear_memcached(fd)
        except:
            logging.exception("[GW] Close socket Exception.")

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

    def __clear_memcached(self, fd, dev_id=None):
        try:
            fd_request_key = get_gw_requests_key(fd)
            self.memcached.delete(fd_request_key)
        except:
            logging.exception("[GW] Clear memcached datas exception.")

    def stop(self):
        for fd in self.connections.keys():
            self.__close_socket(fd)
        self.__stop_check_heartbeat_thread()
        self.__close_main_socket()

    def __del__(self):
        self.stop()
