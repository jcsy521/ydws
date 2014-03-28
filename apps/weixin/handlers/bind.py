# -*- coding: utf-8 -*-

import hashlib
import time
import logging
from hashlib import md5
import urllib2
import json

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

    def getopenid(self):
        code = self.get_argument('code')
        getop = "https://api.weixin.qq.com/sns/oauth2/access_token?appid=wx394eee811bd082b1&secret=a1a255d959889b86612cefe39324ef23&code=%s&grant_type=authorization_code" % code
        f = urllib2.urlopen(getop)
        co = f.read().decode("utf-8")
        jsonT = json.loads(co)
        access_token = jsonT['access_token']
        print("---->co %s") % jsonT
        openid = jsonT['openid']
        return openid

    @tornado.web.removeslash
    def get(self):
        #openid = "oPaxZt1v4rhWN9hBgJ4vLh-nejJw"
        #openid = self.get_argument('openid', 0)
        openid = self.getopenid()
        print("------->>>openid:%s") % openid
        self.render("bind.html",openid = openid) 
    
    @tornado.web.removeslash
    def post(self):
        status = WXErrorCode.SUCCESS
        try:
            data = json_decode(self.request.body)
            print("_______>>>>data:%s") % data
            username = data.get('username')
            password = data.get('password')
            #openid = 'oPaxZt1v4rhWN9hBgJ4vLh-nejJw'
            uid = username
            openid = data.get('openid')
            print("----<<<<<<--->>>openid:%s") % openid
            print("username:password %s:%s") %(username,password)
            sql = "SELECT uid, password FROM T_USER WHERE uid = '%s' and password = PASSWORD(%s) " % (username, password)
            print("SQL:%s") % sql
            user = self.db.query(sql)
            bindsql = "UPDATE T_USER SET openid = '%s' WHERE uid = '%s' " % (openid, username)
            if user:
                self.db.execute(bindsql)
            else:
                status = WXErrorCode.USER_EXIST
                message = WXErrorCode.ERROR_MESSAGE[status]
                self.write_ret(status=status, message=message)
                print("--------======")
            self.write_ret(status=status, message='')
        except Exception as e:

            logging.exception("bind ydcws account failed")
            message = WXErrorCode.ERROR_MESSAGE[status]
            self.write_ret(status=status, message=message)


class UnBindHandler(BaseHandler):

    @tornado.web.removeslash
    def get(self):
        openid = "oPaxZt1v4rhWN9hBgJ4vLh-nejJw"
        
        self.render("unbind.html", openid=openid, username='')

    @tornado.web.removeslash
    def post(self):
        status = WXErrorCode.SUCCESS
        try:
            openid = 'oPaxZt1v4rhWN9hBgJ4vLh-nejJw'
            sql = "SELECT uid, password FROM T_USER WHERE openid = %s" % openid
            user = self.db.query(sql)
            username = ''
            password = ''
            
            for u in user:
                username  = u.get('username')
                password = u.get('password')
            
            bindsql = "UPDATE T_USER SET openid = %s WHERE uid = %s" % ('', username)
            if user:
                self.db.execute(bindsql)
            else:
                status = WXErrorCode.USER_EXIST
                message = WXErrorCode.ERROR_MESSAGE[status]
                self.render("unbind.html", status=status, message=message, username=username)
            self.render("unbind.html", status=status, username=username)
        except Exception as e:
            logging.exception("unbind ydcws account failed")
            status = WXErrorCode.FAILED
            message = WXErrorCode.ERROR_MESSAGE[status]
            self.render("error.html", status=status, message=message, username=username)

