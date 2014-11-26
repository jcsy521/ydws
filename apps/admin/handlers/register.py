#register!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import time
from os import SEEK_SET
import hashlib
import xlwt
from cStringIO import StringIO

import tornado.web
from tornado.escape import json_decode

from base import BaseHandler, authenticated
from codes.errorcode import ErrorCode
from mixin import BaseMixin
from excelheaders import MANUALLOG_FILE_NAME, MANUALLOG_SHEET, MANUALLOG_HEADER
from utils.misc import safe_unicode

from checker import check_privileges 
from constants import PRIVILEGES

class RegisterMixin(BaseMixin):
    KEY_TEMPLATE = "register_report_%s_%s"

    def prepare_data(self, hash_):
        mem_key = self.get_memcache_key(hash_)
        data = self.getvalue(mem_key)

        if data:
            return data

class RegisterClearHandler(BaseHandler, RegisterMixin):

    @authenticated
    @check_privileges([PRIVILEGES.TERMINAL_QUERY])
    @tornado.web.removeslash
    def get(self):
        status = ErrorCode.SUCCESS
        
        umobile = self.get_argument('umobile','dummy')
        remote_ip = self.get_argument('remote_ip','dummy')

        remote_ip_key = "register_remote_ip:%s" % remote_ip 
        umobile_key = "register_umobile:%s" % umobile

        self.redis.delete(remote_ip_key)  
        self.redis.delete(umobile_key)  
        self.write_ret(status)

class RegisterSearchHandler(BaseHandler, RegisterMixin):

    @authenticated
    @check_privileges([PRIVILEGES.TERMINAL_QUERY])
    @tornado.web.removeslash
    def get(self):
        username = self.get_current_user()
        self.render('report/terminalregister.html',
                    username=username,
                    res={},
                    hash_='')

    @authenticated
    @check_privileges([PRIVILEGES.TERMINAL_QUERY])
    @tornado.web.removeslash
    def post(self):
        """Query the limit-info of remote_ip and umobile.
        """
        status = ErrorCode.SUCCESS
        res = {}
        hash_ = ''
        try:
            flag = self.get_argument('flag','get')
            umobile = self.get_argument('umobile', '')
            remote_ip = self.get_argument('remote_ip', '')

            remote_ip_key = "register_remote_ip:%s" % remote_ip 
            umobile_key = "register_umobile:%s" % umobile
            remote_ip_times = self.redis.getvalue(remote_ip_key)  
            umobile_times = self.redis.getvalue(umobile_key)  

            remote_ip_ttl = self.redis.ttl(remote_ip_key)  
            umobile_ttl = self.redis.ttl(umobile_key)  

            if umobile:
                umobile = dict(umobile=umobile,
                               umobile_times=umobile_times if umobile_times else '__',
                               umobile_ttl=umobile_ttl if umobile_times else '__')
            else:
                umobile = {} 

            if remote_ip:
                remote_ip = dict(remote_ip=remote_ip,
                                 remote_ip_times=remote_ip_times if remote_ip_times else '__',
                                 remote_ip_ttl=remote_ip_ttl if remote_ip_times else '__')
            else:
                remote_ip = {}

            if umobile or remote_ip:
                res = dict(umobile=umobile,
                           remote_ip=remote_ip) 
            else:
                res = {} 

            m = hashlib.md5()
            m.update(self.request.body)
            hash_ = m.hexdigest()
            mem_key = self.get_memcache_key(hash_)
            self.redis.setvalue(mem_key, res, time=self.MEMCACHE_EXPIRY)

            self.render('report/terminalregister.html',
                        status=status, res=res, hash_=hash_)
        except Exception as e:
            logging.exception("Search register for %s,it is does'\nt exists", umobile)
            self.render('errors/error.html', message=ErrorCode.FAILED)


       _tmp_file.close()
