# -*- coding: utf-8 -*-
import socket
import select
import time
import thread
import logging
import base64

from dotdict import DotDict
from base import BaseParser

class Terminal(object):

    login_mg = "[%s,,1,1.0.0,A123,T1,15002494865,13011292217,460023615223538,355889008722099,CLW]"
    heartbeat_mg = "[%s,1a2b3c4d,1,1.0.0,A123,T2,23:9:95]"
    realtime_mg = "[%s,1a2b3c4d,1,1.0.0,A123,T4,1,E,113.252432,N,22.564152,120.3,270.5,1,460:00:10101:03633,23:9:100,%s]"

    location_mg = "[%s,1a2b3c4d,1,1.0.0,A123,T3,1,E,113.25,N,22.564152,120.3,270.5,1,460:00:10101:03633,23:9:100,%s]"
    query_args_mg = "[%s,1a2b3c4d,1,1.0.0,A123,T5,%s=%s]"
    set_args_mg = "[%s,1a2b3c4d,1,1.0.0,A123,T6,%s,%s]"
    reboot_mg = "[%s,1a2b3c4d,1,1.0.0,A123,T7,1]"
    remote_set_mg = "[%s,1a2b3c4d,1,1.0.0,A123,T8,1]"
    remote_unset_mg = "[%s,1a2b3c4d,1,1.0.0,A123,T9,1]"
    locationdesc_mg = "[%s,1a2b3c4d,1,1.0.0,A123,T10,E,113.252432,N,22.564152]"
    pvt_mg = "[%s,1a2b3c4d,1,1.0.0,A123,T11,{E,113.252432,N,22.564152,120.3,270.5,1343278800},{E,114.252432,N,23.564152,130.3,280.5,1343279800}]"
    charge_mg = "[%s,1a2b3c4d,1,1.0.0,A123,T12,%s]"
    move_report_mg = "[%s,1a2b3c4d,1,1.0.0,A123,T13,1,E,113.2524,N,22.5641,120.3,270.5,1,460:00:10101:03633,23:9:100,%s,1]"
    poweroff_report_mg = "[%s,1a2b3c4d,1,1.0.0,A123,T15,1,E,113.252,N,22.564,120.3,270.5,1,460:00:10101:03633,23:9:100,%s,1]"
    powerlow_report_mg = "[%s,1a2b3c4d,1,1.0.0,A123,T14,1,E,113.252,N,22.564,120.3,270.5,1,460:00:10101:03633,23:9:20,%s,1]"
    sos_report_mg = "[%s,1a2b3c4d,1,1.0.0,A123,T16,1,E,113.2524,N,22.5641,120.3,270.5,1,460:00:10101:03633,23:9:100,%s,1]" 
    #speed_report_mg = "[%s,1,V1.0.0,A123045612AA123487,T15,1,E,113.2524,N,22.5641,120.3,270.5,1, 460:00:16662:40953]"
    #mileage_count_mg = "[%s, , ,A123045612AA123487,T16,2000]"

    ARGS = DotDict(PSW="123456",
                   GSM=16,
                   LOGIN=1,
                   FREQ=15,
                   TRACE=1,
                   PULSE=120,
                   MOBILE="15002494865",
                   PARENT_MOBILE="13011292217",
                   RADIUS=300,
                   VIB=1,
                   VIBL=7,
                   POF=1,
                   SPEED=100,
                   SMS=1,
                   SOFTVERSION='v1.0.0',
                   GPS=10,
                   VBAT='3713300:4960750:303500',
                   VIN='11145600',
                   PLCID='123',
                   IMSI='460023615223538',
                   IMEI='355889008722099'
                   )

    def __init__(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.connect(('192.168.1.8', 9909))
        self.logging = self.initlog() 

    def login(self):
        t_time = time.strftime("%Y-%m-%d %H:%M:%S")
        t_time = int(time.time())
        self.logging.info("Send login message:\n%s", (self.login_mg % t_time))
        self.socket.send(self.login_mg % t_time)
        time.sleep(1)
  
    def login_response(self):
        self.logging.info("login success!")

    def heartbeat_response(self):
        self.logging.info("heartbeat send success!")

    def upload_response(self):
        self.logging.info("location upload success!")

    def heartbeat(self):
        time.sleep(2)
        while True:
            self.logging.info("Send heartbeat:\n%s", self.heartbeat_mg)
            self.socket.send(self.heartbeat_mg % int(time.time()))
            time.sleep(120)
    
    def realtime(self):
        #t_time = time.strftime("%Y-%m-%d %H:%M:%S")
        t_time = int(time.time())
        msg = self.realtime_mg % (t_time, t_time)
        self.logging.info("Send realtime response:\n%s", msg)
        self.socket.send(msg)

    def upload_position(self):
        time.sleep(5)
        while True:
            t_time = int(time.time())
            msg = self.location_mg % (t_time, t_time)
            self.logging.info("Upload location:\n%s", msg)
            self.socket.send(msg)
            time.sleep(60)
 
    def report_once_mg(self):
        time.sleep(30)
        s = u'查询余额服务：您好，您的总账户余额为343.91元，感谢您的使用'
        t_time = int(time.time())
        charge = base64.b64encode(s.encode("utf-8", 'ignore'))
        charge_mg = self.charge_mg % (t_time, charge)
        mgs = [(self.locationdesc_mg % t_time),(self.pvt_mg % t_time), charge_mg] 
        for mg in mgs:
            print '----', mg
            self.logging.info("Send report mg:\n%s", mg)
            self.socket.send(mg)
            time.sleep(30)

    def report_mg(self):
        time.sleep(10)
        report_mgs = [self.move_report_mg, self.poweroff_report_mg, self.powerlow_report_mg, self.sos_report_mg]
        while True:
            for report_mg in report_mgs:
                t_time = int(time.time())
                msg = report_mg % (t_time, t_time)
                self.logging.info("Send report mg:\n%s", msg)
                self.socket.send(msg)
                time.sleep(60)

    def query_args(self, bp):
        t_time = time.strftime("%Y-%m-%d %H:%M:%S")
        packet = bp.packet_info
        query_arg = packet[2]
        for arg in self.ARGS.keys():
            if query_arg == arg:
                query_value = self.ARGS[arg]
                msg = self.query_args_mg % (t_time, arg, query_value)
                #self.logging.info("Send query args %s:\n%s", (arg, msg)) 
                print '--send msg: ', msg
                self.socket.send(msg)
                break

    def set_args(self, bp):
        t_time = time.strftime("%Y-%m-%d %H:%M:%S")
        packet = bp.packet_info
        set_arg = packet[2].split("=")[0]
        set_value = packet[2].split("=")[1]
        if set_arg.upper() in self.ARGS.keys():
            self.ARGS[set_arg] = set_value
            suc = self.set_args_mg %(t_time, set_arg, "1")
            self.logging.info("Send set args %s success:\n%s", (set_arg, suc))
            self.socket.send(self.set_args_mg % (t_time, set_arg, "1"))
        else:
            suc = self.set_args_mg %(t_time, set_arg, "0")
            self.logging.info("Send set args %s failed:\n%s", (set_arg, suc))
            self.socket.send(self.set_args_mg % (t_time, set_arg, "0"))

    def restart(self):
        self.logging.info("Restart terminal...")

    def remote_set(self):
        t_time = time.strftime("%Y-%m-%d %H:%M:%S")
        self.logging.info("Send remote_set mg:\n%s", (self.remote_set_mg % t_time))
        self.socket.send(self.remote_set_mg % t_time)
        
    def remote_unset(self):
        t_time = time.strftime("%Y-%m-%d %H:%M:%S")
        self.logging.info("Send remote_unset mg:\n%s", (self.remote_unset_mg % t_time))
        self.socket.send(self.remote_unset_mg % t_time)

    def remote_lock(self):
        t_time = time.strftime("%Y-%m-%d %H:%M:%S")
        self.logging.info("Send remote_lock mg:\n%s", (self.remote_lock_mg % t_time))
        self.socket.send(self.remote_lock_mg % t_time)

    def mileage_count(self):
        self.logging.info("Report mileage_count success!")

    def locationdesc(self, bp):
        self.logging.info("Report locationdesc success!")
        desc = bp.packet_info[-1:][0]
        locationdesc = base64.b64decode(desc)
        locationdesc = locationdesc.decode("utf-8")
        print 'locationdesc: ', locationdesc

    def pvt(self):
        self.logging.info("Report pvt success!")
    def charge(self):
        self.logging.info("Report charge success!")
    def async(self):
        self.logging.info("Report async success!")

    def start_each_thread(self):
        thread.start_new_thread(self.heartbeat, ())
        thread.start_new_thread(self.upload_position, ())
        thread.start_new_thread(self.report_mg, ())
        thread.start_new_thread(self.report_once_mg, ())


    def handle_recv(self, bp):
        if bp.type == "S1":
            self.login_response()
            self.start_each_thread()
        elif bp.type == "S2":
            self.heartbeat_response()
        elif bp.type == "S3":
            self.upload_response()
        elif bp.type == "S4":
            self.realtime()
        elif bp.type == "S5":
            self.query_args(bp)
        elif bp.type == "S6":
            self.set_args(bp)
        elif bp.type == "S7":
            self.restart()
        elif bp.type == "S8":
            self.remote_set()
        elif bp.type == "S9":
            self.remote_unset()
        elif bp.type == "S10":
            self.locationdesc(bp)
        elif bp.type == "S11":
            self.pvt()
        elif bp.type == "S12":
            self.charge()
        elif bp.type in ("S13, S14, S15, S16"):
            self.async()
        #elif bp.type == "S16":
        #    self.mileage_count()
    
    def tcpClient(self):
        try:
            self.login()
            while True:
                infds, _, _ = select.select([self.socket], [], [], 1)
                if len(infds) > 0:
                    dat = self.socket.recv(1024)
                    self.logging.info("Recv:%s", dat)
                    print 'recv data: ', dat
                    bp = BaseParser(dat)
                    self.handle_recv(bp)
        except Exception as e:
            self.logging.error("What's wrong, reconnect it.")
        finally:
            self.socket.close()

    def initlog(self):
        logger = logging.getLogger()
        hdlr = logging.FileHandler("terminal.log")
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
        hdlr.setFormatter(formatter)
        logger.addHandler(hdlr)
        logger.setLevel(logging.NOTSET)
    
        return logger
       
if __name__ == "__main__":   
    terminal = Terminal()
    terminal.tcpClient()
