# -*- coding: utf-8 -*-

import logging
import time

import tornado.web
from tornado.escape import json_decode, json_encode

from base import BaseHandler, authenticated
from utils.dotdict import DotDict
from codes.errorcode import ErrorCode
from helpers.wspushhelper import WSPushHelper
from helpers.queryhelper import QueryHelper
from utils.public import get_push_key


class WSPushTestHandler(BaseHandler):

    @tornado.web.removeslash
    def get(self):
        """Acquire push account through uid

        :arg uid: user uid
        """

        status = ErrorCode.SUCCESS
        try:
            # NOTE:  get_uid
            uid = self.get_argument('uid', '')
            logging.info("Get push account request from uid:%s", uid)
            wspush = dict(id='',
                          key='')

            json_data = WSPushHelper.register_wspush(uid, self.redis)
            if json_data:
                data = json_data.get("data")
                id = data.get('push_id', '')
                key = data.get('psd', '')
                wspush['id'] = id
                wspush['key'] = key
                logging.info("[UWEB] WSPushHandler get push account successfully. id:%s, key:%s",
                             id, key)
                self.write_ret(status=status,
                               dict_=dict(wspush=wspush))
            else:
                status = ErrorCode.SERVER_BUSY
                self.write_ret(status=status)
        except Exception as e:
            logging.exception("[UWEB] WSPushHandler get push account failed, Exception:%s",
                              e.args)
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)

    @tornado.web.removeslash
    def post(self):
        """Acquire push account through uid

        @uid: user uid
        """
        status = ErrorCode.SUCCESS
        try:
            data = DotDict(json_decode(self.request.body))
            tid = data.tid
            s_type = data.s_type
            if data.get('category', None):
                category = int(data.get('category'))
            else:
                category = 1

            logging.info("[UWEB] Test wspush request: %s.",
                         data)
        except Exception as e:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            logging.exception("[UWEB] Invalid data format. body: %s, Exception: %s",
                              self.request.body, e.args)
            self.write_ret(status)
            return

        try:
            # user = self.db.get("select owner_mobile")
            user = QueryHelper.get_user_by_tid(tid, self.db)
            uid = user.owner_mobile
            if s_type == 'S3':
                WSPushHelper.pushS3(tid, self.db, self.redis)
            elif s_type == 'S4':
                WSPushHelper.pushS4(tid, self.db, self.redis)
            elif s_type == 'S5':
                body = dict(tid=tid,
                            category=category,
                            pbat=100,
                            type=1,
                            timestamp=int(time.time()),
                            longitude=419004000,
                            latitude=143676000,
                            clongitude=419004000,
                            clatitude=143676000,
                            name='test name',
                            speed=111,
                            degree=203,
                            gsm=0,
                            locate_error=100,
                            gps=25,
                            alias='111',
                            region_id=11
                            )
                WSPushHelper.pushS5(tid, body, self.db, self.redis)
            elif s_type == 'S6':
                WSPushHelper.pushS6(tid, self.db, self.redis)
            elif s_type == 'S7':
                WSPushHelper.pushS7(tid, self.db, self.redis)
            elif s_type == 'S8':
                acc_message=1
                WSPushHelper.pushS8(tid, acc_message, self.db, self.redis)

            self.write_ret(status=status)
        except Exception as e:
            logging.exception("[UWEB] WSPushHandler get push account failed, Exception:%s",
                              e.args)
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)
