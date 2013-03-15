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
from Queue import Queue
import thread

from tornado.escape import json_decode

from utils.dotdict import DotDict
from utils.repeatedtimer import RepeatedTimer
from utils.checker import check_phone
from db_.mysql import DBConnection
from utils.myredis import MyRedis
from utils.misc import get_terminal_address_key, get_terminal_sessionID_key,\
     get_terminal_info_key, get_lq_sms_key, get_lq_interval_key, get_location_key,\
     get_terminal_time, get_sessionID, safe_unicode, get_psd, get_offline_lq_key,\
     get_resend_key, get_lastinfo_key
from constants.GATEWAY import T_MESSAGE_TYPE, HEARTBEAT_INTERVAL,\
     SLEEP_HEARTBEAT_INTERVAL
from constants.MEMCACHED import ALIVED
from constants import EVENTER, GATEWAY, UWEB, SMS
from codes.smscode import SMSCode

from helpers.seqgenerator import SeqGenerator
from helpers.confhelper import ConfHelper
from helpers.queryhelper import QueryHelper
from helpers.smshelper import SMSHelper
from helpers.lbmphelper import LbmpSenderHelper
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
from clw.packet.composer.login import LoginRespComposer
from clw.packet.composer.heartbeat import HeartbeatRespComposer
from clw.packet.composer.async import AsyncRespComposer
from clw.packet.composer.runtime import RuntimeRespComposer
from clw.packet.composer.locationdesc import LocationDescRespComposer
from clw.packet.composer.config import ConfigRespComposer
from clw.packet.composer.fobinfo import FobInfoRespComposer
from gf.packet.composer.uploaddatacomposer import UploadDataComposer

