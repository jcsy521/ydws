# -*- coding: utf-8 -*-

import time
import logging
import base64

import tornado.web
from tornado.web import removeslash
from tornado.escape import json_decode

from mixin.avatar import AvatarMixin
from base import authenticated, BaseHandler
from codes.errorcode import ErrorCode
from utils.dotdict import DotDict
from constants import UWEB

class AvatarHandler(BaseHandler, AvatarMixin):
    """ Show avatar for mobile client loggin
    """

    @authenticated
    @tornado.web.removeslash
    def post(self):
        status = ErrorCode.SUCCESS
        try:
            data = DotDict(json_decode(self.request.body))
            mobile = data.get('mobile', None)
            avatar = base64.urlsafe_b64decode(str(data.avatar))
            logging.info("[avatar] Request: %s, avatar: %s",
                         mobile, avatar)
        except Exception as e:
            logging.error("[avatar] Illegal format, body: %s, avatar: %s.",
                          self.request.body, avatar)
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            self.write_ret(status)
            return

        try:
            terminal = self.db.get("SELECT tid FROM T_TERMINAL_INFO WHERE mobile = %s",
                                   mobile)
            tid = terminal.tid
            avatar_name = tid + '.png'
            avatar_path = self.application.settings['avatar_path'] + avatar_name
            avatar_full_path = self.application.settings['server_path'] + avatar_path

            img = open(avatar_full_path, 'w')
            img.write(avatar)
            img.close()
            avatar_time = self.update_avatar_time(tid)
            logging.info("[avatar] avatar_time: %s, tid: %s, user: %s",
                         avatar_time, tid, self.current_user.uid)
            if status == 0:
                self.write_ret(status,
                               dict_=dict(avatar_path=avatar_path,
                                          avatar_time=avatar_time))
            else:
                self.write_ret(status, message=ErrorCode.ERROR_MESSAGE[status],
                               dict_=dict(avatar_path=avatar_path,
                                          avatar_time=avatar_time))
        except Exception as e:
            logging.exception("[avatar] Post avatar failed, user: %s. Exception: %s",
                              self.current_user.uid, e.args)
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)
