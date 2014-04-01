# -*- coding: utf-8 -*-

import hashlib
import time
import logging
from hashlib import md5
import urllib2
import json
import MySQLdb

import tornado.web
from tornado.escape import json_encode, json_decode

from utils.dotdict import DotDict
from utils.misc import get_ios_push_list_key, get_ios_id_key, get_ios_badge_key,\
     get_android_push_list_key, get_terminal_info_key, get_location_key, get_lastinfo_time_key, DUMMY_IDS
from utils.checker import check_sql_injection, check_phone
from utils.public import get_group_info_by_tid
from codes.wxerrorcode import WXErrorCode
from constants import UWEB, EVENTER, GATEWAY
from base import BaseHandler, authenticated
from helpers.notifyhelper import NotifyHelper
from helpers.queryhelper import QueryHelper 
from helpers.lbmphelper import get_locations_with_clatlon
from helpers.downloadhelper import get_version_info 
from helpers.confhelper import ConfHelper


class BindHandler(BaseHandler):

    @tornado.web.removeslash
    def get(self):
        #openid = "oPaxZt1v4rhWN9hBgJ4vLh-nejJw"
        openid = self.getopenid()
        user = self.db.get("SELECT uid FROM T_USER WHERE openid = %s", openid)
        if user is not None:
            status = WXErrorCode.USER_BINDED
            self.render("error.html",
                        status=status,
                        message=WXErrorCode.ERROR_MESSAGE[status])
            return
            
        self.render("bind.html", openid=openid)
    
    @tornado.web.removeslash
    def post(self):
        status = WXErrorCode.SUCCESS
        try:
            data = json_decode(self.request.body)
            username = data.get('username')
            password = data.get('password')
            openid = data.get('openid')

            sql = "SELECT uid, openid FROM T_USER WHERE uid = '%s' and password = PASSWORD(%s) "\
                  % (username, password)
            try:
                user = self.db.query(sql)
            except MySQLdb.Error, e:
                status = WXErrorCode.USER_EXIST
                self.write_ret(status=status, message=WXErrorCode.ERROR_MESSAGE[status])
                logging.exception("[WEIXIN] bind check user post(), Exception:%s",
                              e.args)
                return

            bindsql = "UPDATE T_USER SET openid = '%s' WHERE uid = '%s' " % (openid, username)
            if user:
                if user[0]['openid'] is None:
                    user[0]['openid'] = ''
                if len(user[0]['openid']) == 0:
                    try:
                        self.db.execute(bindsql)
                    except MySQLdb.Error, e:
                        status = WXErrorCode.USER_EXIST
                        self.write_ret(status=status, message=WXErrorCode.ERROR_MESSAGE[status])
                        logging.exception("[WEIXIN] bind user post(), Exception:%s",
                              e.args)
                        return

                else:
                    status = WXErrorCode.USER_BINDED
                    self.write_ret(status=status, message=WXErrorCode.ERROR_MESSAGE[status])
                    return

            else:
                status = WXErrorCode.USER_EXIST
                self.write_ret(status=status, message=WXErrorCode.ERROR_MESSAGE[status])
                return

            self.write_ret(status=status, message=WXErrorCode.ERROR_MESSAGE[status])
        except Exception as e:
            logging.exception("[WEIXIN] bind ydcws account failed, Exception:%s",
                              e.args)
            message = WXErrorCode.ERROR_MESSAGE[status]
            self.render('error.html',
                        status=status,
                        message=message)


class UnBindHandler(BaseHandler):

    @tornado.web.removeslash
    def get(self):
        status = WXErrorCode.SUCCESS
        try:
            openid = self.getopenid()
            user = self.db.get("SELECT uid, password FROM T_USER WHERE openid = %s LIMIT 1",
                               openid)
            if user is None:
                username = ''
                status = WXErrorCode.USER_BIND
                self.render("error.html",
                            status=status,
                            message=WXErrorCode.ERROR_MESSAGE[status])
                return
            else:
                username = user['uid']

            self.render("unbind.html",
                        openid=openid,
                        username=username,
                        status=status)

        except Exception as e:
            status = WXErrorCode.FAILED
            self.render("error.html", status=status, message=WXErrorCode.ERROR_MESSAGE[status])
            logging.exception("[WEIXIN] unbind GET() fail, Execption:%s",
                              e.args)
    @tornado.web.removeslash
    def post(self):
        status = WXErrorCode.SUCCESS
        try:
            data = json_decode(self.request.body)
            openid = data.get('openid', '')
            username = data.get('username', '')
            password = data.get('password', '')
            sql = "SELECT uid, password, openid FROM T_USER WHERE uid = '%s' and password = PASSWORD('%s') "\
                  % (username, password)
            try:
                user = self.db.query(sql)
            except MySQLdb.Error as e:
                logging.exception("[WEIXIN]unbind check account failed, Exception:%s",
                              e.args)
            
            if not user:
                status = WXErrorCode.USER_EXIST
                message = WXErrorCode.ERROR_MESSAGE[status]
                self.write_ret(status=status, message=message)
                return
            else:
                if user[0]['openid'] is None or len(user[0]['openid']) == 0:
                    status = WXErrorCode.USER_BIND
                    message = WXErrorCode.ERROR_MESSAGE[status]
                    self.write_ret(status=status, message=message)
                    return
            
            username = ''
            password = ''
            for u in user:
                username = u.get('uid', '')
                password = u.get('password', '')
                unbindsql = "UPDATE T_USER SET openid = '' WHERE uid = '%s' " % username
                try:
                    self.db.execute(unbindsql)
                except MySQLdb.Error as e:
                    logging.exception("[WEIXIN] unbind account failed, Exception:%s",
                              e.args)
                
            message = WXErrorCode.ERROR_MESSAGE[status]
            self.write_ret(status, message=message)

        except Exception as e:
            logging.exception("[WEIXIN] unbind ydcws account failed, Exception: %s",
                              e.args)
            status = WXErrorCode.FAILED
            message = WXErrorCode.ERROR_MESSAGE[status]
            self.render("error.html",
                        status=status,
                        message=message)
