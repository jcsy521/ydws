# -*- coding: utf-8 -*-

import socket, select, errno 
import logging
import time
import Queue

from utils.dotdict import DotDict
from utils.repeatedtimer import RepeatedTimer
from utils.misc import get_terminal_address_key, get_alarm_status_key,\
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
        self.online_terminals = [] 
        self.memcached = None 
        self.db = None

        self.socket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((ConfHelper.GW_SERVER_CONF.host, ConfHelper.GW_SERVER_CONF.port))
        self.__start_check_heartbeat_thread()

    def recv(self, si_requests_queue, gw_requests_queue):
        try:
            while True:
                response, address = self.socket.recvfrom(1024)
                logging.info("[GW] recv: %s", response)
                if response:
                    self.handle_response_from_terminal(response,
                                                       address,
                                                       si_requests_queue,
                                                       gw_requests_queue)
        except socket.error as e:
            logging.exception("[GW]sock recv error: %s", e.args)
        except KeyboardInterrupt:
            logging.warn("[GW] Ctrl-C is pressed")
        except Exception as e:
            logging.exception("[GW] sock recv Exception:%s", e.args)
        finally:
            self.stop()

    def send(self, gw_requests_queue):
        try:
            while True:
                try:
                    request = gw_requests_queue.get(True, 1)
                    self.socket.sendto(request.packet, request.address)
                    logging.info("[GW] send: %s", request.packet)
                except Queue.Empty:
                    pass
        except socket.error as e:
            logging.exception("[GW]sock error: %s", e.args)
        except KeyboardInterrupt:
            logging.warn("[GW] Ctrl-C is pressed")
        except Exception as e:
            logging.exception("[GW] Main socket Exception:%s", e.args)
        finally:
            self.stop()
        
    def handle_response_from_terminal(self, response, address, si_requests_queue, gw_requests_queue):
         try:
             clw = T_CLWCheck(response)
             for packet_info in clw.packets_info:
                 if packet_info.head.type == T_MESSAGE_TYPE.LOGIN:
                     logging.info("[GW] Recv login message:\n%s", packet_info.message)
                     self.handle_login(packet_info.head, packet_info.body,
                                       address, gw_requests_queue) 
                 elif packet_info.head.type == T_MESSAGE_TYPE.HEARTBEAT:
                     logging.info("[GW] Recv heartbeat message:\n%s", packet_info.message)
                     self.handle_heartbeat(packet_info.head, packet_info.body,
                                           address, gw_requests_queue)
                 else:
                     logging.info("[GW] Recv message from terminal:\n%s", packet_info.message)
                     self.foward_packet_to_si(packet_info, packet_info.message, address,
                                              si_requests_queue, gw_requests_queue)
         except:
             logging.exception("[GW] Recv Exception.")

    def handle_login(self, t_info, content, address, gw_requests_queue):
        try:
            args = DotDict(success=LOGIN_SUCCESS,
                           info="0")
            lp = LoginParser(content)
            t_info.update(lp.ret) 
                    
            try:
                if t_info["u_msisdn"] and t_info["t_msisdn"]:
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
                                    "         NULL, NULL, NULL, DEFAULT, DEFAULT,"
                                    "         NULL, NULL, DEFAULT, NULL)"
                                    "  ON DUPLICATE KEY"
                                    "    UPDATE tid = VALUES(tid),"
                                    "           imsi = VALUES(imsi),"
                                    "           imei = VALUES(imei),"
                                    "           factory_name = VALUES(factory_name)",
                                    t_info["dev_id"], t_info["imsi"],
                                    t_info["imei"], t_info["factory_name"])
                else:
                    args.success = LOGIN_FAILD
                    logging.error("[GW] login terminal miss sim or owner_mobile information")
            except:
                args.success = LOGIN_FAILD
                args.info = "1"
                logging.exception("[GW] %s login Faild.", t_info["dev_id"])

            if args.success == LOGIN_SUCCESS:
                self.update_terminal_status(t_info["dev_id"], address)
                self.update_login_status(t_info["dev_id"], LOGIN_SUCCESS)
                if not t_info["dev_id"] in self.online_terminals:
                    self.online_terminals.append(t_info["dev_id"])
                logging.info("[GW] %s login success!", t_info['dev_id'])

            lc = LoginRespComposer(args)
            request = DotDict(packet=lc.buf,
                              address=address)
            gw_requests_queue.put(request)
        except:
            logging.exception("[GW] Hand login exception.")
        
    def handle_heartbeat(self, heartbeat_info, content, address, gw_requests_queue):
        try:
            terminal_status = self.get_terminal_status(heartbeat_info.dev_id)
            if terminal_status:
                hp = HeartbeatParser(content)
                heartbeat_info.update(hp.ret) 
                hc = HeartbeatRespComposer()
                request = DotDict(packet=hc.buf,
                                  address=address)
                self.update_terminal_status(heartbeat_info.dev_id, address)
                self.update_terminal_info(heartbeat_info)
                gw_requests_queue.put(request)
            else:
                logging.error("[GW] Invalid heartbeat request from: %s", heartbeat_info.dev_id) 
        except:
            logging.exception("[GW] Hand heartbeat exception.")

    def foward_packet_to_si(self, packet, response, address, si_requests_queue, gw_requests_queue):
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
                self.update_terminal_status(dev_id, address)
                if packet.head.type == T_MESSAGE_TYPE.POSITION:
                    rc = PositionRespComposer()
                    request = DotDict(packet=rc.buf,
                                      address=address)
                    gw_requests_queue.put(request)
                    ap = AsyncParser(packet.body, packet.head)
                    position = ap.ret
                    status = int(position['status'], 16)
                    if status & 255 != 255:
                        if status & 512 != 0:
                            self.update_terminal_status(dev_id, DUMMY_FD, False)
                        if status & 2 == 0:
                            self.update_terminal_defend_status(dev_id)
                        elif status & 2 == 2:
                            self.update_terminal_defend_status(dev_id, False)
            else:
                logging.error("[GW] Invalid terminal request from: %s", packet.head.dev_id) 
        except:
            logging.exception("[GW] Handle SI message exception.")

    def append_si_request(self, request, si_requests_queue):
        si_fds = self.memcached.get('fds')
        if si_fds:
            si_fd = si_fds[0]
            request = dict({"packet":request})
            si_requests_queue.put(request, False)

    def update_terminal_status(self, dev_id, address, flag=True):
        terminal_status_key = get_terminal_address_key(dev_id)
        if flag:
            self.memcached.set(terminal_status_key, address, 2*HEARTBEAT_INTERVAL)
        else:
            self.memcached.set(terminal_status_key, address, 2*SLEEP_HEARTBEAT_INTERVAL)

    def update_terminal_info(self, t_info):
        self.db.execute("UPDATE T_TERMINAL_INFO_R"
                        "  SET gps_num = %s,"
                        "  volume = %s,"
                        "  gsm = %s"
                        "  WHERE tid = %s",
                        t_info['GPS'], t_info['POWER'], 
                        t_info['GSM'], t_info['dev_id'])

    def update_terminal_defend_status(self, dev_id, flag=True):
        defend_status = 1
        if not flag:
            defend_status = 0
        self.db.execute("UPDATE T_TERMINAL_INFO_W"
                        "  SET defend_status = %s"
                        "  WHERE tid = %s",
                        defend_status, dev_id)
 
    def get_terminal_status(self, dev_id):
        terminal_status_key = get_terminal_address_key(dev_id)
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
                    status = self.get_terminal_status(dev_id)
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

    def __close_socket(self):
        try:
            self.socket.close()
        except:
            logging.exception("[GW] Close socket Exception.")

    def __clear_memcached(self, dev_id=None):
        pass

    def stop(self):
        self.__close_socket()
        self.__stop_check_heartbeat_thread()
        self.__clear_memcached()

    def __del__(self):
        self.stop()
