# -*- coding:utf-8 -*-

"""This module is designed for delegation and the log.
"""

import time
import tornado.web

from helpers.confhelper import ConfHelper
from helpers.uwebhelper import UWebHelper
from helpers.queryhelper import QueryHelper
from helpers.smshelper import SMSHelper
from utils.dotdict import DotDict
from utils.checker import check_sql_injection
from errors import ErrorCode
from codes.smscode import SMSCode
from constants import UWEB
from base import BaseHandler, authenticated

from constants import PRIVILEGES
from checker import check_privileges

class DelegationMixin(object):

    def log_delegation(self, administrator_id, cid, uid, tid):
        timestamp = int(time.time())
        self.db.execute("INSERT INTO T_DELEGATION_LOG(administrator_id, cid, uid, tid, timestamp)"
                        "  VALUES (%s, %s, %s, %s, %s)",
                        administrator_id, cid, uid, tid, timestamp) 

class DelegationHandler(BaseHandler, DelegationMixin):

    @authenticated
    @check_privileges([PRIVILEGES.DELEGATION])
    @tornado.web.removeslash
    def get(self):
        """Jump to the delegation.html.
        """       
        self.render("delegation/delegation.html", 
                    message=None, 
                    url=None)

    @authenticated
    @check_privileges([PRIVILEGES.DELEGATION])
    @tornado.web.removeslash
    def post(self):
        tmobile = self.get_argument('tmobile', '')

        #if not check_sql_injection(tmobile): 
        #   self.get() 
        #   return 

        message = None
        url = None        
        cid = UWEB.DUMMY_CID
        oid = UWEB.DUMMY_OID
        terminal = self.db.get("SELECT tid, owner_mobile"
                               "  FROM T_TERMINAL_INFO"
                               "  WHERE mobile = %s"
                               "    AND service_status = %s"
                               "    AND (%s BETWEEN begintime AND endtime)",
                               tmobile, UWEB.SERVICE_STATUS.ON,
                               int(time.time()))
        if not terminal:
            message = ErrorCode.TERMINAL_NOT_FOUND
            self.render("delegation/delegation.html", message=message, url=url)
        else:
            user = self.db.get("SELECT uid"
                               "  FROM T_USER"
                               "  WHERE mobile = %s",
                               terminal.owner_mobile)

            if user:
                administrator = self.db.get("SELECT type"
                                            "  FROM T_ADMINISTRATOR"
                                            "  WHERE id = %s",
                                            self.current_user.id)
                uid = user.uid
                tid = terminal.tid
                url = '/'.join([ConfHelper.UWEB_CONF.url_out,
                                UWebHelper.URLS.DELEGATION[1:],
                                str(uid),
                                str(tid),
                                str(tmobile),
                                str(cid),
                                str(oid)])
                sign = UWebHelper.get_sign(''.join([str(user.uid),
                                                    str(terminal.tid),
                                                    str(tmobile),
                                                    str(cid),
                                                    str(oid)]))
                url += "?s=" + sign
                self.log_delegation(self.current_user.id, 
                                    cid, uid, tid)
                
                if administrator.type != "0":
                    pass
                #    sms = SMSCode.SMS_DELEGATION % (time.strftime("%Y-%m-%d %H:%M:%S"), 
                #                                    tmobile)
                #    SMSHelper.send(terminal.owner_mobile, sms)
                
                self.render("delegation/delegation.html", message=message, url=url)
            else:
                message = ErrorCode.USER_NOT_ORDERED
                self.render("delegation/delegation.html", message=message, url=url)


class DelegationIndividualHandler(BaseHandler, DelegationMixin):

    @authenticated
    @check_privileges([PRIVILEGES.DELEGATION])
    @tornado.web.removeslash
    def get(self):
        """Jump to the delegation_individual.html.
        """
        self.render("delegation/delegation_individual.html", 
                    message=None, 
                    url=None)

    @authenticated
    @check_privileges([PRIVILEGES.DELEGATION])
    @tornado.web.removeslash
    def post(self):
        uid = self.get_argument('uid', '')
        message = None
        url = None
        user = QueryHelper.get_user_by_uid(uid, self.db)
        if not user:
            message = ErrorCode.USER_NOT_FOUND
            self.render("delegation/delegation_individual.html", 
                        message=message, 
                        url=url)
        else:
            tid = 'dummy'
            tmobile = 'dummy'
            cid = UWEB.DUMMY_CID
            oid = UWEB.DUMMY_OID

            url = '/'.join([ConfHelper.UWEB_CONF.url_out,
                            UWebHelper.URLS.DELEGATION[1:],
                            str(uid),
                            str(tid),
                            str(tmobile),
                            str(cid), 
                            str(oid)])
            sign = UWebHelper.get_sign(''.join([str(uid),
                                                str(tid),
                                                str(tmobile),
                                                str(cid),
                                                str(oid),
                                                ]))
            url += "?s=" + sign   
            self.log_delegation(self.current_user.id, 
                                cid, uid, tid)
            
            self.render("delegation/delegation_individual.html", 
                        message=message, 
                        url=url)

