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
from utils.myredis import MyRedis
from helpers.smshelper import SMSHelper
from helpers.emailhelper import EmailHelper 
from helpers.confhelper import ConfHelper
from constants import GATEWAY
from constants import SMS
from codes.smscode import SMSCode

class SimulatorTerminalTest(object):
    """Provide location for TEST Account. 
    """
    
    def __init__(self):
        """Provide some necessary info and create a socket.
        """
        self.tid = 'T123SIMULATOR' 
        self.tmobile = '18310505991'
        self.imsi = '888823615223531'
        self.imei = '888888900872201'

        self.login_mg = "[%s,,1,1.0.0,%s,T1,%s,18310505991,%s,%s,CLW,2,]"
        self.heartbeat_mg = "[%s,%s,1,1.0.0,%s,T2,23:9:95,1,0]"
        self.location_mg = "[%s,%s,1,1.0.0,%s,T3,1,E,113.25,N,22.564152,120.3,270.5,1,460:0:9876:3171,23:9:100,%s]"
        self.location_mg = "[%(time)s,%(sessionid)s,1,1.0.0,%(tid)s,T3,1,E,%(lon)s,N,%(lat)s,%(speed)s,%(degree)s,1,%(cellid)s,23:9:100,%(time)s]"

        self.db = DBConnection().db
        self.redis = MyRedis()

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        host = ConfHelper.GW_SERVER_CONF.host
        port = int(ConfHelper.GW_SERVER_CONF.port)
        self.socket.connect((host, port))

    #####NOTE: Send packet. 
    def login(self):
        """Send packet T1.
        """
        t_time = int(time.time())
        login_mg = self.login_mg % (t_time, self.tid, self.tmobile, self.imsi, self.imei)
        logging.info("[CK] Send login message:\n%s", login_mg) 
        self.socket.send(login_mg)
        time.sleep(1)
  
    def heartbeat(self):
        """Send packet T2.
        """
        time.sleep(10)
        logging.info("[CK] Simulator terminal heartbeat thread start...")
        while True:
            heartbeat_mg = self.heartbeat_mg % (int(time.time()), self.sessionID, self.tid)
            logging.info("[CK] Send heartbeat:\n%s", heartbeat_mg)
            self.socket.send(heartbeat_mg)
            time.sleep(300)

    def upload_position(self):
        """Send packet T3.
        """
        time.sleep(10)
        logging.info("[CK] Simulator terminal upload position thread start...")
        locations = self.db.query("SELECT latitude, longitude, speed, degree, cellid"
                                  " FROM T_LOCATION_SIMULATOR"
                                  "  WHERE type = 0" 
                                  " GROUP BY timestamp" 
                                  " ORDER BY timestamp")

        count = len(locations)
        self.redis.set('count',count)

        n = self.redis.get('n')
        if n:
            n = int(n)
        else:
            n = 0 
            self.redis.set('n',n)

        while True:
            if n == count:
              n = 0
              self.redis.set('n',n)
            loc = locations[n]
            t_time = int(time.time())
            r = dict(time=t_time,
                     sessionid=self.sessionID,
                     tid=self.tid,
                     lon=float(loc['longitude'])/3600000,
                     lat=float(loc['latitude'])/3600000,
                     speed=loc['speed'],
                     degree=loc['degree'],
                     cellid=loc['cellid'] if loc['cellid'] else '460:0:9876:3171')
            msg = self.location_mg % r

            logging.info("[CK] Upload location:\n%s", msg)
            self.socket.send(msg)
            n = n+1 
            self.redis.set('n',n)
            time.sleep(300) # 5 min

    #NOTE: Handle the response
    def pase_packet(self, packet):
        """Make some simple split
        """
        packet_info = packet[1:][:-1].split(",")
        return packet_info

    def handle_recv(self, packet_info):
        """Receive respnses from Gateway and handle them.
        """
        type = packet_info[1]
        if type == GATEWAY.S_MESSAGE_TYPE.LOGIN:
            self.login_response(packet_info)
        elif type == GATEWAY.S_MESSAGE_TYPE.HEARTBEAT:
            self.heartbeat_response(packet_info)
        elif type == GATEWAY.S_MESSAGE_TYPE.POSITION:
            self.upload_response(packet_info)
        else:
            pass

    def heartbeat_response(self, packet_info):
        """Receve response S2.
        """
        if packet_info[2] == "0":
            logging.info("[CK] Heartbeat send success!")
        else:
            logging.info("[CK] Login faild, login agin...")
            time.sleep(5)
            self.login()

    def upload_response(self, packet_info):
        """Receve response S3.
        """
        if packet_info[2] == "0":
            logging.info("[CK] Location upload success!")
        else:
            logging.info("[CK] Login faild, login agin...")
            time.sleep(5)
            self.login()

    def login_response(self, packet_info):
        """Receve response S1.
        """
        if packet_info[2] == "0":
            self.sessionID = packet_info[3]
            self.start_each_thread()
            logging.info("[CK] Login success!")
        else:
            logging.info("[CK] Login faild, login agin...")
            time.sleep(5)
            self.login()


    def start_each_thread(self):
        thread.start_new_thread(self.heartbeat, ())
        thread.start_new_thread(self.upload_position, ())

    def udp_client(self):
        """Main method.

        workflow:
        login:
        while True:
            receive response from GATEWAY
            handle_recv
        """
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
