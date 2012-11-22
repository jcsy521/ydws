# -*- coding: utf-8 -*-
import socket
import select
import time
import thread
import logging
import base64

from tornado.ioloop import IOLoop

from dotdict import DotDict
from base import BaseParser

class Terminal(object):
    
    def __init__(self, tid, tmobile, imsi, imei):
        self.tid = tid
        self.tmobile = tmobile
        self.imsi = imsi
        self.imei = imei

        self.login_mg = "[%s,,1,1.0.0,%s,T1,%s,15901258591,%s,%s,CLW,2,]"
        self.heartbeat_mg = "[%s,%s,1,1.0.0,%s,T2,23:9:95,1,0]"
        self.realtime_mg = "[%s,%s,1,1.0.0,%s,T4,%s,E,113.252432,N,22.564152,120.3,270.5,1,460:00:10101:03633,23:9:100,%s]"

        self.location_mg = "[%s,%s,1,1.0.0,%s,T3,0,E,113.25,N,22.564152,120.3,270.5,1,460:0:9876:3171,23:9:100,%s]"
        self.query_args_mg = "[%s,%s,1,1.0.0,%s,T5,%s]"
        self.set_args_mg = "[%s,%s,1,1.0.0,%s,T6,%s]"
        self.reboot_mg = "[%s,%s,1,1.0.0,%s,T7,1]"
        self.remote_set_mg = "[%s,%s,1,1.0.0,%s,T8,0]"
        self.remote_unset_mg = "[%s,%s,1,1.0.0,%s,T9,0]"
        self.locationdesc_mg = "[%s,%s,1,1.0.0,%s,T10,E,113.252432,N,22.564152,0,460:0:4489:25196]"
        self.pvt_mg = "[%s,%s,1,1.0.0,%s,T11,{E,113.252432,N,22.564152,120.3,270.5,1351492202},{E,114.252432,N,23.564152,130.3,280.5,1351492158},{E,115.252432,N,24.564152,130.3,280.5,1351492002},{E,116.252432,N,25.564152,130.3,280.5,1351492058},{E,117.252432,N,26.564152,130.3,280.5,1351491902}]"
        self.charge_mg = "[%s,%s,1,1.0.0,%s,T12,%s]"
        self.move_report_mg = "[%s,%s,1,1.0.0,%s,T13,0,E,113.2524,N,22.5641,120.3,270.5,1,460:00:10101:03633,23:9:100,%s,1,]"
        self.shake_report_mg = "[%s,%s,1,1.0.0,%s,T15,0,E,113.252,N,22.564,120.3,270.5,1,460:00:10101:03633,23:9:100,%s,1,]"
        self.terminal_powerlow_mg = "[%s,%s,1,1.0.0,%s,T14,0,E,114.252,N,24.564,123.3,273.5,1,460:00:10101:03633,23:9:20,%s,1,]"
        self.fob_powerlow_mg = "[%s,%s,1,1.0.0,%s,T14,1,E,116.252,N,26.564,126.3,276.5,1,460:0:10101:03633,20:6:35,%s,0,9999]"
        self.terminal_poweroff_mg = "[%s,%s,1,1.0.0,%s,T14,1,E,116.252,N,26.564,126.3,276.5,1,460:0:10101:03633,20:6:3,%s,1,]"
        self.terminal_powerfull_mg = "[%s,%s,1,1.0.0,%s,T14,1,E,116.252,N,26.564,126.3,276.5,1,460:0:10101:03633,20:6:100,%s,1,]"
        self.sos_report_mg = "[%s,%s,1,1.0.0,%s,T16,0,E,113.2524,N,22.5641,120.3,270.5,1,460:00:10101:03633,23:9:100,%s,1,]" 
        self.config_mg = "[%s,%s,1,1.0.0,%s,T17]"
        self.defend_report_mg = "[%s,%s,1,1.0.0,%s,T18,1]"
        self.fobinfo_mg = "[%s,%s,1,1.0.0,%s,T19,ABCDEF,0]"
        self.fob_operate = "[%s,%s,1,1.0.0,%s,T20,0]"
        self.sleep_mg = "[%s,%s,1,1.0.0,%s,T21,1]"
        self.fob_status_mg = "[%s,%s,1,1.0.0,%s,T22,1]"
        self.unbind_mg = "[%s,%s,1,1.0.0,%s,T24,1]"
        self.unbind_status_mg = "[%s,%s,1,1.0.0,%s,T25]"

        self.ARGS = DotDict(PSW="111111",
                            GSM=16,
                            LOGIN=1,
                            FREQ=0,
                            PULSE=0,
                            WHITE_LIST=0,
                            VIBCHK=0,
                            SERVICE_STATUS=0,
                            TRACE=0,
                            PBAT=80,
                            MOBILE=self.tmobile,
                            PARENT_MOBILE="15901258591",
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
                            IMSI=self.imsi,
                            IMEI=self.imei
                            )

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.connect(('192.168.1.8', 10025))
        self.logging = self.initlog() 

    def login(self):
        t_time = int(time.time())
        login_mg = self.login_mg % (t_time, self.tid, self.tmobile, self.imsi, self.imei)
        self.logging.info("Send login message:\n%s", login_mg) 
        self.socket.send(login_mg)
        time.sleep(1)
  
    def login_response(self, bp):
        info = bp.packet_info 
        self.sessionID = info[3]
        self.logging.info("login success!")
        t_time = int(time.time())
        mg = self.config_mg% (t_time, self.sessionID, self.tid)
        self.socket.send(mg)
        print 'send config: ', mg

    def heartbeat_response(self):
        self.logging.info("heartbeat send success!")

    def upload_response(self):
        self.logging.info("location upload success!")

    def heartbeat(self):
        time.sleep(30)
        while True:
            heartbeat_mg = self.heartbeat_mg % (int(time.time()), self.sessionID, self.tid)
            self.logging.info("Send heartbeat:\n%s", heartbeat_mg)
            self.socket.send(heartbeat_mg)
            time.sleep(30)
    
    def realtime(self, io_loop):
        t_time = int(time.time())
        def callback():
            valid = 1
            msg = self.realtime_mg % (t_time, self.sessionID,self.tid, valid, t_time)
            self.logging.info("Send realtime response:\n%s", msg)
            self.socket.send(msg)
            #if valid != 1:
            #    t_time2 = int(time.time())
            #    l_msg = self.location_mg % (t_time2, self.sessionID, self.tid, t_time2)
            #    time.sleep(5)
            #    print 'before send...'
            #    self.socket.send(l_msg)
            #    print 'send: ', l_msg
        io_loop.add_timeout(t_time+3, callback)
        thread.start_new_thread(self.start_io_loop, (io_loop,))

    def upload_position(self):
        time.sleep(5)
        while True:
            t_time = int(time.time())
            msg = self.location_mg % (t_time, self.sessionID, self.tid, t_time)
            self.logging.info("Upload location:\n%s", msg)
            self.socket.send(msg)
            time.sleep(60)
 
    def report_once_mg(self):
        #time.sleep(30)
        s = u'查询余额服务：您好，您的总账户余额为343.91元，感谢您的使用'
        t_time = int(time.time())
        charge = base64.b64encode(s.encode("utf-8", 'ignore'))
        charge_mg = self.charge_mg % (t_time, self.sessionID, self.tid, charge)

        pvt_mg = self.pvt_mg % (t_time, self.sessionID, self.tid)

        locationdesc_mg = self.locationdesc_mg % (t_time, self.sessionID, self.tid)

        defend_status_mg = self.defend_status_mg % (t_time, self.sessionID)

        mgs = [charge_mg, pvt_mg, locationdesc_mg, defend_status_mg]
        for mg in mgs:
            self.logging.info("Send report mg:\n%s", mg)
            self.socket.send(mg)
            time.sleep(30)

    def report_mg(self):
        time.sleep(5)
         report_mgs = [self.move_report_mg, self.poweroff_report_mg, self.powerlow_report_mg, self.sos_report_mg]
        while True:
            for report_mg in report_mgs:
                t_time = int(time.time())
                msg = report_mg % (t_time, self.sessionID, self.tid, t_time)
                self.logging.info("Send report mg:\n%s", msg)
                self.socket.send(msg)
                time.sleep(50)

    def query_args(self, bp):
        t_time = int(time.time())
        packet = bp.packet_info
        query_arg = packet[2:]
        res = []
        for arg in query_arg:
            query_value = self.ARGS[arg]
            r = arg + '=' + str(query_value)
            res.append(r)
        args = ','.join(res)
        msg = self.query_args_mg % (t_time, self.sessionID, self.tid, args)
        #self.logging.info("Send query args %s:\n%s", (arg, msg)) 
        self.socket.send(msg)

    def set_args(self, bp):
        t_time = int(time.time()) 
        packet = bp.packet_info[2:]
        res = []
        for item in packet:
            self.ARGS[item.split('=')[0]] = item.split('=')[1]
            res.append(item.split('=')[0] + '=' + '0')
        set_arg = ','.join(res)
        suc = self.set_args_mg %(t_time, self.sessionID, self.tid, set_arg)
        self.socket.send(suc)
        self.logging.info("Send set args %s success:\n%s", (set_arg, suc))

    def restart(self):
        self.logging.info("Restart terminal...")

    def remote_set(self):
        t_time = int(time.time())
        remote_set_mg = self.remote_set_mg % (t_time, self.sessionID, self.tid)
        self.logging.info("Send remote_set mg:\n%s", remote_set_mg) 
        self.socket.send(remote_set_mg)
        
    def remote_unset(self):
        t_time = int(time.time())
        remote_unset_mg = self.remote_unset_mg % (t_time, self.sessionID, self.tid)
        self.logging.info("Send remote_unset mg:\n%s", remote_unset_mg) 
        self.socket.send(remote_unset_mg)

    def remote_lock(self):
        t_time = int(time.time())
        self.logging.info("Send remote_lock mg:\n%s", (self.remote_lock_mg % t_time))
        self.socket.send(self.remote_lock_mg % t_time)

    def mileage_count(self):
        self.logging.info("Report mileage_count success!")

    def locationdesc(self, bp):
        self.logging.info("Report locationdesc success!")
        desc = bp.packet_info[-1:][0]
        locationdesc = base64.b64decode(desc)
        locationdesc = locationdesc.decode("utf-8")
    def config(self, bp):
        print 'config: ', bp
        self.logging.info("Report config success!")
    def defend_status(self, bp):
        print 'defend status: ', bp
        self.logging.info("Report defend_status success!")

    def pvt(self):
        self.logging.info("Report pvt success!")
    def charge(self):
        self.logging.info("Report charge success!")
    def async(self):
        self.logging.info("Report async success!")

    def start_each_thread(self):
        thread.start_new_thread(self.heartbeat, ())
        thread.start_new_thread(self.upload_position, ())
        #thread.start_new_thread(self.report_mg, ())
        #thread.start_new_thread(self.report_once_mg, ())


    def handle_recv(self, bp, io_loop):
        if bp.type == "S1":
            self.login_response(bp)
            self.start_each_thread()
        elif bp.type == "S2":
            self.heartbeat_response()
        elif bp.type == "S3":
            self.upload_response()
        elif bp.type == "S4":
            self.realtime(io_loop)
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
        elif bp.type == "S17":
            self.config(bp)
        elif bp.type == "S18":
            self.defend_status()
    
    def tcpClient(self, io_loop):
        try:
            self.login()
            while True:
                infds, _, _ = select.select([self.socket], [], [], 1)
                if len(infds) > 0:
                    dat = self.socket.recv(1024)
                    self.logging.info("Recv:%s", dat)
                    print 'recv data: ', dat
                    bp = BaseParser(dat)
                    self.handle_recv(bp, io_loop)
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

    def start_io_loop(self, io_loop):
        io_loop.start()
       
if __name__ == "__main__":   
    import sys
    
    io_loop = IOLoop.instance()
    args = dict(tid='B123',
                tmobile='18810496308',
                imsi='888823615223538',
                imei='888888900872209')
    keys = ['tid', 'tmobile', 'imsi', 'imei']
    for i, key in enumerate(keys):
        if len(sys.argv) > i+1:
            args[key] = sys.argv[i+1]
        else:
            break

    terminal = Terminal(args['tid'], args['tmobile'], args['imsi'], args['imei'])
    thread.start_new_thread(terminal.tcpClient, (io_loop,))
    while True:
        time.sleep(10)
