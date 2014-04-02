# -*- coding: utf-8 -*-

import logging
import time
import datetime
from dateutil.relativedelta import relativedelta
import urllib2, json
import xml.etree.ElementTree as ET
import hashlib
import MySQLdb

import tornado.web
from tornado.escape import json_decode, json_encode
from tornado.ioloop import IOLoop

from utils.misc import get_terminal_sessionID_key, get_terminal_address_key,\
    get_terminal_info_key, get_lq_sms_key, get_lq_interval_key, get_del_data_key,\
    get_alert_freq_key, get_tid_from_mobile_ydwq, safe_unicode
from utils.dotdict import DotDict
from utils.checker import check_sql_injection, check_zs_phone, check_cnum
from utils.public import record_add_action, delete_terminal
from base import BaseHandler, authenticated
from codes.errorcode import ErrorCode
from codes.smscode import SMSCode 
from constants import UWEB, SMS, GATEWAY, EVENTER

from helpers.queryhelper import QueryHelper  
from helpers.seqgenerator import SeqGenerator
from helpers.gfsenderhelper import GFSenderHelper
from helpers.smshelper import SMSHelper
from base import BaseHandler
from codes.wxerrorcode import WXErrorCode


class EventHandler(BaseHandler):

    @tornado.web.removeslash
    def get(self):
        """Get event info.
        """
        status = WXErrorCode.SUCCESS
        try:
            body = self.request.body
            openid = self.getopenid()
            user = self.db.get("SELECT uid, mobile "
                               "  FROM T_USER "
                               "  WHERE openid = %s", 
                               openid)

            if user is None:
                mobile = ''
                status = WXErrorCode.USER_BIND
                message=WXErrorCode.ERROR_MESSAGE[status]
                self.render('error.html',
                            status=status,
                            message=message)
                return
            else:
                mobile = user['mobile']
            try:
                res = self.db.query("SELECT tid FROM T_TERMINAL_INFO "
                                    "  WHERE owner_mobile = %s",
                                    mobile)
            except MySQLdb.Error as e:
                logging.exception("[WEIXIN]event search terminals failed, Exception:%s",
                              e.args)
            if not res:
                res = []
            for r in res:
                terminal = QueryHelper.get_terminal_info(r['tid'], self.db, self.redis)  
                r['alias'] = terminal['alias']
            self.render("event.html",  
                        openid=openid, 
                        res=res)

        except Exception as e:
            status = WXErrorCode.FAILED
            logging.exception("[WEIXIN] get event failed, Execptin:%s ",
                              e.args)
            self.render('error.html', 
                        status=status,
                        message=WXErrorCode.ERROR_MESSAGE[status])

    @tornado.web.removeslash
    def post(self):
        """Get event info.
        """
        status = WXErrorCode.SUCCESS
        try:
            data = DotDict(json_decode(self.request.body))
            logging.info("[WEIXIN] event request body: %s", self.request.body)
            tid = data.tid
            openid = data.get('openid')
            start_time = data.start_time
            end_time = data.end_time
        except Exception as e:
            status = WXErrorCode.ILLEGAL_DATA_FORMAT
            logging.exception("[WEIXIN] Invalid data format. Exception: %s",
                              e.args)
            self.render('error.html', 
                        status=status,
                        message=WXErrorCode.ERROR_MESSAGE[status])
            return

        try:
            checksql = "SELECT  uid FROM T_USER WHERE openid = '%s'" % openid
            user = self.db.query(checksql)
            if not user:
                status = WXErrorCode.USER_BIND
                message = WXErrorCode.ERROR_MESSAGE[status]
                self.render('error.html',
                            status=status,
                            message=message)
                return

            sql = ("SELECT tid, latitude, longitude, clatitude, clongitude," 
                   "  timestamp, name, type, speed, degree,"
                   "  category, pbat, terminal_type, fobid, rid, locate_error"
                   "  FROM V_EVENT"
                   "  WHERE tid ='%s'"
                   "    AND (timestamp BETWEEN %s AND %s)"
                   "  ORDER BY timestamp DESC") %\
                (tid, start_time, end_time)

            #sql = ("SELECT tid, latitude, longitude, clatitude, clongitude," 
             #      "  timestamp, name, type, speed, degree,"
              #     "  category, pbat, terminal_type, fobid, rid, locate_error"
               #    "  FROM V_EVENT"
                #   "   where timestamp BETWEEN %s AND %s"
                 #  "  ORDER BY timestamp DESC limit 21 ") %\
               # (start_time, end_time)
            events = self.db.query(sql)
                
            alias_dict = {}
            terminal_info_key = get_terminal_info_key(tid)
            terminal_info = self.redis.getvalue(terminal_info_key)
            alias_dict[tid] = terminal_info['alias'] if terminal_info['alias'] else terminal_info['mobile']

            # change the type form decimal to float.
            for event in events:
                event['alias'] = '' # alias_dict[event['tid']] 
                event['pbat'] = event['pbat'] if event['pbat'] is not None else 0
                event['fobid'] = event['fobid'] if event['fobid'] is not None else u''
                event['name'] = event['name'] if event['name'] is not None else u''
                event['degree'] = float(event['degree'])
                event['speed'] = float(event['speed'])
                event['comment'] = ''
                if event['category'] == EVENTER.CATEGORY.POWERLOW:
                    if event['terminal_type'] == '1':
                        if int(event['pbat']) == 100:
                            event['comment'] = ErrorCode.ERROR_MESSAGE[ErrorCode.TRACKER_POWER_FULL] 
                        elif int(event['pbat']) <= 5:
                            event['comment'] = ErrorCode.ERROR_MESSAGE[ErrorCode.TRACKER_POWER_OFF] 
                        else:
                            event['comment'] = (ErrorCode.ERROR_MESSAGE[ErrorCode.TRACKER_POWER_LOW]) % event['pbat']
                    else:
                        event['comment'] = ErrorCode.ERROR_MESSAGE[ErrorCode.FOB_POWER_LOW] % event['fobid']

                if event['category'] in [EVENTER.CATEGORY.REGION_ENTER, EVENTER.CATEGORY.REGION_OUT]:
                    region = self.db.get("SELECT name AS region_name"
                                         "  FROM T_REGION"
                                         "  WHERE id = %s",
                                         event.rid)
                    
                    region_name = safe_unicode(region.region_name) if region else u''
                    event['comment'] = u'围栏名：'+ region_name
 
            r = events * 2 + events[0:6]
            self.write_ret(status,
                           dict_=DotDict(res=r))

            print "jjjjjj res:",r
        except Exception as e:
            logging.exception("[WEIXIN] search event failed POST(), Execption:%s",
                              e.args)
            status=WXErrorCode.FAILED
            message=WXErrorCode.ERROR_MESSAGE[status]
            self.render('error.html',
                        status=status,
                        message=message)


