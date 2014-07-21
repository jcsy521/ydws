# -*- coding: utf-8 -*-

import socket, select, errno 

import os
import logging
import time
from time import sleep
import datetime
from dateutil.relativedelta import relativedelta
import base64
import pika
from pika.adapters import *
from pika.exceptions import AMQPConnectionError, AMQPChannelError
import json
from functools import partial
from Queue import Queue, Empty
import thread
import multiprocessing

from tornado.escape import json_decode
from tornado.ioloop import IOLoop

from utils.dotdict import DotDict
from utils.repeatedtimer import RepeatedTimer
from utils.checker import check_phone, check_zs_phone
from db_.mysql import DBConnection
from utils.myredis import MyRedis
from utils.misc import (get_terminal_address_key, get_terminal_sessionID_key,
     get_terminal_info_key, get_lq_sms_key, get_lq_interval_key, get_location_key,
     get_terminal_time, get_sessionID, safe_unicode, get_psd, get_offline_lq_key,
     get_resend_key, get_lastinfo_key, get_login_time_key, get_acc_status_info_key)
from utils.public import insert_location, delete_terminal, record_add_action, get_terminal_type_by_tid,\
     clear_data
from constants.GATEWAY import T_MESSAGE_TYPE, HEARTBEAT_INTERVAL,\
     SLEEP_HEARTBEAT_INTERVAL
from constants.MEMCACHED import ALIVED
from constants import EVENTER, GATEWAY, UWEB, SMS
from codes.smscode import SMSCode

from helpers.seqgenerator import SeqGenerator
from helpers.confhelper import ConfHelper
from helpers.queryhelper import QueryHelper
from helpers.smshelper import SMSHelper
from helpers.lbmpsenderhelper import LbmpSenderHelper
from helpers.urlhelper import URLHelper
from helpers.uwebhelper import UWebHelper
from helpers import lbmphelper
  
from clw.packet.parser.codecheck import T_CLWCheck 
from clw.packet.parser.login import LoginParser
from clw.packet.parser.heartbeat import HeartbeatParser 
from clw.packet.parser.async import AsyncParser
from clw.packet.parser.config import ConfigParser
from clw.packet.parser.fobinfo import FobInfoParser
from clw.packet.parser.locationdesc import LocationDescParser
from clw.packet.parser.unbind import UNBindParser
from clw.packet.parser.unusualactivate import UnusualActivateParser
from clw.packet.parser.misc import MiscParser
from clw.packet.parser.acc_status import ACCStatusParser
from clw.packet.composer.login import LoginRespComposer
from clw.packet.composer.heartbeat import HeartbeatRespComposer
from clw.packet.composer.async import AsyncRespComposer
from clw.packet.composer.runtime import RuntimeRespComposer
from clw.packet.composer.locationdesc import LocationDescRespComposer
from clw.packet.composer.config import ConfigRespComposer
from clw.packet.composer.fobinfo import FobInfoRespComposer
from clw.packet.composer.unbind import UNBindComposer
from clw.packet.composer.unusualactivate import UnusualActivateComposer
from clw.packet.composer.misc import MiscComposer
from clw.packet.composer.acc_status import ACCStatusComposer
from gf.packet.composer.uploaddatacomposer import UploadDataComposer

from error import GWException


