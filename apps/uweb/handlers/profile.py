# -*- coding: utf-8 -*-

"""This module is designed for user profile.
"""

import logging

from tornado.escape import json_decode
import tornado.web

from utils.misc import get_terminal_info_key, safe_unicode
from utils.dotdict import DotDict
from utils.checker import check_sql_injection, check_cnum, check_name
from utils.public import update_operator, update_corp
from helpers.queryhelper import QueryHelper

from base import BaseHandler, authenticated
from codes.errorcode import ErrorCode


class ProfileHandler(BaseHandler):

    @authenticated
    @tornado.web.removeslash
    def get(self):
        """Display profile of current user.
        """
        status = ErrorCode.SUCCESS
        try: 
            tid = self.get_argument('tid',None) 
            # check tid whether exist in request and update current_user
            self.check_tid(tid)

            profile = DotDict()
            # 1: user
            user = QueryHelper.get_user_by_uid(self.current_user.uid, self.db)
            if not user:
                status = ErrorCode.LOGIN_AGAIN
                logging.error("[UWEB] User does not exist, redirect to login.html. uid: %s.", 
                              self.current_user.uid)
                self.write_ret(status)
                return

            # 2: car 
            car = QueryHelper.get_car_by_tid(self.current_user.tid, self.db)            
            profile.update(user)
            profile.update(car)
            self.write_ret(status,
                           dict_=dict(profile=profile))
        except Exception as e:
            logging.exception("[UWEB] Get user profile failed. uid:%s, tid:%s, Exception: %s", 
                              self.current_user.uid, self.current_user.tid, e.args) 
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)

    @authenticated
    @tornado.web.removeslash
    def put(self):
        """Modify profile of current user.
        """
        status = ErrorCode.SUCCESS
        try:
            data = DotDict(json_decode(self.request.body))
            tid = data.get('tid',None) 
            # check tid whether exist in request and update current_user
            self.check_tid(tid)
            logging.info("[UWEB] User profile request: %s, uid: %s, tid: %s", 
                         data, self.current_user.uid, self.current_user.tid)
        except Exception as e:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            self.write_ret(status)
            return 

        try:
            if data.has_key('name')  and not check_name(data.name):
                status = ErrorCode.ILLEGAL_NAME 
                self.write_ret(status)
                return
     
            name = data.get('name', None)
            if name is not None:
                sql_cmd = "UPDATE T_USER SET name = %s WHERE uid = %s"
                self.db.execute(sql_cmd, 
                                name, self.current_user.uid)

            cnum = data.get('cnum', None)
            if cnum is not None:
                self.db.execute("UPDATE T_CAR"
                                "  SET cnum = %s"
                                "  WHERE tid = %s",
                                safe_unicode(cnum), self.current_user.tid)
                terminal_info_key = get_terminal_info_key(self.current_user.tid)
                terminal_info = self.redis.getvalue(terminal_info_key)
                if terminal_info:
                    terminal_info['alias'] = cnum if cnum else self.current_user.sim 
                    self.redis.setvalue(terminal_info_key, terminal_info)

            self.write_ret(status)
        except Exception as e:
            logging.exception("[UWEB] Update profile failed. uid:%s, tid:%s, Exception: %s", 
                              self.current_user.uid, self.current_user.tid, e.args)
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)

class ProfileCorpHandler(BaseHandler):

    @authenticated
    @tornado.web.removeslash
    def get(self):
        """Display profile of current corp.
        """
        status = ErrorCode.SUCCESS
        try: 
            profile = DotDict()
            # 1: user
            corp = QueryHelper.get_corp_by_cid(self.current_user.cid, self.db)
            if not corp:
                status = ErrorCode.LOGIN_AGAIN
                logging.error("[UWEB] Corp does not exist, redirect to login.html. cid: %s.", 
                              self.current_user.cid)
                self.write_ret(status)
                return

            profile.update(corp)
            self.write_ret(status,
                           dict_=dict(profile=profile))
        except Exception as e:
            logging.exception("[UWEB] Get corp profile failed. cid:%s, tid:%s, Exception: %s", 
                              self.current_user.cid, self.current_user.tid, e.args) 
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)

    @authenticated
    @tornado.web.removeslash
    def put(self):
        """Modify profile of current corp. 
        """
        status = ErrorCode.SUCCESS
        try:
            data = DotDict(json_decode(self.request.body))
            logging.info("[UWEB] Corp profile request: %s, uid: %s, tid: %s", 
                         data, self.current_user.uid, self.current_user.tid)
        except Exception as e:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            self.write_ret(status)
            return 

        try:
            if data.has_key('c_email') and len(data.c_email)>50:
                status = ErrorCode.ILLEGAL_EMAIL 
                self.write_ret(status, 
                               message=u'联系人邮箱的最大长度是50个字符！')
                return

            update_corp(data, self.current_user.cid, self.db, self.redis)
            self.write_ret(status)
        except Exception as e:
            logging.exception("[UWEB] Update corp profile failed. cid:%s, tid:%s, Exception: %s", 
                              self.current_user.cid, self.current_user.tid, e.args)
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)

class ProfileOperHandler(BaseHandler):

    @authenticated
    @tornado.web.removeslash
    def get(self):
        """Display profile of current operator.
        """
        status = ErrorCode.SUCCESS
        try: 
            profile = DotDict()
            # 1: user     
            oper = QueryHelper.get_operator_by_oid(self.current_user.oid, self.db)
            if not oper:
                status = ErrorCode.LOGIN_AGAIN
                logging.error("[UWEB] Operator does not exist, redirect to login.html. oid: %s.", 
                              self.current_user.oid)
                self.write_ret(status)
                return
            
            profile.update(oper)
            for key in profile.keys():
                profile[key] = profile[key] if profile[key] else ''
            self.write_ret(status,
                           dict_=dict(profile=profile))
        except Exception as e:
            logging.exception("[UWEB] Get corp profile failed. oid:%s, tid:%s, Exception: %s", 
                              self.current_user.oid, self.current_user.tid, e.args) 
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)

    @authenticated
    @tornado.web.removeslash
    def put(self):
        """Modify profile of current operator. 
        """
        status = ErrorCode.SUCCESS
        try:
            data = DotDict(json_decode(self.request.body))
            logging.info("[UWEB] Operator profile request: %s, oid: %s, tid: %s", 
                         data, self.current_user.oid, self.current_user.tid)
        except Exception as e:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            self.write_ret(status)
            return 

        try:
            #if data.has_key('email')  and not check_sql_injection(data.email):
            if data.has_key('email') and len(data.email)>50:
                status = ErrorCode.ILLEGAL_EMAIL 
                self.write_ret(status, 
                               message=u'联系人邮箱的最大长度是50个字符！')
                return

            update_operator(data, self.current_user.oid, self.db, self.redis)
            self.write_ret(status)
        except Exception as e:
            logging.exception("[UWEB] Update operator profile failed. oid:%s, Exception: %s", 
                              self.current_user.oid, e.args)
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)