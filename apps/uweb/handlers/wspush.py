# -*- coding: utf-8 -*-

import logging
import time

import tornado.web
from tornado.escape import json_decode, json_encode

from base import BaseHandler, authenticated
from utils.dotdict import DotDict
from codes.errorcode import ErrorCode
from helpers.wspushhelper import WSPushHelper
from utils.public import get_push_key


class WSPushHandler(BaseHandler):

    @authenticated
    @tornado.web.removeslash
    def get(self):
        """Acquire push account through uid

        @uid: user uid
        """
        status = ErrorCode.SUCCESS
        try:
            #NOTE:  get_uid
            uid = self.current_user.uid
            logging.info("Get push account request from uid:%s", uid)
            wspush = dict(id='',
                          key='')

            t = int(time.time()) * 1000
            #NOTE: uid? cid? 
            push_key = get_push_key(uid, t)
            json_data = WSPushHelper.register(uid, t, push_key)
            if json_data:
                data = json_data.get("data")
                id = data.get('push_id', '')
                key = data.get('psd', '')
                wspush['id']=id
                wspush['key']=key
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
