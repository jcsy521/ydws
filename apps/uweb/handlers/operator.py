# -*- coding: utf-8 -*-

"""This module is designed for operator.
"""

import logging

import tornado.web
from tornado.escape import json_decode

from utils.dotdict import DotDict
from utils.misc import DUMMY_IDS, str_to_list
from constants import UWEB
from codes.errorcode import ErrorCode
from base import BaseHandler, authenticated

from helpers.wspushhelper import WSPushHelper
       
class OperatorHandler(BaseHandler):

    @authenticated
    @tornado.web.removeslash
    def get(self):
        """ """ 
        status = ErrorCode.SUCCESS
        try:
            page_number = int(self.get_argument('pagenum'))
            page_count = int(self.get_argument('pagecnt'))
            fields = DotDict(name="name LIKE '%%%%%s%%%%'",
                             mobile="mobile LIKE '%%%%%s%%%%'")
            for key in fields.iterkeys():
                v = self.get_argument(key, None)
                if v:
                    fields[key] = fields[key] % (v,)
                else:
                    fields[key] = None
        except Exception as e:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            logging.exception("[UWEB] Invalid data format. Exception: %s",
                              e.args)
            self.write_ret(status)
            return

        try:
            where_clause = ' AND '.join([v for v in fields.itervalues()
                                         if v is not None])
            page_size = UWEB.LIMIT.PAGE_SIZE
            if where_clause:
                where_clause = ' AND ' + where_clause
            if page_count == -1:
                sql = "SELECT count(id) AS count FROM T_OPERATOR" + \
                      "  WHERE 1=1 " + where_clause
                sql += " AND corp_id = %s" % (self.current_user.cid,)
                res = self.db.get(sql) 
                count = res.count
                d, m = divmod(count, page_size)
                page_count = (d + 1) if m else d

            sql = "SELECT id, oid, name, mobile, email, address FROM T_OPERATOR" +\
                  "  WHERE 1=1 " + where_clause
            sql += " AND corp_id = %s LIMIT %s, %s" % (self.current_user.cid, page_number * page_size, page_size)
            operators = self.db.query(sql)
            #operators = self.db.query("SELECT id, oid, name, mobile FROM T_OPERATOR"
            #                          "  WHERE corp_id = %s " + where_clause +
            #                          "  LIMIT %s, %s",
            #                          self.current_user.cid, page_number * page_size, page_size)
            for item,operator in enumerate(operators):
                groups = self.db.query("SELECT T_GROUP.id, T_GROUP.name"
                                      "  FROM T_GROUP, T_GROUP_OPERATOR"
                                      "  WHERE T_GROUP_OPERATOR.oper_id = %s"
                                      "    AND T_GROUP.id = T_GROUP_OPERATOR.group_id",
                                      operator.oid)
                group_ids = [str(group.id) for group in groups]
                operator['seq'] = item+1+page_size*page_number
                operator['group_id'] = ','.join(group_ids) if group_ids else ''
                for key in operator.keys():
                    operator[key] = operator[key] if operator[key] else ''
            self.write_ret(status,
                           dict_=DotDict(res=operators,
                                         pagecnt=page_count))
        except Exception as e:
            logging.exception("[UWEB] cid: %s get operator failed. Exception: %s", 
                              self.current_user.cid, e.args) 
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)
        

    @authenticated
    @tornado.web.removeslash
    def post(self):
        """Create a new operator.
        """
        status = ErrorCode.SUCCESS
        try:
            data = DotDict(json_decode(self.request.body))
            mobile = data.mobile
            name = data.name
            email = data.email
            address = data.address
            group_id = data.group_id
            group_ids = map(int, str_to_list(group_id))
            logging.info("[UWEB] add operator request: %s, cid: %s", 
                         data, self.current_user.cid)
        except Exception as e:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            logging.exception("[UWEB] Invalid data format. body:%s, Exception: %s",
                              self.request.body, e.args)
            self.write_ret(status)
            return

        try:
            self.db.execute("INSERT T_OPERATOR(oid, mobile, password,"
                            "  name, corp_id, email, address)"
                            "  VALUES(%s, %s, password(%s), %s, %s, %s, %s)",
                            mobile, mobile, '111111', name, self.current_user.cid,
                            email, address)
            self.db.executemany("INSERT INTO T_GROUP_OPERATOR(group_id, oper_id)"
                                "  VALUES( %s, %s)", 
                                [(gid, mobile) for gid in group_ids])

            self.write_ret(status)
        except Exception as e:
            logging.exception("[UWEB] cid: %s create operator failed. Exception: %s", 
                              self.current_user.cid, e.args) 
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)

    @authenticated
    @tornado.web.removeslash
    def put(self):
        """Modify a existing operator.
        """
        status = ErrorCode.SUCCESS
        try:
            data = DotDict(json_decode(self.request.body))
            id = data.id
            name = data.name
            mobile = data.mobile
            email = data.email
            address = data.address
            group_id = data.group_id
            group_ids = map(int, str_to_list(group_id))
            logging.info("[UWEB] modify operator request: %s, cid: %s", 
                         data, self.current_user.cid)
        except Exception as e:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            logging.exception("[UWEB] Invalid data format. body:%s, Exception: %s",
                              self.request.body, e.args)
            self.write_ret(status)

        try:                
            operator = self.db.get("select oid from T_OPERATOR where id=%s", id)
            uids = [mobile,]

            self.db.execute("UPDATE T_OPERATOR"
                            "  SET name = %s,"
                            "      mobile = %s,"
                            "      oid = %s,"
                            "      email = %s,"
                            "      address = %s"
                            "  WHERE id = %s",
                            name, mobile, mobile, email, address, id)
            
            if group_ids is not None:
                self.db.execute("DELETE FROM T_GROUP_OPERATOR "
                                "  WHERE oper_id = %s",
                                operator.oid) 
                self.db.executemany("INSERT INTO T_GROUP_OPERATOR(group_id, oper_id)"
                                    "  VALUES(%s, %s)", 
                                    [(group_id, mobile) for group_id in group_ids])
            
            WSPushHelper.pushS3_dummy(uids, self.db, self.redis)
            self.write_ret(status)
        except Exception as e:
            logging.exception("[UWEB] cid: %s modify operator failed. Exception: %s", 
                              self.current_user.cid, e.args) 
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)

    @authenticated
    @tornado.web.removeslash
    def delete(self):
        """Delete a operator.
        """
        status = ErrorCode.SUCCESS
        try:
            delete_ids = map(int, str_to_list(self.get_argument('ids', None)))
            logging.info("[UWEB] delete operator: %s, cid: %s", 
                         delete_ids, self.current_user.cid)
        except Exception as e:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            logging.exception("[UWEB] Invalid data format. Exception: %s",
                              e.args)
            self.write_ret(status)
            return

        try:            
            self.db.execute("DELETE FROM T_OPERATOR WHERE id IN %s",
                            tuple(delete_ids + DUMMY_IDS)) 
            self.write_ret(status)
        except Exception as e:
            logging.exception("[UWEB] cid: %s delete operator failed. Exception: %s", 
                              self.current_user.cid, e.args) 
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)