class DelegationEnterpriseHandler(BaseHandler, DelegationMixin):

    @authenticated
    @check_privileges([PRIVILEGES.DELEGATION])
    @tornado.web.removeslash
    def get(self):
        """Jump to the delegation_enterprise.html.
        """
        self.render("delegation/delegation_enterprise.html", 
                    message=None, 
                    url=None)

    @authenticated
    @check_privileges([PRIVILEGES.DELEGATION])
    @tornado.web.removeslash
    def post(self):
        cid = self.get_argument('cid', '')
        message = None
        url = None
        corp = QueryHelper.get_corp_by_cid(cid, self.db)
        if not corp:
            message = ErrorCode.USER_NOT_FOUND
            self.render("delegation/delegation_enterprise.html", 
                        message=message, 
                        url=url)
        else:
            uid = 'dummy'
            tid = 'dummy'
            tmobile = 'dummy'
            cid = cid
            oid = UWEB.DUMMY_OID

            url = '/'.join([ConfHelper.UWEB_CONF.url_out,
                            UWebHelper.URLS.DELEGATION[1:],
                            str(uid),
                            str(tid),
                            str(tmobile),
                            str(cid), 
                            str(oid)])
            sign = UWebHelper.get_sign(''.join([str(uid),
                                                str(tid),
                                                str(tmobile),
                                                str(cid),
                                                str(oid),
                                                ]))
            url += "?s=" + sign
            self.log_delegation(self.current_user.id, 
                                cid, uid, tid)
            
            self.render("delegation/delegation_enterprise.html", 
                        message=message, 
                        url=url)

class DelegationLogHandler(BaseHandler):

    @authenticated
    @check_privileges([PRIVILEGES.DELEGATION])
    @tornado.web.removeslash
    def get(self):
        """Jump to the log.html for delegation.
        """
        self.render("delegation/log.html",
                    logs=[],
                    interval=[])

    @authenticated
    @check_privileges([PRIVILEGES.DELEGATION])
    @tornado.web.removeslash
    def post(self):
        """Retrieve the log of delegation.
        """
        # check administrator_id
        start_time = int(self.get_argument('start_time'))
        end_time = int(self.get_argument('end_time'))
        select_clause = "SELECT T_ADMINISTRATOR.name as administrator, T_ADMINISTRATOR.login," \
                      + " T_DELEGATION_LOG.timestamp, T_TERMINAL_INFO.mobile as tmobile," \
                      + " T_USER.name as user_name "
        
        from_table_clause = " FROM T_DELEGATION_LOG, T_ADMINISTRATOR, T_TERMINAL_INFO, T_USER "
        
        where_clause = " WHERE T_DELEGATION_LOG.timestamp BETWEEN %s AND %s" \
                     + " AND T_DELEGATION_LOG.administrator_id = T_ADMINISTRATOR.id" \
                     + " AND T_DELEGATION_LOG.uid = T_USER.uid" \
                     + " AND T_DELEGATION_LOG.tid = T_TERMINAL_INFO.tid"
        where_clause = where_clause % (start_time, end_time,)
            
        fields = DotDict(administrator="T_ADMINISTRATOR.name LIKE '%%%%%s%%%%'",
                         login="T_ADMINISTRATOR.login LIKE '%%%%%s%%%%'",
                         user_name="T_USER.name LIKE '%%%%%s%%%%'",
                         mobile="T_USER.mobile LIKE '%%%%%s%%%%'",
                         tmobile="T_TERMINAL_INFO.mobile LIKE '%%%%%s%%%%'")
        for key in fields.iterkeys():
            v = self.get_argument(key, None)
            if v:
                if not check_sql_injection(v):
                    self.get()
                    return 
                fields[key] = fields[key] % (v,)
            else:
                fields[key] = None
        terms = [where_clause] + [v for v in fields.itervalues() if v]
        where_clause = ' AND '.join(terms)
        
        sql = select_clause + from_table_clause + where_clause
        sql += " ORDER BY T_DELEGATION_LOG.timestamp DESC"
        logs = self.db.query(sql)
        for i, log in enumerate(logs):
            log['id'] = i + 1
        self.render("delegation/log.html",
                    logs=logs,
                    interval=[start_time, end_time])
