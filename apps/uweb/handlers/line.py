# -*- coding: utf-8 -*-

"""This module is designed for ZNBC.

#NOTE: deprecated.
"""

import logging

import tornado.web
from tornado.escape import json_encode, json_decode

from utils.dotdict import DotDict
from utils.misc import DUMMY_IDS, str_to_list
from utils.checker import check_sql_injection
from constants import UWEB
from codes.errorcode import ErrorCode
from base import BaseHandler, authenticated

       
class LineHandler(BaseHandler):

    @authenticated
    @tornado.web.removeslash
    def get(self):
        """ """ 
        status = ErrorCode.SUCCESS
        try:
            page_number = int(self.get_argument('pagenum'))
            page_count = int(self.get_argument('pagecnt'))
            #reserved API
            fields = DotDict(name="name LIKE '%%%%%s%%%%'")
            
            for key in fields.iterkeys():
                v = self.get_argument(key, None)
                if v:
                    if not check_sql_injection(v):
                        status = ErrorCode.SELECT_CONDITION_ILLEGAL
                        self.write_ret(status)
                        return  
                    fields[key] = fields[key] % (v,)
                else:
                    fields[key] = None
        except Exception as e:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            logging.exception("[UWEB] cid: %s get line data format illegal. Exception: %s", 
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
                sql = "SELECT count(id) as count FROM T_LINE" + \
                      "  WHERE 1=1 " + where_clause
                sql += " AND cid = %s" % (self.current_user.cid,)
                res = self.db.get(sql) 
                count = res.count
                d, m = divmod(count, page_size)
                page_count = (d + 1) if m else d

            sql = "SELECT id AS line_id, name AS line_name FROM T_LINE" +\
                  "  WHERE 1=1 " + where_clause
            sql += " AND cid = %s LIMIT %s, %s" % (self.current_user.cid, page_number * page_size, page_size)
            lines = self.db.query(sql)
            for line in lines:
                stations = self.db.query("SELECT name, latitude, longitude, seq "
                                         "  FROM T_STATION "
                                         "  WHERE line_id = %s",
                                         line.line_id)
                line["stations"] = stations
                
            self.write_ret(status,
                           dict_=DotDict(lines=lines,
                                         pagecnt=page_count))
        except Exception as e:
            logging.exception("[UWEB] cid: %s get line failed. Exception: %s", 
                              self.current_user.cid, e.args) 
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)
        

    @authenticated
    @tornado.web.removeslash
    def post(self):
        """Create a new line.
        """
        try:
            data = DotDict(json_decode(self.request.body))
            logging.info("[UWEB] add line request: %s, cid: %s", 
                         data, self.current_user.cid)
        except Exception as e:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            #logging
            self.write_ret(status)
            return

        try:
            status = ErrorCode.SUCCESS
            line_name = data.line_name
            stations = data.stations
            
            lid = self.db.execute("INSERT T_LINE(id, name, cid)"
                                  "  VALUES(NULL, %s, %s)",
                                  line_name, self.current_user.cid)
            for station in stations:
                station = DotDict(station)
                self.db.execute("INSERT T_STATION(id, name, latitude, longitude, seq, line_id)"
                                "  VALUES(NULL, %s, %s, %s, %s, %s)",
                                station.name, station.latitude, station.longitude, station.seq, lid)
            
            self.write_ret(status)
        except Exception as e:
            logging.exception("[UWEB] cid: %s create line failed. Exception: %s", 
                              self.current_user.cid, e.args) 
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)


    @authenticated
    @tornado.web.removeslash
    def delete(self):
        """Delete a line.
        """
        try:
            delete_ids = map(int, str_to_list(self.get_argument('ids', None)))
            logging.info("[UWEB] delete line: %s, cid: %s", 
                         delete_ids, self.current_user.cid)
        except Exception as e:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            self.write_ret(status)
            return

        try:
            status = ErrorCode.SUCCESS
            self.db.execute("DELETE FROM T_LINE_PASSENGER WHERE line_id IN %s",
                            tuple(delete_ids + DUMMY_IDS)) 
            self.db.execute("DELETE FROM T_LINE WHERE id IN %s",
                            tuple(delete_ids + DUMMY_IDS)) 

            self.write_ret(status)
        except Exception as e:
            logging.exception("[UWEB] cid: %s delete line failed. Exception: %s", 
                              self.current_user.cid, e.args) 
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)


