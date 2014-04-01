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
    get_alert_freq_key, get_tid_from_mobile_ydwq
from utils.dotdict import DotDict
from utils.checker import check_sql_injection, check_zs_phone, check_cnum
from utils.public import record_add_action, delete_terminal
from base import BaseHandler, authenticated
from codes.errorcode import ErrorCode
from codes.smscode import SMSCode 
from constants import UWEB, SMS, GATEWAY

from helpers.queryhelper import QueryHelper  
from helpers.seqgenerator import SeqGenerator
from helpers.gfsenderhelper import GFSenderHelper
from helpers.smshelper import SMSHelper
from base import BaseHandler
from codes.wxerrorcode import WXErrorCode
from mixin import BaseMixin


class TerminalsMixin(BaseMixin):

    KEY_TEMPLATE = "terminals_report_%s_%s"

    def prepare_data(self, hash_):
        mem_key = self.get_memcache_key(hash_)
        data = self.getvalue(mem_key)

        if data:
            return data


class TerminalsHandler(BaseHandler, TerminalsMixin):

    @tornado.web.removeslash
    def get(self):
        """Get terminal info.
        """
        status = WXErrorCode.SUCCESS
        try:

            openid = self.getopenid()
            body = self.request.body
            checksql = "SELECT  uid FROM T_USER WHERE openid = '%s'" % openid

            try:    
                user = self.db.query(checksql)
            except MySQLdb.Error as e:
                logging.exception("[WEIXIN] terminals get() check openid, Exception:%s",
                              e.args)

            tlist = []
            listsql = "SELECT t.tid , t.dev_type, t.mobile, t.owner_mobile, t.alias, t.gsm, t.gps, " \
                      "t.login,t.login_time, t.offline_time, t.domain, t.service_status, t.defend_status, " \
                      "t.mannual_status,t.begintime, t.endtime, t.group_id, t.activation_code, t.biz_type, " \
                      "pbat FROM T_TERMINAL_INFO as t INNER JOIN T_USER on T_USER.openid = '%s' " \
                      "and t.owner_mobile=T_USER.mobile" % openid
            if user:
                try:
                    tlist = self.db.query(listsql)
                except MySQLdb.Error as e:
                    logging.exception("[WEIXIN] terminals get() search terminals list, Exception:%s",
                              e.args)
            else:
                status = WXErrorCode.USER_BIND
                message = WXErrorCode.ERROR_MESSAGE[status]
                self.render('error.html',
                            status=status,
                            message=message)
                return

            res = []
            if not tlist:
                tlist = []
            for t in tlist:
                localsql = "SELECT name, clatitude, clongitude FROM T_LOCATION WHERE  tid = '%s'  AND " \
                           "NOT (latitude = 0 OR longitude = 0) ORDER BY timestamp DESC limit 1" % t.get('tid')
                try:
                    local = self.db.query(localsql)
                except MySQLdb.Error as e:
                    logging.exception("[WEIXIN] terminals get() search location, Exception:%s",
                              e.args)
                clongitude = 0
                clatitude = 0
                for l in local:
                    clongitude = l.get('clongitude')
                    clatitude = l.get('clatitude')
                    name = l.get('name')
                _res = dict(tid=t.get('tid'),
                            dev_type=t.get('dev_type'),
                            mobile=t.get('mobile'),
                            owner_mobile=t.get('owner_mobile'),
                            alias=t.get('alias'),
                            gsm=t.get('gsm'),
                            gps=t.get('gps'),
                            login=t.get('login'),
                            login_time=t.get('login_time'),
                            offline_time=t.get('offline_time'),
                            domain=t.get('domain'),
                            service_status=t.get('service_status'),
                            defend_status=t.get('defend_status'),
                            mannual_status=t.get('mannual_status'),
                            begintime=t.get('begintime'),
                            endtime=t.get('endtime'),
                            group_id=t.get('group_id'),
                            activation_code=t.get('activation_code'),
                            biz_type=t.get('biz_type'),
                            pbat=t.get('pbat'),
                            clongitude=clongitude,
                            clatitude=clatitude
                            )
                res.append(_res)
                  
            self.render("terminals.html",
                        status=status,
                        res=res)

        except Exception as e:
            logging.exception("[WEIXIN] list of terminals failed, Execption:%s ", 
                              e.args)
            self.render('error.html',
                        message=WXErrorCode.FAILED)

