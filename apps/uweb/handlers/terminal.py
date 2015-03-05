# -*- coding: utf-8 -*-

"""This module is designed for terminal's management.
"""

import logging
import time
import datetime
from dateutil.relativedelta import relativedelta

import tornado.web
from tornado.escape import json_decode

from utils.misc import get_del_data_key, get_tid_from_mobile_ydwq
from utils.dotdict import DotDict
from utils.checker import check_sql_injection, check_zs_phone, check_cnum
from utils.public import (record_add_action, delete_terminal,
     add_terminal, add_user, clear_sessionID, get_use_scene_by_vibl)
from base import BaseHandler, authenticated
from codes.errorcode import ErrorCode
from codes.smscode import SMSCode
from constants import UWEB, GATEWAY

from helpers.queryhelper import QueryHelper
from helpers.gfsenderhelper import GFSenderHelper
from helpers.confhelper import ConfHelper
from helpers.smshelper import SMSHelper
from helpers.wspushhelper import WSPushHelper

from mixin.terminal import TerminalMixin


class TerminalHandler(BaseHandler, TerminalMixin):

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

            car_sets = DotDict()

            terminal = QueryHelper.get_available_terminal(self.current_user.tid, self.db)
            if not terminal:
                status = ErrorCode.LOGIN_AGAIN
                logging.error("[UWEB] The terminal with tid: %s does not exist,"
                              "  redirect to login.html",
                              self.current_user.tid)
                self.write_ret(status)
                return

            user = QueryHelper.get_user_by_mobile(terminal.owner_mobile, self.db)
            if not user:
                logging.error("[UWEB] The user with uid: %s does not exist,"
                              "  redirect to login.html", 
                              self.current_user.uid)
                self.clear_cookie(self.app_name)
                self.write_ret(ErrorCode.LOGIN_AGAIN)
                return

            # NOTE: deprecated.
            if terminal['mannual_status'] == 1:
                terminal['parking_defend'] = 0
            else:
                terminal['parking_defend'] = 1

            # NOTE: deprecated.
            whitelist = QueryHelper.get_white_list_by_tid(
                self.current_user.tid, self.db)

            car_info = QueryHelper.get_car_by_tid(
                self.current_user.tid, self.db)
            car = dict(corp_cnum=car_info.get('cnum', ''))

            # add tow dict: terminal, car. add two value: whitelist_1,
            # whitelist_2
            white_list = [terminal.owner_mobile]
            for item in whitelist:
                white_list.append(item['mobile'])

            car_sets.update(terminal)
            car_sets.update(car)
            car_sets.update(DotDict(white_list=white_list))
            self.write_ret(status,
                           dict_=dict(car_sets=car_sets))
        except Exception as e:
            status = ErrorCode.SERVER_BUSY
            logging.exception("[UWEB] uid: %s tid: %s get terminal failed. Exception: %s",
                              self.current_user.uid, self.current_user.tid, e.args)
            self.write_ret(status)

    @authenticated
    @tornado.web.removeslash
    def put(self):
        """Update the parameters of terminal.
        """
        status = ErrorCode.SUCCESS
        try:
            data = DotDict(json_decode(self.request.body))
            tid = data.get('tid', None)
            # check tid whether exist in request and update current_user
            self.check_tid(tid)
            logging.info("[UWEB] Terminal request: %s, uid: %s, tid: %s",
                         data, self.current_user.uid, self.current_user.tid)
        except Exception as e:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            self.write_ret(status)
            return

        try:
            terminal = QueryHelper.get_available_terminal(
                self.current_user.tid, self.db)
            if not terminal:
                status = ErrorCode.LOGIN_AGAIN
                logging.error("[UWEB] The terminal with tid: %s does not exist,"
                              "  redirect to login.html",
                              self.current_user.tid)
                self.write_ret(status)
                return

            user = QueryHelper.get_user_by_uid(self.current_user.uid, self.db)
            if not user:
                status = ErrorCode.LOGIN_AGAIN
                logging.error("[UWEB] The user with uid: %s does not exist,"
                              "  redirect to login.html",
                              self.current_user.uid)
                self.write_ret(status)
                return

            # sql injection
            if data.has_key('corp_cnum') and not check_cnum(data.corp_cnum):
                status = ErrorCode.ILLEGAL_CNUM
                self.write_ret(status)
                return

            # NOTE: deprecated
            if data.has_key('white_list'):
                white_list = ":".join(data.white_list)
                if not check_sql_injection(white_list):
                    status = ErrorCode.ILLEGAL_WHITELIST
                    self.write_ret(status)
                    return

            self.update_terminal_db(data)
            # NOTE: wspush to client
            if status == ErrorCode.SUCCESS:
                WSPushHelper.pushS7(tid, self.db, self.redis)
            self.write_ret(status)
        except Exception as e:
            logging.exception("[UWEB] uid:%s, tid:%s update terminal info failed. Exception: %s",
                              self.current_user.uid, self.current_user.tid, e.args)
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)


