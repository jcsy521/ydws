# -*- coding: utf-8 -*-

"""This module is designed for settings for client.
"""

import logging
import time

import tornado.web
from tornado.escape import json_decode, json_encode
from tornado.ioloop import IOLoop

from helpers.seqgenerator import SeqGenerator
from helpers.gfsenderhelper import GFSenderHelper
from utils.misc import get_today_last_month
from utils.dotdict import DotDict
from utils.checker import check_sql_injection
from base import BaseHandler, authenticated
from codes.errorcode import ErrorCode
from constants import UWEB, SMS, GATEWAY
from helpers.queryhelper import QueryHelper
from mixin.terminal import TerminalMixin


class AppSettingsHandler(BaseHandler, TerminalMixin):

    """Get basic information for Android, IOS.

    :url /appsettings
    """

    @authenticated
    @tornado.web.removeslash
    def get(self):
        """Get terminal info.
        """
        status = ErrorCode.SUCCESS
        try:
            tid = self.get_argument('tid', None)
            # check tid whether exist in request and update current_user
            self.check_tid(tid)

            # part 1: terminal
            tracker = DotDict()
            # 1: terminal
            # NOTE: static_val, move_val are deprecated
            terminal = QueryHelper.get_available_terminal(
                self.current_user.tid, self.db)

            if not terminal:
                status = ErrorCode.LOGIN_AGAIN
                logging.error(
                    "The terminal with tid: %s does not exist, redirect to login.html", self.current_user.tid)
                self.write_ret(status)
                return

            # 撤防，智能设防
            if terminal['mannual_status'] != UWEB.DEFEND_STATUS.YES:
                terminal['parking_defend'] = 1
            else:  # 强力设防
                terminal['parking_defend'] = 0

            # 2: sos is deprecatd
            user = QueryHelper.get_user_by_uid(self.current_user.uid, self.db)
            if not user:
                status = ErrorCode.LOGIN_AGAIN
                logging.error(
                    "The user with uid: %s does not exist, redirect to login.html", self.current_user.uid)
                self.write_ret(status)
                return

            sos = dict(mobile='')
            tracker.update(sos)

            tracker.update(dict(push_status=terminal.push_status))
            tracker.update(dict(sos_pop=terminal.white_pop))
            tracker.update(dict(vibl=terminal.vibl))
            tracker.update(dict(static_val=terminal.static_val))
            tracker.update(dict(parking_defend=terminal.parking_defend))
            tracker.update(dict(owner_mobile=terminal.owner_mobile))
            tracker.update(dict(speed_limit=terminal.speed_limit))

            # part 2: profile

            profile = DotDict()

            car = QueryHelper.get_car_by_tid(self.current_user.tid, self.db)

            profile.update(dict(name=user.name,
                                mobile=user.mobile,
                                email=user.email,
                                cnum=car.cnum))

            # part 3: sms option
            sms_options = QueryHelper.get_sms_option(user.mobile, self.db)

            # part 5: corp info
            corp = DotDict()
            corp = QueryHelper.get_corp_by_cid(self.current_user.cid, self.db)

            self.write_ret(status,
                           dict_=dict(tracker=tracker,
                                      sms_options=sms_options,
                                      profile=profile,
                                      corp=corp))
        except Exception as e:
            status = ErrorCode.SERVER_BUSY
            logging.exception("[UWEB] Get appsetting failed. uid: %s tid: %s, Exception: %s",
                              self.current_user.uid, self.current_user.tid, e.args)
            self.write_ret(status)
