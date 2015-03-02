# -*- coding: utf-8 -*-

"""This module is designed for ZNBC.

#NOTE: deprecated.
"""

import logging
import httplib2

import tornado.web
from tornado.escape import json_decode

from utils.dotdict import DotDict
from utils.misc import safe_utf8
from codes.errorcode import ErrorCode
from base import BaseHandler, authenticated
from helpers.confhelper import ConfHelper
from helpers.smshelper import SMSHelper
from urllib import urlencode

       
class InformationHandler(BaseHandler):
    
    @authenticated
    @tornado.web.removeslash
    def get(self):
        """ """ 
        status = ErrorCode.SUCCESS
        try:
            page_number = int(self.get_argument('pagenum'))
            page_count = int(self.get_argument('pagecnt'))
            #reserved API
            fields = DotDict(name="name LIKE '%%%%%s%%%%'",
                             mobile="mobile LIKE '%%%%%s%%%%'")
            for key in fields.iterkeys():
                v = self.get_argument(key, None)
                if v:
                    fields[key] = fields[key] % (v,)
                else:
                    fields[key] = None
        except Exception as e:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            logging.exception("[UWEB] cid: %s Send message to ios push server data format illegal. Exception: %s", 
                              self.current_user.cid, e.args) 
            self.write_ret(status)
            return

        try:
            where_clause = ' AND '.join([v for v in fields.itervalues()
                                         if v is not None])
            page_size = 20
            if where_clause:
                where_clause = ' AND ' + where_clause
            if page_count == -1:
                sql = "SELECT count(id) as count FROM T_PASSENGER" + \
                      "  WHERE 1=1 " + where_clause
                sql += " AND cid = %s" % (self.current_user.cid,)
                res = self.db.get(sql) 
                count = res.count
                d, m = divmod(count, page_size)
                page_count = (d + 1) if m else d

            sql = "SELECT id, pid, name, mobile FROM T_PASSENGER" +\
                  "  WHERE 1=1 " + where_clause
            sql += " AND cid = %s LIMIT %s, %s" % (self.current_user.cid, page_number * page_size, page_size)
            passengers = self.db.query(sql)
            for passenger in passengers:
                for key in passenger.keys():
                    passenger[key] = passenger[key] if passenger[key] else ''
            self.write_ret(status,
                           dict_=DotDict(passengers=passengers,
                                         pagecnt=page_count))
        except Exception as e:
            logging.exception("[UWEB] cid: %s get passenger failed. Exception: %s", 
                              self.current_user.cid, e.args) 
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)

    @authenticated
    @tornado.web.removeslash
    def post(self):
        """push message to ios push server.
        """
        try:
            data = DotDict(json_decode(self.request.body))
            logging.info("[UWEB] Send message to ios push server request: %s, cid: %s", 
                         data, self.current_user.cid)
        except Exception as e:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            #logging
            self.write_ret(status)
            return

        try:
            status = ErrorCode.SUCCESS
            sms_way = int(data.sms_way)
            push_way = int(data.push_way)
            all_passenger = int(data.all_passenger)
            message = data.message
            push_pids = []
            sms_mobiles = []
            push_status = ErrorCode.FAILED
            sms_status = ErrorCode.FAILED
            
            # 1:select all
            if push_way == 1:
                if all_passenger == 1:
                    # must query, when select all passenger web only transmit the first page passengers' pids and mobiles
                    passengers = self.db.query("SELECT pid"
                                               "  FROM T_PASSENGER tp, T_CORP tc"
                                               "  WHERE tp.cid = tc.cid"
                                               "  AND tc.cid = %s"
                                               "  AND tp.push = 1"
                                               "  AND pid != '' ",
                                               self.current_user.cid)
                    push_pids = [passenger.pid for passenger in passengers]
                    
                else:
                    #pid may be ''
                    pids = data.pids
                    for pid in pids:
                        if pid != '':
#                            passenger = self.db.get("SELECT id"
#                                                    "  FROM T_PASSENGER "
#                                                    "  WHERE pid = %s"
#                                                    "  AND push = 1",
#                                                    pid)
#                            if passenger:
                            push_pids = push_pids.append(pid)
            
                push_status = push(push_pids, message)
            if sms_way == 1:
                if all_passenger == 1:
                    passengers = self.db.query("SELECT tp.mobile"
                                               "  FROM T_PASSENGER tp, T_CORP tc"
                                               "  WHERE tp.cid = tc.cid"
                                               "  AND tc.cid = %s",
                                               self.current_user.cid)
                    sms_mobiles = [passenger.mobile for passenger in passengers]
                else:
                    #mobile is not ''
                    sms_mobiles = data.mobiles
                sms_status = send_sms(sms_mobiles, message)
            
            if push_status == ErrorCode.FAILED and sms_status == ErrorCode.FAILED:
                status = ErrorCode.FAILED
            else:
                status = ErrorCode.SUCCESS
                
            self.write_ret(status)
        except Exception as e:
            logging.exception("[UWEB] cid: %s send message failed. Exception: %s", 
                              self.current_user.cid, e.args) 
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)


def send_sms(mobiles, message):
    if mobiles is None:
        return ErrorCode.SUCCESS
    num = 0
    try:
        for mobile in mobiles:
            ret = SMSHelper.send(mobile, message)
            ret = json_decode(ret)
            status = ret['status']
            if status == ErrorCode.SUCCESS:
                num += 1
                
        if num != len(mobiles):
            status = ErrorCode.FAILED
            return status
        else:
            status = ErrorCode.SUCCESS
            return status
    except Exception as e:
            logging.exception("[UWEB] Send sms to sms server failed. Exception: %s", 
                              e.args) 
            status = ErrorCode.SERVER_BUSY
            return status


def push(pids, message):
    if pids is None:
        return ErrorCode.SUCCESS
    alert = u'资讯推送'
    
    try:
        h = httplib2.Http()
        headers = {"Content-type": "application/x-www-form-urlencoded; charset=utf-8"}
        url = ConfHelper.OPENFIRE_CONF.ios_push_url 
        num = 0
        for pid in pids:
            data = DotDict(uid=pid,
                           alert=safe_utf8(alert),#下拉列表推送消息title
                           badge=1,#图标右上角消息条数提示
                           body=safe_utf8(message))
            response, content = h.request(url, 'POST', body=urlencode(data), headers=headers)
            if response['status'] == '200':
                ret = json_decode(content)
                if ret['status'] == 0:
                    num += 1
                    logging.info("Push to push server success! pid: %s", pid)
                else:
                    logging.error("Push to push server failed! pid: %s, Message: %s", pid, ret['message'])
            else:
                logging.error("Send message to push server failed! response: %s", response)
                
        if num != len(pids):
            status = ErrorCode.FAILED
            return status
        else:
            status = ErrorCode.SUCCESS
            return status
    except Exception as e:
        logging.exception("[UWEB] Send message to push server failed. Exception: %s", 
                          e.args) 
        status = ErrorCode.SERVER_BUSY
        return status
