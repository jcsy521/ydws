# -*- coding: utf-8 -*-

"""This module is designed for ZNBC.

#NOTE：deprecated.
"""

import logging

import tornado.web

from utils.dotdict import DotDict
from codes.errorcode import ErrorCode
from base import BaseHandler

       
class CorpSearchHandler(BaseHandler):

    @tornado.web.removeslash
    def post(self):
        """get corp line info by corp_name.
        """
        try:
            corp_name = self.get_argument('corp_name')
            logging.info("[CLIENT] search request corp_name : %s ", 
                         corp_name)
        except Exception as e:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            self.write_ret(status)
            return

        try:
            status = ErrorCode.SUCCESS
            sql = "SELECT cid, name AS corp_name, address AS corp_addr, type FROM T_CORP WHERE name LIKE '%%%%%s%%%%' " % (corp_name,)
            corporations = self.db.query(sql)
            for corporation in corporations:
                lines = self.db.query("SELECT id AS line_id, name AS line_name "
                                      "  FROM T_LINE"
                                      "  WHERE cid = %s",
                                      corporation.cid)
                for line in lines:
                    stations = self.db.query("SELECT name AS station_name, longitude AS station_lon, "
                                             "       latitude AS station_lat, seq"
                                             "  FROM T_STATION"
                                             "  WHERE line_id = %s",
                                             line.line_id)
                    line["stations"] = stations
                    
                corporation["lines"] = lines
            self.write_ret(status, 
                           dict_=DotDict(search_info=corporations))
        except Exception as e:
            logging.exception("[CLIENT] search corp : %s failed. Exception: %s", 
                              corp_name, e.args) 
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)