class MyGWServer(object):
    """
    GWServer communicate with terminals.
    It receive MT packets from terminals and handle them, And send MO
    packets to terminals.

    There are two process: 
      - publish process(recv packets and put response into queue)
      - consume process(send packets from queue)
    """

    def __init__(self, conf_file):
        ConfHelper.load(conf_file)

        for i in ('port', 'count', 'check_heartbeat_interval'):
            ConfHelper.GW_SERVER_CONF[i] = int(ConfHelper.GW_SERVER_CONF[i])

        #NOTE: define some variable 
        self.check_heartbeat_thread = None
        self.redis = None 
        self.db = None
        self.db_list = []
        self.exchange = 'ydws_exchange'
        self.gw_queue = 'ydws_gw_requests_queue@' +\
                        ConfHelper.GW_SERVER_CONF.host + ':' +\
                        str(ConfHelper.GW_SERVER_CONF.port)
        self.si_queue = 'ydws_si_requests_queue@' +\
                        ConfHelper.SI_SERVER_CONF.host + ':' +\
                        str(ConfHelper.SI_SERVER_CONF.port)
        self.gw_binding = 'ydws_gw_requests_binding@' +\
                          ConfHelper.GW_SERVER_CONF.host + ':' +\
                          str(ConfHelper.GW_SERVER_CONF.port)
        self.si_binding = 'ydws_si_requests_binding@' +\
                          ConfHelper.SI_SERVER_CONF.host + ':' +\
                          str(ConfHelper.SI_SERVER_CONF.port)

        #NOTE: initialize socket 
        self.socket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((ConfHelper.GW_SERVER_CONF.host, ConfHelper.GW_SERVER_CONF.port))

    def __connect_rabbitmq(self, host):
        """
        Connect rabbitmq
        """
        connection = None
        channel = None
        try:
            parameters = pika.ConnectionParameters(host=host)
            connection = BlockingConnection(parameters)
            #NOTE: default 50, maybe make it bigger.
            connection.set_backpressure_multiplier(50)
            #NOTE: Write buffer exceeded warning threshold
            #reconnect_rabbitmq = partial(self.__reconnect_rabbitmq, *(connection, host))
            #connection.add_backpressure_callback(reconnect_rabbitmq)
            channel = connection.channel()
            channel.exchange_declare(exchange=self.exchange,
                                     durable=False,
                                     auto_delete=True)
            channel.queue_declare(queue=self.gw_queue,
                                  durable=False, # not persistent
                                  exclusive=False, 
                                  auto_delete=True) # all client break connection, auto del
            channel.queue_bind(exchange=self.exchange,
                               queue=self.gw_queue,
                               routing_key=self.gw_binding)
            logging.info("[GW] Create GW request queue: %s, binding: %s",
                         self.gw_queue, self.gw_binding)
            logging.info("[GW] Create SI request queue: %s, binding: %s",
                         self.si_queue, self.si_binding)
        except Exception as e:
            logging.exception("[GW] Connect Rabbitmq-server failed. Exception：%s", e.args)
            raise GWException

        return connection, channel

    def __reconnect_rabbitmq(self, connection, host):
        """
        This is for catching any unpredictable AMQPConnectionError.
        Release resource for reconnect. 
        """
        logging.info("[GW] Reconnect rabbitmq...") 

        if connection and connection.is_open:
            connection.close()

        def __wait():
            interval = int(ConfHelper.GW_SERVER_CONF.retry_interval)
            logging.error("Retry connect in %d seconds.", interval)
            sleep(interval)

        connection = None
        channel = None
        for retry in xrange(int(ConfHelper.GW_SERVER_CONF.retry_count)):
            try:
                connection, channel = self.__connect_rabbitmq(host)
                if connection and connection.is_open:
                    logging.info("[GW] Rabbitmq reconnected!")
                    break
                else:
                    __wait()
            except:
                logging.exception("[GW] Connect rabbitmq error.")
                __wait()

        return connection, channel

    def consume(self, host):
        """Consume connection.

        workflow:
        1. get packet from rabbitmq_queue
        2. send packet to terminal
        """
        logging.info("[GW] Consume process, name: %s, pid: %s started...", 
                     multiprocessing.current_process().name, os.getpid())
        try:
            consume_connection, consume_channel = self.__connect_rabbitmq(host)
            while True:
                try:
                    method, header, body = consume_channel.basic_get(queue=self.gw_queue)
                    if method.NAME == 'Basic.GetEmpty':
                        sleep(0.1) 
                    else:
                        consume_channel.basic_ack(delivery_tag=method.delivery_tag)
                        self.send(body)
                except AMQPConnectionError as e:
                    logging.exception("[GW] Rabbitmq consume error: %s", e.args)
                    consume_connection, consume_channel = self.__reconnect_rabbitmq(consume_connection, host)
                    continue 
        except KeyboardInterrupt:
            logging.warn("[GW] Ctrl-C is pressed")
        except GWException:
            logging.exception("[GW] Unknow Exception...")
        finally:
            logging.info("[GW] Rabbitmq consume connection close...")
            self.__close_rabbitmq(consume_connection, consume_channel)

    def send(self, body):
        """Send packet to terminal.
        """
        try:
            message = json.loads(body)
            message = DotDict(message)
            logging.info("[GW] Send packet: %s to dev_id: %s, address: %s", message.packet, message.dev_id, message.address)
            self.socket.sendto(message.packet, tuple(message.address))
        except socket.error as e:
            logging.exception("[GW] Sock send error: %s", e.args)
        except Exception as e:
            logging.exception("[GW] Unknown send Exception:%s", e.args)

    def publish(self, host):
        """Publish connection. 

        1. get packet from terminal
        2. put this packet into queue
        3. handle packets of queue by multi threads
        """

        logging.info("[GW] Publish process, name: %s, pid: %s started...", 
                     multiprocessing.current_process().name, os.getpid())
        try:
            queue = Queue()
            #NOTE: multi threads handle packets
            publish_connection, publish_channel = self.__connect_rabbitmq(host)
            for i in range(int(ConfHelper.GW_SERVER_CONF.workers)):
                db = DBConnection().db
                self.db_list.append(db)
                logging.info("[GW] publish thread%s started...", i)
                thread.start_new_thread(self.handle_packet_from_terminal,
                                        (queue, host, publish_connection, publish_channel, i, db))
            #NOTE: recv packet and put it into queue
            while True:
                self.recv(queue)
        except KeyboardInterrupt:
            logging.warn("[GW] Ctrl-C is pressed")
        except GWException as e:
            logging.exception("[GW] Unknow Exception: %s", e.args)
        finally:
            logging.info("[GW] Rabbitmq publish connection close...")
            self.__close_rabbitmq(publish_connection, publish_channel)

    def recv(self, queue):
        """Recv packet from terminal.
        """
        try:
            response, address = self.socket.recvfrom(1024)
            logging.info("[GW] Recv: %s from %s", response, address)
            if response:
                item = dict(response=response,
                            address=address)
                queue.put(item)
        except socket.error as e:
            logging.exception("[GW] Sock recv error: %s", e.args)
            # reconnect socket?
            self.__close_socket()
            sleep(0.1)
            self.socket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((ConfHelper.GW_SERVER_CONF.host, ConfHelper.GW_SERVER_CONF.port))
        except Exception as e:
            logging.exception("[GW] Unknow recv Exception:%s", e.args)

    def divide_packets(self, packets):
        """Divide multi-packets into a list, that contains valid packet.

        @param: multi-packets
        @return: valid_packets
        """
        valid_packets = []

        while len(packets) > 0:
            start_index = packets.find('[')
            end_index = packets.find(']')
            if start_index == -1 or end_index == -1:
                logging.error("[GW] Invalid packets:%s", packets)
                packets = ''
            elif end_index < start_index:
                logging.error("[GW] Invalid packets:%s", packets[:start_index])
                packets = packets[start_index:]
            else:
                packet = packets[start_index:end_index+1]
                tmp_index = packet[1:].rfind('[')
                if tmp_index != -1:
                    logging.error("[GW] Invalid packets:%s", packets[:tmp_index])
                    packet = packet[tmp_index:]
                valid_packets.append(packet)
                packets = packets[end_index+1:]

        return valid_packets
        
    def handle_packet_from_terminal(self, queue, host, connection, channel, name, db):
        """Handle packet recv from terminal:

        - login
        - heartbeat
        - locationdesc
        - config
        - defendstatus
        - fobinfo
        - sleepstatus
        - fobstatus
        - unbindstatus
        - other, forward it to si.
        """
        while True:
            try:
                if not connection.is_open:
                    connection, channel = self.__reconnect_rabbitmq(connection, host)
                    continue
                else:
                    try:
                        if queue.qsize() != 0:
                            item  = queue.get(False)
                            packets = item.get('response')
                            address = item.get('address')
                            packets = self.divide_packets(packets)
                            for packet in packets:
                                clw = T_CLWCheck(packet)
                                if not clw.head:
                                    break
                                command = clw.head.command
                                if command == T_MESSAGE_TYPE.LOGIN: # T1
                                    logging.info("[GW] Thread%s recv login packet:\n%s", name, packet)
                                    self.handle_login(clw, address, connection, channel, db) 
                                elif command == T_MESSAGE_TYPE.HEARTBEAT: # T2
                                    logging.info("[GW] Thread%s recv heartbeat packet:\n%s", name, packet)
                                    self.handle_heartbeat(clw, address, connection, channel, db)
                                elif command == T_MESSAGE_TYPE.LOCATIONDESC: # T10
                                    logging.info("[GW] Thread%s recv locationdesc packet:\n%s", name, packet)
                                    self.handle_locationdesc(clw, address, connection, channel, db)
                                elif command == T_MESSAGE_TYPE.CONFIG: # T17
                                    logging.info("[GW] Thread%s recv query config packet:\n%s", name,  packet)
                                    self.handle_config(clw, address, connection, channel, db)
                                elif command == T_MESSAGE_TYPE.DEFENDSTATUS: # T18, deprecated
                                    logging.info("[GW] Thread%s recv defend status packet:\n%s", name, packet)
                                    self.handle_defend_status(clw, address, connection, channel, db)
                                elif command == T_MESSAGE_TYPE.FOBINFO: # T19 deprecated 
                                    logging.info("[GW] Thread%s recv fob info packet:\n%s", name, packet)
                                    self.handle_fob_info(clw, address, connection, channel, db)
                                elif command == T_MESSAGE_TYPE.SLEEPSTATUS: # T21
                                    logging.info("[GW] Thread%s recv sleep status packet:\n%s", name, packet)
                                    self.handle_terminal_sleep_status(clw, address, connection, channel, db)
                                elif command == T_MESSAGE_TYPE.FOBSTATUS: # T22, deprecated
                                    logging.info("[GW] Thread%s recv fob status packet:\n%s", name, packet)
                                    self.handle_fob_status(clw, address, connection, channel, db)
                                elif command == T_MESSAGE_TYPE.RUNTIMESTATUS: # T23
                                    logging.info("[GW] Thread%s recv runtime status packet:\n%s", name, packet)
                                    self.handle_runtime_status(clw, address, connection, channel, db)
                                elif command == T_MESSAGE_TYPE.UNBINDSTATUS: # T24
                                    logging.info("[GW] Thread%s recv unbind status packet:\n%s", name, packet)
                                    self.handle_unbind_status(clw, address, connection, channel, db)
                                elif command == T_MESSAGE_TYPE.UNUSUALACTIVATE: # T27
                                    logging.info("[GW] Thread%s recv unusual activate packet:\n%s", name, packet)
                                    self.handle_unusual_activate(clw, address, connection, channel, db)
                                elif command == T_MESSAGE_TYPE.MISC: # T28
                                    logging.info("[GW] Thread%s recv misc packet:\n%s", name, packet)
                                    self.handle_misc(clw, address, connection, channel, db)
                                elif command == T_MESSAGE_TYPE.ACC_STATUS: # T30
                                    logging.info("[GW] Thread%s recv power status packet:\n%s", name, packet)
                                    self.handle_acc_status(clw, address, connection, channel, db)
                                else: #NOTE: others will be forwar to SI server
                                    logging.info("[GW] Thread%s recv packet from terminal:\n%s", name, packet)
                                    self.foward_packet_to_si(clw, packet, address, connection, channel, db)
                        else:
                            sleep(0.1)
                    except Empty:
                        logging.info("[GW] Thread%s queue empty.", name)
                        sleep(0.1)
                    except GWException:
                        logging.exception("[GW] Thread%s handle packet Exception.", name) 
            except:
                logging.exception("[GW] Thread%s recv Exception.", name)

    def handle_login(self, info, address, connection, channel, db):
        """
        S1
        Handle the login packet.

        workflow:
        1: check packet
        if not dev_id:
            send packt to terminal, illegal_devid
        if mobile is not whitelist: 
            send sms to owner, mobile is not whitelist
            
        if version is bigger than 2.2.0:
            handle_new_login
        else:
            handle_old_login
        """
        try:
            args = DotDict(success=GATEWAY.LOGIN_STATUS.SUCCESS,
                           sessionID='')

            if len(info.body) == 7:
                info.body.append("")
                info.body.append("")
                logging.info("[GW] old version is compatible, append bt_name, bt_mac")

            lp = LoginParser(info.body, info.head)
            t_info = lp.ret
            if not t_info['dev_id']:
                args.success = GATEWAY.LOGIN_STATUS.ILLEGAL_DEVID
                lc = LoginRespComposer(args)
                request = DotDict(packet=lc.buf,
                                  address=address,
                                  dev_id=t_info['dev_id'])
                self.append_gw_request(request, connection, channel)
                logging.error("[GW] Login failed! Invalid terminal dev_id: %s", t_info['dev_id'])
                return

            if t_info['t_msisdn']:
                logging.info("[GW] Checking whitelist, terminal mobile: %s, Terminal: %s",
                             t_info['t_msisdn'], t_info['dev_id'])
                if not check_zs_phone(t_info['t_msisdn'], db):
                    args.success = GATEWAY.LOGIN_STATUS.NOT_WHITELIST 
                    lc = LoginRespComposer(args)
                    request = DotDict(packet=lc.buf,
                                      address=address,
                                      dev_id=t_info['dev_id'])
                    self.append_gw_request(request, connection, channel)
                    sms = SMSCode.SMS_MOBILE_NOT_WHITELIST % t_info['t_msisdn']
                    SMSHelper.send(t_info['u_msisdn'], sms)
                    logging.error("[GW] Login failed! terminal mobile: %s not whitelist, dev_id: %s",
                                  t_info['t_msisdn'], t_info['dev_id'])
                    return

            #NOTE: check the version. 
            # if version is after 2.2.0, go to handle_new_login; else go to handle_old_login
            softversion = t_info['softversion']
            item = softversion.split(".")
            new_softversion = True

            if int(item[0]) > 2:
                new_softversion = True
            elif int(item[0]) == 2:
                if int(item[1]) < 2:
                    new_softversion = False 
                else:
                    new_softversion = True 
            else:
                new_softversion = False

            if new_softversion: 
                # after v2.2.0
                logging.info("[GW] New softversion(>=2.2.0): %s, go to new login handler...",
                             softversion)
                self.handle_new_login(t_info, address, connection, channel, db)
            else:
                # before v2.2.0
                logging.info("[GW] Old softversion(<2.2.0): %s, go to old login handler...",
                             softversion)
                self.handle_old_login(t_info, address, connection, channel, db)
            # check use sence
            ttype = get_terminal_type_by_tid(t_info['dev_id'])
            logging.info("[GW] Terminal %s 's type  is %s", t_info['dev_id'], ttype)

        except:
            logging.exception("[GW] Handle login exception.")
            raise GWException

    def handle_new_login(self, t_info, address, connection, channel, db):
        """Handle the login packet with version bigger than 2.2.0
        S1

        t_info:{'dev_id' // tid
                't_msisdn' // tmobile
                'u_msisdn' // umobile
                'imei' // sim's id 
                'imsi' // track's id 
                'dev_type' 
                'softversion' // version of terminal, like 2.3.0
                'timestamp'
                'psd' 
                'keys_num' 
                'sessionID' 
                'command'  
                'factory_name'  
               }

        flag(t_info['psd']):
          0 - boot_normally
          1 - active_terminal
          2 - assert_reboot 
          3 - network_uncovered 
          4 - server_no_response 
          5 - config_changed 
          6 - session_expired 
          7 - terminal_unactived 
          8 - package_send_fail 
          9 - simcard_error 
         10 - gprs_error 
         11 - mcu_timeout
         12 - reboot_by_sms
        100 - script_reload 

        workflow:
        if normal login:
           if sn and imsi exist, but msisdn and msisdn are empty: 
               send register sms again 
           normal login, check [SN,PHONE,IMSI,USER] is matching or not.
        else: #JH
           delete old bind relation of tid, and send message to old user.
           update new bind relation of tmobile, and send message to new user.

        login response packet:
        0 - success, then get a sessionID for terminal and record terminal's address
        1 - unregister, terminal login first.
        3 - illegal sim, a mismatch between [SN,PHONE,IMSI,USER] 
        6 - not whitelist

        """

        args = DotDict(success=GATEWAY.LOGIN_STATUS.SUCCESS,
                       sessionID='')
        resend_key = get_resend_key(t_info.dev_id, t_info.timestamp, t_info.command)
        resend_flag = self.redis.getvalue(resend_key)

        sms = ''
        t_status = None
        #NOTE: new softversion, new meaning, 1: active; othter: normal login
        flag = t_info['psd'] 
        terminal = db.get("SELECT tid, group_id, mobile, imsi, owner_mobile, service_status,"
                          "       defend_status, mannual_status, icon_type, login_permit, alias, vibl, use_scene, push_status"
                          "  FROM T_TERMINAL_INFO"
                          "  WHERE mobile = %s LIMIT 1",
                          t_info['t_msisdn']) 

        #NOTE: normal login
        if flag != "1": # normal login
            #NOTE: no tmobile and ower_mobile 
            if (not t_info['t_msisdn']) and (not t_info['u_msisdn']):
                t = db.get("SELECT tid, group_id, mobile, imsi, owner_mobile, service_status"
                           "  FROM T_TERMINAL_INFO"
                           "  WHERE service_status=1"
                           "      AND tid = %s "
                           "      AND imsi = %s LIMIT 1",
                           t_info['dev_id'], t_info['imsi']) 
                if t: 
                    args.success = GATEWAY.LOGIN_STATUS.ILLEGAL_SIM
                    t_info['t_msisdn'] = t.mobile
                    t_info['u_msisdn'] = t.owner_mobile
                    register_sms = SMSCode.SMS_REGISTER % (t.owner_mobile, t.mobile)
                    SMSHelper.send_to_terminal(t.mobile, register_sms)
                    logging.info("[GW] A crash terminal tid:%s, imei:%s has no tmobile: %s, umobile:%s in login packet, so send %s again.",
                                 t_info['dev_id'], t_info['imei'], t_info['t_msisdn'], t_info['u_msisdn'], register_sms)
                else:
                    args.success = GATEWAY.LOGIN_STATUS.ILLEGAL_SIM
                    logging.info("[GW] A crash terminal:%s login without umobile and tmobile, and there is no record in db.", t_info['dev_id'])
            else:
                #NOTE: no tmobile 
                if not t_info['t_msisdn']:
                    # login first.
                    tid_terminal = db.get("SELECT tid, mobile, owner_mobile, service_status"
                                          " FROM T_TERMINAL_INFO"
                                          " WHERE tid = %s LIMIT 1", t_info['dev_id'])
                    args.success = GATEWAY.LOGIN_STATUS.ILLEGAL_SIM
                    if tid_terminal:
                        #NOTE: mobile is not not JH, send caution to owner
                        sms_ = SMSCode.SMS_NOT_JH % tid_terminal.mobile 
                        SMSHelper.send(tid_terminal.owner_mobile, sms_)
                    logging.warn("[GW] terminal: %s login at first time.",
                                 t_info['dev_id'])
                #NOTE: tmobile is exist
                elif terminal:
                    alias = QueryHelper.get_alias_by_tid(terminal['tid'], self.redis, db)
                    if terminal['tid'] != t_info['dev_id']:
                        args.success = GATEWAY.LOGIN_STATUS.ILLEGAL_SIM
                        sms = SMSCode.SMS_TERMINAL_HK % alias 
                        logging.warn("[GW] Terminal changed dev, mobile: %s, old_tid: %s, new_tid: %s",
                                     t_info['t_msisdn'], terminal['tid'], t_info['dev_id'])
                    elif terminal['imsi'] != t_info['imsi']:
                        args.success = GATEWAY.LOGIN_STATUS.ILLEGAL_SIM
                        sms = SMSCode.SMS_TERMINAL_HK % alias 
                        logging.warn("[GW] Terminal imsi is wrong, tid: %s, mobile: %s, old_imsi: %s, new_imsi: %s",
                                     t_info['dev_id'], t_info['t_msisdn'], terminal['imsi'], t_info['imsi'])
                    elif terminal['owner_mobile'] != t_info['u_msisdn']:
                        register_sms = SMSCode.SMS_REGISTER % (terminal['owner_mobile'], terminal['mobile']) 
                        SMSHelper.send_to_terminal(terminal['mobile'], register_sms)
                        logging.warn("[GW] Terminal owner_mobile is wrong, tid: %s, old_owner_mobile: %s, new_owner_mobile: %s, send the regist sms: %s again",
                                     t_info['dev_id'], terminal['owner_mobile'], t_info['u_msisdn'], register_sms)
                    elif terminal['service_status'] == UWEB.SERVICE_STATUS.TO_BE_UNBIND:
                        t_status = UWEB.SERVICE_STATUS.TO_BE_UNBIND
                        logging.warn("[GW] Terminal is unbinded. tid: %s, mobile: %s", 
                                     t_info["dev_id"], t_info['t_msisdn'])            
                    else:
                        logging.info("[GW] Terminal normal login successfully. tid: %s, mobile: %s", 
                                     t_info['dev_id'], t_info['t_msisdn'])
                else:
                    args.success = GATEWAY.LOGIN_STATUS.UNREGISTER
                    logging.error("[GW] Terminal login failed, unregister. tid: %s, mobile: %s", 
                                  t_info['dev_id'], t_info['t_msisdn'])
        #NOTE: JH
        else: # JH 
            logging.info("[GW] Terminal JH started. tid: %s, mobile: %s",
                         t_info['dev_id'], t_info['t_msisdn'])
            # 0. Initialize the valus keeps same as the default value in database.
            group_id = -1
            login_permit = 1 
            mannual_status = UWEB.DEFEND_STATUS.YES
            defend_status = UWEB.DEFEND_STATUS.YES
            icon_type = 0
            alias = ''
            push_status = 1
            vibl = 1
            use_scene = 3
            # send JH sms to terminal. default active time is one year.
            begintime = datetime.datetime.now() 
            endtime = begintime + relativedelta(years=1)

            # 1. check data validation
            logging.info("[GW] Checking terminal mobile: %s and owner mobile: %s, Terminal: %s",
                         t_info['t_msisdn'], t_info['u_msisdn'], t_info['dev_id'])
            if not (check_phone(t_info['u_msisdn']) and check_phone(t_info['t_msisdn'])):
                args.success = GATEWAY.LOGIN_STATUS.ILLEGAL_SIM
                lc = LoginRespComposer(args)
                request = DotDict(packet=lc.buf,
                                  address=address,
                                  dev_id=t_info['dev_id'])
                self.append_gw_request(request, connection, channel)
                if t_info['u_msisdn']:
                    # send JH failed caution to owner
                    sms = SMSCode.SMS_JH_FAILED
                    SMSHelper.send(t_info['u_msisdn'], sms)
                logging.error("[GW] Login failed! Invalid terminal mobile: %s or owner_mobile: %s, tid: %s",
                              t_info['t_msisdn'], t_info['u_msisdn'], t_info['dev_id'])
                return

            # 2. delete to_be_unbind terminal
            if terminal and terminal.service_status == UWEB.SERVICE_STATUS.TO_BE_UNBIND:
                logging.info("[GW] Delete terminal which is to_be_unbind. tid: %s, mobile: %s", 
                             terminal['tid'], terminal['mobile'])
                delete_terminal(terminal['tid'], db, self.redis)
                terminal = None

            # 3. add user info
            exist = db.get("SELECT id FROM T_USER"
                                "  WHERE mobile = %s",
                                t_info['u_msisdn'])

            #NOTE: Check ydcw or ajt
            ajt = QueryHelper.get_ajt_whitelist_by_mobile(t_info['t_msisdn'], db)
            if ajt:
               url_out = ConfHelper.UWEB_CONF.ajt_url_out
            else:
               url_out = ConfHelper.UWEB_CONF.url_out
            logging.info("[GW] Login url is: %s, tid: %s, mobile: %s ", 
                         url_out, t_info['dev_id'], t_info['t_msisdn'])

            if exist:
                logging.info("[GW] Owner already existed. tid: %s, mobile: %s", 
                             t_info['dev_id'], t_info['t_msisdn'])
                sms = SMSCode.SMS_USER_ADD_TERMINAL % (t_info['t_msisdn'],
                                                       url_out)
            else:
                # get a new psd for new user
                logging.info("[GW] Create new owner started. tid: %s, mobile: %s", t_info['dev_id'], t_info['t_msisdn'])
                psd = get_psd()
                db.execute("INSERT INTO T_USER(uid, password, name, mobile)"
                           "  VALUES(%s, password(%s), %s, %s)",
                           t_info['u_msisdn'], psd,
                           t_info['u_msisdn'], t_info['u_msisdn'])
                db.execute("INSERT INTO T_SMS_OPTION(uid)"
                           "  VALUES(%s)",
                           t_info['u_msisdn'])
                sms = SMSCode.SMS_JH_SUCCESS % (t_info['t_msisdn'],
                                                url_out,
                                                t_info['u_msisdn'],
                                                psd)

            # 4. JH existed tmobile
            is_refurbishment = False
            if terminal:
                if (terminal['tid'] == t_info['dev_id']) and \
                   (terminal['imsi'] == t_info['imsi']) and \
                   (terminal['owner_mobile'] == t_info['u_msisdn']):
                    # 4.1 SCN: Refurbishment, the terminal-info has existed in platform. JH it again.
                    is_refurbishment = True 
                    # check the login packet whether is send again 
                    if resend_flag:
                        sms = ''
                        logging.info("[GW] Recv resend packet, do not send sms. tid: %s, mobile: %s", 
                                     t_info['dev_id'], t_info['t_msisdn'])
                    else:
                        sms = SMSCode.SMS_USER_ADD_TERMINAL % (t_info['t_msisdn'],
                                                               url_out)
                        logging.info("[GW] Terminal is refurbishment. tid: %s, mobile: %s", 
                                     t_info['dev_id'], t_info['t_msisdn'])
                else:     
                    # 4.2 existed tmobile changed dev or corp terminal login first, get the old info(group_id, login_permit and so on) before change
                    group_id = terminal.group_id
                    login_permit = terminal.login_permit 
                    mannual_status = terminal.mannual_status
                    defend_status = terminal.defend_status
                    icon_type = terminal.icon_type
                    alias = terminal.alias
                    vibl = terminal.vibl
                    use_scene = terminal.use_scene
                    push_status = terminal.push_status
                    if terminal.tid == terminal.mobile:
                        # corp terminal login first, keep corp info
                        db.execute("UPDATE T_REGION_TERMINAL"
                                   "  SET tid = %s"
                                   "  WHERE tid = %s",
                                   t_info['dev_id'], t_info['t_msisdn'])
                        logging.info("[GW] Corp terminal login first, tid: %s, mobile: %s.",
                                     t_info['dev_id'], t_info['t_msisdn'])
                    elif terminal.tid != t_info['dev_id']:
                        logging.info("[GW] Terminal changed dev, mobile: %s, new_tid: %s, delete old_tid: %s.",
                                     t_info['t_msisdn'], t_info['dev_id'], terminal.tid)
                    else:
                        # Refurbishment, change user
                        logging.info("[GW] Terminal change user, tid: %s, mobile: %s, new_owner_mobile: %s, old_owner_mobile: %s",
                                     t_info['dev_id'], t_info['t_msisdn'], t_info['u_msisdn'],
                                     terminal.owner_mobile)
                    #NOTE: If terminal has exist, firt remove the terminal 
                    logging.info("[GW] Terminal is deleted, tid: %s, mobile: %s.",
                                 terminal['tid'], terminal['mobile']) 
                    del_user = True
                    if terminal.owner_mobile != t_info['u_msisdn']:
                        # send message to old user of dev_id
                        sms_ = SMSCode.SMS_DELETE_TERMINAL % terminal.mobile 
                        SMSHelper.send(terminal.owner_mobile, sms_)
                        if terminal.tid == t_info['dev_id']: 
                            # clear data belongs to the terminal 
                            clear_data(terminal.tid, db)
                        logging.info("[GW] Send delete terminal message: %s to user: %s",
                                     sms_, terminal.owner_mobile)
                    else:
                        del_user = False
                    delete_terminal(terminal.tid, db, self.redis, del_user=del_user)

            #NOTE: Normal JH.
            if not is_refurbishment:
                # 5. delete existed tid
                tid_terminal = db.get("SELECT tid, mobile, owner_mobile, service_status"
                                      "  FROM T_TERMINAL_INFO"
                                      "  WHERE tid = %s LIMIT 1",
                                      t_info['dev_id'])
                if tid_terminal:
                    logging.info("[GW] Terminal is deleted, tid: %s, mobile: %s.",
                                 tid_terminal['tid'], tid_terminal['mobile']) 
                    del_user = True
                    if tid_terminal['owner_mobile'] != t_info['u_msisdn']:
                        if tid_terminal['service_status'] == UWEB.SERVICE_STATUS.TO_BE_UNBIND:
                            logging.info("[GW] Terminal is to_be_unbind, tid: %s, mobile: %s, delete it.",
                                         tid_terminal['tid'], tid_terminal['mobile']) 
                        else:
                            # send message to old user of dev_id
                            sms_ = SMSCode.SMS_DELETE_TERMINAL % tid_terminal['mobile'] 
                            SMSHelper.send(tid_terminal['owner_mobile'], sms_)
                            logging.info("[GW] Send delete terminal message: %s to user: %s",
                                         sms_, tid_terminal['owner_mobile'])
                            # user changed, must clear history data of dev_id
                            clear_data(tid_terminal['tid'], db)
                    else:
                        del_user = False
                    delete_terminal(tid_terminal['tid'], db, self.redis, del_user=del_user)

                # 6 add terminal info

                # record the add action, enterprise or individual
                record_add_action(t_info['t_msisdn'], group_id, int(time.time()), db)
                
                # check use sence
                ttype = get_terminal_type_by_tid(t_info['dev_id'])
                logging.info("[GW] Terminal's type is %s. tid: %s, mobile: %s", 
                             ttype, t_info['dev_id'], t_info['t_msisdn']) 
                #if ttype == 'zj200':
                #    use_scene = 1
                #    vibl = 2 
                #else:
                #    use_scene = 3
                #    vibl = 1
                db.execute("INSERT INTO T_TERMINAL_INFO(tid, group_id, dev_type, mobile,"
                           "  owner_mobile, imsi, imei, factory_name, softversion,"
                           "  keys_num, login, service_status, defend_status,"
                           "  mannual_status, push_status, icon_type, begintime, endtime, "
                           "  offline_time, login_permit, alias, vibl, use_scene,"
                           "  bt_name, bt_mac)"
                           "  VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, DEFAULT, %s, %s, %s, "
                           "  %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                           t_info['dev_id'], group_id, t_info['dev_type'],
                           t_info['t_msisdn'], t_info['u_msisdn'],
                           t_info['imsi'], t_info['imei'],
                           t_info['factory_name'],
                           t_info['softversion'], t_info['keys_num'], 
                           GATEWAY.SERVICE_STATUS.ON,
                           defend_status, mannual_status, push_status, icon_type,
                           int(time.mktime(begintime.timetuple())),
                           4733481600,
                           int(time.mktime(begintime.timetuple())),
                           login_permit, alias, vibl, use_scene,
                           t_info['bt_name'], t_info['bt_mac'])
                db.execute("INSERT INTO T_CAR(tid, cnum)"
                           "  VALUES(%s, %s)",
                           t_info['dev_id'], alias)
                logging.info("[GW] Terminal JH success! tid: %s, mobile: %s.",
                             t_info['dev_id'], t_info['t_msisdn'])
                # subscription LE for new sim
                thread.start_new_thread(self.subscription_lbmp, (t_info,)) 
                #self.request_location(t_info['dev_id'], db)

        if args.success == GATEWAY.LOGIN_STATUS.SUCCESS:
            # get SessionID
            if resend_flag:
                logging.warn("[GW] Recv resend login packet and use old sessionID! packet: %s, tid: %s, mobile: %s.", 
                             t_info, t_info['dev_id'], t_info['t_msisdn']) 
                args.sessionID = self.get_terminal_sessionID(t_info['dev_id'])
                if not args.sessionID:
                    args.sessionID = get_sessionID()
            else:
                args.sessionID = get_sessionID()
                terminal_sessionID_key = get_terminal_sessionID_key(t_info['dev_id'])
                self.redis.setvalue(terminal_sessionID_key, args.sessionID)
                self.redis.setvalue(resend_key, True, GATEWAY.RESEND_EXPIRY)
            # record terminal address
            self.update_terminal_status(t_info["dev_id"], address)
            #NOTE: When termianl is normal login, update some properties to platform.
            info = DotDict(login=GATEWAY.TERMINAL_LOGIN.ONLINE,
                           mobile=t_info['t_msisdn'],
                           keys_num=t_info['keys_num'],
                           softversion=t_info['softversion'],
                           login_time=int(time.time()),
                           dev_id=t_info["dev_id"],
                           bt_mac=t_info['bt_mac'],
                           bt_name=t_info['bt_name'])
            self.update_terminal_info(info, db)
            logging.info("[GW] Terminal login success! tid: %s, mobile: %s",
                         t_info['dev_id'], t_info['t_msisdn'])

        lc = LoginRespComposer(args)
        request = DotDict(packet=lc.buf,
                          address=address,
                          dev_id=t_info["dev_id"])
        self.append_gw_request(request, connection, channel)

        if sms and t_info['u_msisdn']:
            logging.info("[GW] Send sms to owner. mobile: %s, content: %s",
                        t_info['u_msisdn'], sms)
            SMSHelper.send(t_info['u_msisdn'], sms)

        if t_status == UWEB.SERVICE_STATUS.TO_BE_UNBIND:
            seq = str(int(time.time()*1000))[-4:]
            args_ = DotDict(seq=seq,
                            tid=t_info["dev_id"])
            ubc = UNBindComposer(args_)
            request = DotDict(packet=ubc.buf,
                              address=address,
                              tid=t_info["dev_id"])
            self.append_gw_request(request, connection, channel)
            logging.warn("[GW] Terminal is unbinded, tid: %s, send unbind packet.", t_info["dev_id"])            

    def subscription_lbmp(self, t_info):
        """ Subscription LE for new sim
        """
        data = DotDict(sim=t_info['t_msisdn'],
                       action="A")
        response = LbmpSenderHelper.forward(LbmpSenderHelper.URLS.SUBSCRIPTION, data) 
        response = json_decode(response) 
        if response['success'] == '000': 
            logging.info("[GW] Terminal: %s subscription LE success! SIM: %s",
                         t_info['dev_id'], t_info['t_msisdn'])
        else:
            logging.warn("[GW] Terminal: %s subscription LE failed! SIM: %s, response: %s",
                         t_info['dev_id'], t_info['t_msisdn'], response)

    def handle_old_login(self, t_info, address, connection, channel, db):
        """
        S1
        Login response packet:

        0 - success, then get a sessionID for terminal and record terminal's address
        1 - illegal format of sim
        2 - expired, service stop or endtime < now
        3 - illegal sim, a mismatch between imsi and sim
        4 - psd wrong. HK
        5 - dev_id is empty
        6 - not whitelist
        """
        sms = None
        args = DotDict(success=GATEWAY.LOGIN_STATUS.SUCCESS,
                       sessionID='')
        resend_key = get_resend_key(t_info.dev_id, t_info.timestamp, t_info.command)
        resend_flag = self.redis.getvalue(resend_key)

        logging.info("[GW] Checking terminal mobile: %s and owner mobile: %s, Terminal: %s",
                     t_info['t_msisdn'], t_info['u_msisdn'], t_info['dev_id'])
        if not (check_phone(t_info['u_msisdn']) and check_phone(t_info['t_msisdn'])):
            args.success = GATEWAY.LOGIN_STATUS.ILLEGAL_SIM
            lc = LoginRespComposer(args)
            request = DotDict(packet=lc.buf,
                              address=address,
                              dev_id=t_info["dev_id"])
            self.append_gw_request(request, connection, channel)
            logging.error("[GW] Login failed! Invalid terminal mobile: %s or owner_mobile: %s, dev_id: %s",
                          t_info['t_msisdn'], t_info['u_msisdn'], t_info['dev_id'])
            return

        t_status = db.get("SELECT service_status"
                          "  FROM T_TERMINAL_INFO"
                          "  WHERE mobile = %s",
                          t_info['t_msisdn'])
        if t_status and t_status.service_status == GATEWAY.SERVICE_STATUS.OFF:
            args.success = GATEWAY.LOGIN_STATUS.EXPIRED
            lc = LoginRespComposer(args)
            request = DotDict(packet=lc.buf,
                              address=address,
                              dev_id=t_info["dev_id"])
            self.append_gw_request(request, connection, channel)
            logging.error("[GW] Login failed! terminal service expired! mobile: %s, dev_id: %s",
                          t_info['t_msisdn'], t_info['dev_id'])
            return


        logging.info("[GW] Checking imsi: %s and mobile: %s, Terminal: %s",
                     t_info['imsi'], t_info['t_msisdn'], t_info['dev_id'])
        tmobile = db.get("SELECT imsi FROM T_TERMINAL_INFO"
                         "  WHERE mobile = %s", t_info['t_msisdn'])
        if tmobile and tmobile.imsi and tmobile.imsi != t_info['imsi']:
            # check terminal and give a appropriate HK notification
            terminal = db.get("SELECT id FROM T_TERMINAL_INFO WHERE tid=%s", t_info['dev_id'])
            if terminal:
                alias = QueryHelper.get_alias_by_tid(t_info['dev_id'], self.redis, db)
            else: 
                alias = t_info['t_msisdn']
            args.success = GATEWAY.LOGIN_STATUS.ILLEGAL_SIM
            sms = SMSCode.SMS_TERMINAL_HK % alias 
            SMSHelper.send(t_info['u_msisdn'], sms)
            lc = LoginRespComposer(args)
            request = DotDict(packet=lc.buf,
                              address=address,
                              dev_id=t_info["dev_id"])
            self.append_gw_request(request, connection, channel)
            logging.error("[GW] Login failed! Illegal SIM: %s for Terminal: %s",
                          t_info['t_msisdn'], t_info['dev_id'])
            return

        terminal = db.get("SELECT id, mobile, owner_mobile, service_status"
                          "  FROM T_TERMINAL_INFO"
                          "  WHERE tid = %s", t_info['dev_id'])
        if terminal:
            if terminal.mobile != t_info['t_msisdn']:
                logging.info("[GW] Terminal: %s changed mobile, old mobile: %s, new mobile: %s",
                             t_info['dev_id'], terminal.mobile,
                             t_info['t_msisdn'])
                if (terminal.owner_mobile == t_info['u_msisdn'] or
                    terminal.service_status == UWEB.SERVICE_STATUS.TO_BE_UNBIND):
                    # delete old terminal!
                    logging.info("[GW] Delete old tid bind relation. tid: %s, owner_mobile: %s, service_status: %s",
                                 t_info['dev_id'], t_info['u_msisdn'],
                                 terminal.service_status)
                    delete_terminal(t_info['dev_id'], db, self.redis, del_user=False)
                    exist = db.get("SELECT tid, owner_mobile, service_status FROM T_TERMINAL_INFO"
                                        "  WHERE mobile = %s LIMIT 1",
                                        t_info['t_msisdn'])
                    if exist:
                        # cannot send unbind packet to dev_id
                        t_status = None
                        logging.info("[GW] Delete old tmobile bind relation. tid: %s, mobile: %s",
                                     exist.tid, t_info['t_msisdn'])
                        delete_terminal(exist.tid, db, self.redis, del_user=False)
                        if exist.service_status == UWEB.SERVICE_STATUS.TO_BE_UNBIND:
                            logging.info("[GW] Terminal: %s of %s is to_be_unbind, delete it.",
                                         exist.tid, t_info['t_msisdn'])
                        elif exist.owner_mobile != t_info['u_msisdn']:
                            sms = SMSCode.SMS_DELETE_TERMINAL % t_info['t_msisdn']
                            SMSHelper.send(exist.owner_mobile, sms)
                    terminal = None
                else:
                    args.success = GATEWAY.LOGIN_STATUS.ILLEGAL_SIM
                    sms = SMSCode.SMS_TID_EXIST % t_info['dev_id']
                    SMSHelper.send(t_info['u_msisdn'], sms)
                    lc = LoginRespComposer(args)
                    request = DotDict(packet=lc.buf,
                                      address=address,
                                      dev_id=t_info["dev_id"])
                    self.append_gw_request(request, connection, channel)
                    logging.error("[GW] Login failed! Terminal: %s already bound by %s, new mobile: %s",
                                  t_info['dev_id'], terminal.mobile, t_info['t_msisdn'])
                    return

        #NOTE: Check ydcw or ajt 
        ajt = QueryHelper.get_ajt_whitelist_by_mobile(t_info['t_msisdn'], db) 
        if ajt: 
            url_out = ConfHelper.UWEB_CONF.ajt_url_out 
        else: 
            url_out = ConfHelper.UWEB_CONF.url_out 
        logging.info("[GW] Terminal: %s, login url is: %s", t_info['t_msisdn'], url_out)

        if t_info['psd']:
            # check terminal exist or not when HK
            if not terminal:
                args.success = GATEWAY.LOGIN_STATUS.UNREGISTER
                sms = SMSCode.SMS_TID_NOT_EXIST
                SMSHelper.send(t_info['u_msisdn'], sms)
                lc = LoginRespComposer(args)
                request = DotDict(packet=lc.buf,
                                  address=address,
                                  dev_id=t_info["dev_id"])
                self.append_gw_request(request, connection, channel)
                logging.error("[GW] Login failed! Terminal %s execute HK, but tid is not exist",
                              t_info['dev_id'])
                return
            # HK, change terminal mobile or owner mobile
            logging.info("[GW] Checking password. Terminal: %s",
                         t_info['dev_id'])
            owner = db.get("SELECT id FROM T_USER"
                           "  WHERE mobile = %s"
                           "    AND password = password(%s)",
                           terminal.owner_mobile, t_info['psd'])
            if not owner:
                # psd wrong
                sms = SMSCode.SMS_PSD_WRONG
                args.success = GATEWAY.LOGIN_STATUS.PSD_WRONG
                logging.error("[GW] Login failed! Password invalid. Terminal: %s",
                              t_info['dev_id'])
            else:
                if terminal:
                    if terminal.mobile != t_info['t_msisdn']:
                        # terminal HK
                        logging.info("[GW] Terminal: %s HK started.", t_info['dev_id'])
                        # unbind old tmobile
                        old_bind = db.get("SELECT id, tid FROM T_TERMINAL_INFO"
                                          "  WHERE mobile = %s"
                                          "    AND id != %s",
                                          t_info['t_msisdn'], terminal.id)
                        if old_bind:
                            # clear db
                            db.execute("DELETE FROM T_TERMINAL_INFO"
                                       "  WHERE id = %s", 
                                       old_bind.id) 
                            # clear redis
                            sessionID_key = get_terminal_sessionID_key(old_bind.tid)
                            address_key = get_terminal_address_key(old_bind.tid)
                            info_key = get_terminal_info_key(old_bind.tid)
                            lq_sms_key = get_lq_sms_key(old_bind.tid)
                            lq_interval_key = get_lq_interval_key(old_bind.tid)
                            keys = [sessionID_key, address_key, info_key, lq_sms_key, lq_interval_key]
                            self.redis.delete(*keys)
                            logging.info("[GW] Delete old bind Terminal: %s, SIM: %s",
                                         t_info['dev_id'], t_info['t_msisdn'])

                        # update new tmobile
                        db.execute("UPDATE T_TERMINAL_INFO"
                                   "  SET mobile = %s,"
                                   "      imsi = %s"
                                   "  WHERE id = %s",
                                   t_info['t_msisdn'],
                                   t_info['imsi'], terminal.id)
                        # clear redis
                        sessionID_key = get_terminal_sessionID_key(t_info['dev_id'])
                        address_key = get_terminal_address_key(t_info['dev_id'])
                        info_key = get_terminal_info_key(t_info['dev_id'])
                        lq_sms_key = get_lq_sms_key(t_info['dev_id'])
                        lq_interval_key = get_lq_interval_key(t_info['dev_id'])
                        keys = [sessionID_key, address_key, info_key, lq_sms_key, lq_interval_key]
                        self.redis.delete(*keys)
                        # HK sms
                        sms = SMSCode.SMS_TERMINAL_HK_SUCCESS % (terminal.mobile, t_info['t_msisdn'])
                        # subscription LE for new sim
                        thread.start_new_thread(self.subscription_lbmp, (t_info,)) 
                        #self.request_location(t_info['dev_id'], db)
                        logging.info("[GW] Terminal: %s HK success!", t_info['dev_id'])

                    if terminal.owner_mobile != t_info['u_msisdn']:
                        logging.info("[GW] Owner HK started. Terminal: %s", t_info['dev_id'])
                        # owner HK
                        user = db.get("SELECT id FROM T_USER"
                                      "  WHERE mobile = %s",
                                      t_info['u_msisdn'])
                        if user:
                            logging.info("[GW] Owner already existed. Terminal: %s", t_info['dev_id'])
                            sms = SMSCode.SMS_USER_ADD_TERMINAL % (t_info['t_msisdn'],
                                                                   url_out) 
                        else:
                            logging.info("[GW] Create new owner started. Terminal: %s", t_info['dev_id'])
                            psd = get_psd()
                            db.execute("INSERT INTO T_USER"
                                       "  VALUES(NULL, %s, password(%s), %s, %s, NULL, NULL, NULL)",
                                       t_info['u_msisdn'],
                                       psd,
                                       t_info['u_msisdn'],
                                       t_info['u_msisdn'])
                            db.execute("INSERT INTO T_SMS_OPTION(uid)"
                                       "  VALUES(%s)",
                                       t_info['u_msisdn'])
                            sms = SMSCode.SMS_USER_HK_SUCCESS % (t_info['u_msisdn'],
                                                                 url_out,
                                                                 t_info['u_msisdn'],
                                                                 psd)
                        db.execute("UPDATE T_TERMINAL_INFO"
                                   "  SET owner_mobile = %s"
                                   "  WHERE id = %s",
                                   t_info['u_msisdn'], terminal.id)
                        logging.info("[GW] Owner of %s HK success!", t_info['dev_id'])
                else:
                    logging.error("[GW] What happened? Cannot find old terminal by dev_id: %s",
                                  t_info['dev_id']) 
        else:
            # login or JH
            if terminal:
                # login
                logging.info("[GW] Terminal: %s Normal login started!",
                             t_info['dev_id']) 
            else:
                # SMS JH or admin JH or change new dev JH
                logging.info("[GW] Terminal: %s, mobile: %s JH started.",
                             t_info['dev_id'], t_info['t_msisdn'])
                exist = db.get("SELECT id FROM T_USER"
                               "  WHERE mobile = %s",
                               t_info['u_msisdn'])
                if exist:
                    logging.info("[GW] Owner already existed. Terminal: %s", t_info['dev_id'])
                    sms = SMSCode.SMS_USER_ADD_TERMINAL % (t_info['t_msisdn'],
                                                           url_out)
                else:
                    # get a new psd for new user
                    logging.info("[GW] Create new owner started. Terminal: %s", t_info['dev_id'])
                    psd = get_psd()
                    db.execute("INSERT INTO T_USER(uid, password, name, mobile)"
                               "  VALUES(%s, password(%s), %s, %s)",
                               t_info['u_msisdn'], psd,
                               t_info['u_msisdn'], t_info['u_msisdn'])
                    db.execute("INSERT INTO T_SMS_OPTION(uid)"
                               "  VALUES(%s)",
                               t_info['u_msisdn'])
                    sms = SMSCode.SMS_JH_SUCCESS % (t_info['t_msisdn'],
                                                    url_out,
                                                    t_info['u_msisdn'],
                                                    psd)

                admin_terminal = db.get("SELECT id, tid FROM T_TERMINAL_INFO"
                                        "  WHERE tid = %s",
                                        t_info['t_msisdn'])
                if admin_terminal:
                    # admin JH
                    db.execute("UPDATE T_TERMINAL_INFO"
                               "  SET tid = %s,"
                               "      dev_type = %s,"
                               "      owner_mobile = %s,"
                               "      imsi = %s,"
                               "      imei = %s,"
                               "      factory_name = %s,"
                               "      keys_num = %s,"
                               "      softversion = %s"
                               "  WHERE id = %s",
                               t_info['dev_id'],
                               t_info['dev_type'],
                               t_info['u_msisdn'],
                               t_info['imsi'],
                               t_info['imei'],
                               t_info['factory_name'],
                               t_info['keys_num'],
                               t_info['softversion'],
                               admin_terminal.id)
                    db.execute("UPDATE T_CAR SET tid = %s"
                               "  WHERE tid = %s",
                               t_info['dev_id'], t_info['t_msisdn'])
                    logging.info("[GW] Terminal %s by ADMIN JH success!", t_info['dev_id'])
                else:
                    exist_terminal = db.get("SELECT id, tid FROM T_TERMINAL_INFO"
                                            "  WHERE mobile = %s",
                                            t_info['t_msisdn'])
                    if exist_terminal:
                        # unbind old tmobile
                        db.execute("DELETE FROM T_TERMINAL_INFO"
                                   "  WHERE id = %s",
                                   exist_terminal.id)
                        # clear redis
                        sessionID_key = get_terminal_sessionID_key(exist_terminal.tid)
                        address_key = get_terminal_address_key(exist_terminal.tid)
                        info_key = get_terminal_info_key(exist_terminal.tid)
                        lq_sms_key = get_lq_sms_key(exist_terminal.tid)
                        lq_interval_key = get_lq_interval_key(exist_terminal.tid)
                        keys = [sessionID_key, address_key, info_key, lq_sms_key, lq_interval_key]
                        self.redis.delete(*keys)
                        logging.info("[GW] Terminal %s change dev, old dev: %s!",
                                     t_info['dev_id'], exist_terminal.tid)

                    # send JH sms to terminal. default active time
                    # is one year.
                    begintime = datetime.datetime.now() 
                    endtime = begintime + relativedelta(years=1)
                    # record the add action, enterprise or individual
                    record_add_action(t_info['t_msisdn'], -1, int(time.time()), db)

                    db.execute("INSERT INTO T_TERMINAL_INFO(tid, dev_type, mobile,"
                               "  owner_mobile, imsi, imei, factory_name, softversion,"
                               "  keys_num, login, service_status, begintime, endtime, offline_time)"
                               "  VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, DEFAULT, %s, %s, %s, %s)",
                               t_info['dev_id'], t_info['dev_type'],
                               t_info['t_msisdn'], t_info['u_msisdn'],
                               t_info['imsi'], t_info['imei'],
                               t_info['factory_name'],
                               t_info['softversion'], t_info['keys_num'], 
                               GATEWAY.SERVICE_STATUS.ON,
                               int(time.mktime(begintime.timetuple())),
                               int(time.mktime(endtime.timetuple())),
                               int(time.mktime(begintime.timetuple())))
                    db.execute("INSERT INTO T_CAR(tid)"
                               "  VALUES(%s)",
                               t_info['dev_id'])
                    logging.info("[GW] Terminal %s by SMS JH success!", t_info['dev_id'])

                # subscription LE for new sim
                thread.start_new_thread(self.subscription_lbmp, (t_info,)) 
                #self.request_location(t_info['dev_id'], db)

        if args.success == GATEWAY.LOGIN_STATUS.SUCCESS:
            # get SessionID
            if resend_flag:
                args.sessionID = self.get_terminal_sessionID(t_info['dev_id'])
                logging.warn("[GW] Recv resend login packet: %s and use old sessionID: %s!", t_info, args.sessionID) 
                if not args.sessionID:
                    args.sessionID = get_sessionID()
            else:
                args.sessionID = get_sessionID()
                terminal_sessionID_key = get_terminal_sessionID_key(t_info['dev_id'])
                self.redis.setvalue(terminal_sessionID_key, args.sessionID)
                self.redis.setvalue(resend_key, True, GATEWAY.RESEND_EXPIRY)
            # record terminal address
            self.update_terminal_status(t_info["dev_id"], address)
            # set login
            info = DotDict(login=GATEWAY.TERMINAL_LOGIN.ONLINE,
                           mobile=t_info['t_msisdn'],
                           keys_num=t_info['keys_num'],
                           login_time=int(time.time()),
                           dev_id=t_info["dev_id"])
            self.update_terminal_info(info, db)
            logging.info("[GW] Terminal %s login success! SIM: %s",
                         t_info['dev_id'], t_info['t_msisdn'])

        lc = LoginRespComposer(args)
        request = DotDict(packet=lc.buf,
                          address=address,
                          dev_id=t_info["dev_id"])
        self.append_gw_request(request, connection, channel)
                
        if sms and t_info['u_msisdn']:
            SMSHelper.send(t_info['u_msisdn'], sms)

        # unbind terminal of to_be_unbind
        if t_status and t_status.service_status == UWEB.SERVICE_STATUS.TO_BE_UNBIND:
            logging.info("[GW] Terminal: %s is unbinded, send unbind packet.", t_info["dev_id"])            
            seq = str(int(time.time()*1000))[-4:]
            args = DotDict(seq=seq,
                           tid=t_info["dev_id"])
            ubc = UNBindComposer(args)
            request = DotDict(packet=ubc.buf,
                              address=address,
                              dev_id=t_info["dev_id"])
            self.append_gw_request(request, connection, channel)

    def handle_heartbeat(self, info, address, connection, channel, db):
        """
        S2
        heartbeat packet

        0: success, then record new terminal's address
        1: invalid SessionID 
        3: acc_status is changed 
        """
        try:
            head = info.head
            body = info.body
            dev_id = head.dev_id
            args = DotDict(success=GATEWAY.RESPONSE_STATUS.SUCCESS)
            sessionID = self.get_terminal_sessionID(dev_id)
            if sessionID != head.sessionID:
                args.success = GATEWAY.RESPONSE_STATUS.INVALID_SESSIONID 
            else:
                hp = HeartbeatParser(body, head)
                heartbeat_info = hp.ret 
                is_sleep = False
                if heartbeat_info['sleep_status'] == '0':
                    heartbeat_info['login'] = GATEWAY.TERMINAL_LOGIN.SLEEP
                    is_sleep = True
                elif heartbeat_info['sleep_status'] == '1':
                    heartbeat_info['login'] = GATEWAY.TERMINAL_LOGIN.ONLINE
                    is_sleep = False
                elif heartbeat_info['sleep_status'] == '2': # query mode
                    acc_status_info_key = get_acc_status_info_key(dev_id)
                    acc_status_info = self.redis.getvalue(acc_status_info_key)
                    if acc_status_info and int(acc_status_info['op_status']) == 0:  
                        args.timestamp = acc_status_info['timestamp']
                        args.op_type = acc_status_info['op_type']
                        # modify t2_status in acc_status_info
                        acc_status_info['t2_status'] = 1 # T2 query occurs 
                        self.redis.setvalue(acc_status_info_key, acc_status_info, EVENTER.ACC_STATUS_EXPIRY)
                    else: # if acc_status_info['op_status'] is 1, or no acc_status_info, set op_type is 2
                        args.timestamp = '' 
                        args.op_type = 2 # wait 


                else: #NOTE: it should never occur
                    logging.error("[GW] Recv wrong sleep status: %s", heartbeat_info)
                del heartbeat_info['sleep_status']

                self.update_terminal_status(head.dev_id, address, is_sleep)
                self.update_terminal_info(heartbeat_info, db)

            if args['success'] == GATEWAY.RESPONSE_STATUS.SUCCESS:
                acc_status_info_key = get_acc_status_info_key(dev_id)
                acc_status_info = self.redis.getvalue(acc_status_info_key)
                if acc_status_info and (not acc_status_info['t2_status']): # T2(query) is need
                    args['success'] = 3 # acc_status is changed
                    logging.info("[GW] ACC_status is changed, dev_id: %s, acc_status_info: %s", 
                                 dev_id, acc_status_info)
            hc = HeartbeatRespComposer(args)
            request = DotDict(packet=hc.buf,
                              address=address,
                              dev_id=dev_id)
            self.append_gw_request(request, connection, channel)
        except Exception as e:
            logging.exception("[GW] Hand heartbeat failed. Exception: %s.", 
                              e.args)
            raise GWException

    def handle_locationdesc(self, info, address, connection, channel, db):
        """
        S10
        locationdesc packet

        0: success, then return locationdesc to terminal and record new terminal's address
        1: invalid SessionID 
        """
        try:
            head = info.head
            body = info.body
            dev_id = head.dev_id
            if len(body) == 6:
                body.append(20) 
                logging.info("[GW] old version is compatible, append locate_error")

            resend_key = get_resend_key(head.dev_id, head.timestamp, head.command)
            resend_flag = self.redis.getvalue(resend_key)
            go_ahead = False 
            args = DotDict(success=GATEWAY.RESPONSE_STATUS.SUCCESS,
                           locationdesc="",
                           ew="E",
                           lon=0.0,
                           ns="N",
                           lat=0.0)
            sessionID = self.get_terminal_sessionID(head.dev_id)
            if sessionID != head.sessionID:
                args.success = GATEWAY.RESPONSE_STATUS.INVALID_SESSIONID
                logging.error("[GW] Invalid sessionID, terminal: %s", head.dev_id)
            else:
                if resend_flag:
                    logging.warn("[GW] Recv resend packet, head: %s, body: %s and drop it!",
                                 info.head, info.body)
                else:
                    go_ahead = True

            lc = LocationDescRespComposer(args)
            request = DotDict(packet=lc.buf,
                              address=address,
                              dev_id=dev_id)
            self.append_gw_request(request, connection, channel)
            self.update_terminal_status(head.dev_id, address)
            #NOTE: Check ydcw or ajt 
            ajt = QueryHelper.get_ajt_whitelist_by_mobile(head.dev_id, db) 
            if ajt: 
                url_out = ConfHelper.UWEB_CONF.ajt_url_out 
            else: 
                url_out = ConfHelper.UWEB_CONF.url_out

            if go_ahead:
                self.redis.setvalue(resend_key, True, GATEWAY.RESEND_EXPIRY)
                ldp = LocationDescParser(body, head)
                location = ldp.ret
                logging.info("[GW] T10 packet parsered:%s", location)
                if not  location.has_key('gps_time'):
                    location['gps_time'] = int(time.time())
                    logging.info("[GW] what's up? location:%s hasn't gps_time.", location)
                location['t'] = EVENTER.INFO_TYPE.POSITION
                if location['valid'] != GATEWAY.LOCATION_STATUS.SUCCESS:
                    cellid = True
                else:
                    cellid = False
                location = lbmphelper.handle_location(location, self.redis, cellid=cellid, db=db)
                location.name = location.get('name') if location.get('name') else ""
                location.name = safe_unicode(location.name)
                user = QueryHelper.get_user_by_tid(head.dev_id, db)
                tname = QueryHelper.get_alias_by_tid(head.dev_id, self.redis, db)
                dw_method = u'GPS' if not cellid else u'基站'
                if location.cLat and location.cLon:
                    if user:
                        current_time = get_terminal_time(int(time.time()))
                        sms = SMSCode.SMS_DW_SUCCESS % (tname, dw_method,
                                                        location.name, 
                                                        safe_unicode(current_time)) 
                        url = url_out + '/wapimg?clon=' +\
                              str(location.cLon/3600000.0) + '&clat=' + str(location.cLat/3600000.0)
                        tiny_id = URLHelper.get_tinyid(url)
                        if tiny_id:
                            base_url = url_out + UWebHelper.URLS.TINYURL
                            tiny_url = base_url + '/' + tiny_id
                            logging.info("[GW] get tiny url successfully. tiny_url:%s", tiny_url)
                            self.redis.setvalue(tiny_id, url, time=EVENTER.TINYURL_EXPIRY)
                            sms += u"点击 " + tiny_url + u" 查看定位器位置。" 
                        else:
                            logging.info("[GW] get tiny url failed.")
                        SMSHelper.send(user.owner_mobile, sms)
                else:
                    if user:
                        sms = SMSCode.SMS_DW_FAILED % (tname, dw_method)
                        SMSHelper.send(user.owner_mobile, sms)
                if not (location.lat and location.lon):
                    args.success = GATEWAY.RESPONSE_STATUS.CELLID_FAILED
                else:
                    insert_location(location, db, self.redis)

        except:
            logging.exception("[GW] Handle locationdesc exception.")
            raise GWException

    def handle_config(self, info, address, connection, channel, db):
        """
        S17
        Config packet

        0: success, then record new terminal's address
        1: invalid SessionID 
        """
        try:
            head = info.head
            body = info.body
            dev_id = head.dev_id
            args = DotDict(success=GATEWAY.RESPONSE_STATUS.SUCCESS,
                           domain="",
                           freq="",
                           trace="",
                           static_val="",
                           move_val="",
                           trace_para="",
                           vibl="",
                           use_scene="",
                           stop_interval="",
                           test="",
                           gps_enhanced="")
            sessionID = self.get_terminal_sessionID(head.dev_id)
            if sessionID != head.sessionID:
                args.success = GATEWAY.RESPONSE_STATUS.INVALID_SESSIONID 
            else:
                self.update_terminal_status(head.dev_id, address)
                terminal = db.get("SELECT track, freq, trace, static_val,"
                                  "       move_val, trace_para, vibl, domain,"
                                  "       use_scene, stop_interval, test, gps_enhanced"
                                  "  FROM T_TERMINAL_INFO"
                                  "  WHERE tid = %s", head.dev_id)
                args.domain = terminal.domain
                args.freq = terminal.freq
                args.trace = terminal.trace
                args.static_val = terminal.static_val
                args.move_val = terminal.move_val
                args.use_scene = terminal.use_scene
                args.stop_interval = terminal.stop_interval
                args.test = terminal.test
                args.gps_enhanced = terminal.gps_enhanced
                if terminal.track == 1: # turn on track
                    args.trace_para = "60:1"
                else:
                    args.trace_para = terminal.trace_para
                args.vibl = terminal.vibl

            if args['success'] == GATEWAY.RESPONSE_STATUS.SUCCESS: 
                acc_status_info_key = get_acc_status_info_key(dev_id) 
                acc_status_info = self.redis.getvalue(acc_status_info_key) 
                if acc_status_info and (not acc_status_info['t2_status']): # T2(query) is need
                    args['success'] = 3 # acc_status is changed 
                    logging.info("[GW] ACC_status is changed, dev_id: %s, acc_status_info: %s", 
                                 dev_id, acc_status_info)

            hc = ConfigRespComposer(args)
            request = DotDict(packet=hc.buf,
                              address=address,
                              dev_id=dev_id)
            self.append_gw_request(request, connection, channel)
        except:
            logging.exception("[GW] Hand query config exception.")
            raise GWException

    def handle_defend_status(self, info, address, connection, channel, db):
        """
        defend status report packet
        0: success, then record new terminal's address
        1: invalid SessionID 
        """
        try:
            head = info.head
            body = info.body
            dev_id = head.dev_id
            resend_key = get_resend_key(head.dev_id, head.timestamp, head.command)
            resend_flag = self.redis.getvalue(resend_key)

            # old version is compatible
            if len(body) == 1:
                body.append('0')
                logging.info("[GW] old version is compatible, append mannual status 0")
            args = DotDict(success=GATEWAY.RESPONSE_STATUS.SUCCESS,
                           command=head.command)
            sessionID = self.get_terminal_sessionID(head.dev_id)
            if sessionID != head.sessionID:
                args.success = GATEWAY.RESPONSE_STATUS.INVALID_SESSIONID 
            else:
                if resend_flag:
                    logging.warn("[GW] Recv resend packet, head: %s, body: %s and drop it!",
                                 info.head, info.body)
                else: 
                    self.redis.setvalue(resend_key, True, GATEWAY.RESEND_EXPIRY)
                    hp = AsyncParser(body, head)
                    defend_info = hp.ret 
                    defend_info['mannual_status'] = defend_info['defend_status']
                    if defend_info['defend_source'] != 0:
                        # come from sms or web 
                        if defend_info['defend_source'] == "1":
                            _status = u"设防" if defend_info['defend_status'] == "1" else u"撤防"
                            tname = QueryHelper.get_alias_by_tid(head.dev_id, self.redis, db)
                            sms = SMSCode.SMS_DEFEND_SUCCESS % (tname, _status) 
                            user = QueryHelper.get_user_by_tid(head.dev_id, db)
                            if user:
                                SMSHelper.send(user.owner_mobile, sms)
                        del defend_info['defend_status']
                    del defend_info['defend_source']
                    self.update_terminal_info(defend_info, db)
                self.update_terminal_status(head.dev_id, address)

            if args['success'] == GATEWAY.RESPONSE_STATUS.SUCCESS: 
                acc_status_info_key = get_acc_status_info_key(dev_id) 
                acc_status_info = self.redis.getvalue(acc_status_info_key) 
                if acc_status_info and (not acc_status_info['t2_status']): # T2(query) is need
                    args['success'] = 3 # acc_status is changed 
                    logging.info("[GW] ACC_status is changed, dev_id: %s, acc_status_info: %s", 
                                 dev_id, acc_status_info)
            hc = AsyncRespComposer(args)
            request = DotDict(packet=hc.buf,
                              address=address,
                              dev_id=dev_id)
            self.append_gw_request(request, connection, channel)
        except:
            logging.exception("[GW] Handle defend status report exception.")
            raise GWException

    def handle_fob_info(self, info, address, connection, channel, db):
        """
        fob info packet: add or remove fob
        0: success, then record new terminal's address
        1: invalid SessionID
        """
        try:
            head = info.head
            body = info.body
            dev_id = head.dev_id
            args = DotDict(success=GATEWAY.RESPONSE_STATUS.SUCCESS)
            sessionID = self.get_terminal_sessionID(head.dev_id)
            if sessionID != head.sessionID:
                args.success = GATEWAY.RESPONSE_STATUS.INVALID_SESSIONID 
            else:
                fp = FobInfoParser(body, head)
                fobinfo = fp.ret
                self.update_terminal_status(head.dev_id, address)
                self.update_fob_info(fobinfo, db)

            fc = FobInfoRespComposer(args)
            request = DotDict(packet=fc.buf,
                              address=address,
                              dev_id=dev_id)
            self.append_gw_request(request, connection, channel)
        except:
            logging.exception("[GW] Handle fob info report exception.")
            raise GWException

    def handle_terminal_sleep_status(self, info, address, connection, channel, db):
        """
        sleep status packet: 0-sleep, 1-LQ
        0: success, then record new terminal's address
        1: invalid SessionID
        """
        try:
            head = info.head
            body = info.body
            dev_id = head.dev_id
            resend_key = get_resend_key(head.dev_id, head.timestamp, head.command)
            resend_flag = self.redis.getvalue(resend_key)

            args = DotDict(success=GATEWAY.RESPONSE_STATUS.SUCCESS,
                           command=head.command)
            sessionID = self.get_terminal_sessionID(head.dev_id)
            is_sleep = False
            if sessionID != head.sessionID:
                args.success = GATEWAY.RESPONSE_STATUS.INVALID_SESSIONID 
            else:
                if resend_flag:
                    logging.warn("[GW] Recv resend packet, head: %s, body: %s and drop it!",
                                 info.head, info.body)
                else: 
                    self.redis.setvalue(resend_key, True, GATEWAY.RESEND_EXPIRY)
                    hp = AsyncParser(body, head)
                    sleep_info = hp.ret 
                    if sleep_info['sleep_status'] == '0':
                        sleep_info['login'] = GATEWAY.TERMINAL_LOGIN.SLEEP
                        #self.send_lq_sms(head.dev_id)
                        #logging.info("[GW] Recv sleep packet, LQ it: %s", head.dev_id)
                        is_sleep = True
                    elif sleep_info['sleep_status'] == '1':
                        sleep_info['login'] = GATEWAY.TERMINAL_LOGIN.ONLINE
                    else:
                        logging.info("[GW] Recv wrong sleep status: %s", sleep_info)
                    del sleep_info['sleep_status']
                    self.update_terminal_info(sleep_info, db)

                self.update_terminal_status(head.dev_id, address, is_sleep)

            if args['success'] == GATEWAY.RESPONSE_STATUS.SUCCESS: 
                acc_status_info_key = get_acc_status_info_key(dev_id) 
                acc_status_info = self.redis.getvalue(acc_status_info_key) 
                if acc_status_info and (not acc_status_info['t2_status']): # T2(query) is need
                    args['success'] = 3 # acc_status is changed 
                    logging.info("[GW] ACC_status is changed, dev_id: %s, acc_status_info: %s", 
                                 dev_id, acc_status_info)

            hc = AsyncRespComposer(args)
            request = DotDict(packet=hc.buf,
                              address=address,
                              dev_id=dev_id)
            self.append_gw_request(request, connection, channel)
        except:
            logging.exception("[GW] Handle sleep status report exception.")
            raise GWException

    def handle_fob_status(self, info, address, connection, channel, db):
        """
        fob status packet: 0-no fob near, 1-have fob near
        0: success, then record new terminal's address
        1: invalid SessionID
        """
        try:
            head = info.head
            body = info.body
            dev_id = head.dev_id
            resend_key = get_resend_key(head.dev_id, head.timestamp, head.command)
            resend_flag = self.redis.getvalue(resend_key)

            args = DotDict(success=GATEWAY.RESPONSE_STATUS.SUCCESS,
                           command=head.command)
            sessionID = self.get_terminal_sessionID(head.dev_id)
            if sessionID != head.sessionID:
                args.success = GATEWAY.RESPONSE_STATUS.INVALID_SESSIONID 
            else:
                if resend_flag:
                    logging.warn("[GW] Recv resend packet, head: %s, body: %s and drop it!",
                                 info.head, info.body)
                else: 
                    self.redis.setvalue(resend_key, True, GATEWAY.RESEND_EXPIRY)
                    hp = AsyncParser(body, head)
                    fob_info = hp.ret 
                    info = DotDict(fob_status=fob_info['fob_status'],
                                   dev_id=fob_info['dev_id'])
                    self.update_terminal_info(fob_info, db)
                self.update_terminal_status(head.dev_id, address)

            hc = AsyncRespComposer(args)
            request = DotDict(packet=hc.buf,
                              address=address,
                              dev_id=dev_id)
            self.append_gw_request(request, connection, channel)
        except:
            logging.exception("[GW] Handle fob status report exception.")
            raise GWException

    def handle_runtime_status(self, info, address, connection, channel, db):
        """
        S23
        runtime status packet: {login [0:unlogin | 1:login],
                                defend_status [0:undefend | 1:defend],
                                gps:gsm:pbat [0-100:0-9:0-100]} 

        0: success, then record new terminal's address
        1: invalid SessionID
        """
        try:
            head = info.head
            body = info.body
            dev_id = head.dev_id
            resend_key = get_resend_key(dev_id, head.timestamp, head.command)
            resend_flag = self.redis.getvalue(resend_key)
            if len(body) == 3:
                body.append('-1')
                body.append('0')
                logging.info("[GW] old version is compatible, append fob_pbat, is_send")
            if len(body) == 4:
                body.append('0')
                logging.info("[GW] old version is compatible, append is_send")
            args = DotDict(success=GATEWAY.RESPONSE_STATUS.SUCCESS,
                           command=head.command,
                           mannual_status='')
            sessionID = self.get_terminal_sessionID(head.dev_id)
            if sessionID != head.sessionID:
                args.success = GATEWAY.RESPONSE_STATUS.INVALID_SESSIONID 
            else:
                if resend_flag:
                    logging.warn("[GW] Recv resend packet, head: %s, body: %s and drop it!",
                                 info.head, info.body)
                    terminal_info = QueryHelper.get_terminal_info(head.dev_id, db,
                                                                  self.redis)
                    args.mannual_status = terminal_info['mannual_status']
                else:
                    self.redis.setvalue(resend_key, True, GATEWAY.RESEND_EXPIRY)
                    hp = AsyncParser(body, head)
                    runtime_info = hp.ret 
                    self.update_terminal_status(head.dev_id, address)
                    terminal_info = self.update_terminal_info(runtime_info, db)
                    args.mannual_status = terminal_info['mannual_status']
                    db.execute("INSERT INTO T_RUNTIME_STATUS"
                               "  VALUES(NULL, %s, %s, %s, %s, %s, %s, %s, %s)",
                               head.dev_id, runtime_info['login'], runtime_info['defend_status'],
                               runtime_info['gps'], runtime_info['gsm'], runtime_info['pbat'],
                               runtime_info['fob_pbat'], head.timestamp)

                    is_send = int(runtime_info['is_send'])
                    if is_send:
                        terminal_info_key = get_terminal_info_key(head.dev_id) 
                        terminal_info = QueryHelper.get_terminal_info(head.dev_id, db, self.redis)
                        alias = QueryHelper.get_alias_by_tid(head.dev_id, self.redis, db)
                        communication_staus = u'正常'
                        communication_mode = u'撤防'
                        gsm_strength = u'强'
                        gps_strength = u'强'
                        if int(terminal_info['login']) == GATEWAY.TERMINAL_LOGIN.ONLINE:
                            communication_staus = u'正常'
                        else:
                            communication_staus = u'异常'

                        if int(terminal_info['mannual_status']) == UWEB.DEFEND_STATUS.YES:
                            communication_mode = u'设防'
                        else:
                            communication_mode= u'撤防'

                        pbat = int(terminal_info.get('pbat', 0))

                        gsm = int(terminal_info.get('gsm', 0))
                        if gsm < 3:
                            gsm_strength = u'弱'
                        elif gsm < 6:
                            gsm_strength = u'较弱'

                        gps = int(terminal_info.get('gps', 0))
                        if gps < 10:
                            gps_strength = u'弱' 
                        elif gps < 20:
                            gps_strength = u'较弱' 
                        elif gps < 30:
                            gps_strength = u'较强' 

                        runtime_sms = SMSCode.SMS_RUNTIME_STATUS % (alias, communication_staus, communication_mode, int(pbat), gsm_strength, gps_strength)
                        SMSHelper.send(terminal_info.owner_mobile, runtime_sms)
                        logging.info("[GW] Send runtime_status sms to user: %s, tid: %s",
                                     terminal_info.owner_mobile, head.dev_id)

                self.update_terminal_status(head.dev_id, address)

            if args['success'] == GATEWAY.RESPONSE_STATUS.SUCCESS: 
                acc_status_info_key = get_acc_status_info_key(dev_id) 
                acc_status_info = self.redis.getvalue(acc_status_info_key) 
                if acc_status_info and (not acc_status_info['t2_status']): # T2(query) is need
                    args['success'] = 3 # acc_status is changed 
                    logging.info("[GW] ACC_status is changed, dev_id: %s, acc_status_info: %s", 
                                 dev_id, acc_status_info)

            rc = RuntimeRespComposer(args)
            request = DotDict(packet=rc.buf,
                              address=address,
                              dev_id=dev_id)
            self.append_gw_request(request, connection, channel)
        except:
            logging.exception("[GW] Handle runtime status report exception.")
            raise GWException

    def handle_unbind_status(self, info, address, connection, channel, db):
        """
        Unbind status report packet

        0: success, then record new terminal's address
        1: invalid SessionID 
        """
        try:
            head = info.head
            body = info.body
            dev_id = head.dev_id
            # before v2.2.0
            if len(body) == 0:
                body.append("0")

            args = DotDict(success=GATEWAY.RESPONSE_STATUS.SUCCESS,
                           command=head.command)
            ap = AsyncParser(body, head)
            info = ap.ret 
            flag = info['flag']
            delete_terminal(head.dev_id, db, self.redis)
            if int(flag) == 1:
                clear_data(head.dev_id, db)

            hc = AsyncRespComposer(args)
            request = DotDict(packet=hc.buf,
                              address=address,
                              dev_id=dev_id)
            self.append_gw_request(request, connection, channel)
        except:
            logging.exception("[GW] Handle unbind status report exception.")
            raise GWException

    def handle_unusual_activate(self, info, address, connection, channel, db):
        """Unusual activate report packet: owner_mobile changed.

        0: success, then record new terminal's address
        1: invalid SessionID 
        """
        try:
            head = info.head
            body = info.body
            dev_id = head.dev_id
            resend_key = get_resend_key(head.dev_id, head.timestamp, head.command)
            resend_flag = self.redis.getvalue(resend_key)

            args = DotDict(success=GATEWAY.RESPONSE_STATUS.SUCCESS,
                           command=head.command)
            if resend_flag:
                logging.warn("[GW] Recv resend packet, head: %s, body: %s and drop it!",
                             info.head, info.body)
            else: 
                self.redis.setvalue(resend_key, True, GATEWAY.RESEND_EXPIRY)
                uap = UnusualActivateParser(body, head)
                t_info = uap.ret
                terminal = db.get("SELECT mobile FROM T_TERMINAL_INFO"
                                  "  WHERE tid = %s LIMIT 1",
                                  t_info['dev_id'])
                if terminal:
                    sms = SMSCode.SMS_UNUSUAL_ACTIVATE % terminal['mobile'] 
                    SMSHelper.send(t_info['u_msisdn'], sms)
                else:
                    logging.error("[GW] Terminal: %s is not existent, what's up?", t_info['dev_id'])

            uac = UnusualActivateComposer(args)
            request = DotDict(packet=uac.buf,
                              address=address,
                              dev_id=dev_id)
            self.append_gw_request(request, connection, channel)
        except:
            logging.exception("[GW] Hand unusual activate report exception.")
            raise GWException
            
    def handle_misc(self, info, address, connection, channel, db):
        """
        S28
        misc: debugging for terminal.

        0: success, then record new terminal's address
        1: invalid SessionID 
        """
        try:
            head = info.head
            body = info.body
            dev_id = head.dev_id

            args = DotDict(success=GATEWAY.RESPONSE_STATUS.SUCCESS,
                           command=head.command)
            sessionID = self.get_terminal_sessionID(dev_id)
            if sessionID != head.sessionID: 
                args.success = GATEWAY.RESPONSE_STATUS.INVALID_SESSIONID
            else:
                uap = MiscParser(body, head)
                t_info = uap.ret
                db.execute("UPDATE T_TERMINAL_INFO"
                           " SET misc = %s"
                           "    WHERE tid = %s ",
                           t_info['misc'], head.dev_id)

            if args['success'] == GATEWAY.RESPONSE_STATUS.SUCCESS: 
                acc_status_info_key = get_acc_status_info_key(dev_id) 
                acc_status_info = self.redis.getvalue(acc_status_info_key) 
                if acc_status_info and (not acc_status_info['t2_status']): # T2(query) is need
                    args['success'] = 3 # acc_status is changed 
                    logging.info("[GW] ACC_status is changed, dev_id: %s, acc_status_info: %s", 
                                 dev_id, acc_status_info)
            uac = MiscComposer(args)
            request = DotDict(packet=uac.buf,
                              address=address,
                              dev_id=dev_id)
            self.append_gw_request(request, connection, channel)
        except:
            logging.exception("[GW] Handle misc report exception.")
            raise GWException
            
    def handle_acc_status(self, info, address, connection, channel, db):
        """
        S30
        ACC_status: 

        0: success, then record new terminal's address
        1: invalid SessionID 
        """
        try:
            head = info.head
            body = info.body
            dev_id = head.dev_id

            args = DotDict(success=GATEWAY.RESPONSE_STATUS.SUCCESS,
                           command=head.command)
            sessionID = self.get_terminal_sessionID(dev_id)
            if sessionID != head.sessionID: 
                args.success = GATEWAY.RESPONSE_STATUS.INVALID_SESSIONID
            else:
                uap = MiscParser(body, head)
                t_info = uap.ret
                acc_status_info_key = get_acc_status_info_key(dev_id)
                acc_status_info = self.redis.getvalue(acc_status_info_key)
                if acc_status_info:  
                    acc_status_info['op_status'] = 1 # success
                    self.redis.setvalue(acc_status_info_key, acc_status_info, EVENTER.ACC_STATUS_EXPIRY)
                else: # It should never occur. 
                    logging.error("[GW] ACC_status can not be found. dev_id: %s",
                                  dev_id)
                    pass

            asc = ACCStatusComposer(args)
            request = DotDict(packet=asc.buf,
                              address=address,
                              dev_id=dev_id)
            self.append_gw_request(request, connection, channel)
        except:
            logging.exception("[GW] Handle acc status exception.")
            raise GWException

    def foward_packet_to_si(self, info, packet, address, connection, channel, db):
        """
        Response packet or position/report/charge packet

        0: success, then forward it to SIServer and record new terminal's address
        1: invalid SessionID 
        """
        try:
            head = info.head
            args = DotDict(success=GATEWAY.RESPONSE_STATUS.SUCCESS,
                           command=head.command)
            dev_id = head.dev_id
            resend_key = get_resend_key(dev_id, head.timestamp, head.command)
            resend_flag = self.redis.getvalue(resend_key)
            sessionID = self.get_terminal_sessionID(dev_id)
            if sessionID != head.sessionID:
                args.success = GATEWAY.RESPONSE_STATUS.INVALID_SESSIONID
                logging.error("[GW] Invalid sessionID, Terminal: %s", dev_id)
            else:
                seq = str(int(time.time() * 1000))[-4:]
                uargs = DotDict(seq=seq,
                                dev_id=dev_id,
                                content=packet)
                content = UploadDataComposer(uargs).buf
                logging.info("[GW] Forward message to SI:\n%s", content)
                if resend_flag:
                    logging.warn("[GW] Recv resend packet: %s, and drop it!", packet)
                else:
                    self.append_si_request(content, connection, channel)
                self.update_terminal_status(dev_id, address)

            #NOTE: Handle the packet.
            if head.command in (T_MESSAGE_TYPE.POSITION, T_MESSAGE_TYPE.MULTIPVT,
                                T_MESSAGE_TYPE.CHARGE, T_MESSAGE_TYPE.ILLEGALMOVE,
                                T_MESSAGE_TYPE.POWERLOW, T_MESSAGE_TYPE.ILLEGALSHAKE,
                                T_MESSAGE_TYPE.EMERGENCY, T_MESSAGE_TYPE.POWERDOWN, 
                                T_MESSAGE_TYPE.STOP):
                logging.info("[GW] Head command: %s.", head.command)
                if args['success'] == GATEWAY.RESPONSE_STATUS.SUCCESS: 
                    acc_status_info_key = get_acc_status_info_key(dev_id) 
                    acc_status_info = self.redis.getvalue(acc_status_info_key) 
                    if acc_status_info and (not acc_status_info['t2_status']): # T2(query) is need 
                        logging.info("[GW] ACC_status is changed, dev_id: %s, acc_status_info: %s", 
                                     dev_id, acc_status_info)
                        args['success'] = 3 # acc_status is changed

                #NOTE: composer response for terminal 
                rc = AsyncRespComposer(args)
                request = DotDict(packet=rc.buf,
                                  address=address,
                                  dev_id=dev_id)
                self.append_gw_request(request, connection, channel)
                # resend flag
                if not resend_flag:
                    self.redis.setvalue(resend_key, True, GATEWAY.RESEND_EXPIRY)
            elif head.command == GATEWAY.T_MESSAGE_TYPE.UNBIND:
                logging.info("[GW] Head command: %s.", head.command)
                up = UNBindParser(info.body, info.head)
                status = up.ret['status']
                if status == GATEWAY.STATUS.SUCCESS:
                    delete_terminal(dev_id, db, self.redis)
            else:
                logging.exception("[GW] Invalid command: %s.", head.command)
        except:
            logging.exception("[GW] Handle SI message exception.")
            raise GWException

    def append_gw_request(self, request, connection, channel):
        """Append request to GW.
        """
        message = json.dumps(request)
        # make message not persistent
        properties = pika.BasicProperties(delivery_mode=1,)
        channel.basic_publish(exchange=self.exchange,
                              routing_key=self.gw_binding,
                              body=message,
                              properties=properties)

    def append_si_request(self, request, connection, channel):
        """Append request to SI.
        """
        request = dict({"packet":request})
        message = json.dumps(request)
        # make message not persistent
        properties = pika.BasicProperties(delivery_mode=1,)
        channel.basic_publish(exchange=self.exchange,
                              routing_key=self.si_binding,
                              body=message,
                              properties=properties)

    def get_terminal_sessionID(self, dev_id):
        """Get terminal's sessionid generated by platform in last interactive.
        """
        terminal_sessionID_key = get_terminal_sessionID_key(dev_id) 
        #NOTE: eval is issued in getvalue method, if session contains 'e',
        # the sessionid may becomes a float,  so use get method here.
        sessionID = self.redis.get(terminal_sessionID_key)

        return sessionID

    def update_terminal_status(self, dev_id, address, is_sleep=False):
        """Keep the latest address of termianl in redis.
        """
        terminal_status_key = get_terminal_address_key(dev_id)
        lq_interval_key = get_lq_interval_key(dev_id)
        is_lq = self.redis.getvalue(lq_interval_key)
        if is_sleep:
            self.redis.delete(lq_interval_key)
            is_lq = False

        if is_lq and not is_sleep:
            self.redis.setvalue(terminal_status_key, address, 10 * HEARTBEAT_INTERVAL)
        else:
            self.redis.setvalue(terminal_status_key, address, (1 * SLEEP_HEARTBEAT_INTERVAL + 300))

    def update_fob_info(self, fobinfo, db):
        """Update fob's information.
        """
        terminal_info_key = get_terminal_info_key(fobinfo['dev_id'])
        terminal_info = QueryHelper.get_terminal_info(fobinfo['dev_id'],
                                                      db, self.redis)

        if int(fobinfo['operate']) == GATEWAY.FOB_OPERATE.ADD:
            db.execute("INSERT INTO T_FOB(tid, fobid)"
                       "  VALUES(%s, %s)"
                       "  ON DUPLICATE KEY"
                       "  UPDATE tid = VALUES(tid),"
                       "         fobid = VALUES(fobid)",
                       fobinfo['dev_id'], fobinfo['fobid'])
            fob_list = terminal_info['fob_list']
            if fob_list:
                fob_list.append(fobinfo['fobid'])
            else:
                fob_list = [fobinfo['fobid'],]
            terminal_info['fob_list'] = list(set(fob_list))
            terminal_info['keys_num'] = len(terminal_info['fob_list']) 
            db.execute("UPDATE T_TERMINAL_INFO"
                       "  SET keys_num = %s"
                       "  WHERE tid = %s", 
                       terminal_info['keys_num'], fobinfo['dev_id'])
            self.redis.setvalue(terminal_info_key, terminal_info)
        elif int(fobinfo['operate']) == GATEWAY.FOB_OPERATE.REMOVE:
            db.execute("DELETE FROM T_FOB"
                       "  WHERE fobid = %s"
                       "    AND tid = %s",
                       fobinfo['fobid'], fobinfo['dev_id'])
            fob_list = terminal_info['fob_list']
            if fob_list:
                if fobinfo['fobid'] in fob_list:
                    fob_list.remove(fobinfo['fobid'])
            else:
                fob_list = []
            terminal_info['fob_list'] = list(set(fob_list))
            terminal_info['keys_num'] = len(terminal_info['fob_list']) 
            db.execute("UPDATE T_TERMINAL_INFO"
                       "  SET keys_num = %s"
                       "  WHERE tid = %s", 
                       terminal_info['keys_num'], fobinfo['dev_id'])
            self.redis.setvalue(terminal_info_key, terminal_info)
        else:
            pass

    def update_terminal_info(self, t_info, db):
        """Update terminal's info in db and redis.
        NOTE: 
        Only those properties which are different from platform is needed to change.
        """
        terminal_info_key = get_terminal_info_key(t_info['dev_id'])
        terminal_info = QueryHelper.get_terminal_info(t_info['dev_id'],
                                                      db, self.redis)

        #1: db
        fields = []
        # gps, gsm, pbat, changed by position report
        keys = ['mobile', 'defend_status', 'login', 'keys_num', 'fob_status', 'mannual_status', 
                'softversion', 'bt_mac', 'bt_name']
        for key in keys:
            value = t_info.get(key, None)
            t_value = terminal_info.get(key, '')
            if value is not None and value != t_value:
                fields.append(key + " = " + "'" + str(t_info[key]) + "'")
        if 'login_time' in t_info:
            fields.append('login_time' + " = " + str(t_info['login_time']))
            login_time_key = get_login_time_key(t_info['dev_id'])
            self.redis.setvalue(login_time_key, t_info['login_time'])
        set_clause = ','.join(fields)
        if set_clause:
            sql_cmd = ("UPDATE T_TERMINAL_INFO "
                       "  SET " + set_clause + 
                       "  WHERE tid = %s")
            db.execute(sql_cmd, t_info['dev_id'])
        #2: redis
        for key in terminal_info:
            value = t_info.get(key, None)
            if value is not None:
                terminal_info[key] = value
        self.redis.setvalue(terminal_info_key, terminal_info)

        return terminal_info

    def get_terminal_status(self, dev_id):
        """Get address through dev_id. 

        workflow:
        if address is not null:
            terminal is on line  
        else:
            terminal is off line  
        """
        terminal_status_key = get_terminal_address_key(dev_id)
        return self.redis.getvalue(terminal_status_key)

    def request_location(self, dev_id, db):
        """Request location.
        """
        location = DotDict({'dev_id':dev_id,
                            'valid':GATEWAY.LOCATION_STATUS.FAILED,
                            't':EVENTER.INFO_TYPE.POSITION,
                            'lat':None,
                            'lon':None,
                            'alt':0,
                            'cLat':None,
                            'cLon':None,
                            'gps_time':None,
                            'type':1,
                            'name':'',
                            'degree':0,
                            'speed':0.0,
                            'cellid':'0:0:0:0'})
        location = lbmphelper.handle_location(location, self.redis,
                                              cellid=True, db=db)
        if location.cLat and location.cLon:
            insert_location(location, db, self.redis)

    def __close_rabbitmq(self, connection=None, channel=None):
        """Close rabbitmq.
        """
        if connection and connection.is_open:
            try:
                channel.queue_delete(queue=self.gw_queue)
            except AMQPChannelError as e:
                logging.exception("[GW] Delete gw_queue failed: already delete. Exception: %s",
                                  e.args)
            connection.close()

    def __close_socket(self):
        """Close socket.
        """
        try:
            self.socket.close()
        except Exception as e:
            logging.exception("[GW] Close socket Failed. Exception: %s.",
                              e.args)

    def __clear_memcached(self, dev_id=None):
        """Clear memcached.
        """
        pass

    def stop(self):
        """Stop socket, memcached, db
        """
        self.__close_socket()
        self.__clear_memcached()
        for db in self.db_list:
            db.close()

    def __del__(self):
        """Invoke stop method.
        """
        self.stop()
