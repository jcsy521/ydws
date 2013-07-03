#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import time
import logging
import linecache

import tornado.web
from tornado.escape import  json_decode

from fileconf import FileConf
from utils.dotdict import DotDict
from codes.errorcode import ErrorCode
from base import authenticated, BaseHandler

class GWPacketHandler(BaseHandler):
    
    @authenticated
    def get(self):
        username = self.get_current_user()
        n_role = self.db.get("select role from T_LOG_ADMIN where name = %s", username)
        self.render("packet/packet.html",
                     username=username,
                     role=n_role.role)

    @authenticated
    @tornado.web.removeslash
    def post(self):

        try:
            data = json_decode(self.request.body)
            start_time = data.get("start_time")
            end_time = data.get("end_time")
            mobile = data.get("mobile")
            packet_type = data.get("packet_types")
            is_report = data.get("is_report")
        except Exception as e:
            logging.exception("[LOG] Wrong data format. Exception: %s", 
                               e.args)
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            self.write_ret(status)
            return
        
        try:
            result = self.acbdb.get("SELECT tid FROM T_TERMINAL_INFO WHERE mobile = %s",
                                     mobile)
            fc = FileConf()
            file_path = fc.getLogFile()
            files = os.listdir(file_path)
            lst = []
            if result:
                tid = result['tid']
                for file in files:
                    lines= linecache.getlines(file_path+file)
                    if len(lines) !=0:
                        first_num = 0
                        last_num = len(lines)-1
                        while lines[first_num][0] != '[':
                            first_num = first_num+1
                        first_time = '20%s' % lines[first_num][3:18]
                        while lines[last_num][0] != '[':
                            last_num = last_num - 1
                        last_time = '20%s' % lines[last_num][3:18]
                        if start_time > last_time or end_time < first_time:
                            logging.info("[LOG] Ignored file: %s, BeginTime: %s, EndTime: %s", file, first_time, last_time)
                        else:
                            p1 = re.compile(tid, re.I)
                            p2 = re.compile("recv:", re.I)
                            p3 = re.compile(packet_type, re.I)
                            for num in range(len(lines)):
                                if p1.search(lines[num]) and p2.search(lines[num]) and p3.search(lines[num]):
                                    if  '20%s' % lines[num][3:18] > start_time and '20%s' % lines[num][3:18] < end_time:
                                        ldata = lines[num].split(',')
                                        packet_type = ldata[5][0:3]
                                        packet_time = lines[num][3:18]
                                        packet = lines[num]
                                        p = {'packet_time':packet_time,
                                             'packet_type':packet_type ,
                                             'packet':packet}
                                        lst.append(p)
                                        if is_report == 1:
                                            ip = lines[num].split('\'')[1]
                                            match_type = 'S' + ldata[5][1:3]
                                            next_num = num + 1
                                            p6 = re.compile("I ", re.I)
                                            p7 = re.compile("send:", re.I)
                                            p8 = re.compile(ip, re.I)
                                            p9 = re.compile(match_type, re.I)
                                            while True:
                                                if p6.search(lines[next_num]) and p7.search(lines[next_num]) and p8.search(lines[next_num]) and p9.search(lines[next_num]):
                                                    packet_time = lines[next_num][3:18]
                                                    packet = lines[next_num]
                                                    p = {'packet_time':packet_time,
                                                         'packet_type':match_type ,
                                                         'packet':packet}
                                                    lst.append(p)
                                                    
                                                    break
                                                else:
                                                    next_num = next_num + 1
                                                    if next_num == num + 500:
                                                        break
                                        elif is_report == 0:
                                            pass
                    else: 
                         pass
                self.write_ret(ErrorCode.SUCCESS,
                               dict_=DotDict(packet_list=lst))
            else:
                logging.error("[LOG] TID: %s don't has terminal.", mobile)
                self.write_ret(ErrorCode.TERMINAL_NOT_EXISTED, dict_=None)
        except Exception as e:
            logging.exception("[LOG] Mobile: %s 's battery inquiry is failed. Exception: %s", 
                              mobile, e.args)
            self.write_ret(ErrorCode.FAILED, dict_=None)

