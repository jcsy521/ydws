# -*- coding:utf-8 -*-

import time
import tornado.web

from helpers.confhelper import ConfHelper
from helpers.uwebhelper import UWebHelper
from helpers.smshelper import SMSHelper
from utils.dotdict import DotDict
from utils.checker import check_sql_injection
from utils.misc import DUMMY_IDS
from errors import ErrorCode
from codes.smscode import SMSCode
from constants import XXT, AREA

from base import BaseHandler, authenticated
from datetime import datetime

from constants import PRIVILEGES
from checker import check_privileges


class DelegationHandler(BaseHandler):

    def __log_delegation(self, administrator_id, xxt_uid, xxt_tid):
        timestamp = int(time.time() * 1000)
        self.db.execute("INSERT INTO T_DELEGATION_LOG"
                        "  VALUES (NULL, %s, %s, %s, %s)",
                        administrator_id, xxt_uid, xxt_tid, timestamp) 

    @authenticated
    @check_privileges([PRIVILEGES.DELEGATION])
    @tornado.web.removeslash
    def get(self):
        self.render("delegation/delegation.html", message=None, url=None)

    @authenticated
    @check_privileges([PRIVILEGES.DELEGATION])
    @tornado.web.removeslash
    def post(self):
        target_mobile = self.get_argument('targetmobile', '')

        if not check_sql_injection(target_mobile): 
           self.get() 
           return 
        message = None
        url = None
        optype_status = (XXT.OPER_TYPE.CREATE,
                         XXT.OPER_TYPE.RESUME,
                         XXT.OPER_TYPE.UPDATE)
        xxt_target = self.db.get("SELECT xxt_tid, parent_mobile, group_id"
                                 "  FROM T_XXT_TARGET"
                                 "  WHERE mobile = %s"
                                 "    AND optype IN %s"
                                 "  LIMIT 1",
                                 target_mobile, tuple(optype_status))
        if not xxt_target:
            message = ErrorCode.CHILD_NOT_FOUND
            self.render("delegation/delegation.html", message=message, url=url)
        else:
            xxt_user = self.db.get("SELECT xxt_uid"
                                   "  FROM T_XXT_USER"
                                   "  WHERE mobile = %s"
                                   "    AND optype IN %s"
                                   "  LIMIT 1",
                                   xxt_target.parent_mobile, tuple(optype_status))

            if xxt_user:
                # judge administrator type
                administrator = self.db.get("SELECT type"
                                            "  FROM T_ADMINISTRATOR"
                                            "  WHERE id = %s"
                                            "  LIMIT 1",
                                            self.current_user.id)
                if administrator.type == "1":
                    # get administrator's group ids
                    groups = self.db.query("SELECT xxt_id"
                                           "  FROM T_XXT_GROUP, T_ADMINISTRATOR"
                                           "  WHERE T_ADMINISTRATOR.login = T_XXT_GROUP.phonenum"
                                           "  AND T_ADMINISTRATOR.id = %s",
                                           self.current_user.id)
                    privilege_group_ids = [g.xxt_id for g in groups]
                    
                    # judge user's group in administrator's groups
                    if xxt_target.group_id not in privilege_group_ids:
                        message = ErrorCode.CHILD_NOT_FOUND
                        self.render("delegation/delegation.html", message=message, url=url)
                        return
                elif administrator.type == "2":
                    city = self.db.get("SELECT city_id"
                                       "  FROM T_XXT_GROUP"
                                       "  WHERE xxt_id = %s"
                                       "  LIMIT 1",
                                       xxt_target.group_id)
                    
                    # get administrator's city ids
                    privilege_areas = self.db.query("SELECT area_id"
                                                    "  FROM T_AREA_PRIVILEGE"
                                                    "  WHERE administrator_id = %s"
                                                    "    AND category = %s",
                                                    self.current_user.id,
                                                    AREA.CATEGORY.CITY)
                    privilege_cities = [a.area_id for a in privilege_areas]

                    # judge user's city in administrator's cities
                    if city.city_id not in privilege_cities: 
                        message = ErrorCode.CHILD_NOT_FOUND
                        self.render("delegation/delegation.html", message=message, url=url)
                        return
                
                url = '/'.join([ConfHelper.UWEB_CONF.url_out,
                                UWebHelper.URLS.DELEGATION[1:],
                                str(xxt_user.xxt_uid),
                                str(xxt_target.xxt_tid),
                                str(target_mobile)])
                sign = UWebHelper.get_sign(''.join([str(xxt_user.xxt_uid),
                                                    str(xxt_target.xxt_tid),
                                                    str(target_mobile)]))
                privileges = self.db.query("SELECT tpgd.privilege_id AS pid"
                                           "  FROM T_PRIVILEGE AS tp, T_PRIVILEGE_GROUP_DATA AS tpgd"
                                           "  WHERE tp.administrator_id = %s"
                                           "    AND tp.privilege_group_id = tpgd.privilege_group_id",
                                           self.current_user.id)
                privilege_ids = [p.pid for p in privileges]
                privilege = PRIVILEGES.DELEGATION
                if PRIVILEGES.HIGH_LEVEL_DELEGATION in privilege_ids:
                    privilege = PRIVILEGES.HIGH_LEVEL_DELEGATION

                url += "?s=" + sign + "&p=" + str(privilege)
                self.__log_delegation(self.current_user.id, 
                                      xxt_user.xxt_uid, xxt_target.xxt_tid)
                
                # if super administrator, don't send sms
                if administrator.type != "0":
                    sms = SMSCode.SMS_DELEGATION % (time.strftime("%Y-%m-%d %H:%M:%S"), 
                                                    target_mobile)
                    SMSHelper.send(xxt_target.parent_mobile, sms)
                
                self.render("delegation/delegation.html", message=message, url=url)
            else:
                message = ErrorCode.PARENT_NOT_FOUND
                self.render("delegation/delegation.html", message=message, url=url)


