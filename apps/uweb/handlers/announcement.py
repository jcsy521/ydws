# -*- coding: utf-8 -*-

"""This module is designed for announcement in YDWQ.
"""

import logging
import time

import tornado.web
from tornado.escape import json_decode

from utils.dotdict import DotDict
from utils.misc import safe_utf8, str_to_list, DUMMY_IDS
from utils.public import record_announcement
from helpers.queryhelper import QueryHelper
from codes.errorcode import ErrorCode
from constants import UWEB

from helpers.smshelper import SMSHelper
from base import BaseHandler, authenticated


class AnnouncementHandler(BaseHandler):

    """Record the announcement info.

    :url /announcement
    """

    @authenticated
    @tornado.web.removeslash
    def post(self):
        """Insert new items."""
        status = ErrorCode.SUCCESS
        try:
            data = DotDict(json_decode(self.request.body))
            content = data.get('content', '')
            mobiles = data.get('mobiles', None)
            logging.info("[UWEB] Announcement request: %s", data)
        except Exception as e:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            self.write_ret(status)
            return

        try:
            mobiles_ = u''
            if mobiles is not None:
                mobiles_ = ','.join(mobiles)
                for mobile in mobiles:
                    SMSHelper.send(mobile, content)

            announcement = dict(cid=self.current_user.cid,
                                content=content,
                                mobiles=mobiles_)
            record_announcement(self.db, announcement)

            self.write_ret(status)
        except Exception as e:
            status = ErrorCode.SERVER_BUSY
            logging.exception(
                "[UWEB] record share failed, Exception: %s", e.args)
            self.write_ret(status)

    @authenticated
    @tornado.web.removeslash
    def delete(self):
        """Delete announcement. 
        """
        status = ErrorCode.SUCCESS
        try:
            delete_ids = map(int, str_to_list(self.get_argument('ids', None)))
            logging.info("[UWEB] Delete announcement: %s",
                         delete_ids)
        except Exception as e:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            logging.exception(
                "[UWEB] data format illegal. Exception: %s", e.args)
            self.write_ret(status)
            return

        try:
            self.db.execute("DELETE FROM T_ANNOUNCEMENT_LOG WHERE id IN %s",
                            tuple(delete_ids + DUMMY_IDS))
            self.write_ret(status)
        except Exception as e:
            status = ErrorCode.SERVER_BUSY
            logging.exception("[UWEB] Delete announcement failed. Exception: %s",
                              e.args)
            self.write_ret(status)


class AnnouncementListHandler(BaseHandler):

    """Query announcement records.

    :url  /announcement/list
    """

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
                res = QueryHelper.get_announcement(
                    self.current_user.cid, start_time, end_time, self.db)

                d, m = divmod(res.count, page_size)
                page_count = (d + 1) if m else d

            res = QueryHelper.get_announcement_paged(
                self.current_user.cid, start_time, end_time, page_number * page_size, page_size, self.db)

            self.write_ret(status=status,
                           dict_=DotDict(res=res,
                                         pagecnt=page_count))
        except Exception as e:
            logging.exception("[UWEB] Get announcement list failed.")
            status = ErrorCode.SUCCESS
            self.write_ret(status=status)