class TerminalCorpHandler(BaseHandler, TerminalMixin):

    @authenticated
    @tornado.web.removeslash
    def get(self):
        """Show information of a terminal.
        """
        status = ErrorCode.SUCCESS
        try:
            if self.current_user.oid == UWEB.DUMMY_OID:  # enterprise
                terminals = QueryHelper.get_all_terminals_by_cid(self.current_user.cid, self.db)
            else:  # operator
                terminals = QueryHelper.get_all_terminals_by_oid(self.current_user.oid, self.db)

            res = []
            for terminal in terminals:
                res.append(dict(tid=terminal.tid,
                                tmobile=terminal.mobile))

            self.write_ret(status,
                           dict_=dict(res=res))
        except Exception as e:
            logging.exception("[UWEB] Get terminal info failed. "
                              "  cid:%s, Exception: %s",
                              self.current_user.cid, e.args)
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)

    @authenticated
    @tornado.web.removeslash
    def post(self):
        """Add a terminal.
        """
        status = ErrorCode.SUCCESS
        try:
            data = DotDict(json_decode(self.request.body))
            logging.info("[UWEB] Corp add terminal request: %s, cid: %s",
                         data, self.current_user.cid)
        except Exception as e:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            self.write_ret(status)
            return

        try:
            if data.has_key('cnum') and not check_cnum(data.cnum):
                status = ErrorCode.ILLEGAL_CNUM
                self.write_ret(status)
                return

            # 1 year
            begintime = int(time.time())
            now_ = datetime.datetime.now()
            endtime = now_ + relativedelta(years=1)
            endtime = int(time.mktime(endtime.timetuple()))

            # 1: add terminal
            #umobile = data.umobile if data.umobile else self.current_user.cid
            if data.umobile:
                umobile = data.umobile
            else:
                corp = QueryHelper.get_corp_by_cid(self.current_user.cid, self.db)
                umobile = corp.get('c_mobile', '')

            terminal = QueryHelper.get_terminal_by_tmobile(data.tmobile, self.db)
            if terminal:
                if terminal.service_status == UWEB.SERVICE_STATUS.TO_BE_UNBIND:
                    delete_terminal(terminal.tid, self.db, self.redis)
                else:
                    logging.error(
                        "[UWEB] mobile: %s already existed.", data.tmobile)
                    status = ErrorCode.TERMINAL_ORDERED
                    self.write_ret(status)
                    return

            vibl = data.get("vibl")
            use_scene = get_use_scene_by_vibl(vibl)

            biz_type = data.get('biz_type', UWEB.BIZ_TYPE.YDWS)
            tid = data.tmobile

            terminal_info = dict(tid=tid,
                                 group_id=data.group_id,
                                 tmobile=data.tmobile,
                                 owner_mobile=umobile,
                                 mannual_status=UWEB.DEFEND_STATUS.YES,
                                 begintime=begintime,
                                 endtime=4733481600,
                                 offline_time=begintime,
                                 cnum=data.cnum,
                                 icon_type=data.icon_type,
                                 login_permit=data.login_permit,
                                 push_status=data.push_status,
                                 vibl=data.vibl,
                                 use_scene=use_scene,
                                 biz_type=biz_type,
                                 speed_limit=data.speed_limit,
                                 stop_interval=data.stop_interval,
                                 service_status=UWEB.SERVICE_STATUS.ON)

            if int(biz_type) == UWEB.BIZ_TYPE.YDWS:
                # 0. check tmobile is whitelist or not
                white_list = check_zs_phone(data.tmobile, self.db)
                if not white_list:
                    logging.error("[UWEB] mobile: %s is not whitelist.", data.tmobile)
                    status = ErrorCode.MOBILE_NOT_ORDERED
                    message = ErrorCode.ERROR_MESSAGE[status] % data.tmobile
                    self.write_ret(status, message=message)
                    return

                # 4: send message to terminal
                register_sms = SMSCode.SMS_REGISTER % (umobile, data.tmobile)
                ret = SMSHelper.send_to_terminal(data.tmobile, register_sms)
            else:
                tid = get_tid_from_mobile_ydwq(data.tmobile)
                activation_code = QueryHelper.get_activation_code(self.db)
                terminal_info['tid'] = tid
                terminal_info['activation_code'] = activation_code
                terminal_info['service_status'] = UWEB.SERVICE_STATUS.TO_BE_ACTIVATED
                register_sms = SMSCode.SMS_REGISTER_YDWQ % (ConfHelper.UWEB_CONF.url_out, activation_code)
                ret = SMSHelper.send(data.tmobile, register_sms)

            add_terminal(terminal_info, self.db, self.redis)
            # record the add action
            bind_info = dict(tid=data.tmobile,
                             tmobile=data.tmobile,
                             umobile=umobile,
                             group_id=data.group_id,
                             cid=self.current_user.cid,
                             add_time=int(time.time()))
            record_add_action(bind_info, self.db)

            if ret:
                ret = DotDict(json_decode(ret))
                if ret.status == ErrorCode.SUCCESS:
                    self.db.execute("UPDATE T_TERMINAL_INFO"
                                    "  SET msgid = %s"
                                    "  WHERE mobile = %s",
                                    ret['msgid'], data.tmobile)
                else:
                    logging.error("[UWEB] Send %s to terminal %s failed.", 
                                  register_sms, data.tmobile)
            else:
                logging.error("[UWEB] Send %s to terminal %s failed.", 
                              register_sms, data.tmobile)

            # NOTE: add user
            user_info = dict(umobile=umobile,
                             password='111111',
                             uname=umobile)
            add_user(user_info, self.db, self.redis)

            self.write_ret(status)
        except Exception as e:
            logging.exception("[UWEB] Update terminal info failed. cid:%s, Exception: %s",
                              self.current_user.cid, e.args)
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)

    @authenticated
    @tornado.web.removeslash
    def delete(self):
        """Delete a terminal.
        """
        try:
            status = ErrorCode.SUCCESS
            tid = self.get_argument('tid', None)
            flag = self.get_argument('flag', 0)
            logging.info("[UWEB] Corp delete terminal request. tid: %s, flag: %s, cid: %s",
                         tid, flag, self.current_user.cid)

            terminal = QueryHelper.get_available_terminal(tid, self.db)
            if not terminal:
                logging.error("[UWEB] The terminal with tid: %s does not exist!", 
                              tid)
                status = ErrorCode.TERMINAL_NOT_EXISTED
                self.write_ret(status)
                return

            t_info = QueryHelper.get_terminal_basic_info(tid, self.db)
            key = get_del_data_key(tid)
            self.redis.set(key, flag)
            biz_type = QueryHelper.get_biz_type_by_tmobile(
                terminal.mobile, self.db)
            if int(biz_type) == UWEB.BIZ_TYPE.YDWS:
                if terminal.login != GATEWAY.TERMINAL_LOGIN.ONLINE:
                    if terminal.mobile == tid:
                        delete_terminal(tid, self.db, self.redis)
                    else:
                        status = self.send_jb_sms(
                            terminal.mobile, terminal.owner_mobile, tid)

                    if status == ErrorCode.SUCCESS:
                        WSPushHelper.pushS3(tid, self.db, self.redis, t_info)
                    self.write_ret(status)
                    return
            else:
                delete_terminal(tid, self.db, self.redis)
                if status == ErrorCode.SUCCESS:
                    WSPushHelper.pushS3(tid, self.db, self.redis, t_info)
                self.write_ret(status)
                return

            # unbind terminal
            seq = str(int(time.time() * 1000))[-4:]
            args = DotDict(seq=seq,
                           tid=tid)
            response = GFSenderHelper.forward(GFSenderHelper.URLS.UNBIND, args)
            response = json_decode(response)
            logging.info(
                "[UWEB] UNBind terminal: %s, response: %s", tid, response)
            if response['success'] == ErrorCode.SUCCESS:
                logging.info("[UWEB] uid:%s, tid: %s, tmobile:%s GPRS unbind successfully",
                             self.current_user.uid, tid, terminal.mobile)
            else:
                status = response['success']
                # unbind failed. clear sessionID for relogin, then unbind it
                # again
                clear_sessionID(self.redis, tid)
                logging.error('[UWEB] uid:%s, tid: %s, tmobile:%s GPRS unbind failed, message: %s, send JB sms...',
                              self.current_user.uid, tid, terminal.mobile,
                              ErrorCode.ERROR_MESSAGE[status])
                status = self.send_jb_sms(
                    terminal.mobile, terminal.owner_mobile, tid)

            if status == ErrorCode.SUCCESS:
                WSPushHelper.pushS3(tid, self.db, self.redis, t_info)
            self.write_ret(status)
        except Exception as e:
            logging.exception("[UWEB] Delete terminal failed. cid: %s, Exception: %s",
                              self.current_user.cid, e.args)
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)
