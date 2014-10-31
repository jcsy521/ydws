# -*- coding: utf-8 -*-

import time
import logging
import base64
import datetime
from dateutil.relativedelta import relativedelta

import tornado.web
from tornado.web import removeslash
from tornado.escape import json_decode

from mixin.avatar import AvatarMixin
from base import authenticated, BaseHandler
from codes.errorcode import ErrorCode
from codes.smscode import SMSCode 
from utils.dotdict import DotDict
from utils.public import record_add_action, delete_terminal, add_terminal 
from utils.misc import get_tid_from_mobile_ydwq 
from utils.checker import check_zs_phone
from constants import UWEB
from helpers.smshelper import SMSHelper
from helpers.queryhelper import QueryHelper
from helpers.confhelper import ConfHelper

class YDWQBindHandler(BaseHandler, AvatarMixin):
    """Show avatar for mobile client login.
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
            if int(group_id) == -1:
                group = QueryHelper.get_default_group_by_cid(self.current_user.cid, self.db)
                group_id = group.gid
            cnum = data.get('cnum', None)
            avatar = None
            avatar_ = data.get('avatar', None)
            if avatar_:
                avatar = base64.urlsafe_b64decode(str(avatar_))
            logging.info("[BIND] umobile: %s, tmobile: %s",
                         umobile, tmobile)
        except Exception as e:
            logging.exception("[BIND] Illegal format, body: %s, Exception: %s",
                              self.request.body, e.args)
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            self.write_ret(status)
            return

        try:
            # record the add action 
            begintime = int(time.time())
            now_ = datetime.datetime.now()
            endtime = now_ + relativedelta(years=1)
            endtime = int(time.mktime(endtime.timetuple()))

            #white_list = check_zs_phone(tmobile, self.db) 
            #if not white_list:
            #    logging.error("[UWEB] mobile: %s is not whitelist.", tmobile)
            #    status = ErrorCode.MOBILE_NOT_ORDERED
            #    message = ErrorCode.ERROR_MESSAGE[status] % tmobile
            #    self.write_ret(status, message=message)
            #    return

            # avatar
            terminal = self.db.get("SELECT id, tid, service_status FROM T_TERMINAL_INFO WHERE mobile = %s",
                                   tmobile)
            if terminal:
                if terminal.service_status == UWEB.SERVICE_STATUS.TO_BE_UNBIND:
                    delete_terminal(terminal.tid, self.db, self.redis)
                else:
                    status = ErrorCode.TERMINAL_ORDERED
                    logging.error("[UWEB] mobile: %s already existed.", tmobile)
                    self.write_ret(status)
                    return
 
            tid = get_tid_from_mobile_ydwq(tmobile)
            activation_code = QueryHelper.get_activation_code(self.db)
            terminal_info = dict(tid=tid,
                                 group_id=group_id,
                                 tmobile=tmobile,
                                 owner_mobile=umobile,
                                 mannual_status=UWEB.DEFEND_STATUS.YES,
                                 begintime=begintime,
                                 endtime=4733481600,
                                 offline_time=begintime,
                                 cnum=cnum,
                                 icon_type=0,
                                 login_permit=1,
                                 push_status=1,
                                 vibl=1,
                                 use_scene=3,
                                 activation_code=activation_code,
                                 service_status=UWEB.SERVICE_STATUS.TO_BE_ACTIVATED)
            add_terminal(terminal_info, self.db, self.redis)
            bind_info = dict(tid=tmobile, 
                             tmobile=tmobile,
                             umobile=umobile,
                             group_id=group_id,
                             cid=self.current_user.cid, 
                             add_time=begintime)
            record_add_action(bind_info, self.db)
            avatar_full_path, avatar_path, avatar_name, avatar_time = self.get_avatar_info(tmobile)

            register_sms = SMSCode.SMS_REGISTER_YDWQ % (ConfHelper.UWEB_CONF.url_out, activation_code)
            ret = SMSHelper.send(tmobile, register_sms)
            ret = DotDict(json_decode(ret))
            if ret.status == ErrorCode.SUCCESS:
                self.db.execute("UPDATE T_TERMINAL_INFO"
                                "  SET msgid = %s"
                                "  WHERE mobile = %s",
                                ret['msgid'], tmobile)

                if avatar:
                    avatar_name = tmobile + '.png'
                    avatar_path = self.application.settings['avatar_path'] + avatar_name
                    avatar_full_path = self.application.settings['server_path'] + avatar_path

                    img = open(avatar_full_path, 'w')
                    img.write(avatar)
                    img.close()
                    avatar_time = self.update_avatar_time(tmobile)
                    logging.info("[BIND] avatar_time: %s, tmobile: %s, user: %s",
                                 avatar_time, tmobile, self.current_user.cid)
                else:
                    logging.error("[BIND] Termianl: %s has no avatar.",
                                  tmobile)
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
