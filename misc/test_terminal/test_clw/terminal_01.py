# -*- coding: utf-8 -*-
import socket
import select
import time
import thread
import logging
import base64
import random

from tornado.ioloop import IOLoop

from dotdict import DotDict
from base import BaseParser

class Terminal(object):
    
    def __init__(self, tid, tmobile, umobile, imsi, imei):
        self.tid = tid
        self.tmobile = tmobile
        self.umobile = umobile
        self.imsi = imsi
        self.imei = imei

        #NOTE: JH
        self.login_mg = "[%s,,D,2.3.0,%s,T1,%s,%s,%s,%s,CLW,2,1,DBJ-3771728252,e3-94-9c-6f-53-9c]"
        #NOTE: normal login 
        self.login_mg = "[%s,,D,2.3.0,%s,T1,%s,%s,%s,%s,CLW,2,0,DBJ-3771728252,e3-94-9c-6f-53-9c,jia,jia2]"

        #self.login_mg = "[%s,,1,2.3.0,%s,T1,%s,%s,%s,%s,CLW,2,1,DBJ-3771728252,e3-94-9c-6f-53-9c]"

        #v 3.3

        self.heartbeat_mg = "[%s,%s,1,2.0.0,%s,T2,23:9:95,1,0]"
        #v 3.4
        self.heartbeat_mg = "[%s,%s,1,3.2.RLYC205204,%s,T2,23:9:95,2,0]"

        #self.heartbeat_mg = "[%s,%s,1,3.2.RLYC205204,%s,T2,23:9:"+str(pbat)+",2,0]"
        self.heartbeat_mg = "[%s,%s,1,3.2.RLYC205204,%s,T2,23:9:%s,2,0]"

        #NOTE: depressed
        #self.realtime_mg = "[%s,%s,1,1.0.0,%s,T4,%s,E,113.252432,N,22.564152,120.3,270.5,1,460:00:10101:03633,23:9:100,%s]"
        #self.realtime_mg = "[%s,%s,1,1.0.0,%s,T4,%s,E,113.252432,N,22.564152,120.3,270.5,1,460:00:10101:03633,23:9:100,%s,24]"

        #self.location_mg = "[%s,%s,1,1.0.0,%s,T3,1,E,116.252,N,26.564,120.3,270.5,1,460:0:9876:3171,23:9:100,%s]"
        self.location_mg = "[%s,%s,1,1.0.0,%s,T3,1,E,116.252,N,26.564,120.3,270.5,1,460:0:9876:3171,23:9:100,%s,23]"

        self.query_args_mg = "[%s,%s,1,1.0.0,%s,T5,%s]"
        self.set_args_mg = "[%s,%s,1,1.0.0,%s,T6,%s]"
        self.reboot_mg = "[%s,%s,1,1.0.0,%s,T7,1]"
        self.remote_set_mg = "[%s,%s,1,1.0.0,%s,T8,0]"
        self.remote_unset_mg = "[%s,%s,1,1.0.0,%s,T9,0]"

        #self.locationdesc_mg = "[%s,%s,1,1.0.0,%s,T10,E,113.252432,N,22.564152,460:0:4489:25196,1]"
        self.locationdesc_mg = "[%s,%s,1,1.0.0,%s,T10,E,113.252432,N,22.564152,460:0:4489:25196,1]"
        #self.locationdesc_mg = "[%s,%s,1,1.0.0,%s,T10,E,113.252432,N,22.564152,460:0:4489:25196,1,30]"

        #NOTE: multi-point
        #self.pvt_mg = "[%s,%s,1,1.0.0,%s,T11,{E,113.252432,N,22.564152,120.3,270.5,1351492202},{E,114.252432,N,23.564152,130.3,280.5,1351492158},{E,115.252432,N,24.564152,130.3,280.5,1351492002},{E,116.252432,N,25.564152,130.3,280.5,1351492058},{E,117.252432,N,26.564152,130.3,280.5,1351491902}]"

        self.pvt_mg = "[%s,%s,1,1.0.0,%s,T11,{E,113.252432,N,22.564152,120.3,270.5,1351492202,20,jiatest_misc},{E,114.252432,N,23.564152,130.3,280.5,1351492158,31},{E,115.252432,N,24.564152,130.3,280.5,1351492002},{E,116.252432,N,25.564152,130.3,280.5,1351492058,31},{E,117.252432,N,26.564152,130.3,280.5,1351491902,31,jia_test_misc}]"
     
        #self.pvt_mg = "[%s,%s,1,1.0.0,%s,T11,{E,113.252432,N,22.564152,133.3,270.5,1351492202,20,jia_test_misc}]"
        #self.pvt_mg = "[%s,%s,1,1.0.0,%s,T11,{E,113.252432,N,22.564152,133.3,270.5,1351492202,20,jia_test_misc}]"

        #PVT: only one point
        #self.pvt_mg = "[%s,%s,1,1.0.0,%s,T11,{E,%s,N,%s,120.3,270.5,%s}]"
        #self.pvt_mg = "[%s,%s,1,1.0.0,%s,T11,{E,%s,N,%s,120.3,270.5,%s,31}]"

        self.charge_mg = "[%s,%s,1,1.0.0,%s,T12,%s]"
        self.move_report_mg = "[%s,%s,1,1.0.0,%s,T13,2,E,113.2524,N,22.5641,120.3,270.5,1,460:00:10101:03633,23:9:100,%s,1,]"
        #self.move_report_mg = "[%s,%s,1,1.0.0,%s,T13,2,E,113.2524,N,22.5641,120.3,270.5,1,460:00:10101:03633,23:9:100,%s,1,,33]"

        #no is_nofify
        #self.shake_report_mg = "[%s,%s,1,1.0.0,%s,T15,0,E,113.252,N,22.564,120.3,270.5,1,460:00:10101:03633,23:9:100,%s,1,]"
        # is_notify
        self.shake_report_mg = "[%s,%s,1,1.0.0,%s,T15,0,E,113.252,N,22.564,120.3,270.5,1,460:00:10101:03633,23:9:100,%s,1,fobid,20,1]"
        #self.shake_report_mg = "[%s,%s,1,1.0.0,%s,T15,0,E,113.252,N,22.564,120.3,270.5,1,460:00:10101:03633,23:9:100,%s,1,,35]"

        self.terminal_powerlow_mg = "[%s,%s,1,1.0.0,%s,T14,0,E,114.252,N,24.564,123.3,273.5,1,460:00:10101:03633,23:9:3,%s,1,]"
        #self.terminal_powerlow_mg = "[%s,%s,1,1.0.0,%s,T14,0,E,114.252,N,24.564,123.3,273.5,1,460:00:10101:03633,23:9:3,%s,1,,34]"

        self.fob_powerlow_mg = "[%s,%s,1,1.0.0,%s,T14,1,E,116.252,N,26.564,126.3,276.5,1,460:0:10101:03633,20:6:35,%s,0,9999]"
        #self.fob_powerlow_mg = "[%s,%s,1,1.0.0,%s,T14,1,E,116.252,N,26.564,126.3,276.5,1,460:0:10101:03633,20:6:35,%s,0,9999,34]"

        self.terminal_poweroff_mg = "[%s,%s,1,1.0.0,%s,T14,1,E,116.252,N,26.564,126.3,276.5,1,460:0:10101:03633,20:6:3,%s,1,]"
        #self.terminal_powerfull_mg = "[%s,%s,1,1.0.0,%s,T14,1,E,116.252,N,26.564,126.3,276.5,1,460:0:10101:03633,20:6:100,%s,1,,34]"

        self.terminal_stop_mg = "[%s,%s,1,1.0.0,%s,T29,0,E,116.252,N,26.564,126.3,276.5,1,460:0:10101:03633,20:6:10,%s,1,]"
        self.sos_report_mg = "[%s,%s,1,1.0.0,%s,T16,0,E,113.2524,N,22.5641,120.3,270.5,1,460:00:10101:03633,23:9:100,%s,1,]" 
        #self.sos_report_mg = "[%s,%s,1,1.0.0,%s,T16,0,E,113.2524,N,22.5641,120.3,270.5,1,460:00:10101:03633,23:9:100,%s,1,,36]" 

        self.terminal_powerdown_mg = "[%s,%s,1,1.0.0,%s,T26,1,E,116.252,N,26.564,126.3,276.5,1,460:0:10101:03633,20:6:10,%s,1,]"
        #self.terminal_powerdown_mg = "[%s,%s,1,1.0.0,%s,T26,1,E,116.252,N,26.564,126.3,276.5,1,460:0:10101:03633,20:6:10,%s,1,,46]"

        self.terminal_stop_mg = "[%s,%s,1,1.0.0,%s,T29,1,E,116.252,N,26.564,126.3,276.5,1,460:0:10101:03633,20:6:10,%s,1,]"
        #self.terminal_stop_mg = "[%s,%s,1,1.0.0,%s,T29,0,E,116.252,N,26.564,126.3,276.5,1,460:0:10101:03633,20:6:10,%s,1,,49]"

        self.config_mg = "[%s,%s,1,1.0.0,%s,T17]"
        self.defend_report_mg = "[%s,%s,1,1.0.0,%s,T18,0,0]"
        self.fobinfo_mg = "[%s,%s,1,1.0.0,%s,T19,ABCDEF,1]"
        self.fob_operate = "[%s,%s,1,1.0.0,%s,T20,0]"
        self.sleep_status_mg = "[%s,%s,1,1.0.0,%s,T21,1]"
        self.fob_status_mg = "[%s,%s,1,1.0.0,%s,T22,1]"
        self.runtime_status_mg = "[%s,%s,1,1.0.0,%s,T23,1,0,23:9:100,-1,1]"
        self.unbind_mg = "[%s,%s,1,1.0.0,%s,T24,0]"
        self.unbind_status_mg = "[%s,%s,1,1.0.0,%s,T25,1]"
        self.unusual_activate_mg = "[%s,%s,1,1.0.0,%s,T27,%s,%s,%s]"

        self.misc_mg = "[%s,%s,1,1.0.0,%s,T28,jiaxiaoleitest]"

        self.power_status_mg = "[%s,%s,1,1.0.0,%s,T30,0,0,1405655013]"

        self.power_status_report_mg = "[%s,%s,1,1.0.0,%s,T31,1]"

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
                            SOFTVERSION='2.2.0',
                            GPS=10,
                            VBAT='3713300:4960750:303500',
                            VIN='11145600',
                            PLCID='123',
                            FOBS='ABCDEF:BBCDEF',
                            IMSI=self.imsi,
                            IMEI=self.imei
                            )

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.connect(('192.168.1.9', 10025))
        #self.socket.connect(('192.168.1.9', 6203))
        #self.socket.connect(('192.168.1.105', 10025))
        self.logging = self.initlog() 

    def login(self):
        t_time = int(time.time())
        #t_time = 1355454637
        login_mg = self.login_mg % (t_time, self.tid, self.tmobile, self.umobile, self.imsi, self.imei)
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

    def heartbeat_response(self):
        self.logging.info("heartbeat send success!")

    def upload_response(self):
        self.logging.info("location upload success!")

    def misc(self):
        #time.sleep(30)
        time.sleep(1)
        misc_mg = self.misc_mg % (int(time.time()), self.sessionID, self.tid)
        self.logging.info("Send misc:\n%s", misc_mg)
        self.socket.send(misc_mg)
        time.sleep(10)

    def heartbeat(self):
        time.sleep(10)
        #time.sleep(30)
        while True:
            pbat = random.choice(range(30,100))
            heartbeat_mg = self.heartbeat_mg % (int(time.time()), self.sessionID, self.tid, pbat)
            self.logging.info("Send heartbeat:\n%s", heartbeat_mg)
            print "Send heartbeat:\n%s" %  heartbeat_mg
            self.socket.send(heartbeat_mg)
            time.sleep(10)
            #time.sleep(30)
    
    #def realtime(self, io_loop):
    #    t_time = int(time.time())
    #    def callback():
    #        valid = 1
    #        msg = self.realtime_mg % (t_time, self.sessionID,self.tid, valid, t_time)
    #        self.logging.info("Send realtime response:\n%s", msg)
    #        self.socket.send(msg)
    #        #if valid != 1:
    #        #    t_time2 = int(time.time())
    #        #    l_msg = self.location_mg % (t_time2, self.sessionID, self.tid, t_time2)
    #        #    time.sleep(5)
    #        #    print 'before send...'
    #        #    self.socket.send(l_msg)
    #        #    print 'send: ', l_msg
    #    io_loop.add_timeout(t_time+33, callback)
    #    thread.start_new_thread(self.start_io_loop, (io_loop,))

    def upload_position(self):
        time.sleep(5)
        while True:
            t_time = int(time.time())
            msg = self.location_mg % (t_time, self.sessionID, self.tid, t_time)
            self.logging.info("Upload location:\n%s", msg)
            self.socket.send(msg)
            time.sleep(30)
 
    def report_once_mg(self):
        """Some special packet.
        """
        #time.sleep(5)
        time.sleep(2)
        #time.sleep(30)
        t_time = int(time.time())

        s = u'查询余额服务：您好，您的总账户余额为343.91元，感谢您的使用'
        #charge = base64.b64encode(s.encode("utf-8", 'ignore'))
        charge_mg = self.charge_mg % (t_time, self.sessionID, self.tid, charge)
        #pvt_mg = self.pvt_mg % (t_time, self.sessionID, self.tid)
        pvt_mg = self.pvt_mg % (t_time, self.sessionID, self.tid)
        unbind_status_mg = self.unbind_status_mg % (t_time, 'abcd', self.tid)
        defend_status_mg = self.defend_report_mg % (t_time, self.sessionID, self.tid)
        runtime_status_mg = self.runtime_status_mg % (t_time, self.sessionID, self.tid)
        sleep_status_mg = self.sleep_status_mg % (t_time, self.sessionID, self.tid)
        fob_status_mg = self.fob_status_mg % (t_time, self.sessionID, self.tid)

        location_mg = self.location_mg % (t_time, self.sessionID, self.tid, t_time)
        #realtime_mg = self.realtime_mg % (t_time, self.sessionID, self.tid, 1, t_time)
        locationdesc_mg = self.locationdesc_mg % (t_time, self.sessionID, self.tid)

        fobinfo_mg = self.fobinfo_mg % (t_time, self.sessionID, self.tid)
        unusual_activate_mg = self.unusual_activate_mg % (t_time, self.sessionID, self.tid, '1234', '15901258591', self.imsi)

        power_status_mg = self.power_status_mg % (t_time, self.sessionID, self.tid)
        
        power_status_report_mg = self.power_status_report_mg % (t_time, self.sessionID, self.tid)

        mgs = [charge_mg, pvt_mg, locationdesc_mg, defend_status_mg, runtime_status_mg, power_status_report_mg, power_status_mg, realtime_mg ]

        #mgs = [runtime_status_mg]
        #mgs = [power_status_mg]
        #mgs = [power_status_report_mg]
        #mgs = [pvt_mg]
        #mgs = [realtime_mg]
        #NOTE: realtime_mg must has a S4 ahead 
        for mg in mgs:
            #self.logging.info("Send report mg:\n%s", mg)
            self.socket.send(mg)
            time.sleep(2)
            #time.sleep(30)

        #lat = 116.420
        #lon = 39.912
        ###for i in range(100000):
        #for i in range(3):
        #    t_time = int(time.time())
        #    lat += 0.002
        #    lon += 0.003
        #    pvt_mg = self.pvt_mg % (t_time, self.sessionID, self.tid, lat, lon, t_time)
        #    print 'args', (t_time, self.sessionID, self.tid, lat, lon, t_time)
        #    print 'test', pvt_mg
        #    self.socket.send(pvt_mg)
        #    time.sleep(20)

    def report_mg(self):
        time.sleep(10)
        #report_mgs = [self.move_report_mg, self.terminal_powerlow_mg, self.shake_report_mg, self.sos_report_mg]
        #report_mgs = [self.terminal_powerfull_mg, self.terminal_powerlow_mg, self.terminal_poweroff_mg, self.fob_powerlow_mg]
        report_mgs = [self.move_report_mg, self.fob_powerlow_mg, self.shake_report_mg, self.sos_report_mg, self.terminal_powerdown_mg, self.terminal_stop_mg]
        #report_mgs = [self.terminal_powerdown_mg]
        #report_mgs = [self.shake_report_mg]
        #report_mgs = [self.terminal_stop_mg]
        while True:
            for report_mg in report_mgs:
                t_time = int(time.time())
                msg = report_mg % (t_time, self.sessionID, self.tid, t_time)
                self.logging.info("Send report mg:\n%s", msg)
                self.socket.send(msg)
                time.sleep(30)
                #time.sleep(1)

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
        ggmsg = self.query_args_mg % (t_time, self.sessionID, self.tid, args)
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
        #self.logging.info("Send set args %s success:\n%s", (set_arg, suc))

    def restart(self):
        self.logging.info("Restart terminal...")

    def remote_set(self):
        #t_time = time.strftime("%Y-%m-%d %H:%M:%S")
        time.sleep(30)
        t_time = int(time.time())
        remote_set_mg = self.remote_set_mg % (t_time, self.sessionID, self.tid)
        self.logging.info("Send remote_set mg:\n%s", remote_set_mg) 
        self.socket.send(remote_set_mg)
        
    def remote_unset(self):
        #t_time = time.strftime("%Y-%m-%d %H:%M:%S")
        time.sleep(25)
        t_time = int(time.time())
        remote_unset_mg = self.remote_unset_mg % (t_time, self.sessionID, self.tid)
        self.logging.info("Send remote_unset mg:\n%s", remote_unset_mg) 
        self.socket.send(remote_unset_mg)

    def remote_lock(self):
        #t_time = time.strftime("%Y-%m-%d %H:%M:%S")
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
        self.logging.info("Report config success!")

    def defend_status(self, bp):
        self.logging.info("Report defend_status success!")
        t_time = int(time.time())
        msg = self.fob_operate % (t_time, self.sessionID, self.tid)
        self.socket.send(msg)

    def pvt(self):
        self.logging.info("Report pvt success!")

    def charge(self):
        self.logging.info("Report charge success!")

    def async(self):
        self.logging.info("Report async success!")

    def unbind(self):
        t_time = int(time.time())
        msg= self.unbind_mg % (t_time, self.sessionID, self.tid)
        self.socket.send(msg)
        self.logging.info("Unbind success!")
        #time.sleep(3)
        #t_time = int(time.time())
        #unbind_status_mg = self.unbind_status_mg % (t_time, self.sessionID, self.tid)
        #self.socket.send(unbind_status_mg)

    #NOTE: depressed
    #def fob_operate(self, bp):
    #    t_time = int(time.time())
    #    msg = self.fob_operate % (t_time, self.sessionID, self.tid)
    #    self.socket.send(msg)

    def read_mg(self):
        """Read package from logfile then send them to gateway.
        """
        time.sleep(20)
        #NOTE:  
        logfile = '15919176710.log'
        sessionid = '0otq0d4v'
        tid = "ACB2012777"

        f = open(logfile)
        for line in f:
            line = line.replace(sessionid, self.sessionID)
            line = line.replace(tid, "gzx333")
            line = line.replace(" ", "")
            self.socket.send(line)
            time.sleep(5)

    def start_each_thread(self):
        thread.start_new_thread(self.heartbeat, ())
        thread.start_new_thread(self.upload_position, ())
        thread.start_new_thread(self.report_mg, ())
        thread.start_new_thread(self.report_once_mg, ())
        thread.start_new_thread(self.misc, ())
        #NOTE:  get log from log file
        #thread.start_new_thread(self.read_mg, ())


    def handle_recv(self, bp, io_loop):
        if bp.type == "S1":
            self.login_response(bp)
            self.start_each_thread()
        elif bp.type == "S2":
            self.heartbeat_response()
        elif bp.type == "S3":
            self.upload_response()
        #elif bp.type == "S4":
        #    self.realtime(io_loop)
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
        elif bp.type == "S19":
            pass
        elif bp.type == "S20":
            self.defend_status(bp)
        elif bp.type == "S24":
            self.unbind()
        else:
            pass
    
    def tcpClient(self, io_loop):
        try:
            self.login()
            while True:
                infds, _, _ = select.select([self.socket], [], [], 1)
                if len(infds) > 0:
                    dat = self.socket.recv(1024)
                    self.logging.info("Recv:%s", dat)
                    print 'recv: ', dat
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


    def initlog_new(self):

        logger = logging.getLogger()
        #logger = logging.getLogger(color=True, fmt=DEFAULT_FORMAT, datefmt=DEFAULT_DATE_FORMAT, colors=DEFAULT_COLORS)
        #logger = logging.getLogger(fmt=DEFAULT_FORMAT, datefmt=DEFAULT_DATE_FORMAT, colors=DEFAULT_COLORS)

        hdlr = logging.FileHandler("terminal.log")

        #DEFAULT_FORMAT = '%(color)s[%(levelname)1.1s %(asctime)s %(module)s:%(lineno)d]%(end_color)s %(message)s' 
        DEFAULT_FORMAT = '%(asctime)s %(levelname)s %(message)s' 
        #DEFAULT_FORMAT = '%(color)s[%(levelname)1.1s %(asctime)s %(module)s:%(lineno)d]%(end_color)s %(message)s %y%m%d %H:%M:%S' 
        DEFAULT_DATE_FORMAT = '%y%m%d %H:%M:%S' 
        DEFAULT_COLORS = { 
            logging.DEBUG: 4,  # Blue 
            logging.INFO: 2,  # Green 
            logging.WARNING: 3,  # Yellow 
            logging.ERROR: 1,  # Red 
        }


        #formatter = logging.Formatter('---------------------  %(asctime)s %(levelname)s %(message)s')
        formatter = logging.Formatter(fmt=DEFAULT_FORMAT, datefmt=DEFAULT_DATE_FORMAT)

        hdlr.setFormatter(formatter)

        logger.addHandler(hdlr)
    
        return logger

    def start_io_loop(self, io_loop):
        io_loop.start()
       
if __name__ == "__main__":   
    import sys
    
    io_loop = IOLoop.instance()

    args = dict(tid='T123SIMULATOR',
                tmobile='13011292217',
                umobile='18310505991',
                imsi='18310505991',
                imei='')
    keys = ['tid', 'tmobile', 'imsi', 'imei']
    for i, key in enumerate(keys):
        if len(sys.argv) > i+1:
            args[key] = sys.argv[i+1]
        else:
            break

    terminal = Terminal(args['tid'], args['tmobile'], args['umobile'], args['imsi'], args['imei'])
    thread.start_new_thread(terminal.tcpClient, (io_loop,))
    while True:
        time.sleep(10)
