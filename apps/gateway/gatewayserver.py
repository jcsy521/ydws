# -*- coding: utf-8 -*-

import socket, select, errno 
import logging
import time
import Queue
import base64

from utils.dotdict import DotDict
from utils.repeatedtimer import RepeatedTimer
from utils.misc import get_terminal_address_key, get_alarm_status_key,\
     get_terminal_time, get_sessionID, get_terminal_sessionID_key
from constants.GATEWAY import T_MESSAGE_TYPE, S_MESSAGE_TYPE, HEARTBEAT_INTERVAL,\
     LOGIN_STATUS, SLEEP_HEARTBEAT_INTERVAL, DUMMY_FD
from constants.MEMCACHED import ALIVED
from constants import EVENTER, GATEWAY
from codes.smscode import SMSCode
from codes.clwcode import CLWCode

from helpers.seqgenerator import SeqGenerator
from helpers.confhelper import ConfHelper
from helpers.queryhelper import QueryHelper
from helpers.smshelper import SMSHelper
from helpers import lbmphelper
  
from clw.packet.parser.codecheck import T_CLWCheck 
from clw.packet.parser.login import LoginParser
from clw.packet.parser.heartbeat import HeartbeatParser 
from clw.packet.parser.async import AsyncParser
from clw.packet.parser.locationdesc import LocationDescParser
from clw.packet.composer.login import LoginRespComposer
from clw.packet.composer.heartbeat import HeartbeatRespComposer
from clw.packet.composer.async import AsyncRespComposer
from clw.packet.composer.locationdesc import LocationDescRespComposer
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
        print ConfHelper.GW_SERVER_CONF.host, ConfHelper.GW_SERVER_CONF.port
        self.socket.bind((ConfHelper.GW_SERVER_CONF.host, ConfHelper.GW_SERVER_CONF.port))
        self.__start_check_heartbeat_thread()

    def recv(self, si_requests_queue, gw_requests_queue):
        try:
            while True:
                response, address = self.socket.recvfrom(1024)
                logging.info("[GW] recv: %s from %s", response, address)
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
                    logging.info("[GW] send: %s to %s", request.packet, request.address)
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
                 print 'head: ', packet_info.head
                 print 'body: ', packet_info.body
                 if packet_info.head.command == T_MESSAGE_TYPE.LOGIN:
                     logging.info("[GW] Recv login message:\n%s", packet_info.message)
                     self.handle_login(packet_info.head, packet_info.body,
                                       address, gw_requests_queue) 
                 elif packet_info.head.command == T_MESSAGE_TYPE.HEARTBEAT:
                     logging.info("[GW] Recv heartbeat message:\n%s", packet_info.message)
                     self.handle_heartbeat(packet_info.head, packet_info.body,
                                           address, gw_requests_queue)
                 elif packet_info.head.command == T_MESSAGE_TYPE.LOCATIONDESC:
                     logging.info("[GW] Recv locationdesc message:\n%s", packet_info.message)
                     self.handle_locationdesc(packet_info.head, packet_info.body,
                                              address, gw_requests_queue)
                 else:
                     logging.info("[GW] Recv message from terminal:\n%s", packet_info.message)
                     self.foward_packet_to_si(packet_info, packet_info.message, address,
                                              si_requests_queue, gw_requests_queue)
         except:
             logging.exception("[GW] Recv Exception.")

    def handle_locationdesc(self, head, body, address, gw_requests_queue):
        try:
            args = DotDict(success="0",
                           locationdesc="")
            ldp = LocationDescParser(body, head)
            location = ldp.ret
            location['valid'] = CLWCode.LOCATION_SUCCESS
            location['t'] = EVENTER.INFO_TYPE.POSITION
            location = lbmphelper.handle_location(location, self.memcached)
            locationdesc = unicode(location.name)
            locationdesc = locationdesc.encode("utf-8", 'ignore')
            args.locationdesc = base64.b64encode(locationdesc)
            lc = LocationDescRespComposer(args)
            request = DotDict(packet=lc.buf,
                              address=address)
            gw_requests_queue.put(request)
        except:
            logging.exception("[GW] Handle locationdesc exception.")

    def handle_login(self, head, body, address, gw_requests_queue):
        try:
            args = DotDict(success=LOGIN_STATUS.SUCCESS,
                           sessionID='')
            lp = LoginParser(body, head)
            t_info = lp.ret
                    
            if t_info['u_msisdn'] and t_info['t_msisdn']:
                terminal = self.db.get("SELECT * FROM T_TERMINAL_INFO"
                                       "  WHERE tid = %s",
                                       t_info['dev_id'])
                if terminal:
                    #TODO 服务到期？？
                    if (terminal.endtime < time.time() or
                        terminal.service_status == '0'):
                        args.success = LOGIN_STATUS.EXPIRED
                        logging.error("[GW] Terminal %s expired!", t_info['t_msisdn'])
                    elif terminal.mobile != t_info['t_msisdn']:
                        # illegal sim
                        args.success = LOGIN_STATUS.ILLEGAL_SIM
                    elif (terminal.owner_mobile != t_info['u_msisdn'] or
                          terminal.imsi != t_info['imsi'] or
                          terminal.imei != t_info['imei'] or
                          terminal.factory_name != t_info['factory_name']):
                        self.db.execute("UPDATE T_TEMINAL_INFO"
                                        "  SET owner_mobile = %s"
                                        "      imsi = %s"
                                        "      imei = %s"
                                        "      factory_name = %s",
                                        t_info['u_msisdn'],
                                        t_info['imsi'],
                                        t_info['imei'],
                                        t_info['factory_name']) 
                        logging.info("[GW] Terminal %s changes info! old_info: %s, new_info: %s",
                                     t_info['t_msisdn'], terminal, t_info)
                    else:
                        pass
                else:
                    self.db.execute("INSERT INTO T_TERMINAL_INFO"
                                    "  (id, tid, mobile, owner_mobile, imsi, imei, factory_name)"
                                    "  VALUES(NULL, %s, %s, %s, %s, %s, %s)",
                                    t_info['dev_id'], t_info['t_msisdn'],
                                    t_info['u_msisdn'], t_info['imsi'],
                                    t_info['imei'], t_info['factory_name'])
                    logging.info("[GW] New terminal %s Regists!", t_info['t_msisdn'])
            else:
                args.success = LOGIN_STATUS.UNREGISTER 
                logging.error("[GW] login terminal %s miss sim or owner_mobile information",
                              t_info['dev_id'])

            if args.success == LOGIN_STATUS.SUCCESS:
                #args.sessionID = get_sessionID()
                args.sessionID = '1a2b3c4d'
                terminal_sessionID_key = get_terminal_sessionID_key(t_info['dev_id'])
                self.memcached.set(terminal_sessionID_key, args.sessionID)

                self.update_terminal_status(t_info["dev_id"], address)
                self.update_login_status(t_info["dev_id"], LOGIN_STATUS.SUCCESS)
                if not t_info["dev_id"] in self.online_terminals:
                    self.online_terminals.append(t_info["dev_id"])
                logging.info("[GW] %s login success!", t_info['dev_id'])

            lc = LoginRespComposer(args)
            request = DotDict(packet=lc.buf,
                              address=address)
            gw_requests_queue.put(request)
        except:
            logging.exception("[GW] Hand login exception.")
        
    def handle_heartbeat(self, head, body, address, gw_requests_queue):
        try:
            args = DotDict(success="0")
            sessionID = self.get_terminal_sessionID(head.dev_id)
            if sessionID != head.sessionID:
                args.success = "1"
            else:
                terminal_status = self.get_terminal_status(head.dev_id)
                if terminal_status:
                    hp = HeartbeatParser(body, head)
                    heartbeat_info = hp.ret 
                    self.update_terminal_status(head.dev_id, address)
                    self.update_terminal_info(heartbeat_info)
                else:
                    args.success = "1"
                    logging.error("[GW] Invalid heartbeat request from: %s", head.dev_id) 
            hc = HeartbeatRespComposer(args)
            request = DotDict(packet=hc.buf,
                              address=address)
            gw_requests_queue.put(request)
        except:
            logging.exception("[GW] Hand heartbeat exception.")

    def foward_packet_to_si(self, packet, response, address, si_requests_queue, gw_requests_queue):
        try:
            args = DotDict(success="0",
                           command=packet.head.command)
            dev_id = packet.head.dev_id
            sessionID = self.get_terminal_sessionID(dev_id)
            if sessionID != packet.head.sessionID:
                args.success = "1"
                logging.error("[GW] Invalid sessionID, packet: %s", response)
            else:
                terminal_status = self.get_terminal_status(dev_id)
                if terminal_status:
                    uargs = DotDict(seq=SeqGenerator.next(self.db),
                                    dev_id=dev_id,
                                    content=response)
                    content = UploadDataComposer(uargs).buf
                    logging.info("[GW] Forward message to SI:\n%s", content)
                    self.append_si_request(content, si_requests_queue)
                    self.update_terminal_status(dev_id, address)
                else:
                    args.success = "1"
                    logging.error("[GW] Invalid packet: %s", response)

            rc = AsyncRespComposer(args)
            request = DotDict(packet=rc.buf,
                              address=address)
            gw_requests_queue.put(request)
        except:
            logging.exception("[GW] Handle SI message exception.")

    def append_si_request(self, request, si_requests_queue):
        si_fds = self.memcached.get('fds')
        if si_fds:
            si_fd = si_fds[0]
            request = dict({"packet":request})
            si_requests_queue.put(request, False)

    def get_terminal_sessionID(self, dev_id):
        terminal_sessionID_key = get_terminal_sessionID_key(dev_id) 
        sessionID = self.memcached.get(terminal_sessionID_key)

        return sessionID

    def update_terminal_status(self, dev_id, address, flag=True):
        terminal_status_key = get_terminal_address_key(dev_id)
        if flag:
            self.memcached.set(terminal_status_key, address, 2*HEARTBEAT_INTERVAL)
        else:
            self.memcached.set(terminal_status_key, address, 2*SLEEP_HEARTBEAT_INTERVAL)

    def update_terminal_info(self, t_info):
        self.db.execute("UPDATE T_TERMINAL_INFO"
                        "  SET gps = %s,"
                        "      gsm = %s,"
                        "      pbat = %s"
                        "  WHERE tid = %s",
                        t_info['gps'], t_info['gsm'], 
                        t_info['pbat'], t_info['dev_id'])

    def get_terminal_status(self, dev_id):
        terminal_status_key = get_terminal_address_key(dev_id)
        return self.memcached.get(terminal_status_key)

    def update_login_status(self, dev_id, login):
        try:
            self.db.execute("UPDATE T_TERMINAL_INFO"
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
        #timestamp = int(time.time() * 1000)
        #rname = EVENTER.RNAME.HEARTBEAT_LOST
        #category = EVENTER.CATEGORY[rname]
        #lid = self.db.execute("INSERT INTO T_LOCATION(tid, timestamp, category, type)"
        #                      "  VALUES(%s, %s, %s, %s)",
        #                      dev_id, timestamp, category, 1)
        #self.db.execute("INSERT INTO T_EVENT"
        #                "  VALUES (NULL, %s, %s, %s)",
        #                dev_id, lid, category)
        #alarm_key = get_alarm_status_key(dev_id)
        #alarm_status = self.memcached.get(alarm_key)
        #if alarm_status != rname: 
        #    self.memcached.set(alarm_key, category) 
        #user = QueryHelper.get_umobile_by_dev_id(dev_id, self.db)
        #current_time = get_terminal_time(timestamp) 
        #sms = SMSCode.SMS_HEARTBEAT_LOST % (dev_id, current_time)
        #if user:
        #    SMSHelper.send(user.owner_mobile, sms)
        #    logging.warn("[GW] Terminal %s Heartbeat lost report:\n%s", dev_id, sms)
        logging.error("[GW] Terminal %s Heartbeat lost!!!", dev_id)
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
