# -*- coding: utf-8 -*-

import os.path
import site

TOP_DIR_ = os.path.abspath(os.path.join(__file__, "../../.."))
site.addsitedir(os.path.join(TOP_DIR_, "libs"))

import logging
import socket
import select
import time
import thread

from db_.mysql import DBConnection
from helpers.smshelper import SMSHelper
from helpers.emailhelper import EmailHelper 
from helpers.confhelper import ConfHelper
from constants import GATEWAY
from constants import SMS
from codes.smscode import SMSCode

class SimulatorTerminal(object):
    
    def __init__(self):
        self.tid = 'B123SIMULATOR' 
        self.tmobile = '18810496308'
        self.imsi = '888823615223538'
        self.imei = '888888900872209'

        self.login_mg = "[%s,,1,1.0.0,%s,T1,%s,15901258591,%s,%s,CLW,2,]"
        self.heartbeat_mg = "[%s,%s,1,1.0.0,%s,T2,23:9:95,1,0]"
        self.location_mg = "[%s,%s,1,1.0.0,%s,T3,1,E,113.25,N,22.564152,120.3,270.5,1,460:0:9876:3171,23:9:100,%s]"

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        host = ConfHelper.GW_SERVER_CONF.host
        port = int(ConfHelper.GW_SERVER_CONF.port)
        self.socket.connect((host, port))

    def login(self):
        t_time = int(time.time())
        login_mg = self.login_mg % (t_time, self.tid, self.tmobile, self.imsi, self.imei)
        logging.info("[CK] Send login message:\n%s", login_mg) 
        self.socket.send(login_mg)
        time.sleep(1)
  
    def login_response(self, packet_info):
        if packet_info[2] == "0":
            self.sessionID = packet_info[3]
            self.start_each_thread()
            logging.info("[CK] Login success!")
        else:
            logging.info("[CK] Login faild, login agin...")
            time.sleep(5)
            self.login()

    def heartbeat_response(self, packet_info):
        if packet_info[2] == "0":
            logging.info("[CK] Heartbeat send success!")
        else:
            logging.info("[CK] Login faild, login agin...")
            time.sleep(5)
            self.login()

    def upload_response(self, packet_info):
        if packet_info[2] == "0":
            logging.info("[CK] Location upload success!")
        else:
            logging.info("[CK] Login faild, login agin...")
            time.sleep(5)
            self.login()

    def heartbeat(self):
        time.sleep(10)
        logging.info("[CK] Simulator terminal heartbeat thread start...")
        while True:
            heartbeat_mg = self.heartbeat_mg % (int(time.time()), self.sessionID, self.tid)
            logging.info("[CK] Send heartbeat:\n%s", heartbeat_mg)
            self.socket.send(heartbeat_mg)
            time.sleep(300)

    def upload_position(self):
        time.sleep(60)
        logging.info("[CK] Simulator terminal upload position thread start...")
        while True:
            t_time = int(time.time())
            msg = self.location_mg % (t_time, self.sessionID, self.tid, t_time)
            logging.info("[CK] Upload location:\n%s", msg)
            self.socket.send(msg)
            time.sleep(300)
 
    def start_each_thread(self):
        thread.start_new_thread(self.heartbeat, ())
        thread.start_new_thread(self.upload_position, ())

    def handle_recv(self, packet_info):
        type = packet_info[1]
        if type == GATEWAY.S_MESSAGE_TYPE.LOGIN:
            self.login_response(packet_info)
        elif type == GATEWAY.S_MESSAGE_TYPE.HEARTBEAT:
            self.heartbeat_response(packet_info)
        elif type == GATEWAY.S_MESSAGE_TYPE.POSITION:
            self.upload_response(packet_info)
        else:
            pass
    
    def udp_client(self):
        try:
            self.login()
            while True:
                infds, _, _ = select.select([self.socket], [], [], 1)
                if len(infds) > 0:
                    dat = self.socket.recv(1024)
                    logging.info("[CK] Recv data: %s", dat)
                    packet_info = self.pase_packet(dat)
                    self.handle_recv(packet_info)
        except KeyboardInterrupt:
            logging.error("Ctrl-C is pressed.")
        except Exception as e:
            logging.error("[CK] What's wrong, reconnect it.%s", e.args)
        finally:
            self.socket.close()

    def pase_packet(self, packet):
        packet_info = packet[1:][:-1].split(",")
        return packet_info
        

