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

class GWBatteryHandler(BaseHandler):

    @authenticated
    def get(self):
        """Jump to battery.html.
        """
        username = self.get_current_user()
        n_role = self.db.get("SELECT role FROM T_LOG_ADMIN"
                             " WHERE name = %s", 
                             username)
        self.render("battery/battery.html",
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
            sn = data.get("sn")
            search_type = data.get("search_type")
        except Exception as e:
            logging.exception("[LOG] Wrong data format. Exception: %s", 
                               e.args)
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            self.write_ret(status)
            return

        try:
            if search_type == '0':
                result = self.acbdb.get("SELECT tid "
                                        "  FROM T_TERMINAL_INFO"
                                        "  WHERE mobile = %s", 
                                        mobile)
                if result:
                    tid = result['tid']
                else:
                    logging.error("[LOG] Battery Inquiry: %s don't has terminal.", 
                                  mobile)
                    self.write_ret(ErrorCode.TERMINAL_NOT_EXISTED, 
                                   dict_=None)
                    return
            elif search_type == '1':
                tid = sn

            fc = FileConf()
            file_path = fc.getLogFile() + '/'
            files = os.listdir(file_path)

            # make the files ordered 
            d = {}
            for f in files:
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
                    logging.info("[LOG] skip file time :%s, file name:%s", 
                                 file_time, d[file_time])
                else:
                    ftime.append(file_time)
            files = [d.get(file_time) for file_time in ftime]

            lst = []
            for file in files:
                lines= linecache.getlines(file_path+file)
                linecache.updatecache(file_path+file)
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
                        logging.info("[LOG] Ignored file: %s, BeginTime: %s, EndTime: %s", 
                                     file, first_time, last_time)
                    else:
                        p1 = re.compile(tid, re.I)
                        p2 = re.compile("T2,")
                        p3 = re.compile("I ", re.I)
                        for num in range(len(lines)):
                            if p1.search(lines[num]) and p2.search(lines[num]) and p3.search(lines[num]):
                                if '20%s' % lines[num][3:18]>start_time and '20%s' % lines[num][3:18]<end_time:
                                    battery_time = lines[num][3:18]
                                    battery_num = lines[num].split(',')[6].split(':')[2]
                                    p = {'battery_time':battery_time,
                                         'battery_num':battery_num}
                                    lst.append(p)
                else:
                    pass
                linecache.clearcache()
            self.write_ret(ErrorCode.SUCCESS,
                           dict_=DotDict(res=lst))

        except Exception as e:
            linecache.clearcache()
            logging.exception("[LOG] Mobile: %s 's battery inquiry is failed. Exception: %s",
                              mobile, e.args)
            self.write_ret(ErrorCode.FAILED, dict_=None)