class MyGWServer(object):
    """
    """

    def __init__(self, conf_file):
        ConfHelper.load(conf_file)
        for i in ('port', 'count', 'check_heartbeat_interval'):
            ConfHelper.GW_SERVER_CONF[i] = int(ConfHelper.GW_SERVER_CONF[i])
        self.check_heartbeat_thread = None
        self.online_terminals = [] 
        self.redis = None 
        self.db = None
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

        self.socket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((ConfHelper.GW_SERVER_CONF.host, ConfHelper.GW_SERVER_CONF.port))

    def __connect_rabbitmq(self, host):
        connection = None
        channel = None
        try:
            parameters = pika.ConnectionParameters(host=host)
            connection = BlockingConnection(parameters)
            # default 10, maybe make it bigger.
            connection.set_backpressure_multiplier(50)
            # Write buffer exceeded warning threshold
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
        except:
            logging.exception("[GW] Connect Rabbitmq-server Error!")

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

    def check_heartbeat(self):
        try:
            is_alived = self.redis.getvalue("is_alived")
            if is_alived == ALIVED:
                for dev_id in self.online_terminals:
                    status = self.get_terminal_status(dev_id)
                    offline_lq_key = get_offline_lq_key(dev_id)
                    offline_lq_time = self.redis.getvalue(offline_lq_key)
                    if not status:
                        if not offline_lq_time:
                            self.send_lq_sms(dev_id)
                            self.redis.setvalue(offline_lq_key, int(time.time()), 5*60)
                        elif (time.time() - offline_lq_time) > 2 * 60:
                            self.heartbeat_lost_report(dev_id)
                            self.redis.delete(offline_lq_key)
                        else:
                            pass
        except:
            logging.exception("[GW] Check gateway heartbeat exception.")

    def send_lq_sms(self, dev_id):
        sim = QueryHelper.get_tmobile_by_tid(dev_id, self.redis, self.db)
        if sim:
            interval = SMS.LQ.WEB
            sms = SMSCode.SMS_LQ % interval 
            SMSHelper.send_to_terminal(sim, sms)
            lq_interval_key = get_lq_interval_key(dev_id)
            self.redis.setvalue(lq_interval_key, int(time.time()), (interval*60 - 160))
            logging.info("Send offline LQ: '%s' to Sim: %s", sms, sim)
                
    def heartbeat_lost_report(self, dev_id):
        timestamp = int(time.time())
        rname = EVENTER.RNAME.HEARTBEAT_LOST
        category = EVENTER.CATEGORY[rname]
        lid = self.db.execute("INSERT INTO T_LOCATION(tid, timestamp, category, type)"
                              "  VALUES(%s, %s, %s, %s)",
                              dev_id, timestamp, category, 1)
        self.db.execute("INSERT INTO T_EVENT(tid, lid, category)"
                        "  VALUES (%s, %s, %s)",
                        dev_id, lid, category)
        user = QueryHelper.get_user_by_tid(dev_id, self.db)
        if user:
            sms_option = QueryHelper.get_sms_option_by_uid(user.owner_mobile, 'heartbeat_lost', self.db)
            logging.info("sms option: %s of %s", sms_option, user.owner_mobile)
            if sms_option.heartbeat_lost == UWEB.SMS_OPTION.SEND:
                current_time = get_terminal_time(timestamp) 
                tname = QueryHelper.get_alias_by_tid(dev_id, self.redis, self.db)
                sms = SMSCode.SMS_HEARTBEAT_LOST % (tname, current_time)
                SMSHelper.send(user.owner_mobile, sms)
        logging.warn("[GW] Terminal %s Heartbeat lost!!!", dev_id)
        # 1. memcached clear sessionID
        terminal_sessionID_key = get_terminal_sessionID_key(dev_id)
        self.redis.delete(terminal_sessionID_key)
        # 2. offline
        self.online_terminals.remove(dev_id)
        # 3. db set offline 
        info = DotDict(dev_id=dev_id,
                       login=GATEWAY.TERMINAL_LOGIN.OFFLINE)
        self.update_terminal_info(info)

    def __start_check_heartbeat_thread(self):
        self.check_heartbeat_thread = RepeatedTimer(ConfHelper.GW_SERVER_CONF.check_heartbeat_interval,
                                                    self.check_heartbeat)
        self.check_heartbeat_thread.start()
        logging.info("[GW] Check heartbeat thread started...")

    def __restore_online_terminals(self):
        """
        if restart gatewayserver, record online terminals again.
        """
        db = DBConnection().db
        #redis = MyRedis()
        online_terminals = db.query("SELECT tid FROM T_TERMINAL_INFO"
                                    "  WHERE login != %s",
                                    GATEWAY.TERMINAL_LOGIN.OFFLINE)
        self.online_terminals = [t.tid for t in online_terminals]
        #for terminal in online_terminals:
        #    info = DotDict(dev_id=terminal.tid,
        #                   login=GATEWAY.TERMINAL_LOGIN.OFFLINE)
        #    self.update_terminal_info(info)
        #    terminal_status_key = get_terminal_address_key(terminal.tid)
        #    terminal_sessionID_key = get_terminal_sessionID_key(terminal.tid)
        #    keys = [terminal_status_key, terminal_sessionID_key]
        #    self.redis.delete(*keys)
            #terminal_status_key = get_terminal_address_key(terminal.tid)
            #terminal_status = redis.getvalue(terminal_status_key)
            #if terminal_status:
            #    self.online_terminals.append(terminal.tid)
            #else:
            #    db.execute("UPDATE T_TERMINAL_INFO"
            #               "  SET login = %s"
            #               "  WHERE tid = %s",
            #               GATEWAY.TERMINAL_LOGIN.OFFLINE, terminal.tid)
            #    terminal_sessionID_key = get_terminal_sessionID_key(terminal.tid)
            #    self.redis.delete(terminal_sessionID_key)

        db.close()
        
    def __stop_check_heartbeat_thread(self):
        if self.check_heartbeat_thread is not None:
            self.check_heartbeat_thread.cancel()
            self.check_heartbeat_thread.join()
            logging.info("[GW] Check heartbeat stop.")
            self.check_heartbeat_thread = None

    def consume(self, host):
        logging.info("[GW] consume process: %s started...", os.getpid())
        consume_connection, consume_channel = self.__connect_rabbitmq(host)
        try:
            while True:
                try:
                    method, header, body = consume_channel.basic_get(queue=self.gw_queue)
                    if method.NAME == 'Basic.GetEmpty':
                        sleep(1) 
                    else:
                        consume_channel.basic_ack(delivery_tag=method.delivery_tag)
                        self.send(body)
                except AMQPConnectionError as e:
                    logging.exception("[GW] Rabbitmq consume error: %s", e.args)
                    consume_connection, consume_channel = self.__reconnect_rabbitmq(consume_connection, host)
                    continue 
        except KeyboardInterrupt:
            logging.warn("[GW] Ctrl-C is pressed")
        except Exception as e:
            logging.exception("[GW] Unknow Exception:%s", e.args)
        finally:
            logging.info("[GW] Rabbitmq consume connection close...")
            self.__close_rabbitmq(consume_connection, consume_channel)

    def send(self, body):
        try:
            message = json.loads(body)
            message = DotDict(message)
            logging.info("[GW] send: %s to %s", message.packet, message.address)
            self.socket.sendto(message.packet, tuple(message.address))
        except socket.error as e:
            logging.exception("[GW]sock send error: %s", e.args)
        except Exception as e:
            logging.exception("[GW]unknown send Exception:%s", e.args)

    def publish(self, host):
        logging.info("[GW] publish process: %s started...", os.getpid())
        queue = Queue()
        try:
            #NOTE: self.online_terminals, this process will change it!
            self.__restore_online_terminals()
            self.__start_check_heartbeat_thread()
            thread.start_new_thread(self.handle_packet_from_terminal,
                                    (queue, host))
            self.recv(queue)
        except KeyboardInterrupt:
            logging.warn("[GW] Ctrl-C is pressed")
        except Exception as e:
            logging.exception("[GW] Unknow Exception:%s", e.args)

    def recv(self, queue):
        try:
            while True:
                response, address = self.socket.recvfrom(1024)
                logging.info("[GW] recv: %s from %s", response, address)
                if response:
                    item = dict(response=response,
                                address=address)
                    queue.put(item)
        except socket.error as e:
            logging.exception("[GW]sock recv error: %s", e.args)
        except Exception as e:
            logging.exception("[GW]unknow recv Exception:%s", e.args)

    def divide_packets(self, packets):
        """
        @param: multi-packets
        @return: valid_packets
        divide multi-packets into a list, that contains valid packet.
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
        
    def handle_packet_from_terminal(self, queue, host):
        """
        handle packet recv from terminal:
        - login
        - heartbeat
        - locationdesc
        - other, forward it to si.
        """
        try:
            logging.info("[GW] Handle recv packet thread started...")
            connection, channel = self.__connect_rabbitmq(host)
            while True:
                if not connection.is_open:
                    connection, channel = self.__reconnect_rabbitmq(connection, host)
                    continue
                else:
                    if queue.qsize() != 0:
                        item  = queue.get(False)
                        packets = item.get('response')
                        address = item.get('address')
                        packets = self.divide_packets(packets)
                        for packet in packets:
                            clw = T_CLWCheck(packet)
                            command = clw.head.command
                            if command == T_MESSAGE_TYPE.LOGIN:
                                logging.info("[GW] Recv login packet:\n%s", packet)
                                self.handle_login(clw, address, connection, channel) 
                            elif command == T_MESSAGE_TYPE.HEARTBEAT:
                                logging.info("[GW] Recv heartbeat packet:\n%s", packet)
                                self.handle_heartbeat(clw, address, connection, channel)
                            elif command == T_MESSAGE_TYPE.LOCATIONDESC:
                                logging.info("[GW] Recv locationdesc packet:\n%s", packet)
                                self.handle_locationdesc(clw, address, connection, channel)
                            elif command == T_MESSAGE_TYPE.CONFIG:
                                logging.info("[GW] Recv query config packet:\n%s", packet)
                                self.handle_config(clw, address, connection, channel)
                            elif command == T_MESSAGE_TYPE.DEFENDSTATUS:
                                logging.info("[GW] Recv defend status packet:\n%s", packet)
                                self.handle_defend_status(clw, address, connection, channel)
                            elif command == T_MESSAGE_TYPE.FOBINFO:
                                logging.info("[GW] Recv fob info packet:\n%s", packet)
                                self.handle_fob_info(clw, address, connection, channel)
                            elif command == T_MESSAGE_TYPE.SLEEPSTATUS:
                                logging.info("[GW] Recv sleep status packet:\n%s", packet)
                                self.handle_terminal_sleep_status(clw, address, connection, channel)
                            elif command == T_MESSAGE_TYPE.FOBSTATUS:
                                logging.info("[GW] Recv fob status packet:\n%s", packet)
                                self.handle_fob_status(clw, address, connection, channel)
                            elif command == T_MESSAGE_TYPE.RUNTIMESTATUS:
                                logging.info("[GW] Recv runtime status packet:\n%s", packet)
                                self.handle_runtime_status(clw, address, connection, channel)
                            elif command == T_MESSAGE_TYPE.UNBINDSTATUS:
                                logging.info("[GW] Recv unbind status packet:\n%s", packet)
                                self.handle_unbind_status(clw, address, connection, channel)
                            else:
                                logging.info("[GW] Recv packet from terminal:\n%s", packet)
                                self.foward_packet_to_si(clw, packet, address, connection, channel)
                    else:
                        sleep(0.1)
        except:
            logging.exception("[GW] Recv Exception.")

    def handle_login(self, info, address, connection, channel):
        """
        login packet
        0: success, then get a sessionID for terminal and record terminal's address
        1: unregister, have no u_msisdn or t_msisdn
        2: expired, service stop or endtime < now
        3: illegal sim, a mismatch between imsi and sim 
        4: psd wrong. HK
        """
        try:
            sms = None
            args = DotDict(success=GATEWAY.LOGIN_STATUS.SUCCESS,
                           sessionID='')
            lp = LoginParser(info.body, info.head)
            t_info = lp.ret

            if not t_info['dev_id']:
                args.success = GATEWAY.LOGIN_STATUS.ILLEGAL_DEVID
                lc = LoginRespComposer(args)
                request = DotDict(packet=lc.buf,
                                  address=address)
                self.append_gw_request(request, connection, channel)
                logging.error("[GW] Login failed! Invalid terminal dev_id: %s", t_info['dev_id'])
                return

            logging.info("[GW] Checking terminal mobile: %s and owner mobile: %s, Terminal: %s",
                         t_info['t_msisdn'], t_info['u_msisdn'], t_info['dev_id'])
            if not (check_phone(t_info['u_msisdn']) and check_phone(t_info['t_msisdn'])):
                args.success = GATEWAY.LOGIN_STATUS.UNREGISTER 
                lc = LoginRespComposer(args)
                request = DotDict(packet=lc.buf,
                                  address=address)
                self.append_gw_request(request, connection, channel)
                logging.error("[GW] Login failed! Invalid terminal mobile: %s or owner_mobile: %s, dev_id: %s",
                              t_info['t_msisdn'], t_info['u_msisdn'], t_info['dev_id'])
                return

            t_status = self.db.get("SELECT service_status"
                                   "  FROM T_TERMINAL_INFO"
                                   "  WHERE mobile = %s",
                                   t_info['t_msisdn'])
            if t_status and t_status.service_status == GATEWAY.SERVICE_STATUS.OFF:
                args.success = GATEWAY.LOGIN_STATUS.EXPIRED
                lc = LoginRespComposer(args)
                request = DotDict(packet=lc.buf,
                                  address=address)
                self.append_gw_request(request, connection, channel)
                logging.error("[GW] Login failed! terminal service expired! mobile: %s, dev_id: %s",
                              t_info['t_msisdn'], t_info['dev_id'])
                return
 

            logging.info("[GW] Checking imsi: %s and mobile: %s, Terminal: %s",
                         t_info['imsi'], t_info['t_msisdn'], t_info['dev_id'])
            tmobile = self.db.get("SELECT imsi FROM T_TERMINAL_INFO"
                                  "  WHERE mobile = %s", t_info['t_msisdn'])
            if tmobile and tmobile.imsi and tmobile.imsi != t_info['imsi']:
                args.success = GATEWAY.LOGIN_STATUS.ILLEGAL_SIM
                sms = SMSCode.SMS_TERMINAL_HK % (t_info['t_msisdn'])
                SMSHelper.send(t_info['u_msisdn'], sms)
                lc = LoginRespComposer(args)
                request = DotDict(packet=lc.buf,
                                  address=address)
                self.append_gw_request(request, connection, channel)
                logging.error("[GW] Login failed! Illegal SIM: %s for Terminal: %s",
                              t_info['t_msisdn'], t_info['dev_id'])
                return

            terminal = self.db.get("SELECT id, mobile, owner_mobile"
                                   "  FROM T_TERMINAL_INFO"
                                   "  WHERE tid = %s", t_info['dev_id'])
            if t_info['psd']:
                # check terminal exist or not when HK
                if not terminal:
                    args.success = GATEWAY.LOGIN_STATUS.UNREGISTER
                    sms = SMSCode.SMS_TID_NOT_EXIST
                    SMSHelper.send(t_info['u_msisdn'], sms)
                    lc = LoginRespComposer(args)
                    request = DotDict(packet=lc.buf,
                                      address=address)
                    self.append_gw_request(request, connection, channel)
                    logging.error("[GW] Login failed! Terminal %s execute HK, but tid is not exist",
                                  t_info['dev_id'])
                    return
                # HK, change terminal mobile or owner mobile
                logging.info("[GW] Checking password. Terminal: %s",
                             t_info['dev_id'])
                owner = self.db.get("SELECT id FROM T_USER"
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
                            old_bind = self.db.get("SELECT id, tid FROM T_TERMINAL_INFO"
                                                   "  WHERE mobile = %s"
                                                   "    AND id != %s",
                                                   t_info['t_msisdn'], terminal.id)
                            if old_bind:
                                # clear db
                                self.db.execute("DELETE FROM T_TERMINAL_INFO"
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
                            self.db.execute("UPDATE T_TERMINAL_INFO"
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
                            # subscription le for new sim
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
                            logging.info("[GW] Terminal: %s HK success!", t_info['dev_id'])

                        if terminal.owner_mobile != t_info['u_msisdn']:
                            logging.info("[GW] Owner HK started. Terminal: %s", t_info['dev_id'])
                            # owner HK
                            user = self.db.get("SELECT id FROM T_USER"
                                               "  WHERE mobile = %s",
                                               t_info['u_msisdn'])
                            if user:
                                logging.info("[GW] Owner already existed. Terminal: %s", t_info['dev_id'])
                                sms = SMSCode.SMS_USER_ADD_TERMINAL % (t_info['t_msisdn'],
                                                                       ConfHelper.UWEB_CONF.url_out) 
                            else:
                                logging.info("[GW] Create new owner started. Terminal: %s", t_info['dev_id'])
                                psd = get_psd()
                                self.db.execute("INSERT INTO T_USER"
                                                "  VALUES(NULL, %s, password(%s), %s, %s, NULL, NULL, NULL)",
                                                t_info['u_msisdn'],
                                                psd,
                                                t_info['u_msisdn'],
                                                t_info['u_msisdn'])
                                self.db.execute("INSERT INTO T_SMS_OPTION(uid)"
                                                "  VALUES(%s)",
                                                t_info['u_msisdn'])
                                sms = SMSCode.SMS_USER_HK_SUCCESS % (t_info['u_msisdn'],
                                                                     ConfHelper.UWEB_CONF.url_out,
                                                                     t_info['u_msisdn'],
                                                                     psd)
                            self.db.execute("UPDATE T_TERMINAL_INFO"
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
                    # check tid conflict
                    if terminal.mobile != t_info['t_msisdn']:
                        args.success = GATEWAY.LOGIN_STATUS.ILLEGAL_SIM
                        sms = SMSCode.SMS_TID_EXIST % t_info['dev_id']
                        logging.error("[GW] Login failed! Terminal: %s already bound by %s, new mobile: %s",
                                      t_info['dev_id'], terminal.mobile, t_info['t_msisdn'])
                    else:
                        logging.info("[GW] Terminal: %s Normal login started!",
                                     t_info['dev_id']) 
                else:
                    # SMS JH or admin JH or change new dev JH
                    logging.info("[GW] Terminal: %s JH started.", t_info['dev_id'])
                    exist = self.db.get("SELECT id FROM T_USER"
                                        "  WHERE mobile = %s",
                                        t_info['u_msisdn'])
                    if exist:
                        logging.info("[GW] Owner already existed. Terminal: %s", t_info['dev_id'])
                        sms = SMSCode.SMS_USER_ADD_TERMINAL % (t_info['t_msisdn'],
                                                               ConfHelper.UWEB_CONF.url_out)
                    else:
                        # get a new psd for new user
                        logging.info("[GW] Create new owner started. Terminal: %s", t_info['dev_id'])
                        psd = get_psd()
                        self.db.execute("INSERT INTO T_USER(uid, password, name, mobile)"
                                        "  VALUES(%s, password(%s), %s, %s)",
                                        t_info['u_msisdn'], psd,
                                        t_info['u_msisdn'], t_info['u_msisdn'])
                        self.db.execute("INSERT INTO T_SMS_OPTION(uid)"
                                        "  VALUES(%s)",
                                        t_info['u_msisdn'])
                        sms = SMSCode.SMS_JH_SUCCESS % (t_info['t_msisdn'],
                                                        ConfHelper.UWEB_CONF.url_out,
                                                        t_info['u_msisdn'],
                                                        psd)

                    admin_terminal = self.db.get("SELECT id, tid FROM T_TERMINAL_INFO"
                                                 "  WHERE tid = %s",
                                                 t_info['t_msisdn'])
                    if admin_terminal:
                        # admin JH
                        self.db.execute("UPDATE T_TERMINAL_INFO"
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
                        self.db.execute("UPDATE T_CAR SET tid = %s"
                                        "  WHERE tid = %s",
                                        t_info['dev_id'], t_info['t_msisdn'])
                        logging.info("[GW] Terminal %s by ADMIN JH success!", t_info['dev_id'])
                    else:
                        exist_terminal = self.db.get("SELECT id, tid FROM T_TERMINAL_INFO"
                                                     "  WHERE mobile = %s",
                                                     t_info['t_msisdn'])
                        if exist_terminal:
                            # unbind old tmobile
                            self.db.execute("DELETE FROM T_TERMINAL_INFO"
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
                            # remove old online dev
                            if exist_terminal.tid in self.online_terminals:
                                self.online_terminals.remove(exist_terminal.tid)
                            logging.info("[GW] Terminal %s change dev, old dev: %s!",
                                         t_info['dev_id'], exist_terminal.tid)

                        # send JH sms to terminal. default active time
                        # is one year.
                        begintime = datetime.datetime.now() 
                        endtime = begintime + relativedelta(years=1)
                        self.db.execute("INSERT INTO T_TERMINAL_INFO(tid, dev_type, mobile,"
                                        "  owner_mobile, imsi, imei, factory_name, softversion,"
                                        "  keys_num, login, service_status, begintime, endtime)"
                                        "  VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, DEFAULT, %s, %s, %s)",
                                        t_info['dev_id'], t_info['dev_type'],
                                        t_info['t_msisdn'], t_info['u_msisdn'],
                                        t_info['imsi'], t_info['imei'],
                                        t_info['factory_name'],
                                        t_info['softversion'], t_info['keys_num'], 
                                        GATEWAY.SERVICE_STATUS.ON,
                                        int(time.mktime(begintime.timetuple())),
                                        int(time.mktime(endtime.timetuple())))
                        self.db.execute("INSERT INTO T_CAR(tid)"
                                        "  VALUES(%s)",
                                        t_info['dev_id'])
                        logging.info("[GW] Terminal %s by SMS JH success!", t_info['dev_id'])

                    # subscription LE for new sim
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

            if args.success == GATEWAY.LOGIN_STATUS.SUCCESS:
                # get SessionID
                args.sessionID = get_sessionID()
                terminal_sessionID_key = get_terminal_sessionID_key(t_info['dev_id'])
                self.redis.setvalue(terminal_sessionID_key, args.sessionID)
                # record terminal address
                self.update_terminal_status(t_info["dev_id"], address)
                # append into online terminals
                if not t_info["dev_id"] in self.online_terminals:
                    self.online_terminals.append(t_info["dev_id"])
                # set login
                info = DotDict(login=GATEWAY.TERMINAL_LOGIN.ONLINE,
                               mobile=t_info['t_msisdn'],
                               keys_num=t_info['keys_num'],
                               dev_id=t_info["dev_id"])
                self.update_terminal_info(info)
                logging.info("[GW] Terminal %s login success! SIM: %s",
                             t_info['dev_id'], t_info['t_msisdn'])

            lc = LoginRespComposer(args)
            request = DotDict(packet=lc.buf,
                              address=address)
            self.append_gw_request(request, connection, channel)
                    
            if sms:
                SMSHelper.send(t_info['u_msisdn'], sms)
        except:
            logging.exception("[GW] Hand login exception.")
        
    def handle_heartbeat(self, info, address, connection, channel):
        """
        heartbeat packet
        0: success, then record new terminal's address
        1: invalid SessionID 
        """
        try:
            head = info.head
            body = info.body
            args = DotDict(success=GATEWAY.RESPONSE_STATUS.SUCCESS)
            sessionID = self.get_terminal_sessionID(head.dev_id)
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
                else:
                    logging.info("[GW] Recv wrong sleep status: %s", heartbeat_info)
                del heartbeat_info['sleep_status']

                self.update_terminal_status(head.dev_id, address, is_sleep)
                self.update_terminal_info(heartbeat_info)

            hc = HeartbeatRespComposer(args)
            request = DotDict(packet=hc.buf,
                              address=address)
            self.append_gw_request(request, connection, channel)
        except:
            logging.error("[GW] Hand heartbeat exception.")

    def handle_locationdesc(self, info, address, connection, channel):
        """
        locationdesc packet
        0: success, then return locationdesc to terminal and record new terminal's address
        1: invalid SessionID 
        """
        try:
            head = info.head
            body = info.body
            resend_key = get_resend_key(head.dev_id, head.timestamp, head.command)
            resend_flag = self.redis.getvalue(resend_key)
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
                    self.redis.setvalue(resend_key, True, GATEWAY.RESEND_EXPIRY)
                    ldp = LocationDescParser(body, head)
                    location = ldp.ret
                    location['t'] = EVENTER.INFO_TYPE.POSITION
                    if location['valid'] != GATEWAY.LOCATION_STATUS.SUCCESS:
                        cellid = True
                    else:
                        cellid = False
                    location = lbmphelper.handle_location(location, self.redis, cellid=cellid)
                    location.name = location.get('name') if location.get('name') else ""
                    location.name = safe_unicode(location.name)
                    locationdesc = location.name.encode("utf-8", 'ignore')
                    user = QueryHelper.get_user_by_tid(head.dev_id, self.db)
                    tname = QueryHelper.get_alias_by_tid(head.dev_id, self.redis, self.db)
                    dw_method = u'GPS' if not cellid else u'基站'
                    if location.cLat and location.cLon:
                        if user:
                            current_time = get_terminal_time(int(time.time()))
                            sms = SMSCode.SMS_DW_SUCCESS % (tname, dw_method,
                                                            unicode(locationdesc, 'utf-8'), 
                                                            current_time) 
                            url = ConfHelper.UWEB_CONF.url_out + '/wapimg?clon=' +\
                                  str(location.cLon/3600000.0) + '&clat=' + str(location.cLat/3600000.0)
                            tiny_id = URLHelper.get_tinyid(url)
                            if tiny_id:
                                base_url = ConfHelper.UWEB_CONF.url_out + UWebHelper.URLS.TINYURL
                                tiny_url = base_url + '/' + tiny_id
                                logging.info("[GW] get tiny url successfully. tiny_url:%s", tiny_url)
                                self.redis.setvalue(tiny_id, url, time=EVENTER.TINYURL_EXPIRY)
                                sms += u"点击 " + tiny_url + u" 查看车辆位置。" 
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
                        self.insert_location(location)
                self.update_terminal_status(head.dev_id, address)

            lc = LocationDescRespComposer(args)
            request = DotDict(packet=lc.buf,
                              address=address)
            self.append_gw_request(request, connection, channel)
        except:
            logging.exception("[GW] Handle locationdesc exception.")

    def handle_config(self, info, address, connection, channel):
        """
        config packet
        0: success, then record new terminal's address
        1: invalid SessionID 
        """
        try:
            head = info.head
            body = info.body
            args = DotDict(success=GATEWAY.RESPONSE_STATUS.SUCCESS,
                           domain="",
                           freq="",
                           trace="",
                           static_val="",
                           move_val="",
                           trace_para="",
                           vibl="")
            sessionID = self.get_terminal_sessionID(head.dev_id)
            if sessionID != head.sessionID:
                args.success = GATEWAY.RESPONSE_STATUS.INVALID_SESSIONID 
            else:
                self.update_terminal_status(head.dev_id, address)
                args.domain = ConfHelper.GW_SERVER_CONF.domain 
                terminal = self.db.get("SELECT freq, trace, static_val,"
                                       "       move_val, trace_para, vibl"
                                       "  FROM T_TERMINAL_INFO"
                                       "  WHERE tid = %s", head.dev_id)
                args.freq = terminal.freq
                args.trace = terminal.trace
                args.static_val = terminal.static_val
                args.move_val = terminal.move_val
                args.trace_para = terminal.trace_para
                args.vibl = terminal.vibl

            hc = ConfigRespComposer(args)
            request = DotDict(packet=hc.buf,
                              address=address)
            self.append_gw_request(request, connection, channel)
        except:
            logging.exception("[GW] Hand query config exception.")

    def handle_defend_status(self, info, address, connection, channel):
        """
        defend status report packet
        0: success, then record new terminal's address
        1: invalid SessionID 
        """
        try:
            head = info.head
            body = info.body
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
                            tname = QueryHelper.get_alias_by_tid(head.dev_id, self.redis, self.db)
                            sms = SMSCode.SMS_DEFEND_SUCCESS % (tname, _status) 
                            user = QueryHelper.get_user_by_tid(head.dev_id, self.db)
                            if user:
                                SMSHelper.send(user.owner_mobile, sms)
                        del defend_info['defend_status']
                    del defend_info['defend_source']
                    self.update_terminal_info(defend_info)
                self.update_terminal_status(head.dev_id, address)

            hc = AsyncRespComposer(args)
            request = DotDict(packet=hc.buf,
                              address=address)
            self.append_gw_request(request, connection, channel)
        except:
            logging.exception("[GW] Hand defend status report exception.")

    def handle_fob_info(self, info, address, connection, channel):
        """
        fob info packet: add or remove fob
        0: success, then record new terminal's address
        1: invalid SessionID
        """
        try:
            head = info.head
            body = info.body
            args = DotDict(success=GATEWAY.RESPONSE_STATUS.SUCCESS)
            sessionID = self.get_terminal_sessionID(head.dev_id)
            if sessionID != head.sessionID:
                args.success = GATEWAY.RESPONSE_STATUS.INVALID_SESSIONID 
            else:
                fp = FobInfoParser(body, head)
                fobinfo = fp.ret
                self.update_terminal_status(head.dev_id, address)
                self.update_fob_info(fobinfo)

            fc = FobInfoRespComposer(args)
            request = DotDict(packet=fc.buf,
                              address=address)
            self.append_gw_request(request, connection, channel)
        except:
            logging.exception("[GW] Hand fob info report exception.")

    def handle_terminal_sleep_status(self, info, address, connection, channel):
        """
        sleep status packet: 0-sleep, 1-LQ
        0: success, then record new terminal's address
        1: invalid SessionID
        """
        try:
            head = info.head
            body = info.body
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
                    self.update_terminal_info(sleep_info)

                self.update_terminal_status(head.dev_id, address, is_sleep)

            hc = AsyncRespComposer(args)
            request = DotDict(packet=hc.buf,
                              address=address)
            self.append_gw_request(request, connection, channel)
        except:
            logging.exception("[GW] Hand sleep status report exception.")

    def handle_fob_status(self, info, address, connection, channel):
        """
        fob status packet: 0-no fob near, 1-have fob near
        0: success, then record new terminal's address
        1: invalid SessionID
        """
        try:
            head = info.head
            body = info.body
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
                    self.update_terminal_info(fob_info)
                self.update_terminal_status(head.dev_id, address)

            hc = AsyncRespComposer(args)
            request = DotDict(packet=hc.buf,
                              address=address)
            self.append_gw_request(request, connection, channel)
        except:
            logging.exception("[GW] Hand fob status report exception.")

    def handle_runtime_status(self, info, address, connection, channel):
        """
        runtime status packet: {login [0:unlogin | 1:login],
                                defend_status [0:undefend | 1:defend],
                                gps:gsm:pbat [0-100:0-9:0-100]} 
        0: success, then record new terminal's address
        1: invalid SessionID
        """
        try:
            head = info.head
            body = info.body
            resend_key = get_resend_key(head.dev_id, head.timestamp, head.command)
            resend_flag = self.redis.getvalue(resend_key)
            if len(body) == 3:
                body.append('-1')
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
                    terminal_info = self.get_terminal_info(head.dev_id)
                    args.mannual_status = terminal_info['mannual_status']
                else:
                    self.redis.setvalue(resend_key, True, GATEWAY.RESEND_EXPIRY)
                    hp = AsyncParser(body, head)
                    runtime_info = hp.ret 
                    self.update_terminal_status(head.dev_id, address)
                    terminal_info = self.update_terminal_info(runtime_info)
                    args.mannual_status = terminal_info['mannual_status']
                    self.db.execute("INSERT INTO T_RUNTIME_STATUS"
                                    "  VALUES(NULL, %s, %s, %s, %s, %s, %s, %s, %s)",
                                    head.dev_id, runtime_info['login'], runtime_info['defend_status'],
                                    runtime_info['gps'], runtime_info['gsm'], runtime_info['pbat'],
                                    runtime_info['fob_pbat'], head.timestamp)
                self.update_terminal_status(head.dev_id, address)
            rc = RuntimeRespComposer(args)
            request = DotDict(packet=rc.buf,
                              address=address)
            self.append_gw_request(request, connection, channel)
        except:
            logging.exception("[GW] Handle runtime status report exception.")

    def handle_unbind_status(self, info, address, connection, channel):
        """
        unbind status report packet
        0: success, then record new terminal's address
        1: invalid SessionID 
        """
        try:
            head = info.head
            body = info.body
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
                    self.delete_terminal(head.dev_id)

            hc = AsyncRespComposer(args)
            request = DotDict(packet=hc.buf,
                              address=address)
            self.append_gw_request(request, connection, channel)
        except:
            logging.exception("[GW] Hand defend status report exception.")


    def foward_packet_to_si(self, info, packet, address, connection, channel):
        """
        response packet or position/report/charge packet
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

            if head.command in (T_MESSAGE_TYPE.POSITION, T_MESSAGE_TYPE.MULTIPVT,
                                T_MESSAGE_TYPE.CHARGE, T_MESSAGE_TYPE.ILLEGALMOVE,
                                T_MESSAGE_TYPE.POWERLOW, T_MESSAGE_TYPE.ILLEGALSHAKE,
                                T_MESSAGE_TYPE.EMERGENCY):
                rc = AsyncRespComposer(args)
                request = DotDict(packet=rc.buf,
                                  address=address)
                self.append_gw_request(request, connection, channel)
                # resend flag
                if not resend_flag:
                    self.redis.setvalue(resend_key, True, GATEWAY.RESEND_EXPIRY)
            elif head.command == GATEWAY.T_MESSAGE_TYPE.UNBIND:
                up = UNBindParser(info.body, info.head)
                status = up.ret['status']
                if status == GATEWAY.STATUS.SUCCESS:
                    self.delete_terminal(dev_id)
        except:
            logging.exception("[GW] Handle SI message exception.")

    def append_gw_request(self, request, connection, channel):
        message = json.dumps(request)
        try:
            # make message not persistent
            properties = pika.BasicProperties(delivery_mode=1,)
            channel.basic_publish(exchange=self.exchange,
                                  routing_key=self.gw_binding,
                                  body=message,
                                  properties=properties)
        except AMQPConnectionError as e:
            logging.exception("[GW] Rabbitmq publish into gw_queue error: %s", e.args)
        except Exception as e:
            logging.exception("[GW] Unknown publish error: %s", e.args)

    def append_si_request(self, request, connection, channel):
        request = dict({"packet":request})
        message = json.dumps(request)
        try:
            # make message not persistent
            properties = pika.BasicProperties(delivery_mode=1,)
            channel.basic_publish(exchange=self.exchange,
                                  routing_key=self.si_binding,
                                  body=message,
                                  properties=properties)
        except AMQPConnectionError as e:
            logging.exception("[GW] Rabbitmq publish into si_queue error: %s", e.args)
        except Exception as e:
            logging.exception("[GW] Unknown publish error: %s", e.args)

    def insert_location(self, location):
        # insert data into T_LOCATION
        lid = self.db.execute("INSERT INTO T_LOCATION"
                              "  VALUES (NULL, %s, %s, %s, %s, %s, %s, %s,"
                              "          %s, %s, %s, %s, %s, %s)",
                              location.dev_id, location.lat, location.lon, 
                              location.alt, location.cLat, location.cLon,
                              location.gps_time, location.name,
                              location.category, location.type,
                              location.speed, location.degree,
                              location.cellid)
        is_alived = self.redis.getvalue('is_alived')
        if (is_alived == ALIVED and location.cLat and location.cLon):
            mem_location = DotDict({'id':lid,
                                    'latitude':location.lat,
                                    'longitude':location.lon,
                                    'type':location.type,
                                    'clatitude':location.cLat,
                                    'clongitude':location.cLon,
                                    'timestamp':location.gps_time,
                                    'name':location.name,
                                    'degree':location.degree,
                                    'speed':location.speed})
            location_key = get_location_key(location.dev_id)
            self.redis.setvalue(location_key, mem_location, EVENTER.LOCATION_EXPIRY)

        return lid

    def delete_terminal(self, dev_id):
        # clear db
        user = QueryHelper.get_user_by_tid(dev_id, self.db)
        self.db.execute("DELETE FROM T_TERMINAL_INFO"
                        "  WHERE tid = %s", 
                        dev_id) 
        if user:
            terminals = self.db.query("SELECT id FROM T_TERMINAL_INFO"
                                      "  WHERE owner_mobile = %s",
                                      user.owner_mobile)
            if len(terminals) == 0:
                self.db.execute("DELETE FROM T_USER"
                                "  WHERE mobile = %s",
                                user.owner_mobile)

                lastinfo_key = get_lastinfo_key(user.owner_mobile)
                self.redis.delete(lastinfo_key)
        else:
            logging.info("[GW] User of %s already not exist.", dev_id)
        # clear redis
        sessionID_key = get_terminal_sessionID_key(dev_id)
        address_key = get_terminal_address_key(dev_id)
        info_key = get_terminal_info_key(dev_id)
        lq_sms_key = get_lq_sms_key(dev_id)
        lq_interval_key = get_lq_interval_key(dev_id)
        keys = [sessionID_key, address_key, info_key, lq_sms_key, lq_interval_key]
        self.redis.delete(*keys)
        # offline
        if dev_id in self.online_terminals:
            self.online_terminals.remove(dev_id)
        logging.info("[GW] Delete Terminal: %s, umobile: %s",
                     dev_id, (user.owner_mobile if user else None))
        
    def get_terminal_sessionID(self, dev_id):
        terminal_sessionID_key = get_terminal_sessionID_key(dev_id) 
        sessionID = self.redis.getvalue(terminal_sessionID_key)

        return sessionID

    def update_terminal_status(self, dev_id, address, is_sleep=False):
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

    def update_fob_info(self, fobinfo):
        terminal_info_key = get_terminal_info_key(fobinfo['dev_id'])
        terminal_info = self.redis.getvalue(terminal_info_key)
        if not terminal_info:
            terminal_info = self.db.get("SELECT mannual_status, defend_status,"
                                        "  fob_status, mobile, login, gps, gsm,"
                                        "  pbat, keys_num"
                                        "  FROM T_TERMINAL_INFO"
                                        "  WHERE tid = %s", fobinfo['dev_id'])
            car = self.db.get("SELECT cnum FROM T_CAR"
                              "  WHERE tid = %s", fobinfo['dev_id'])
            fobs = self.db.query("SELECT fobid FROM T_FOB"
                                 "  WHERE tid = %s", fobinfo['dev_id'])
            terminal_info = DotDict(terminal_info)
            terminal_info['alias'] = car.cnum if car.cnum else terminal_info.mobile
            terminal_info['fob_list'] = [fob.fobid for fob in fobs]

        if int(fobinfo['operate']) == GATEWAY.FOB_OPERATE.ADD:
            self.db.execute("INSERT INTO T_FOB(tid, fobid)"
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
            self.db.execute("UPDATE T_TERMINAL_INFO"
                            "  SET keys_num = %s"
                            "  WHERE tid = %s", 
                            terminal_info['keys_num'], fobinfo['dev_id'])
            self.redis.setvalue(terminal_info_key, terminal_info)
        elif int(fobinfo['operate']) == GATEWAY.FOB_OPERATE.REMOVE:
            self.db.execute("DELETE FROM T_FOB"
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
            self.db.execute("UPDATE T_TERMINAL_INFO"
                            "  SET keys_num = %s"
                            "  WHERE tid = %s", 
                            terminal_info['keys_num'], fobinfo['dev_id'])
            self.redis.setvalue(terminal_info_key, terminal_info)
        else:
            pass

    def get_terminal_info(self, dev_id):
        terminal_info_key = get_terminal_info_key(dev_id)
        terminal_info = self.redis.getvalue(terminal_info_key)
        if not terminal_info:
            terminal_info = self.db.get("SELECT mannual_status, defend_status,"
                                        "  fob_status, mobile, login, gps, gsm,"
                                        "  pbat, keys_num"
                                        "  FROM T_TERMINAL_INFO"
                                        "  WHERE tid = %s", dev_id)
            car = self.db.get("SELECT cnum FROM T_CAR"
                              "  WHERE tid = %s", dev_id)
            fobs = self.db.query("SELECT fobid FROM T_FOB"
                                 "  WHERE tid = %s", dev_id)
            terminal_info = DotDict(terminal_info)
            terminal_info['alias'] = car.cnum if car.cnum else terminal_info.mobile
            terminal_info['fob_list'] = [fob.fobid for fob in fobs]
            self.redis.setvalue(terminal_info_key, terminal_info)
        return terminal_info

    def update_terminal_info(self, t_info):
        terminal_info_key = get_terminal_info_key(t_info['dev_id'])
        terminal_info = self.redis.getvalue(terminal_info_key)
        if not terminal_info:
            terminal_info = self.db.get("SELECT mannual_status, defend_status,"
                                        "  fob_status, mobile, login, gps, gsm,"
                                        "  pbat, keys_num"
                                        "  FROM T_TERMINAL_INFO"
                                        "  WHERE tid = %s", t_info['dev_id'])
            car = self.db.get("SELECT cnum FROM T_CAR"
                              "  WHERE tid = %s", t_info['dev_id'])
            fobs = self.db.query("SELECT fobid FROM T_FOB"
                                 "  WHERE tid = %s", t_info['dev_id'])
            terminal_info = DotDict(terminal_info)
            terminal_info['alias'] = car.cnum if car.cnum else terminal_info.mobile
            terminal_info['fob_list'] = [fob.fobid for fob in fobs]

        # db
        fields = []
        # gps, gsm, pbat, changed by position report
        keys = ['mobile', 'defend_status', 'login', 'keys_num', 'fob_status', 'mannual_status']
        for key in keys:
            value = t_info.get(key, None)
            if value is not None and value != terminal_info[key]:
                fields.append(key + " = " + str(t_info[key]))
        set_clause = ','.join(fields)
        if set_clause:
            self.db.execute("UPDATE T_TERMINAL_INFO"
                            "  SET " + set_clause + 
                            "  WHERE tid = %s",
                            t_info['dev_id'])
        # redis
        for key in terminal_info:
            value = t_info.get(key, None)
            if value is not None:
                terminal_info[key] = value
        self.redis.setvalue(terminal_info_key, terminal_info)

        return terminal_info

    def get_terminal_status(self, dev_id):
        terminal_status_key = get_terminal_address_key(dev_id)
        return self.redis.getvalue(terminal_status_key)

    def __close_rabbitmq(self, connection=None, channel=None):
        if connection and connection.is_open:
            try:
                channel.queue_delete(queue=self.gw_queue)
            except AMQPChannelError:
                logging.warn("[GW] Delete gw_queue error: already delete.")
            connection.close()

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
