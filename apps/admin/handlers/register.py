#register!/usr/bin/env python
# -*- coding: utf-8 -*-

"""This module is designed for statistic of register-times.
"""

import logging
import hashlib

import tornado.web

from base import BaseHandler, authenticated
from codes.errorcode import ErrorCode
from mixin import BaseMixin
from checker import check_privileges 
from constants import PRIVILEGES

class RegisterMixin(BaseMixin):
    KEY_TEMPLATE = "register_report_%s_%s"

    def prepare_data(self, hash_):
        """Associated with the post method.

        workflow:

        if get value according the hash:
            return value
        else:
            retrieve the db and return the result.
        """
        mem_key = self.get_memcache_key(hash_)
        data = self.redis.getvalue(mem_key)

        if data:
            return data

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

        self.redis.setvalue(mem_key, res, time=self.MEMCACHE_EXPIRY)
        return res

class RegisterClearHandler(BaseHandler, RegisterMixin):

    @authenticated
    @check_privileges([PRIVILEGES.TERMINAL_QUERY])
    @tornado.web.removeslash
    def get(self):
        """Clean the limitation of register.
        """
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
        """Jump to terminalregister.html.
        """
        username = self.get_current_user()
        self.render('report/terminalregister.html',
                    username=username,
                    res={},
                    hash_='')

    @authenticated
    @check_privileges([PRIVILEGES.TERMINAL_QUERY])
    @tornado.web.removeslash
    def post(self):
        """Query the limit-info according to the given parameters.
        """
        status = ErrorCode.SUCCESS
        try:
            m = hashlib.md5()
            m.update(self.request.body)
            hash_ = m.hexdigest()

            res = self.prepare_data(hash_)        

            self.render('report/terminalregister.html',
                        status=status, res=res, hash_=hash_)
        except Exception as e:
            logging.exception("Search register failed. Exception: %s.", 
                              e.args)
            self.render('errors/error.html', 
                         message=ErrorCode.FAILED)
