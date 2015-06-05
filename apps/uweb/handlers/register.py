# -*- coding: utf-8 -*-

"""This module is designed for registering terminal.
"""

import logging
import random
import string
import time
import hashlib
import re

from tornado.escape import json_decode
import tornado.web

from utils.misc import get_captcha_key
from utils.misc import get_date_from_utc, start_end_of_day
from utils.checker import check_zs_phone
from utils.dotdict import DotDict
from utils.public import delete_terminal, notify_maintainer
from helpers.smshelper import SMSHelper
from helpers.queryhelper import QueryHelper
from helpers.confhelper import ConfHelper

from base import BaseHandler
from codes.errorcode import ErrorCode
from codes.smscode import SMSCode
from constants import UWEB


class RegisterBrowserHandler(BaseHandler):

    @tornado.web.removeslash
    def get(self):
        """Jump to register.html.
        """
        self.render('register.html')


class RegisterHandler(BaseHandler):

    @tornado.web.removeslash
    def get(self):
        """Send captcha to user's phone through sms.
        """
        status = ErrorCode.SUCCESS
        try:
            umobile = self.get_argument('umobile', '')
            tmobile = self.get_argument('tmobile', '')
            remote_ip = self.request.remote_ip

            captcha_image = self.get_argument('captcha_img', '')
            captchahash = self.get_secure_cookie("captchahash_image")

            logging.info("[UWEB] Get captcha-sms request. umobile:%s, tmobile: %s, captcha_img: %s",
                         umobile, tmobile, captcha_image)

            # NOTE: check captcha-sms for brower
            from_brower = False
            if self.request.headers.get('User-Agent', None):
                user_agent = self.request.headers.get('User-Agent').lower()
                if re.search('darwin', user_agent):  # Ios client
                    logging.info("[UWEB] Come from IOS client, do not check captcha-image, User-Agent: %s",
                                 user_agent)
                    from_brower = False
                else:
                    logging.info("[UWEB] Come from browser, check captcha-image, User-Agent: %s",
                                 user_agent)
                    from_brower = True
            else:  # Android client
                from_brower = False
                logging.info(
                    "[UWEB] Come from Android client, do not check captcha-image")

            if from_brower:
                m = hashlib.md5()
                m.update(captcha_image.lower())
                m.update(UWEB.HASH_SALT)
                hash_ = m.hexdigest()
                if hash_.lower() != captchahash.lower():
                    status = ErrorCode.WRONG_CAPTCHA_IMAGE
                    logging.info(
                        "[UWEB] Come from browser, captcha-check failed.")
                    self.write_ret(status)
                    return

                # check tmobile is whitelist or not
                white_list = check_zs_phone(tmobile, self.db)
                if not white_list:
                    logging.info("[UWEB] %s is not whitelist", tmobile)
                    status = ErrorCode.MOBILE_NOT_ORDERED
                    message = ErrorCode.ERROR_MESSAGE[status] % tmobile
                    self.write_ret(status, message=message)
                    return

            # NOTE: check times
            remote_ip_key = "register_remote_ip:%s" % remote_ip
            umobile_key = "register_umobile:%s" % umobile
            remote_ip_times = self.redis.getvalue(remote_ip_key)
            umobile_times = self.redis.getvalue(umobile_key)

            if remote_ip_times is None:
                remote_ip_times = 0

            if umobile_times is None:
                umobile_times = 0

            logging.info("[UWEB] Register. umobile: %s, umobile_times: %s, remote_ip: %s, remote_ip_times: %s",
                         umobile, umobile_times, remote_ip, remote_ip_times)

            # NOTE: In current day, the same remote_ip allows 10 times, the
            # umobile, 3 times
            current_time = int(time.time())
            date = get_date_from_utc(current_time)
            year, month, day = date.year, date.month, date.day
            start_time_, end_time_ = start_end_of_day(
                year=year, month=month, day=day)

            if umobile_times >= 3:  # <= 3 is ok
                status = ErrorCode.REGISTER_EXCESS
            if remote_ip_times >= 10:  # <= 10 is ok
                status = ErrorCode.REGISTER_EXCESS

            if status == ErrorCode.REGISTER_EXCESS:
                body = u'管理员您好：检测到频繁注册，请查看. umobile: %s, umobile_times: %s, remote_ip: %s, remote_ip_times: %s' % (
                    umobile, umobile_times, remote_ip, remote_ip_times)
                #NOTE:hide it briefly
                #notify_maintainer(self.db, self.redis, body, 'register')
                self.write_ret(status)
                return

            psd = ''.join(random.choice(string.digits) for x in range(4))
            captcha_sms = SMSCode.SMS_REG % (psd)
            ret = SMSHelper.send(umobile, captcha_sms)
            ret = DotDict(json_decode(ret))
            if ret.status == ErrorCode.SUCCESS:
                logging.info("[UWEB] Get sms captcha successfully. umobile: %s, captcha: %s.",
                             umobile, psd)
                captcha_key = get_captcha_key(umobile)
                self.redis.setvalue(
                    captcha_key, psd, UWEB.SMS_CAPTCHA_INTERVAL)

                self.redis.set(umobile_key, umobile_times + 1)
                self.redis.expireat(umobile_key, end_time_)
                self.redis.set(remote_ip_key, remote_ip_times + 1)
                self.redis.expireat(remote_ip_key, end_time_)
            else:
                status = ErrorCode.SERVER_BUSY
                logging.error(
                    "[UWEB] Get sms captcha failed. umobile: %s.", umobile)

            self.write_ret(status)
        except Exception as e:
            logging.exception("[UWEB] Get sms captcha failed. umobile:%s. Exception: %s",
                              umobile, e.args)
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)

    @tornado.web.removeslash
    def post(self):
        """Regist a pair of umobile and tmobile.
        """
        status = ErrorCode.SUCCESS
        try:
            data = DotDict(json_decode(self.request.body))
            logging.info("[UWEB] Register request: %s", data)
            umobile = data.umobile
            tmobile = data.tmobile
            captcha = data.captcha
        except Exception as e:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            logging.exception("[UWEB] Invalid data format. Exception: %s",
                              e.args)
            self.write_ret(status)
            return

        try:
            # check tmobile is whitelist or not
            white_list = check_zs_phone(tmobile, self.db)
            if not white_list:
                logging.info("[UWEB] Mobile is not whitelist. tmobile: %s.", tmobile)
                status = ErrorCode.MOBILE_NOT_ORDERED
                message = ErrorCode.ERROR_MESSAGE[status] % tmobile
                self.write_ret(status, message=message)
                return

            captcha_key = get_captcha_key(umobile)
            captcha_old = self.redis.get(captcha_key)
            if captcha_old:
                if captcha == str(captcha_old):
                    terminal = QueryHelper.get_terminal_by_tmobile(
                        tmobile, self.db)
                    if terminal:
                        if terminal.service_status == UWEB.SERVICE_STATUS.TO_BE_UNBIND:
                            # delete to_be_unbind terminal!
                            delete_terminal(terminal.tid, self.db, self.redis)
                        else:
                            status = ErrorCode.TERMINAL_ORDERED
                            logging.info("[UWEB] Regist failed. umobile: %s, tmobile: %s  Message: %s",
                                         umobile, tmobile, ErrorCode.ERROR_MESSAGE[status])
                            self.write_ret(status)
                            return

                    register_sms = SMSCode.SMS_REGISTER % (umobile, tmobile)
                    ret = SMSHelper.send_to_terminal(tmobile, register_sms)
                    ret = DotDict(json_decode(ret))
                    if ret.status == ErrorCode.SUCCESS:
                        logging.info("[UWEB] Regist successfully. umobile: %s, tmobile: %s ",
                                     umobile, tmobile)
                        self.redis.delete(captcha_key)
                    else:
                        status = ErrorCode.REGISTER_FAILED
                        logging.error("[UWEB] Regist failed. umobile: %s, tmobile: %s. Message: %s",
                                      umobile, tmobile, ErrorCode.ERROR_MESSAGE[status])
                else:
                    status = ErrorCode.WRONG_CAPTCHA
                    logging.error("[UWEB] Regist failed. umobile: %s, captcha: %s, captcha_old: %s, Message: %s",
                                  umobile, captcha, captcha_old, ErrorCode.ERROR_MESSAGE[status])
            else:
                status = ErrorCode.NO_CAPTCHA
                logging.error("[UWEB] Register failed. umobile: %s, captcha: %s, Message: %s",
                              umobile, captcha, ErrorCode.ERROR_MESSAGE[status])
            self.write_ret(status)
        except Exception as e:
            logging.exception("[UWEB] Register failed. umobile: %s tmobile: %s , Exception: %s",
                              umobile, tmobile, e.args)
            status = ErrorCode.REGISTER_FAILED
            self.write_ret(status)


