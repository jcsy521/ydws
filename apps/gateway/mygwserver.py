# -*- coding: utf-8 -*-

import socket, select, errno 
import logging
import time
from time import sleep
import datetime
from dateutil.relativedelta import relativedelta
import Queue
import base64
import pika
from pika.adapters import *
import json
from functools import partial

from utils.dotdict import DotDict
from utils.repeatedtimer import RepeatedTimer
from utils.checker import check_phone
from db_.mysql import DBConnection
from utils.myredis import MyRedis
from utils.misc import get_terminal_address_key, get_alarm_status_key,\
     get_terminal_time, get_sessionID, get_terminal_sessionID_key,\
     get_lq_interval_key, get_alias_key, safe_unicode, get_psd
from constants.GATEWAY import T_MESSAGE_TYPE, HEARTBEAT_INTERVAL,\
     SLEEP_HEARTBEAT_INTERVAL
from constants.MEMCACHED import ALIVED
from constants import EVENTER, GATEWAY
from codes.smscode import SMSCode

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
        # RabbitMQ
        self.rabbitmq_connection = None
        self.rabbitmq_channel = None
        self.exchange = 'acb_exchange'
        self.gw_queue = 'gw_requests_queue'
        self.si_queue = 'si_requests_queue'
        self.gw_binding = 'gw_requests_binding'
        self.si_binding = 'si_requests_binding'
        self.rabbitmq_connection, self.rabbitmq_channel = self.__connect_rabbitmq(ConfHelper.RABBITMQ_CONF.host)

        self.socket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((ConfHelper.GW_SERVER_CONF.host, ConfHelper.GW_SERVER_CONF.port))
        #self.__restore_online_terminals()
        #self.__start_check_heartbeat_thread()

    def __connect_rabbitmq(self, host):
        connection = None
        channel = None
        try:
            parameters = pika.ConnectionParameters(host=host)
            connection = BlockingConnection(parameters)
            channel = connection.channel()
            channel.exchange_declare(exchange=self.exchange,
                                     durable=False,
                                     auto_delete=True)
            channel.queue_declare(queue=self.gw_queue,
                                  durable=False, # not persistent
                                  exclusive=True, # only use by creator
                                  auto_delete=True) # all client break connection, auto del
            channel.queue_bind(exchange=self.exchange,
                               queue=self.gw_queue,
                               routing_key=self.gw_binding)
        except:
            logging.exception("[GW] Connect Rabbitmq-server Error!")

        return connection, channel

    def check_heartbeat(self):
        try:
            is_alived = self.redis.getvalue("is_alived")
            if is_alived == ALIVED:
                for dev_id in self.online_terminals:
                    status = self.get_terminal_status(dev_id)
                    if not status:
                        self.heartbeat_lost_report(dev_id)
        except:
            logging.exception("[GW] Check gateway heartbeat exception.")
                
    def get_tname(self, dev_id):
        key = get_alias_key(dev_id)
        name = self.redis.getvalue(key)
        if not name:
            t = self.db.get("SELECT alias, mobile FROM T_TERMINAL_INFO"
                            "  WHERE tid = %s", dev_id)
            name = t.alias if t.alias else t.mobile
            self.redis.setvalue(key, name)
        if isinstance(name, str):
            name = name.decode("utf-8")

        return name

    def heartbeat_lost_report(self, dev_id):
        timestamp = int(time.time())
        rname = EVENTER.RNAME.HEARTBEAT_LOST
        category = EVENTER.CATEGORY[rname]
        lid = self.db.execute("INSERT INTO T_LOCATION(tid, timestamp, category, type)"
                              "  VALUES(%s, %s, %s, %s)",
                              dev_id, timestamp, category, 1)
        self.db.execute("INSERT INTO T_EVENT"
                        "  VALUES (NULL, %s, DEFAULT, %s, NULL, %s)",
                        dev_id, lid, category)
        #alarm_key = get_alarm_status_key(dev_id)
        #alarm_status = self.redis.getvalue(alarm_key)
        #if alarm_status != rname: 
        #    self.redis.setvalue(alarm_key, category) 
        user = QueryHelper.get_user_by_tid(dev_id, self.db)
        current_time = get_terminal_time(timestamp) 
        tname = self.get_tname(dev_id)
        sms = SMSCode.SMS_HEARTBEAT_LOST % (tname, current_time)
        if user:
            SMSHelper.send(user.owner_mobile, sms)
        logging.warn("[GW] Terminal %s Heartbeat lost!!! SMS: %s", dev_id, sms)
        # 1. memcached clear sessionID
        terminal_sessionID_key = get_terminal_sessionID_key(dev_id)
        self.redis.delete(terminal_sessionID_key)
        # 2. offline
        self.online_terminals.remove(dev_id)
        # 3. db set unlogin
        info = DotDict(dev_id=dev_id,
                       login=GATEWAY.TERMINAL_LOGIN.UNLOGIN)
        self.update_terminal_info(info)

    def __start_check_heartbeat_thread(self):
        self.check_heartbeat_thread = RepeatedTimer(ConfHelper.GW_SERVER_CONF.check_heartbeat_interval,
                                                    self.check_heartbeat)
        self.check_heartbeat_thread.start()
        logging.info("[GW] Check heartbeat thread is running...")

    def __restore_online_terminals(self):
        """
        if restart gatewayserver, record online terminals again.
        """
        db = DBConnection().db
        redis = MyRedis()
        online_terminals = db.query("SELECT tid FROM T_TERMINAL_INFO"
                                    "  WHERE login = %s",
                                    GATEWAY.TERMINAL_LOGIN.LOGIN)
        for terminal in online_terminals:
            db.execute("UPDATE T_TERMINAL_INFO"
                       "  SET login = %s"
                       "  WHERE tid = %s",
                       GATEWAY.TERMINAL_LOGIN.UNLOGIN, terminal.tid)
            terminal_status_key = get_terminal_address_key(terminal.tid)
            terminal_sessionID_key = get_terminal_sessionID_key(terminal.tid)
            keys = [terminal_status_key, terminal_sessionID_key]
            self.redis.delete(*keys)
            #terminal_status_key = get_terminal_address_key(terminal.tid)
            #terminal_status = redis.getvalue(terminal_status_key)
            #if terminal_status:
            #    self.online_terminals.append(terminal.tid)
            #else:
            #    db.execute("UPDATE T_TERMINAL_INFO"
            #               "  SET login = %s"
            #               "  WHERE tid = %s",
            #               GATEWAY.TERMINAL_LOGIN.UNLOGIN, terminal.tid)
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
        try:
            while True:
                method, header, body = self.rabbitmq_channel.basic_get(queue=self.gw_queue)
                if method.NAME == 'Basic.GetEmpty':
                    sleep(1) 
                else:
                    self.rabbitmq_channel.basic_ack(delivery_tag=method.delivery_tag)
                    self.send(body)
        except KeyboardInterrupt:
            logging.warn("[GW] Ctrl-C is pressed")
        except Exception as e:
            logging.exception("[GW] Unknow Exception:%s", e.args)
        finally:
            self.stop()

    def send(self, body):
        try:
            message = json.loads(body)
            message = DotDict(message)
            self.socket.sendto(message.packet, tuple(message.address))
            logging.info("[GW] send: %s to %s", message.packet, message.address)
        except socket.error as e:
            logging.exception("[GW]sock send error: %s", e.args)
        except Exception as e:
            logging.exception("[GW]unknown send Exception:%s", e.args)

    def publish(self, host):
        try:
            #NOTE: self.online_terminals, this process will change it!
            self.__restore_online_terminals()
            self.__start_check_heartbeat_thread()

            self.recv()
        except KeyboardInterrupt:
            logging.warn("[GW] Ctrl-C is pressed")
        except Exception as e:
            logging.exception("[GW] Unknow Exception:%s", e.args)
        finally:
            self.stop()

    def recv(self):
        try:
            while True:
                response, address = self.socket.recvfrom(1024)
                logging.info("[GW] recv: %s from %s", response, address)
                if response:
                    self.handle_packet_from_terminal(response,
                                                     address)
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
        
    def handle_packet_from_terminal(self, packets, address):
        """
        handle packet recv from terminal:
        - login
        - heartbeat
        - locationdesc
        - other, forward it to si.
        """
        try:
            packets = self.divide_packets(packets)
            for packet in packets:
                clw = T_CLWCheck(packet)
                command = clw.head.command
                if command == T_MESSAGE_TYPE.LOGIN:
                    logging.info("[GW] Recv login packet:\n%s", packet)
                    self.handle_login(clw, address) 
                elif command == T_MESSAGE_TYPE.HEARTBEAT:
                    logging.info("[GW] Recv heartbeat packet:\n%s", packet)
                    self.handle_heartbeat(clw, address)
                elif command == T_MESSAGE_TYPE.LOCATIONDESC:
                    logging.info("[GW] Recv locationdesc packet:\n%s", packet)
                    self.handle_locationdesc(clw, address)
                else:
                    logging.info("[GW] Recv packet from terminal:\n%s", packet)
                    self.foward_packet_to_si(clw, packet, address)
        except:
            logging.exception("[GW] Recv Exception.")

    def handle_login(self, info, address):
        """
        login packet
        0: success, then get a sessionID for terminal and record terminal's address
        1: unregister, have no u_msisdn or t_msisdn
        2: expired, service stop or endtime < now
        3: illegal sim, a mismatch between imsi and sim 
        4: psd wrong. HK
        """
        try:
            smses = [] 
            is_change = False
            args = DotDict(success=GATEWAY.LOGIN_STATUS.SUCCESS,
                           sessionID='')
            lp = LoginParser(info.body, info.head)
            t_info = lp.ret

            if not (check_phone(t_info['u_msisdn']) and check_phone(t_info['t_msisdn'])):
                args.success = GATEWAY.LOGIN_STATUS.UNREGISTER 
                if check_phone(t_info['u_msisdn']):
                    sms = SMSCode.SMS_JH_FAILED
                    SMSHelper.send(t_info['u_msisdn'], sms)
                lc = LoginRespComposer(args)
                request = DotDict(packet=lc.buf,
                                  address=address)
                self.append_gw_request(request)
                logging.error("[GW] Login failed! Invalid terminal mobile: %s or owner_mobile: %s, dev_id: %s",
                              info['t_msisdn'], t_info['u_msisdn'], t_info['dev_id'])
                return

            terminal = self.db.get("SELECT id, tid, owner_mobile, imsi, service_status, endtime"
                                   "  FROM T_TERMINAL_INFO"
                                   "  WHERE mobile = %s",
                                   t_info['t_msisdn'])
            if terminal:
                if (terminal.endtime < time.time() or
                    terminal.service_status == GATEWAY.SERVICE_STATUS.OFF):
                    # expired or stop service
                    args.success = GATEWAY.LOGIN_STATUS.EXPIRED
                    logging.error("[GW] Login failed! Expired Terminal: %s, SIM: %s",
                                  t_info['dev_id'], t_info['t_msisdn'])
                elif terminal.tid == t_info['t_msisdn']:
                    # first login, admin regist terminal
                    psd = get_psd()
                    sms = SMSCode.SMS_JH_SUCCESS % (t_info['t_msisdn'],
                                                    ConfHelper.UWEB_CONF.url_out,
                                                    t_info['u_msisdn'],
                                                    psd)
                    smses.append(sms)
                    logging.info("[GW] Terminal %s JH success!", t_info['t_msisdn'])
                elif terminal.tid != t_info['dev_id']:
                    # change dev, use same sim
                    is_change = True
                    logging.info("[GW] Terminal %s change dev %s to %s!",
                                 t_info['t_msisdn'], terminal.tid, t_info['dev_id'])
                elif terminal.imsi != t_info['imsi']:
                    # illegal sim, dev change sim
                    args.success = GATEWAY.LOGIN_STATUS.ILLEGAL_SIM
                    sms = SMSCode.SMS_TERMINAL_HK % (t_info['t_msisdn'])
                    smses.append(sms)
                    logging.error("[GW] Login failed! Illegal SIM: %s for Terminal: %s",
                                  t_info['t_msisdn'], t_info['dev_id'])
                elif terminal.owner_mobile != t_info['u_msisdn']:
                    # user change sim
                    user = self.db.get("SELECT id, password"
                                       "  FROM T_USER"
                                       "  WHERE mobile = %s",
                                       terminal.owner_mobile)
                    if user:
                        info = self.db.get("SELECT password(%s) AS psd", t_info['psd'])
                        if info.psd == user.password:
                            exist = self.db.get("SELECT id FROM T_USER"
                                                "  WHERE mobile = %s",
                                                t_info['u_msisdn'])
                            if exist:
                                sms = SMSCode.SMS_USER_ADD_TERMINAL % (t_info['t_msisdn'],
                                                                       ConfHelper.UWEB_CONF.url_out)
                                smses.append(sms)
                            else:
                                psd = get_psd()
                                self.db.execute("INSERT INTO T_USER(uid, password, name, mobile)"
                                                "  VALUES(%s, password(%s), %s, %s)",
                                                t_info['u_msisdn'], psd,
                                                t_info['u_msisdn'], t_info['u_msisdn'])
                                sms = SMSCode.SMS_USER_HK_SUCCESS % (t_info['u_msisdn'],
                                                                     ConfHelper.UWEB_CONF.url_out,
                                                                     t_info['u_msisdn'], psd)
                                smses.append(sms)
                            logging.info("[GW] User change SIM: %s to %s for terminal: %s",
                                         terminal.owner_mobile, t_info['u_msisdn'], t_info['t_msisdn'])
                        else:
                            sms = SMSCode.SMS_PSD_WRONG
                            smses.append(sms)
                            args.success = GATEWAY.LOGIN_STATUS.PSD_WRONG
                            logging.error("[GW] User change SIM %s to %s for terminal %s failed: psd wrong.",
                                          terminal.owner_mobile, t_info['u_msisdn'], t_info['t_msisdn'])
                    else:
                        pass
                else:
                    pass
            else:
                # dev change sim, clear cache
                is_change = True
                terminal = self.db.get("SELECT id, mobile, owner_mobile, imsi, service_status, endtime"
                                       "  FROM T_TERMINAL_INFO"
                                       "  WHERE tid = %s",
                                       t_info['dev_id'])
                if terminal:
                    if (terminal.endtime < time.time() or
                        terminal.service_status == GATEWAY.SERVICE_STATUS.OFF):
                        # expired or stop service
                        args.success = GATEWAY.LOGIN_STATUS.EXPIRED
                        logging.error("[GW] Login failed! Expired Terminal: %s", t_info['dev_id'])
                    elif terminal.mobile != t_info['t_msisdn']:
                        # dev change sim
                        user = self.db.get("SELECT id, password"
                                           "  FROM T_USER"
                                           "  WHERE mobile = %s",
                                           terminal.owner_mobile)
                        if user:
                            info = self.db.get("SELECT password(%s) AS psd", t_info['psd'])
                            if info.psd == user.password:
                                sms = SMSCode.SMS_TERMINAL_HK_SUCCESS % (terminal.mobile, t_info['t_msisdn'])
                                smses.append(sms)
                                if terminal.owner_mobile != t_info['u_msisdn']:
                                    exist = self.db.get("SELECT id FROM T_USER"
                                                        "  WHERE mobile = %s",
                                                        t_info['u_msisdn'])
                                    if exist:
                                        sms = SMSCode.SMS_USER_ADD_TERMINAL % (t_info['t_msisdn'],
                                                                               ConfHelper.UWEB_CONF.url_out)
                                        smses.append(sms)
                                    else:
                                        psd = get_psd()
                                        self.db.execute("INSERT INTO T_USER(uid, password, name, mobile)"
                                                        "  VALUES(%s, password(%s), %s, %s)",
                                                        t_info['u_msisdn'], psd,
                                                        t_info['u_msisdn'], t_info['u_msisdn'])
                                        sms = SMSCode.SMS_USER_HK_SUCCESS % (t_info['u_msisdn'],
                                                                             ConfHelper.UWEB_CONF.url_out,
                                                                             t_info['u_msisdn'], psd)
                                        smses.append(sms)
                                    logging.info("[GW] User change SIM: %s to %s for terminal: %s",
                                                 terminal.owner_mobile, t_info['u_msisdn'], t_info['t_msisdn'])
                                logging.info("[GW] Terminal change SIM: %s to %s, User: %s",
                                             terminal.mobile, t_info['t_msisdn'], t_info['u_msisdn'])
                            else:
                                sms = SMSCode.SMS_PSD_WRONG
                                smses.append(sms)
                                args.success = GATEWAY.LOGIN_STATUS.PSD_WRONG
                                logging.error("[GW] Terminal change SIM %s to %s for user %s failed: psd wrong.",
                                              terminal.mobile, t_info['t_msisdn'], t_info['u_msisdn'])
                        else:
                            pass
                else:
                    # first login, send sms JH terminal. default active time
                    # is one year.
                    begintime = datetime.datetime.now() 
                    endtime = begintime + relativedelta(years=1)
                    exist = self.db.get("SELECT id FROM T_USER"
                                        "  WHERE mobile = %s",
                                        t_info['u_msisdn'])
                    if exist:
                        sms = SMSCode.SMS_USER_ADD_TERMINAL % (t_info['t_msisdn'],
                                                               ConfHelper.UWEB_CONF.url_out)
                        smses.append(sms)
                    else:
                        psd = get_psd()
                        self.db.execute("INSERT INTO T_USER(uid, password, name, mobile)"
                                        "  VALUES(%s, password(%s), %s, %s)",
                                        t_info['u_msisdn'], psd,
                                        t_info['u_msisdn'], t_info['u_msisdn'])
                        sms = SMSCode.SMS_JH_SUCCESS % (t_info['t_msisdn'],
                                                        ConfHelper.UWEB_CONF.url_out,
                                                        t_info['u_msisdn'],
                                                        psd)
                        smses.append(sms)
                    self.db.execute("INSERT INTO T_TERMINAL_INFO(tid, dev_type, mobile,"
                                    "  owner_mobile, imsi, imei, factory_name, softversion,"
                                    "  keys_num, login, service_status, begintime, endtime)"
                                    "  VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                                    t_info['dev_id'], t_info['dev_type'],
                                    t_info['t_msisdn'], t_info['u_msisdn'],
                                    t_info['imsi'], t_info['imei'], t_info['factory_name'],
                                    t_info['softversion'], t_info['keys_num'], 
                                    GATEWAY.TERMINAL_LOGIN.LOGIN,
                                    GATEWAY.SERVICE_STATUS.ON,
                                    int(time.mktime(begintime.timetuple())),
                                    int(time.mktime(endtime.timetuple())))
                    self.db.execute("INSERT INTO T_CAR(tmobile)"
                                    "  VALUES(%s)",
                                    t_info['t_msisdn'])
                    logging.info("[GW] Terminal %s JH success!", t_info['t_msisdn'])

            if is_change:
                alias_key = get_alias_key(t_info['dev_id'])
                alarm_key = get_alarm_status_key(t_info['dev_id'])
                keys = [alias_key, alarm_key]
                self.redis.delete(*keys)
                if terminal:
                    self.db.execute("UPDATE T_TERMINAL_INFO"
                                    "  SET alias = NULL"
                                    "  WHERE id = %s", terminal.id)
                    
            if args.success == GATEWAY.LOGIN_STATUS.SUCCESS:
                if terminal:
                    self.db.execute("DELETE FROM T_TERMINAL_INFO"
                                    "  WHERE tid = %s"
                                    "    AND id != %s",
                                    t_info['dev_id'], terminal.id)
                    self.db.execute("UPDATE T_TERMINAL_INFO"
                                    "  SET tid = %s,"
                                    "      mobile = %s,"
                                    "      dev_type = %s,"
                                    "      owner_mobile = %s,"
                                    "      imsi = %s,"
                                    "      imei = %s,"
                                    "      factory_name = %s,"
                                    "      keys_num = %s,"
                                    "      softversion = %s,"
                                    "      login = %s"
                                    "  WHERE id = %s",
                                    t_info['dev_id'], t_info['t_msisdn'], t_info['dev_type'],
                                    t_info['u_msisdn'], t_info['imsi'], t_info['imei'],
                                    t_info['factory_name'], t_info['keys_num'], t_info['softversion'],
                                    GATEWAY.TERMINAL_LOGIN.LOGIN, terminal.id)
                # get SessionID
                args.sessionID = get_sessionID()
                terminal_sessionID_key = get_terminal_sessionID_key(t_info['dev_id'])
                self.redis.setvalue(terminal_sessionID_key, args.sessionID)
                # record terminal address
                self.update_terminal_status(t_info["dev_id"], address)
                # append into online terminals
                if not t_info["dev_id"] in self.online_terminals:
                    self.online_terminals.append(t_info["dev_id"])
                logging.info("[GW] Terminal %s login success! SIM: %s",
                             t_info['dev_id'], t_info['t_msisdn'])

            lc = LoginRespComposer(args)
            request = DotDict(packet=lc.buf,
                              address=address)
            self.append_gw_request(request)
            for sms in smses:
                SMSHelper.send(t_info['u_msisdn'], sms)
        except:
            logging.exception("[GW] Hand login exception.")
        
    def handle_heartbeat(self, info, address):
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
                self.update_terminal_status(head.dev_id, address)
                self.update_terminal_info(heartbeat_info)

            hc = HeartbeatRespComposer(args)
            request = DotDict(packet=hc.buf,
                              address=address)
            self.append_gw_request(request)
        except:
            logging.exception("[GW] Hand heartbeat exception.")

    def handle_locationdesc(self, info, address):
        """
        locationdesc packet
        0: success, then return locationdesc to terminal and record new terminal's address
        1: invalid SessionID 
        """
        try:
            head = info.head
            body = info.body
            args = DotDict(success=GATEWAY.RESPONSE_STATUS.SUCCESS,
                           locationdesc="")
            sessionID = self.get_terminal_sessionID(head.dev_id)
            if sessionID != head.sessionID:
                args.success = GATEWAY.RESPONSE_STATUS.INVALID_SESSIONID
                logging.error("[GW] Invalid sessionID, terminal: %s", head.dev_id)
            else:
                ldp = LocationDescParser(body, head)
                location = ldp.ret
                location['valid'] = GATEWAY.LOCATION_STATUS.SUCCESS 
                location['t'] = EVENTER.INFO_TYPE.POSITION
                location = lbmphelper.handle_location(location, self.redis)
                location.name = location.get('name') if location.get('name') else ""
                location.name = safe_unicode(location.name)
                locationdesc = location.name.encode("utf-8", 'ignore')
                args.locationdesc = base64.b64encode(locationdesc)
                self.update_terminal_status(head.dev_id, address)

            lc = LocationDescRespComposer(args)
            request = DotDict(packet=lc.buf,
                              address=address)
            self.append_gw_request(request)
        except:
            logging.exception("[GW] Handle locationdesc exception.")

    def foward_packet_to_si(self, info, packet, address):
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
            sessionID = self.get_terminal_sessionID(dev_id)
            if sessionID != head.sessionID:
                args.success = GATEWAY.RESPONSE_STATUS.INVALID_SESSIONID
                logging.error("[GW] Invalid sessionID, Terminal: %s", dev_id)
            else:
                uargs = DotDict(seq=SeqGenerator.next(self.db),
                                dev_id=dev_id,
                                content=packet)
                content = UploadDataComposer(uargs).buf
                logging.info("[GW] Forward message to SI:\n%s", content)
                self.append_si_request(content)
                self.update_terminal_status(dev_id, address)

            if head.command in (T_MESSAGE_TYPE.POSITION, T_MESSAGE_TYPE.MULTIPVT,
                                T_MESSAGE_TYPE.CHARGE, T_MESSAGE_TYPE.ILLEGALMOVE,
                                T_MESSAGE_TYPE.POWERLOW, T_MESSAGE_TYPE.POWEROFF,
                                T_MESSAGE_TYPE.EMERGENCY):
                rc = AsyncRespComposer(args)
                request = DotDict(packet=rc.buf,
                                  address=address)
                self.append_gw_request(request)
        except:
            logging.exception("[GW] Handle SI message exception.")

    def append_gw_request(self, request):
        message = json.dumps(request)
        # make message not persistent
        properties = pika.BasicProperties(delivery_mode=1,)
        self.rabbitmq_channel.basic_publish(exchange=self.exchange,
                                            routing_key=self.gw_binding,
                                            body=message,
                                            properties=properties)

    def append_si_request(self, request):
        #si_fds = self.redis.getvalue('fds')
        #if si_fds:
        #    si_fd = si_fds[0]
        request = dict({"packet":request})
        message = json.dumps(request)
        # make message not persistent
        properties = pika.BasicProperties(delivery_mode=1,)
        self.rabbitmq_channel.basic_publish(exchange=self.exchange,
                                            routing_key=self.si_binding,
                                            body=message,
                                            properties=properties)

    def get_terminal_sessionID(self, dev_id):
        terminal_sessionID_key = get_terminal_sessionID_key(dev_id) 
        sessionID = self.redis.getvalue(terminal_sessionID_key)

        return sessionID

    def update_terminal_status(self, dev_id, address):
        terminal_status_key = get_terminal_address_key(dev_id)
        lq_interval_key = get_lq_interval_key(dev_id)
        is_lq = self.redis.getvalue(lq_interval_key)
        if is_lq:
            self.redis.setvalue(terminal_status_key, address, 2*HEARTBEAT_INTERVAL)
        else:
            self.redis.setvalue(terminal_status_key, address, 2*SLEEP_HEARTBEAT_INTERVAL)

    def update_terminal_info(self, t_info):
        fields = []
        keys = ['dev_type', 'softversion', 'gps', 'gsm', 'pbat',
                'defend_status', 'login']
        for key in keys:
            if t_info.get(key, None) is not None:
                if key == 'softversion':
                     t_info[key] = "'" + t_info[key] + "'"
                fields.append(key + " = " + str(t_info[key]))
        set_clause = ','.join(fields)
        if set_clause:
            self.db.execute("UPDATE T_TERMINAL_INFO"
                            "  SET " + set_clause + 
                            "  WHERE tid = %s",
                            t_info['dev_id'])

    def get_terminal_status(self, dev_id):
        terminal_status_key = get_terminal_address_key(dev_id)
        return self.redis.getvalue(terminal_status_key)

    def __close_rabbitmq(self):
        if self.rabbitmq_connection and self.rabbitmq_connection.is_open:
            self.rabbitmq_connection.close()

    def __close_socket(self):
        try:
            self.socket.close()
        except:
            logging.exception("[GW] Close socket Exception.")

    def __clear_memcached(self, dev_id=None):
        pass

    def stop(self):
        self.__close_socket()
        self.__close_rabbitmq()
        self.__stop_check_heartbeat_thread()
        self.__clear_memcached()

    def __del__(self):
        self.stop()
