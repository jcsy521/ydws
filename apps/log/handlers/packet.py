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
        """Jumtp to packet.html.
        """
        username = self.get_current_user()
        n_role = self.db.get("SELECT role FROM T_LOG_ADMIN WHERE name = %s", username)
        self.render("packet/packet.html",
                     username=username,
                     role=n_role.role)

    @authenticated
    @tornado.web.removeslash
    def post(self):
        try:
            data = json_decode(self.request.body)
            logging.info("[LOG] packet request body: %s", data)
            start_time = data.get("start_time")
            end_time = data.get("end_time")
            mobile = data.get("mobile")
            sn = data.get("sn")
            packet_type = data.get("packet_types")
            is_report = data.get("is_report")
            search_type = data.get("search_type")
        except Exception as e:
            logging.exception("[LOG] Wrong data format. Exception: %s", 
                               e.args)
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            self.write_ret(status)
            return

        try:
            if search_type == '0':
                result = self.acbdb.get("SELECT tid FROM T_TERMINAL_INFO WHERE mobile = %s",
                                        mobile)
                if result:
                    tid = result['tid']
                else:
                    logging.error("[LOG] Packet Inquiry: %s don't has terminal.", mobile)
                    self.write_ret(ErrorCode.TERMINAL_NOT_EXISTED, dict_=None)
                    return
            elif search_type == '1':
                tid = sn

            fc = FileConf()
            file_path = fc.getLogFile() + '/'
            files = os.listdir(file_path)

            # make the files ordered 
            d = {} 
            for f in files: 
                if not f.startswith('error'):
                    continue
                file_time = os.path.getmtime(file_path+f) 
                d[file_time] = f 
                L = d.keys() 
            L.sort() 
            ftime=[]
            for file_time in L:
                format = '%Y%m%d %H:%M:%S'
                tmp = time.localtime(file_time)
                dt = time.strftime(format, tmp)
                if dt < start_time:
                    logging.info("[LOG] skip file time :%s, file name:%s", file_time, d[file_time])
                else:
                    ftime.append(file_time)
            files = [d.get(file_time) for file_time in ftime]

            lst = []
            for file in files:
                logging.info("[LOG] handle file: %s", file)
                lines= linecache.getlines(file_path+file)
                linecache.updatecache(file_path+file)
                if len(lines) !=0:
                    first_num = 0
                    last_num = len(lines)-1
                    if len(lines[first_num]) <= 1:
                        continue
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
                        p3 = re.compile(packet_type)
                        for num in range(len(lines)):
                            if p1.search(lines[num]) and p2.search(lines[num]) and p3.search(lines[num]):
                                if  '20%s' % lines[num][3:18] > start_time and '20%s' % lines[num][3:18] < end_time:
                                    ldata = lines[num].split(',')
                                    T_packet_type = ldata[5][0:3]+','
                                    T_packet_time = lines[num][3:18]
                                    packet = lines[num]
                                    p = {'packet_time':T_packet_time,
                                         'packet_type':T_packet_type ,
                                         'packet':packet}
                                    lst.append(p)
                                    if is_report == 1:
                                        #ip = lines[num].split('\'')[1]
                   
                                        #ip_index = lines[num].find('from')+4
                                        #ip = lines[num][ip_index:][1:-1]
                                        #ip = lines[num].split('\'')[1]

                                        p_ip = re.compile(r"from \('.*?', .*?\)")
                                        ip = p_ip.findall(lines[num])[0][6:-1]

                                        match_type = 'S' + ldata[5][1:3]+','
                                        next_num = num + 1
                                        p6 = re.compile("I ", re.I)
                                        p7 = re.compile("send:", re.I)
                                        p8 = re.compile(ip, re.I)
                                        p9 = re.compile(match_type, re.I)
                                        while True:
                                            if len(lines) - 1 < next_num:
                                                logging.info("[LOG] next_num:%s may be invalid, break", next_num)
                                                break
                                            if p6.search(lines[next_num]) and p7.search(lines[next_num]) and p8.search(lines[next_num]) and p9.search(lines[next_num]):
                                                S_packet_time = lines[next_num][3:18]
                                                packet = lines[next_num]
                                                p = {'packet_time':S_packet_time,
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
                linecache.clearcache()
            self.write_ret(ErrorCode.SUCCESS,
                           dict_=DotDict(res=lst))

        except Exception as e:
            logging.exception("[LOG] Mobile: %s 's packet inquiry is failed. Exception: %s",
                              mobile, e.args)
            linecache.clearcache()
            self.write_ret(ErrorCode.FAILED, dict_=None)