class ReRegisterHandler(BaseHandler):

    @tornado.web.removeslash
    def post(self):
        """Reregist a pair of umobile and tmobile.

        Send sms to terminal.
        """
        status = ErrorCode.SUCCESS
        try:
            data = DotDict(json_decode(self.request.body))
            logging.info("[UWEB] Register request: %s", data)
        except Exception as e:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            self.write_ret(status)
            return

        try:
            tmobile = data.tmobile
            user = QueryHelper.get_user_by_tmobile(tmobile, self.db)
            if user:
                umobile = user.owner_mobile
                terminal = QueryHelper.get_terminal_by_tmobile(
                    tmobile, self.db)
                if int(terminal.biz_type) == UWEB.BIZ_TYPE.YDWS:
                    register_sms = SMSCode.SMS_REGISTER % (umobile, tmobile)
                    ret = SMSHelper.send_to_terminal(tmobile, register_sms)
                else:
                    activation_code = QueryHelper.get_activation_code(self.db)
                    register_sms = SMSCode.SMS_REGISTER_YDWQ % (
                        ConfHelper.UWEB_CONF.url_out, activation_code)
                    ret = SMSHelper.send(tmobile, register_sms)

                ret = DotDict(json_decode(ret))
                if ret.status == ErrorCode.SUCCESS:
                    logging.info("[UWEB] Reregist successfully. umobile: %s, tmobile: %s .",
                                 umobile, tmobile)
                else:
                    status = ErrorCode.REGISTER_FAILED
                    logging.error("[UWEB] Reregister failed. umobile: %s, tmobile: %s. Message: %s",
                                  umobile, tmobile, ErrorCode.ERROR_MESSAGE[status])
            else:
                logging.exception("[UWEB] Terminal has no user, ignore it. tmobile: %s. ",
                                  tmobile)
            self.write_ret(status)
        except Exception as e:
            logging.exception("[UWEB] Reregister failed. tmobile: %s , Exception: %s",
                              tmobile, e.args)
            status = ErrorCode.REGISTER_FAILED
            self.write_ret(status)
