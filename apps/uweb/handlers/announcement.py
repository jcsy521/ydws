# -*- coding: utf-8 -*-

import logging
import time

import tornado.web
from tornado.escape import json_encode, json_decode

from utils.dotdict import DotDict
from utils.misc import safe_utf8, str_to_list, DUMMY_IDS
from codes.errorcode import ErrorCode
from constants import UWEB

from helpers.smshelper import SMSHelper
from base import BaseHandler, authenticated

class AnnouncementHandler(BaseHandler):
    """Record the announcement info.
    """

    @authenticated
    @tornado.web.removeslash
    def post(self):
        """Insert new items."""
        status = ErrorCode.SUCCESS
        try:
            data = DotDict(json_decode(self.request.body))
            content = data.get('content','')
            mobiles = data.get('mobiles', None)
            logging.info("[UWEB] announcement request: %s", data)
        except Exception as e:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            self.write_ret(status)
            return 

        try:
            mobiles_ =  u''
            if mobiles is not None:
                mobiles_ = ','.join(mobiles)
                for mobile in mobiles:
                    SMSHelper.send(mobile, content)

            self.db.execute("INSERT INTO T_ANNOUNCEMENT_LOG(umobile, content, timestamp, mobiles)"
                            "  VALUES(%s, %s, %s, %s)",
                            self.current_user.cid, content, int(time.time()), 
                            mobiles_)

            self.write_ret(status)
        except Exception as e:
            status = ErrorCode.SERVER_BUSY
            logging.exception("[UWEB] record share failed, Exception: %s", e.args)
            self.write_ret(status)

    @authenticated
    @tornado.web.removeslash
    def delete(self):
        """Delete announcement. 
        """
        status = ErrorCode.SUCCESS 
        try:
            delete_ids = map(int, str_to_list(self.get_argument('ids', None))) 
            logging.info("[UWEB] delete announcement: %s", 
                         delete_ids) 
        except Exception as e: 
            status = ErrorCode.ILLEGAL_DATA_FORMAT 
            logging.exception("[UWEB] data format illegal. Exception: %s", e.args) 
            self.write_ret(status) 
            return

        try: 
            self.db.execute("DELETE FROM T_ANNOUNCEMENT_LOG WHERE id IN %s", 
                            tuple(delete_ids + DUMMY_IDS)) 
            self.write_ret(status)
        except Exception as e: 
            status = ErrorCode.SERVER_BUSY 
            logging.exception("[UWEB] delete announcement failed.  Exception: %s", 
                              e.args) 
            self.write_ret(status)


class AnnouncementListHandler(BaseHandler):

    @authenticated 
    @tornado.web.removeslash 
    def post(self): 
        status = ErrorCode.SUCCESS 
        try:
            data = DotDict(json_decode(self.request.body))
            page_size = int(data.get('pagesize', UWEB.LIMIT.PAGE_SIZE))
            page_number = int(data.pagenum)
            page_count = int(data.pagecnt)
            start_time = data.start_time 
            end_time = data.end_time

            logging.info("[UWEB] announcement request: %s, uid: %s", 
                         data, self.current_user.uid)
        except Exception as e:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            logging.info("[UWEB] Invalid data format: %s, Exception: %s", 
                         data, e.args)
            self.write_ret(status)
            return

        try: 
            if page_count == -1:
                res = self.db.get("SELECT COUNT(*) AS count" 
                                  "  FROM T_ANNOUNCEMENT_LOG"
                                  "  WHERE umobile = %s "
                                  "  AND (timestamp BETWEEN %s AND %s)",
                                  self.current_user.cid, start_time, end_time)

                d, m = divmod(res.count, page_size)
                page_count = (d + 1) if m else d 

            res = self.db.query("SELECT id, umobile, content, timestamp, mobiles" 
                                "  FROM T_ANNOUNCEMENT_LOG"
                                "  WHERE umobile = %s"
                                "  AND (timestamp BETWEEN %s AND %s)"
                                "  ORDER BY timestamp DESC"
                                "  LIMIT %s, %s",
                                self.current_user.cid,
                                start_time, end_time,
                                page_number * page_size, page_size) 

            self.write_ret(status=status, 
                           dict_=DotDict(res=res,
                                         pagecnt=page_count)) 
        except Exception as e: 
            logging.exception("[UWEB] Get announcement list failed.") 
            status = ErrorCode.SUCCESS 
            self.write_ret(status=status) 
