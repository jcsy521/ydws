#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import time
import logging

import tornado.web
from tornado.escape import  json_decode

from utils.dotdict import DotDict
from codes.errorcode import ErrorCode
from base import authenticated, BaseHandler, log_file_path

class GWPacketHandler(BaseHandler):
    
    @authenticated
    def get(self):
        username = self.get_current_user()
        n_role = self.db.get("select role from T_LOG_ADMIN where name = %s", username)
        print "role",n_role.role
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
        except Exception as e:
            logging.exception("[LOG] Wrong data format. Exception: %s", 
                               e.args)
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            self.write_ret(status)
            return

        try:
            result = self.acbdb.get("SELECT tid FROM T_TERMINAL_INFO WHERE mobile = %s",
                                     mobile)
            file_path = log_file_path()
            files = os.listdir(file_path)
            lst = []
            if result:
                tid = result['tid']
                for file in files:
                    dat_file = open(file_path+file, 'rb')
                    first_line = dat_file.readline().strip()
                    if first_line:
                        while first_line[0] != '[':
                            first_line = dat_file.readline().strip()
                        first_time = '20%s' % first_line[3:18]
                        #Get the file's recently alter time throught os.stat(filename).st_mtime to last_time
                        last_time = time.strftime("%Y%m%d %H:%M:%S", time.localtime(os.stat(file_path+file).st_mtime) )
                        if start_time > last_time or end_time < first_time:
                            logging.info("[LOG] Ignored file: %s, BeginTime: %s, EndTime: %s", file, first_time, last_time)
                        else:
                            log = open(file_path+file, 'r')
                            p1 = re.compile(tid, re.I)
                            p2 = re.compile("recv:", re.I)
                            p3 = re.compile(packet_type, re.I)
                            for line in log:
                                if p1.search(line) and p2.search(line) and p3.search(line):
                                    if  '20%s' % line[3:18] > start_time and '20%s' % line[3:18] < end_time:
                                        ldata = line.split(',')
                                        packet_type = ldata[5][0:3]
                                        packet_time = line[3:18]
                                        packet = line
                                        p = {'packet_time':packet_time,
                                             'packet_type':packet_type ,
                                             'packet':packet}
                                        lst.append(p)
                            log.close()
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

