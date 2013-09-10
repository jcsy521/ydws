# -*- coding: utf-8 -*-

import logging

import tornado.web
from tornado.escape import json_encode, json_decode

from utils.dotdict import DotDict
from utils.misc import DUMMY_IDS, str_to_list
from utils.checker import check_sql_injection
from constants import UWEB
from codes.errorcode import ErrorCode
from base import BaseHandler, authenticated

       
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
                    #if not check_sql_injection(v):
                    #    status = ErrorCode.SELECT_CONDITION_ILLEGAL
                    #    self.write_ret(status)
                    #    return  
                    fields[key] = fields[key] % (v,)
                else:
                    fields[key] = None
        except Exception as e:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
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
        try:
            data = DotDict(json_decode(self.request.body))
            logging.info("[UWEB] add operator request: %s, cid: %s", 
                         data, self.current_user.cid)
        except Exception as e:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            self.write_ret(status)
            return

        try:
            status = ErrorCode.SUCCESS
            mobile = data.mobile
            name = data.name
            email = data.email
            address = data.address
            group_id = data.group_id
            group_ids = map(int, str_to_list(group_id))
            oid = self.db.execute("INSERT T_OPERATOR(oid, mobile, password, name, corp_id, email, address)"
                                  "  VALUES(%s, %s, password(%s), %s, %s, %s, %s)",
                                  mobile, mobile, '111111', name, self.current_user.cid,
                                  email, address)
            self.db.executemany("INSERT INTO T_GROUP_OPERATOR(group_id, oper_id)"
                                "  VALUES( %s, %s)", 
                                [(group_id, mobile) for group_id in group_ids])
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
        try:
            data = DotDict(json_decode(self.request.body))
            logging.info("[UWEB] modify operator request: %s, cid: %s", 
                         data, self.current_user.cid)

        except Exception as e:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            self.write_ret(status)

        try:
            status = ErrorCode.SUCCESS
            id = data.id
            name = data.name
            mobile = data.mobile
            email = data.email
            address = data.address
            group_id = data.group_id
            group_ids = map(int, str_to_list(group_id))

            operator = self.db.get("select oid from T_OPERATOR where id=%s", id)

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
        try:
            delete_ids = map(int, str_to_list(self.get_argument('ids', None)))
            logging.info("[UWEB] delete operator: %s, cid: %s", 
                         delete_ids, self.current_user.cid)
        except Exception as e:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            self.write_ret(status)
            return

        try:
            status = ErrorCode.SUCCESS
            self.db.execute("DELETE FROM T_OPERATOR WHERE id IN %s",
                            tuple(delete_ids + DUMMY_IDS)) 
            self.write_ret(status)
        except Exception as e:
            logging.exception("[UWEB] cid: %s delete operator failed. Exception: %s", 
                              self.current_user.cid, e.args) 
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)


#class OperatorBindGroupHandler(BaseHandler):
#
#    @authenticated
#    @tornado.web.removeslash
#    def post(self):
#        """Bind some groups to an operator.
#        """
#        try:
#            data = DotDict(json_decode(self.request.body))
#            gids = [str(gid) for gid in data.gids]
#            oid = data.oid 
#            logging.info("[UWEB] bind group to operator request: %s, cid: %s", 
#                         data, self.current_user.cid)
#        except Exception as e:
#            status = ErrorCode.ILLEGAL_DATA_FORMAT
#            self.write_ret(status)
#            return
#
#        try:
#            status = ErrorCode.SUCCESS
#            self.db.executemany("INSERT INTO T_GROUP_OPERATOR(id, group_id, oper_id)"
#                                "  VALUES(NULL, %s, %s)" %\
#                                [(gid, oid) for gid in gids])
#
#            self.write_ret(status)
#        except Exception as e:
#            logging.exception("[UWEB] cid: %s bind group failed. Exception: %s", 
#                              self.current_user.cid, e.args) 
#            status = ErrorCode.SERVER_BUSY
#            self.write_ret(status)
