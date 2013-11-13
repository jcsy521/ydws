# -*- coding: utf-8 -*-

import logging

from tornado.escape import json_decode, json_encode
import tornado.web

from utils.misc import get_today_last_month, get_terminal_info_key, safe_unicode
from utils.dotdict import DotDict
from utils.checker import check_sql_injection, check_cnum, check_name

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
            user = self.db.get("SELECT name, mobile, address, email, remark"
                               "  FROM T_USER"
                               "  WHERE uid = %s"
                               "  LIMIT 1",
                               self.current_user.uid) 
            if not user:
                status = ErrorCode.LOGIN_AGAIN
                logging.error("[UWEB] user with uid: %s does not exist, redirect to login.html", self.current_user.uid)
                self.write_ret(status)
                return
            
            # 2: car
            car = self.db.get("SELECT cnum FROM T_CAR"
                              "  WHERE tid = %s",
                              self.current_user.tid)
            
            profile.update(user)
            profile.update(car)
            self.write_ret(status,
                           dict_=dict(profile=profile))
        except Exception as e:
            logging.exception("[UWEB] user uid:%s tid:%s get user profile failed. Exception: %s", 
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
            logging.info("[UWEB] user profile request: %s, uid: %s, tid: %s", 
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

            #if data.has_key('address')  and not check_sql_injection(data.address):
            #    status = ErrorCode.ILLEGAL_ADDRESS
            #    self.write_ret(status)
            #    return

            #if data.has_key('email')  and not check_sql_injection(data.email):
            #    status = ErrorCode.ILLEGAL_EMAIL 
            #    self.write_ret(status)
            #    return

            #if data.has_key('remark')  and not check_sql_injection(data.remark):
            #    status = ErrorCode.ILLEGAL_REMARK 
            #    self.write_ret(status)
            #    return

            if data.has_key('cnum') and not check_cnum(data.cnum):
                status = ErrorCode.ILLEGAL_CNUM 
                self.write_ret(status)
                return

            fields_ = DotDict()
            fields = DotDict(name="name = '%s'")
                             #mobile="mobile = '%s'",
                             #address="address = '%s'",
                             #email="email = '%s'",
                             #remark="remark = '%s'")
            for key, value in data.iteritems():
                if key == 'name':
                    fields_.setdefault(key, fields[key] % value) 
                elif key == 'cnum':
                    self.db.execute("UPDATE T_CAR"
                                    "  SET cnum = %s"
                                    "  WHERE tid = %s",
                                    safe_unicode(value), self.current_user.tid)
                    terminal_info_key = get_terminal_info_key(self.current_user.tid)
                    terminal_info = self.redis.getvalue(terminal_info_key)
                    if terminal_info:
                        terminal_info['alias'] = value if value else self.current_user.sim 
                        self.redis.setvalue(terminal_info_key, terminal_info)
                else:
                    logging.error("[UWEB] invaid field: %s, drop it!", key)
                    pass

            set_clause = ','.join([v for v in fields_.itervalues() if v is not None])
            if set_clause:
                self.db.execute("UPDATE T_USER SET " + set_clause +
                                "  WHERE uid = %s",
                                self.current_user.uid)
            self.write_ret(status)
        except Exception as e:
            logging.exception("[UWEB] user uid:%s tid:%s update profile failed.  Exception: %s", 
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
            corp = self.db.get("SELECT name c_name, mobile c_mobile, alert_mobile c_alert_mobile, address c_address, email c_email, linkman c_linkman"
                               "  FROM T_CORP"
                               "  WHERE cid = %s"
                               "  LIMIT 1",
                               self.current_user.cid) 
            if not corp:
                status = ErrorCode.LOGIN_AGAIN
                logging.error("[UWEB] corp with cid: %s does not exist, redirect to login.html", self.current_user.cid)
                self.write_ret(status)
                return
            
            profile.update(corp)
            self.write_ret(status,
                           dict_=dict(profile=profile))
        except Exception as e:
            logging.exception("[UWEB] corp cid:%s tid:%s get corp profile failed. Exception: %s", 
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
            logging.info("[UWEB] corp profile request: %s, uid: %s, tid: %s", 
                         data, self.current_user.uid, self.current_user.tid)
        except Exception as e:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            self.write_ret(status)
            return 

        try:
            #if data.has_key('name')  and not check_sql_injection(data.name):
            #    status = ErrorCode.ILLEGAL_NAME 
            #    self.write_ret(status)
            #    return

            #if data.has_key('address')  and not check_sql_injection(data.address):
            #    status = ErrorCode.ILLEGAL_ADDRESS
            #    self.write_ret(status)
            #    return

            #if data.has_key('email')  and not check_sql_injection(data.email):
            if data.has_key('c_email') and len(data.c_email)>50:
                status = ErrorCode.ILLEGAL_EMAIL 
                self.write_ret(status, 
                               message=u'联系人邮箱的最大长度是50个字符！')
                return


            fields_ = DotDict()
            fields = DotDict(c_name="name = '%s'",
                             c_mobile="mobile = '%s'",
                             c_alert_mobile="alert_mobile = '%s'",
                             c_address="address = '%s'",
                             c_linkman="linkman = '%s'",
                             c_email="email = '%s'")
            for key, value in data.iteritems():
                fields_.setdefault(key, fields[key] % value) 
            set_clause = ','.join([v for v in fields_.itervalues() if v is not None])
            if set_clause:
                self.db.execute("UPDATE T_CORP SET " + set_clause +
                                "  WHERE cid = %s",
                                self.current_user.cid)
            self.write_ret(status)
        except Exception as e:
            logging.exception("[UWEB] corp cid:%s tid:%s update corp profile failed. Exception: %s", 
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
            oper = self.db.get("SELECT name, mobile, address, email"
                               "  FROM T_OPERATOR"
                               "  WHERE oid = %s"
                               "  LIMIT 1",
                               self.current_user.oid) 
            if not oper:
                status = ErrorCode.LOGIN_AGAIN
                logging.error("[UWEB] operator with oid: %s does not exist, redirect to login.html", self.current_user.oid)
                self.write_ret(status)
                return
            
            profile.update(oper)
            for key in profile.keys():
                profile[key] = profile[key] if profile[key] else ''
            self.write_ret(status,
                           dict_=dict(profile=profile))
        except Exception as e:
            logging.exception("[UWEB] operator oid:%s tid:%s get corp profile failed. Exception: %s", 
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
            logging.info("[UWEB] operator profile request: %s, oid: %s, tid: %s", 
                         data, self.current_user.oid, self.current_user.tid)
        except Exception as e:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            self.write_ret(status)
            return 

        try:
            #if data.has_key('name')  and not check_sql_injection(data.name):
            #    status = ErrorCode.ILLEGAL_NAME 
            #    self.write_ret(status)
            #    return

            #if data.has_key('address')  and not check_sql_injection(data.address):
            #    status = ErrorCode.ILLEGAL_ADDRESS
            #    self.write_ret(status)
            #    return

            #if data.has_key('email')  and not check_sql_injection(data.email):
            if data.has_key('email') and len(data.email)>50:
                status = ErrorCode.ILLEGAL_EMAIL 
                self.write_ret(status, 
                               message=u'联系人邮箱的最大长度是50个字符！')
                return


            fields_ = DotDict()
            fields = DotDict(address="address = '%s'",
                             email="email = '%s'")
            for key, value in data.iteritems():
                fields_.setdefault(key, fields[key] % value) 
            set_clause = ','.join([v for v in fields_.itervalues() if v is not None])
            if set_clause:
                self.db.execute("UPDATE T_OPERATOR SET " + set_clause +
                                "  WHERE oid = %s",
                                self.current_user.oid)
            self.write_ret(status)
        except Exception as e:
            logging.exception("[UWEB] operator oid:%s update oper profile failed. Exception: %s", 
                              self.current_user.oid, e.args)
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)