class DelegationLogHandler(BaseHandler):

    @authenticated
    @check_privileges([PRIVILEGES.DELEGATION_QUERY])
    @tornado.web.removeslash
    def get(self):
        self.render("delegation/log.html",
                    logs=[],
                    interval=[])

    @authenticated
    @check_privileges([PRIVILEGES.DELEGATION_QUERY])
    @tornado.web.removeslash
    def post(self):
        # check administrator_id
        start_time = int(self.get_argument('start_time'))
        end_time = int(self.get_argument('end_time'))
        select_clause = "SELECT T_ADMINISTRATOR.name as administrator, T_ADMINISTRATOR.login," \
                      + " T_DELEGATION_LOG.timestamp, T_XXT_TARGET.name as child_name," \
                      + " T_XXT_USER.name as parent_name "
        
        administrator = self.db.get("SELECT type"
                                    "  FROM T_ADMINISTRATOR"
                                    "  WHERE id = %s"
                                    "  LIMIT 1",
                                    self.current_user.id)
        # judge administrator type, super : 0, usually : 1, city : 2
        if administrator.type == "1":
            from_table_clause = " FROM T_DELEGATION_LOG, T_ADMINISTRATOR, T_XXT_TARGET, T_XXT_USER "
            
            where_clause = " WHERE T_DELEGATION_LOG.timestamp BETWEEN %s AND %s" \
                         + " AND T_DELEGATION_LOG.administrator_id = T_ADMINISTRATOR.id" \
                         + " AND T_DELEGATION_LOG.xxt_uid = T_XXT_USER.xxt_uid" \
                         + " AND T_DELEGATION_LOG.xxt_tid = T_XXT_TARGET.xxt_tid" \
                         + " AND T_ADMINISTRATOR.id = %s"
            where_clause = where_clause % (start_time, end_time, self.current_user.id,)
            
        elif administrator.type == "2":
            area_ids = self.db.query("SELECT area_id"
                                     "  FROM T_AREA_PRIVILEGE"
                                     "  WHERE administrator_id = %s",
                                     self.current_user.id)
            area_ids = [str(area_id["area_id"]) for area_id in area_ids]
            
            from_table_clause = " FROM T_DELEGATION_LOG, T_ADMINISTRATOR, T_XXT_TARGET, T_XXT_USER, T_AREA_PRIVILEGE "
            
            where_clause = " WHERE T_DELEGATION_LOG.timestamp BETWEEN %s AND %s" \
                         + " AND T_AREA_PRIVILEGE.administrator_id = T_ADMINISTRATOR.id" \
                         + " AND T_DELEGATION_LOG.administrator_id = T_AREA_PRIVILEGE.administrator_id" \
                         + " AND T_DELEGATION_LOG.xxt_uid = T_XXT_USER.xxt_uid" \
                         + " AND T_DELEGATION_LOG.xxt_tid = T_XXT_TARGET.xxt_tid" \
                         + " AND T_ADMINISTRATOR.type != 0" \
                         + " AND T_AREA_PRIVILEGE.area_id in %s"
            where_clause = where_clause % (start_time, end_time, tuple(area_ids + DUMMY_IDS))
        
        elif administrator.type == "0":
            
            from_table_clause = " FROM T_DELEGATION_LOG, T_ADMINISTRATOR, T_XXT_TARGET, T_XXT_USER "
            
            where_clause = " WHERE T_DELEGATION_LOG.timestamp BETWEEN %s AND %s" \
                         + " AND T_DELEGATION_LOG.administrator_id = T_ADMINISTRATOR.id" \
                         + " AND T_DELEGATION_LOG.xxt_uid = T_XXT_USER.xxt_uid" \
                         + " AND T_DELEGATION_LOG.xxt_tid = T_XXT_TARGET.xxt_tid"
            where_clause = where_clause % (start_time, end_time,)
            
        else:
            pass

        fields = DotDict(administrator="T_ADMINISTRATOR.name LIKE '%%%%%s%%%%'",
                         login="T_ADMINISTRATOR.login LIKE '%%%%%s%%%%'",
                         user_name="T_XXT_USER.name LIKE '%%%%%s%%%%'",
                         mobile="T_XXT_USER.mobile LIKE '%%%%%s%%%%'")
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
        
        ################################################################
        #if where_clause:
        #    r = self.db.get("SELECT id FROM T_ADMINISTRATOR"
        #                    "  WHERE 1 = 1 AND " + where_clause)
        #    if r:
        #        administrator_id = r.id
        #    else:
        #        self.render("delegation/log.html", logs=[])
        #        return
        #
        #xxt_uid = None
        # check user id
        #fields = DotDict(name="mobile = '%s'",
        #                 user_name="name = '%s'")
        #for key in fields.iterkeys():
        #    v = self.get_argument(key, None)
        #    if v:
        #        fields[key] = fields[key] % (v,)
        #    else:
        #        fields[key] = v

        #where_clause = ' AND '.join([v for v in fields.itervalues() if v])

        #if where_clause:
        #    r = self.db.get("SELECT xxt_uid FROM T_XXT_USER"
        #                    "  WHERE 1 = 1 AND " + where_clause)
        #    if r:
        #        xxt_uid = r.xxt_uid
        #    else:
        #        self.render("delegation/log.html", logs=[])
        #        return

        # format where clause
        #sql = []
        #if administrator_id is not None:
        #    sql.append("tdl.administrator_id = %s" % (administrator_id,))
        #if xxt_uid is not None:
        #    sql.append("tdl.xxt_uid = %s" % (xxt_uid,))
        #start_time = self.get_argument('start_time', None)
        #if start_time:
        #    sql.append("tdl.timestamp >= %s" % (start_time,))
        #end_time = self.get_argument('end_time', None)
        #if end_time:
        #    sql.append("tdl.timestamp <= %s" % (end_time,))

        #if not sql:
        #    self.render("delegation/log.html", logs=[])
        #    return

        #logs = self.db.query("SELECT ta.name as administrator, ta.login, txu.name as parent_name,"
        #                     "       txt.name as child_name, tdl.timestamp"
        #                     "  FROM T_DELEGATION_LOG AS tdl"
        #                     "  JOIN (T_ADMINISTRATOR AS ta,"
        #                     "        T_XXT_USER AS txu,"
        #                     "        T_XXT_TARGET AS txt)"
        #                     "    ON (tdl.administrator_id = ta.id"
        #                     "    AND tdl.xxt_uid = txu.xxt_uid"
        #                     "    AND tdl.xxt_tid = txt.xxt_tid)"
        #                     "  WHERE " + " AND ".join(sql) + 
        #                     " ORDER BY timestamp")
        sql = select_clause + from_table_clause + where_clause
        sql += " ORDER BY T_DELEGATION_LOG.timestamp DESC"
        logs = self.db.query(sql)
        for i, log in enumerate(logs):
            log['id'] = i + 1
        self.render("delegation/log.html",
                    logs=logs,
                    interval=[start_time, end_time])
