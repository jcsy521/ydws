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
from codes.smscode import SMSCode 
from utils.dotdict import DotDict
from constants import UWEB
from helpers.smshelper import SMSHelper

class BindHandler(BaseHandler, AvatarMixin):
    """ Show avatar for mobile client loggin
    """

    @authenticated
    @tornado.web.removeslash
    def post(self):
        status = ErrorCode.SUCCESS
        try:
            data = DotDict(json_decode(self.request.body))
            tmobile = data.get('tmobile', None)
            umobile = data.get('umobile', None)
            group_id = data.get('group_id', None)
            cnum = data.get('cnum', None)
            avatar = base64.urlsafe_b64decode(str(data.avatar))
            logging.info("[BIND] umobile: %s, tmobile: %s",
                         umobile, tmobile)
        except Exception as e:
            logging.error("[BIND] Illegal format, body: %s, avatar: %s.",
                          self.request.body, avatar)
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            self.write_ret(status)
            return

        try:
            # record the add action 
            begintime = int(time.time())
            record_add_action(tmobile, group_id, begintime, self.db)
            now_ = datetime.datetime.now()
            endtime = now_ + relativedelta(years=1)
            endtime = int(time.mktime(endtime.timetuple()))

            # avatar
            terminal = self.db.get("SELECT tid FROM T_TERMINAL_INFO WHERE mobile = %s",
                                   mobile)
            tid = terminal.tid
            activation_code = QueryHelper.get_activation_code(self.db)
            self.db.execute("INSERT INTO T_TERMINAL_INFO(tid, group_id, mobile, owner_mobile,"
                            "  defend_status, mannual_status, begintime, endtime, offline_time, "
                            "  alias, icon_type, login_permit, push_status, vibl, use_scene, biz_type, "
                            "  activation_code)"
                            "  VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                            tid, group_id, tmobile, umobile, UWEB.DEFEND_STATUS.NO,
                            UWEB.DEFEND_STATUS.NO, begintime, endtime,
                            begintime, cnum, 0, data.login_permit, data.push_status,
                            1, 3, UWEB.BIZ_TYPE.YDWQ,
                            activation_code)
            register_sms = SMSCode.SMS_REGISTER_YDWQ % activation_code
            ret = SMSHelper.send(tmobile, register_sms)
            self.db.execute("INSERT INTO T_CAR(tid, cnum)"
                            "  VALUES(%s, %s)",
                            tid, cnum)
            ret = DotDict(json_decode(ret))
            if ret.status == ErrorCode.SUCCESS:
                self.db.execute("UPDATE T_TERMINAL_INFO"
                                "  SET msgid = %s"
                                "  WHERE mobile = %s",
                                ret['msgid'], data.tmobile)

                avatar_name = tid + '.png'
                avatar_path = self.application.settings['avatar_path'] + avatar_name
                avatar_full_path = self.application.settings['server_path'] + avatar_path

                img = open(avatar_full_path, 'w')
                img.write(avatar)
                img.close()
                avatar_time = self.update_avatar_time(tid)
                logging.info("[BIND] avatar_time: %s, tid: %s, user: %s",
                             avatar_time, tid, self.current_user.uid)
            else:
                logging.error("[BIND] Send %s to terminal %s failed.", register_sms, tmobile)

            self.write_ret(status,
                           dict_=dict(avatar_path=avatar_path,
                                      avatar_time=avatar_time))
        except Exception as e:
            logging.exception("[BIND] Bind terminal failed, user: %s. Exception: %s",
                              self.current_user.uid, e.args)
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)
