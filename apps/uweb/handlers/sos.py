# -*- coding: utf-8 -*-

import logging

import tornado.web
from tornado.escape import json_decode

from codes.errorcode import ErrorCode
from constants import LIMIT, QUERY

from utils.dotdict import DotDict
from utils.checker import check_phone
from utils.misc import get_today_last_month

from errors.updateerror import UpdateException

from mixin.sos import SOSMixin
from base import BaseHandler, authenticated


class SOSHandler(BaseHandler, SOSMixin):
    """Play with SOS number."""

    @authenticated
    @tornado.web.removeslash
    def get(self):
        """ Retrieve item. """
        try:
            sos = self.db.get("SELECT id, phone"
                              "  FROM T_SOS"
                              "  WHERE sim = %s",
                              self.current_user.sim)
            self.set_header(*self.JSON_HEADER)
            self.write_ret(ErrorCode.SUCCESS, dict_=DotDict(sos=sos))
        except:
            self.write_ret(ErrorCode.SERVER_ERROR)

    # it is not supported
    @authenticated
    @tornado.web.removeslash
    def post(self):
        """ Insert new item. """
        status = ErrorCode.SUCCESS

        try:
            sos = DotDict(json_decode(self.request.body))
            self.db.execute("INSERT INTO T_SOS"
                            "  VALUES (NULL, %s, %s)",
                            self.current_user.sim, sos.phone)
            self.update_to_target(self.current_user.sim)
        except UpdateException as e:
            logging.error("Error: %s, Sim: %s", e.args[0],
                          self.current_user.sim)
            status = ErrorCode.FLUSH_SOS_FAILED
        except Exception as e:
            logging.exception("Error: %s, Sim: %s", e.args,
                              self.current_user.sim)
            status = ErrorCode.SERVER_ERROR

        self.write_ret(status)


    @authenticated
    @tornado.web.removeslash
    def put(self):
        """ Update existing item. """
        status = ErrorCode.SUCCESS

        ids = []
        try:
            sos = DotDict(json_decode(self.request.body))

            if not check_phone(sos.phone):
                self.write_ret(ErrorCode.ILLEGAL_PHONE)
                return

            ids.append(DotDict(status=ErrorCode.FAILED, id=sos.id))
            self.update_to_target(self.current_user.sim, sos)
            id = self.db.execute("INSERT INTO T_SOS"
                                 "  VALUES(NULL,%s,%s)"
                                 "  ON DUPLICATE KEY"
                                 "    UPDATE phone = VALUES(phone)",
                                 self.current_user.sim, sos.phone)
            ids[0].id = id
            for item in ids:
                # oops, only one item!
                item.status = ErrorCode.SUCCESS
        except UpdateException as e:
            logging.error("Error: %s, Sim: %s", e.args[0],
                          self.current_user.sim)
            status = ErrorCode.FLUSH_SOS_FAILED
        except Exception as e:
            logging.exception("Error: %s, Sim: %s", e.args,
                              self.current_user.sim)
            status = ErrorCode.SERVER_ERROR

        self.write_ret(status, dict_=DotDict(ids=ids))

class SOSEventHandler(BaseHandler):
    
    @authenticated
    @tornado.web.removeslash
    def get(self, start_time, end_time):
        """Retrieves items.

           date format: utc
        """
        page_size = LIMIT.PAGE_SIZE
        page_number = int(self.get_argument('pagenum'))
        page_count = int(self.get_argument('pagecnt'))

        try:
            # the interval between start_time and end_time is one week
            if (int(end_time) - int(start_time)) > QUERY.INTERVAL:
                self.write_ret(ErrorCode.QUERY_INTERVAL_EXCESS)
                return

	        # we need return the event count to GUI at first time query
            if page_count == -1:
                res = self.db.get("SELECT COUNT(*) as count FROM V_SOS_EVENT"
                                  "  WHERE sim = %s"
                                  "    AND (timestamp BETWEEN %s AND %s)",
                                  self.current_user.sim, start_time, end_time)

                event_count = res.count
                d, m = divmod(event_count, page_size)
                page_count = (d + 1) if m else d

            sos_events = self.db.query("SELECT * FROM V_SOS_EVENT"
                                       "  WHERE sim = %s"
                                       "    AND (timestamp BETWEEN %s AND %s)"
                                       "  ORDER BY timestamp DESC"
                                       "  LIMIT %s,%s",
                                       self.current_user.sim, start_time, end_time,
                                       page_number * page_size, page_size)
            for e in sos_events:
                e["location"] = dict(id=e.id,
                                     name=e.location_name,
                                     timestamp=e.timestamp,
                                     latitude=e.latitude,
                                     longitude=e.longitude,
                                     clatitude=e.clatitude,
                                     clongitude=e.clongitude,
                                     type=e.type)
                del e["id"]
                del e["location_name"]
                del e["timestamp"]
                del e["latitude"]
                del e["longitude"]
                del e["clatitude"]
                del e["clongitude"]
                del e["type"]

            self.write_ret(ErrorCode.SUCCESS, dict_=DotDict(sos_events=sos_events,pagecnt=page_count))
        except Exception as e:
            logging.exception("Sim: %s get sos event failed. Exception: %s", 
                              self.current_user.sim, e.args)
            self.write_ret(ErrorCode.SERVER_BUSY)
