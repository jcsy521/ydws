# -*- coding: utf-8 -*-

"""This module is designed for ZNBC.

#NOTE: deprecated.
"""

import logging

import tornado.web
from tornado.escape import json_decode

from utils.dotdict import DotDict
from utils.misc import DUMMY_IDS, str_to_list
from constants import UWEB
from codes.errorcode import ErrorCode
from base import BaseHandler, authenticated

       
class PassengerHandler(BaseHandler):

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
            logging.exception("[UWEB] cid: %s create passenger data format illegal. Exception: %s", 
                              self.current_user.cid, e.args) 
            self.write_ret(status)
            return

        try:
            where_clause = ' AND '.join([v for v in fields.itervalues()
                                         if v is not None])
            page_size = UWEB.LIMIT.PAGE_SIZE
            if where_clause:
                where_clause = ' AND ' + where_clause
            if page_count == -1:
                sql = "SELECT count(id) as count FROM T_PASSENGER" + \
                      "  WHERE 1=1 " + where_clause
                sql += " AND cid = %s" % (self.current_user.cid,)
                res = self.db.get(sql) 
                count = res.count
                d, m = divmod(count, page_size)
                page_count = (d + 1) if m else d

            sql = "SELECT id, pid, name, mobile FROM T_PASSENGER" +\
                  "  WHERE 1=1 " + where_clause
            sql += " AND cid = %s LIMIT %s, %s" % (self.current_user.cid, page_number * page_size, page_size)
            passengers = self.db.query(sql)
            for passenger in passengers:
                for key in passenger.keys():
                    passenger[key] = passenger[key] if passenger[key] else ''
            self.write_ret(status,
                           dict_=DotDict(passengers=passengers,
                                         pagecnt=page_count))
        except Exception as e:
            logging.exception("[UWEB] cid: %s get passenger failed. Exception: %s", 
                              self.current_user.cid, e.args) 
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)
        

    @authenticated
    @tornado.web.removeslash
    def post(self):
        """Create a new passenger.
        """
        try:
            data = DotDict(json_decode(self.request.body))
            logging.info("[UWEB] add passenger request: %s, cid: %s", 
                         data, self.current_user.cid)
        except Exception as e:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            self.write_ret(status)
            return

        try:
            status = ErrorCode.SUCCESS
            mobile = data.mobile
            name = data.name
            id = self.db.execute("INSERT T_PASSENGER(id, name, mobile, cid)"
                                 "  VALUES(NULL, %s, %s, %s)",
                                 name, mobile, self.current_user.cid)
            self.write_ret(status, dict_=DotDict(id=id))
        except Exception as e:
            logging.exception("[UWEB] cid: %s create passenger failed. Exception: %s", 
                              self.current_user.cid, e.args) 
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)


    @authenticated
    @tornado.web.removeslash
    def put(self):
        """Modify a existing passenger.
        """
        try:
            data = DotDict(json_decode(self.request.body))
            logging.info("[UWEB] modify passenger request: %s, cid: %s", 
                         data, self.current_user.cid)

        except Exception as e:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            self.write_ret(status)
            return

        try:
            status = ErrorCode.SUCCESS
            id = data.id
            name = data.name
            mobile = data.mobile
            self.db.execute("UPDATE T_PASSENGER"
                            "  SET name = %s,"
                            "      mobile = %s"
                            "  WHERE id = %s",
                            name, mobile, id)
            self.write_ret(status)
        except Exception as e:
            logging.exception("[UWEB] cid: %s modify passenger failed. Exception: %s", 
                              self.current_user.cid, e.args) 
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)

    @authenticated
    @tornado.web.removeslash
    def delete(self):
        """Delete a passenger.
        """
        try:
            delete_ids = map(int, str_to_list(self.get_argument('ids', None)))
            logging.info("[UWEB] delete passenger: %s, cid: %s", 
                         delete_ids, self.current_user.cid)
        except Exception as e:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            self.write_ret(status)
            return

        try:
            status = ErrorCode.SUCCESS
            passengers =  self.db.query("SELECT pid FROM T_PASSENGER"
                                        "  WHERE id IN %s",
                                       tuple(delete_ids + DUMMY_IDS))
            pidlist = [passenger.pid for passenger in passengers]
            self.db.execute("DELETE FROM T_LINE_PASSENGER WHERE pid IN %s",
                            tuple(pidlist + DUMMY_IDS))
            
            self.db.execute("DELETE FROM T_PASSENGER WHERE id IN %s",
                            tuple(delete_ids + DUMMY_IDS)) 
            self.write_ret(status)
        except Exception as e:
            logging.exception("[UWEB] cid: %s delete passenger failed. Exception: %s", 
                              self.current_user.cid, e.args) 
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)
