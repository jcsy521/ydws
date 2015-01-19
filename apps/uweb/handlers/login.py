# -*- coding: utf-8 -*-

"""This module is designed for log-in.
"""

import hashlib
import time
import logging
from hashlib import md5
import base64

import tornado.web
from tornado.escape import json_encode, json_decode

from utils.dotdict import DotDict
from utils.misc import (get_ios_push_list_key, get_ios_id_key, get_ios_badge_key,
                        get_android_push_list_key, get_terminal_info_key, get_location_key, 
                        get_lastinfo_time_key, DUMMY_IDS)
from utils.checker import check_sql_injection, check_phone
from utils.public import (get_group_info_by_tid, update_mannual_status,
                          get_push_key, record_login_user)
from codes.errorcode import ErrorCode
from constants import UWEB, EVENTER, GATEWAY
from helpers.notifyhelper import NotifyHelper
from helpers.wspushhelper import WSPushHelper
from helpers.queryhelper import QueryHelper
from helpers.lbmphelper import get_locations_with_clatlon
from helpers.downloadhelper import get_version_info
from helpers.confhelper import ConfHelper

from base import BaseHandler, authenticated
from mixin.avatar import AvatarMixin
from mixin.login import LoginMixin


class LoginHandler(BaseHandler, LoginMixin):

    @tornado.web.removeslash
    def get(self):
        self.render("login.html",
                    username='',
                    password='',
                    user_type=UWEB.USER_TYPE.PERSON,
                    message=None,
                    message_captcha=None)

    @tornado.web.removeslash
    def post(self):
        """We store cid, oid, uid,tid and sim in the cookie to
        authenticate the user.
        """
        username_ = self.get_argument("username", "")
        username = base64.b64decode(username_)[128:] if len(username_) > 128 else username_
        password_ = self.get_argument("password", "")
        password = base64.b64decode(password_)[128:] if len(password_) > 128 else password_
        captcha_ = self.get_argument("captcha", "")
        captcha = base64.b64decode(captcha_)[128:] if len(captcha_) > 128 else captcha_

        user_type = self.get_argument("user_type", UWEB.USER_TYPE.PERSON)
        # NOTE: Get captchahash from cookie
        captchahash = self.get_secure_cookie("captchahash")

        logging.info("[UWEB] Browser login request, username: %s, password: %s, "
                     " user_type: %s, catpcha: %s, captchahash: %s", 
                     username, password, user_type, captcha, captchahash)

        # must check username and password avoid sql injection.
        if not (username.isalnum() and password.isalnum()):
            self.render("login.html",
                        username='',
                        password='',
                        user_type=user_type,
                        message_captcha=None,
                        message=ErrorCode.ERROR_MESSAGE[ErrorCode.ILLEGAL_LABEL])
            return

        m = hashlib.md5()
        m.update(captcha.lower())
        m.update(UWEB.HASH_SALT)
        hash_ = m.hexdigest()

        if hash_.lower() != captchahash.lower():
            self.render("login.html",
                        username=username,
                        password=password,
                        user_type=user_type,
                        message=None,
                        message_captcha=ErrorCode.ERROR_MESSAGE[ErrorCode.WRONG_CAPTCHA])
            return

        # check the user, return uid, tid, sim and status
        cid, oid, uid, terminals, _user_type, status = self.login_passwd_auth(
            username, password, user_type)
        if status == ErrorCode.SUCCESS:
            # role: 0: person; 1: operator; 2: enterprise
            # method 0: web; 1: android; 2: ios
            role = None
            user_id = None
            if _user_type == UWEB.USER_TYPE.PERSON:
                role = 0
                user_id = uid
            elif _user_type == UWEB.USER_TYPE.OPERATOR:
                role = 1
                user_id = oid
            elif _user_type == UWEB.USER_TYPE.CORP:
                role = 2
                user_id = cid
            else:
                logging.error("[UWEB] invalid user_type: %s", _user_type)
                pass

            if (role is not None) and (user_id is not None):
                # NOTE: keep the login log
                login_info = dict(uid=user_id,
                                  role=role,
                                  method=0)
                record_login_user(login_info, self.db)

            # keep current_user in cookie
            self.bookkeep(dict(cid=cid,
                               oid=oid,
                               uid=uid if uid else cid,
                               tid=terminals[0].tid,
                               sim=terminals[0].sim))
            # keep client_id in cookie
            self.set_client_id(username)
            user_info = QueryHelper.get_user_by_uid(uid, self.db)
            if user_info:
                # NOTE: if alias is null, provide cnum or sim instead
                for terminal in terminals:
                    terminal['alias'] = QueryHelper.get_alias_by_tid(
                        terminal.tid, self.redis, self.db)
                self.login_sms_remind(
                    uid, user_info.mobile, terminals, login="WEB")
            else:
                # corp maybe has no user
                pass

            #NOTE：clear cookies
            self.clear_cookie('captchahash')
            self.clear_cookie('captchahash_sms')
            self.clear_cookie('bdshare_firstime')
            self.clear_cookie('USERCURRENTROLE')
            self.redirect(self.get_argument("next", "/index"))
        else:
            logging.info("[UWEB] username: %s login failed, message: %s",
                         username, ErrorCode.ERROR_MESSAGE[status])
            self.render("login.html",
                        username=username,
                        password=password,
                        user_type=user_type,
                        message_captcha=None,
                        message=ErrorCode.ERROR_MESSAGE[status])


class LoginTestHandler(BaseHandler, LoginMixin):

    @tornado.web.removeslash
    def post(self):
        """We store cid, oid, uid, tid and sim in the cookie to
        authenticate the user.
        """
        logging.info("[UWEB] Browser login test")
        cid = UWEB.DUMMY_CID
        oid = UWEB.DUMMY_OID
        uid = ConfHelper.UWEB_CONF.test_uid
        tid = ConfHelper.UWEB_CONF.test_tid
        sim = ConfHelper.UWEB_CONF.test_sim
        self.bookkeep(dict(cid=cid,
                           oid=oid,
                           uid=uid,
                           tid=tid,
                           sim=sim))
        self.clear_cookie('bdshare_firstime')
        self.clear_cookie('captchahash')
        self.clear_cookie('USERCURRENTROLE')
        self.redirect('/index')
        # self.redirect(self.get_argument("next","/"))


class IOSHandler(BaseHandler, LoginMixin, AvatarMixin):

    @tornado.web.removeslash
    def post(self):
        username = self.get_argument("username")
        password = self.get_argument("password")
        iosid = self.get_argument("iosid", '')
        user_type = self.get_argument("user_type", UWEB.USER_TYPE.PERSON)
        biz_type = self.get_argument("biz_type", UWEB.BIZ_TYPE.YDWS)
        versionname = self.get_argument("versionname", "")
        version_type = int(self.get_argument("version_type", 0))
        logging.info("[UWEB] IOS login request, username: %s, password: %s, iosid: %s, user_type: %s",
                     username, password, iosid, user_type)
        # must check username and password avoid sql injection.
        if not (username.isalnum() and password.isalnum()):
            status = ErrorCode.ILLEGAL_LABEL
            self.write_ret(status)
            return

        # check the user, return uid, tid, sim and status
        cid, oid, uid, terminals, user_type, status = self.login_passwd_auth(
            username, password, user_type)
        logging.info("[UWEB] Login auth, cid:%s, oid:%s, uid:%s, user_type:%s", 
                     cid, oid, uid, user_type)
        if status == ErrorCode.SUCCESS:
            # keep the login log
            login_info = dict(uid=uid,
                              role=0,
                              method=2,
                              versionname=versionname)
            record_login_user(login_info, self.db)

            self.bookkeep(dict(cid=cid,
                               oid=oid,
                               uid=uid,
                               tid=terminals[0].tid,
                               sim=terminals[0].sim))
            user_info = QueryHelper.get_user_by_uid(uid, self.db)

            # NOTE: add cars_info, it's same as lastinfo
            cars_info = {}

            if user_type == UWEB.USER_TYPE.PERSON:
                terminals = QueryHelper.get_terminals_by_uid(uid, biz_type, self.db)
            elif user_type == UWEB.USER_TYPE.OPERATOR:
                terminals = QueryHelper.get_terminals_by_oid(oid, biz_type, self.db)
            elif user_type == UWEB.USER_TYPE.CORP:
                terminals = QueryHelper.get_terminals_by_cid(cid, biz_type, self.db)
            else:
                logging.error("[UWEB] Invalid user_type: %s", user_type)

            for terminal in terminals:
                # 1: get terminal
                tid = terminal.tid

                group_info = get_group_info_by_tid(self.db, tid)

                terminal_info_key = get_terminal_info_key(tid)
                terminal_cache = self.redis.getvalue(terminal_info_key)
                # NOTE: the latest gps, gsm, pbat kept in redis
                if terminal_cache:
                    terminal['gps'] = terminal_cache['gps']
                    terminal['gsm'] = terminal_cache['gsm']
                    terminal['pbat'] = terminal_cache['pbat']

                mobile = terminal['mobile']
                terminal['keys_num'] = 0
                if terminal['login'] == GATEWAY.TERMINAL_LOGIN.SLEEP:
                    terminal['login'] = GATEWAY.TERMINAL_LOGIN.ONLINE
                # NOTE: if alias is null, provide cnum or sim instead
                terminal['alias'] = QueryHelper.get_alias_by_tid(
                    tid, self.redis, self.db)
                fobs = self.db.query("SELECT fobid FROM T_FOB"
                                     "  WHERE tid = %s", tid)
                terminal['fob_list'] = [fob.fobid for fob in fobs]
                terminal['sim'] = terminal['mobile']

                # 2: get location
                location = QueryHelper.get_location_info(tid, self.db, self.redis)
                if location and not (location.clatitude or location.clongitude):
                    location_key = get_location_key(str(tid))
                    locations = [location, ]
                    locations = get_locations_with_clatlon(locations, self.db)
                    location = locations[0]
                    self.redis.setvalue(
                        location_key, location, EVENTER.LOCATION_EXPIRY)

                if location and location['name'] is None:
                    location['name'] = ''

                avatar_name, avatar_path, avatar_full_path, avatar_time = self.get_avatar_info(mobile)
                service_status = QueryHelper.get_service_status_by_tmobile(self.db, mobile)
                car_dct = {}

                if location and location['type'] == 1:  # cellid
                    location['locate_error'] = 500  # mile
                car_info = dict(defend_status=terminal['defend_status'] if terminal['defend_status'] is not None else 1,
                                service_status=service_status,
                                mannual_status=terminal['mannual_status'] if terminal['mannual_status'] is not None else 1,
                                fob_status=terminal['fob_status'] if terminal['fob_status'] is not None else 0,
                                timestamp=location['timestamp'] if location else 0,
                                speed=location.speed if location else 0,
                                # NOTE: degree's type is Decimal, float() it before json_encode
                                degree=float(location.degree) if location else 0.00,
                                locate_error=location.get('locate_error', 20) if location else 20,
                                bt_name=terminal['bt_name'] if terminal.get('bt_name', None) is not None else '',
                                bt_mac=terminal['bt_mac'] if terminal.get('bt_mac', None) is not None else '',
                                dev_type=terminal['dev_type'] if terminal.get('dev_type', None) is not None else 'A',
                                name=location.name if location else '',
                                type=location.type if location else 1,
                                latitude=location['latitude'] if location else 0,
                                longitude=location['longitude'] if location else 0,
                                clatitude=location['clatitude'] if location else 0,
                                clongitude=location['clongitude'] if location else 0,
                                login=terminal['login'] if terminal['login'] is not None else 0,
                                gps=terminal['gps'] if terminal['gps'] is not None else 0,
                                gsm=terminal['gsm'] if terminal['gsm'] is not None else 0,
                                pbat=terminal['pbat'] if terminal['pbat'] is not None else 0,
                                mobile=terminal['mobile'],
                                owner_mobile=terminal['owner_mobile'],
                                alias=terminal['alias'],
                                #keys_num=terminal['keys_num'] if terminal['keys_num'] is not None else 0,
                                keys_num=0,
                                group_id=group_info['group_id'],
                                group_name=group_info['group_name'],
                                icon_type=terminal['icon_type'],
                                avatar_path=avatar_path,
                                avatar_time=avatar_time,
                                fob_list=terminal['fob_list'] if terminal['fob_list'] else [])

                car_dct[tid] = car_info
                cars_info.update(car_dct)

            # uid --> iosid_push_list
            # check iosid whether exists in a old ios_push_list
            old_ios_push_list_key = self.redis.get(iosid)
            if old_ios_push_list_key:
                old_ios_push_list = self.redis.getvalue(old_ios_push_list_key)
                if not isinstance(old_ios_push_list, list):
                    self.redis.delete(old_ios_push_list_key)
                    old_ios_push_list = []
                if old_ios_push_list and (iosid in old_ios_push_list):
                    logging.info("[UWEB] iosid:%s has existed in a old_ios_push_list: %s, so remove iosid from the list.",
                                 iosid, old_ios_push_list)
                    old_ios_push_list.remove(iosid)
                    self.redis.set(old_ios_push_list_key, old_ios_push_list)

            ios_push_list_key = get_ios_push_list_key(uid)
            ios_push_list = self.redis.getvalue(ios_push_list_key)
            ios_push_list = ios_push_list if ios_push_list else []
            if iosid not in ios_push_list:
                ios_push_list.append(iosid)
            self.redis.set(ios_push_list_key, ios_push_list)
            self.redis.set(iosid, ios_push_list_key)
            ios_badge_key = get_ios_badge_key(iosid)
            self.redis.setvalue(ios_badge_key, 0, UWEB.IOS_ID_INTERVAL)
            logging.info("[UWEB] username %s, ios_push_lst: %s", username, ios_push_list)

            if user_info:
                self.login_sms_remind(uid, user_info.mobile, terminals, login="IOS")
            else:
                pass  # corp maybe no user_info

            push = dict(id='',
                        key='')
            json_data = WSPushHelper.register_wspush(uid, self.redis)
            if json_data:
                data = json_data['data']
                id = data.get('push_id', '')
                key = data.get('psd', '')
                push['id'] = id
                push['key'] = key

            if version_type >= 1:
                terminals = []
                for k, v in cars_info.iteritems():
                    v.update({'tid': k})
                    terminals.append(v)

                self.write_ret(status,
                               dict_=DotDict(wspush=push,
                                             name=user_info.name if user_info else username,
                                             user_type=user_type,
                                             terminals=terminals))
            else:
                self.write_ret(status,
                               dict_=DotDict(wspush=push,
                                             name=user_info.name if user_info else username,
                                             user_type=user_type,
                                             cars_info=cars_info,
                                             cars=terminals))
        else:
            logging.info("[UWEB] username: %s login failed, message: %s",
                         username, ErrorCode.ERROR_MESSAGE[status])
            self.write_ret(status)


class IOSLoginTestHandler(BaseHandler, LoginMixin, AvatarMixin):

    @tornado.web.removeslash
    def post(self):
        logging.info("[UWEB] IOS login test")
        status = ErrorCode.SUCCESS
        cid = UWEB.DUMMY_CID
        oid = UWEB.DUMMY_OID
        uid = ConfHelper.UWEB_CONF.test_uid
        tid = ConfHelper.UWEB_CONF.test_tid
        sim = ConfHelper.UWEB_CONF.test_sim
        version_type = int(self.get_argument("version_type", 0))
        biz_type = UWEB.BIZ_TYPE.YDWS

        self.bookkeep(dict(cid=cid,
                           oid=oid,
                           uid=uid,
                           tid=tid,
                           sim=sim))
        user_info = QueryHelper.get_user_by_uid(uid, self.db)

        # NOTE: add cars_info, it's same as lastinfo
        cars_info = {}

        # NOTE: the code here is ugly, maybe some day the unwanted field is
        # removed, the code canbe refactored.

        terminals = QueryHelper.get_terminals_by_uid(uid, biz_type, self.db)
        for terminal in terminals:
            # 1: get terminal
            tid = terminal.tid

            group_info = get_group_info_by_tid(self.db, tid)

            terminal_info_key = get_terminal_info_key(tid)
            terminal_cache = self.redis.getvalue(terminal_info_key)
            if terminal_cache:
                terminal['gps'] = terminal_cache['gps']
                terminal['gsm'] = terminal_cache['gsm']
                terminal['pbat'] = terminal_cache['pbat']

            mobile = terminal['mobile']
            terminal['keys_num'] = 0
            if terminal['login'] == GATEWAY.TERMINAL_LOGIN.SLEEP:
                terminal['login'] = GATEWAY.TERMINAL_LOGIN.ONLINE
            # NOTE: if alias is null, provide cnum or sim instead
            terminal['alias'] = QueryHelper.get_alias_by_tid(tid, self.redis, self.db)
            fobs = self.db.query("SELECT fobid FROM T_FOB"
                                 "  WHERE tid = %s", tid)
            terminal['fob_list'] = [fob.fobid for fob in fobs]
            terminal['sim'] = terminal['mobile']

            # 2: get location
            location = QueryHelper.get_location_info(tid, self.db, self.redis)
            if location and not (location.clatitude or location.clongitude):
                location_key = get_location_key(str(tid))
                locations = [location, ]
                locations = get_locations_with_clatlon(locations, self.db)
                location = locations[0]
                self.redis.setvalue(location_key, location, EVENTER.LOCATION_EXPIRY)

            if location and location['name'] is None:
                location['name'] = ''

            avatar_name, avatar_path, avatar_full_path, avatar_time = self.get_avatar_info(mobile)

            service_status = QueryHelper.get_service_status_by_tmobile(self.db, mobile)
            car_dct = {}
            if location and location['type'] == 1:  # cellid
                location['locate_error'] = 500  # mile

            car_info = dict(defend_status=terminal['defend_status'] if terminal['defend_status'] is not None else 1,
                            service_status=service_status,
                            mannual_status=terminal['mannual_status'] if terminal['mannual_status'] is not None else 1,
                            fob_status=terminal['fob_status'] if terminal['fob_status'] is not None else 0,
                            timestamp=location['timestamp'] if location else 0,
                            speed=location.speed if location else 0,
                            # NOTE: degree's type is Decimal, float() it before json_encode
                            degree=float(location.degree) if location else 0.00,
                            locate_error=location.get('locate_error', 20) if location else 20,
                            bt_name=terminal['bt_name'] if terminal.get('bt_name', None) is not None else '',
                            bt_mac=terminal['bt_mac'] if terminal.get('bt_mac', None) is not None else '',
                            dev_type=terminal['dev_type'] if terminal.get('dev_type', None) is not None else 'A',
                            name=location.name if location else '',
                            type=location.type if location else 1,
                            latitude=location['latitude'] if location else 0,
                            longitude=location['longitude'] if location else 0,
                            clatitude=location['clatitude'] if location else 0,
                            clongitude=location['clongitude'] if location else 0,
                            login=terminal['login'] if terminal['login'] is not None else 0,
                            gps=terminal['gps'] if terminal['gps'] is not None else 0,
                            gsm=terminal['gsm'] if terminal['gsm'] is not None else 0,
                            pbat=terminal['pbat'] if terminal['pbat'] is not None else 0,
                            mobile=terminal['mobile'],
                            owner_mobile=terminal['owner_mobile'],
                            alias=terminal['alias'],
                            #keys_num=terminal['keys_num'] if terminal['keys_num'] is not None else 0,
                            keys_num=0,
                            group_id=group_info['group_id'],
                            group_name=group_info['group_name'],
                            icon_type=terminal['icon_type'],
                            avatar_path=avatar_path,
                            avatar_time=avatar_time,
                            fob_list=terminal['fob_list'] if terminal['fob_list'] else [])

            car_dct[tid] = car_info
            cars_info.update(car_dct)

        if version_type >= 1:
            terminals = []
            for k, v in cars_info.iteritems():
                v.update({'tid': k})
                terminals.append(v)
            self.write_ret(status,
                           dict_=DotDict(name=user_info.name if user_info else username,
                                         user_type=UWEB.USER_TYPE.PERSON,
                                         terminals=terminals))
        else:
            self.write_ret(status,
                           dict_=DotDict(name=user_info.name if user_info else username,
                                         user_type=UWEB.USER_TYPE.PERSON,
                                         cars_info=cars_info,
                                         cars=terminals))


class AndroidHandler(BaseHandler, LoginMixin, AvatarMixin):

    @tornado.web.removeslash
    def post(self):
        username = self.get_argument("username")
        password = self.get_argument("password")
        user_type = self.get_argument("user_type", UWEB.USER_TYPE.PERSON)
        biz_type = self.get_argument("biz_type", UWEB.BIZ_TYPE.YDWS)
        devid = self.get_argument("devid", "")
        versionname = self.get_argument("versionname", "")
        version_type = int(self.get_argument("version_type", 0))
        logging.info("[UWEB] Android login request, username: %s, password: %s, user_type: %s, devid: %s",
                     username, password, user_type, devid)
        # must check username and password avoid sql injection.
        if not (username.isalnum() and password.isalnum()):
            status = ErrorCode.ILLEGAL_LABEL
            self.write_ret(status)
            return

        # check the user, return uid, tid, sim and status
        cid, oid, uid, terminals, user_type, status = self.login_passwd_auth(username, password, user_type)
        logging.info(
            "[UWEB] Login auth, cid:%s, oid:%s, uid:%s, user_type:%s", cid, oid, uid, user_type)
        if status == ErrorCode.SUCCESS:
            # role: 0: person; 1: operator; 2: enterprise
            # method 0: web; 1: android; 2: ios
            # NOTE: keep the login log
            login_info = dict(uid=uid,
                              role=0,
                              method=1,
                              versionname=versionname)
            record_login_user(login_info, self.db)

            self.bookkeep(dict(cid=cid,
                               oid=oid,
                               uid=uid,
                               tid=terminals[0].tid,
                               sim=terminals[0].sim))

            user_info = QueryHelper.get_user_by_uid(uid, self.db)

            # NOTE: add cars_info, it's same as lastinfo
            cars_info = {}

            if user_type == UWEB.USER_TYPE.PERSON:
                terminals = QueryHelper.get_terminals_by_uid(uid, biz_type, self.db)
            elif user_type == UWEB.USER_TYPE.OPERATOR:
                terminals = QueryHelper.get_terminals_by_oid(oid, biz_type, self.db)
            elif user_type == UWEB.USER_TYPE.CORP:
                terminals = QueryHelper.get_terminals_by_cid(cid, biz_type, self.db)
            else:
                logging.error("[UWEB] Invalid user_type: %s", user_type)

            for terminal in terminals:
                # 1: get terminal
                tid = terminal.tid

                group_info = get_group_info_by_tid(self.db, tid)

                terminal_info_key = get_terminal_info_key(tid)
                terminal_cache = self.redis.getvalue(terminal_info_key)
                if terminal_cache:
                    terminal['gps'] = terminal_cache['gps']
                    terminal['gsm'] = terminal_cache['gsm']
                    terminal['pbat'] = terminal_cache['pbat']

                mobile = terminal['mobile']
                terminal['keys_num'] = 0
                if terminal['login'] == GATEWAY.TERMINAL_LOGIN.SLEEP:
                    terminal['login'] = GATEWAY.TERMINAL_LOGIN.ONLINE
                # NOTE: if alias is null, provide cnum or sim instead
                terminal['alias'] = QueryHelper.get_alias_by_tid(
                    tid, self.redis, self.db)
                fobs = self.db.query("SELECT fobid FROM T_FOB"
                                     "  WHERE tid = %s", tid)
                terminal['fob_list'] = [fob.fobid for fob in fobs]
                terminal['sim'] = terminal['mobile']

                # 2: get location
                location = QueryHelper.get_location_info(tid, self.db, self.redis)
                if location and not (location.clatitude or location.clongitude):
                    location_key = get_location_key(str(tid))
                    locations = [location, ]
                    locations = get_locations_with_clatlon(locations, self.db)
                    location = locations[0]
                    self.redis.setvalue(location_key, location, EVENTER.LOCATION_EXPIRY)

                if location and location['name'] is None:
                    location['name'] = ''

                avatar_name, avatar_path, avatar_full_path, avatar_time = self.get_avatar_info(mobile)

                service_status = QueryHelper.get_service_status_by_tmobile(
                    self.db, mobile)
                car_dct = {}

                if location and location['type'] == 1:  # cellid
                    location['locate_error'] = 500  # mile

                car_info = dict(defend_status=terminal['defend_status'] if terminal['defend_status'] is not None else 1,
                            service_status=service_status,
                            mannual_status=terminal['mannual_status'] if terminal['mannual_status'] is not None else 1,
                            fob_status=terminal['fob_status'] if terminal['fob_status'] is not None else 0,
                            timestamp=location['timestamp'] if location else 0,
                            speed=location.speed if location else 0,
                            # NOTE: degree's type is Decimal, float() it before json_encode
                            degree=float(location.degree) if location else 0.00,
                            locate_error=location.get('locate_error', 20) if location else 20,
                            bt_name=terminal['bt_name'] if terminal.get('bt_name', None) is not None else '',
                            bt_mac=terminal['bt_mac'] if terminal.get('bt_mac', None) is not None else '',
                            dev_type=terminal['dev_type'] if terminal.get('dev_type', None) is not None else 'A',
                            name=location.name if location else '',
                            type=location.type if location else 1,
                            latitude=location['latitude'] if location else 0,
                            longitude=location['longitude'] if location else 0,
                            clatitude=location['clatitude'] if location else 0,
                            clongitude=location['clongitude'] if location else 0,
                            login=terminal['login'] if terminal['login'] is not None else 0,
                            gps=terminal['gps'] if terminal['gps'] is not None else 0,
                            gsm=terminal['gsm'] if terminal['gsm'] is not None else 0,
                            pbat=terminal['pbat'] if terminal['pbat'] is not None else 0,
                            mobile=terminal['mobile'],
                            owner_mobile=terminal['owner_mobile'],
                            alias=terminal['alias'],
                            #keys_num=terminal['keys_num'] if terminal['keys_num'] is not None else 0,
                            keys_num=0,
                            group_id=group_info['group_id'],
                            group_name=group_info['group_name'],
                            icon_type=terminal['icon_type'],
                            avatar_path=avatar_path,
                            avatar_time=avatar_time,
                            fob_list=terminal['fob_list'] if terminal['fob_list'] else [])
             
                car_dct[tid] = car_info
                cars_info.update(car_dct)

            #push_info = NotifyHelper.get_push_info()

            push_id = devid if devid else uid
            push_key = NotifyHelper.get_push_key(push_id, self.redis)

            version_info = get_version_info("android")
            lastinfo_time_key = get_lastinfo_time_key(uid)
            lastinfo_time = self.redis.getvalue(lastinfo_time_key)

            # uid --> android_push_list
            # check push_id whether exists in a old android_push_list
            old_android_push_list_key = self.redis.get(push_id)
            if old_android_push_list_key:
                old_android_push_list = self.redis.getvalue(
                    old_android_push_list_key)
                if not isinstance(old_android_push_list, list):
                    self.redis.delete(old_android_push_list_key)
                    old_android_push_list = []
                if old_android_push_list and (push_id in old_android_push_list):
                    logging.info("[UWEB] push_id:%s has existed in a old_android_push_list: %s, so remove push_id from the list.",
                                 push_id, old_android_push_list)
                    old_android_push_list.remove(push_id)
                    self.redis.set(old_android_push_list_key, old_android_push_list)

            android_push_list_key = get_android_push_list_key(uid)
            android_push_list = self.redis.getvalue(android_push_list_key)
            android_push_list = android_push_list if android_push_list else []
            if push_id not in android_push_list:
                android_push_list.append(push_id)
            self.redis.set(android_push_list_key, android_push_list)
            self.redis.set(push_id, android_push_list_key)
            logging.info("[UWEB] uid: %s, android_push_lst: %s", username, android_push_list)

            if user_info:
                self.login_sms_remind(uid, user_info.mobile, terminals, login="ANDROID")
            else:
                pass  # corp maybe no user_info

            push = dict(id='',
                        key='')
            json_data = WSPushHelper.register_wspush(uid, self.redis)
            data = json_data['data']
            if data:
                id = data.get('push_id', '')
                key = data.get('psd', '')
                push['id'] = id
                push['key'] = key

            if version_type >= 1:
                terminals = []
                for k, v in cars_info.iteritems():
                    v.update({'tid': k})
                    terminals.append(v)

                self.write_ret(status,
                               dict_=DotDict(wspush=push,
                                             push_id=push_id,
                                             push_key=push_key,
                                             name=user_info.name if user_info else username,
                                             user_type=user_type,
                                             terminals=terminals,
                                             lastinfo_time=lastinfo_time,))
            else:
                self.write_ret(status,
                               dict_=DotDict(wspush=push,
                                             push_id=push_id,
                                             # app_key=push_info.app_key,
                                             push_key=push_key,
                                             name=user_info.name if user_info else username,
                                             user_type=user_type,
                                             cars_info=cars_info,
                                             lastinfo_time=lastinfo_time,
                                             cars=terminals))
        else:
            logging.info("[UWEB] username: %s login failed, message: %s",
                         username, ErrorCode.ERROR_MESSAGE[status])
            self.write_ret(status)


class AndroidLoginTestHandler(BaseHandler, LoginMixin, AvatarMixin):

    @tornado.web.removeslash
    def post(self):
        logging.info("[UWEB] Android login test")
        status = ErrorCode.SUCCESS
        cid = UWEB.DUMMY_CID
        oid = UWEB.DUMMY_OID
        uid = ConfHelper.UWEB_CONF.test_uid
        tid = ConfHelper.UWEB_CONF.test_tid
        sim = ConfHelper.UWEB_CONF.test_sim
        version_type = int(self.get_argument("version_type", 0))
        biz_type = UWEB.BIZ_TYPE.YDWS

        self.bookkeep(dict(cid=cid,
                           oid=oid,
                           uid=uid,
                           tid=tid,
                           sim=sim))

        user_info = QueryHelper.get_user_by_uid(uid, self.db)

        # NOTE: add cars_info, it's same as lastinfo
        cars_info = {}

        terminals = QueryHelper.get_terminals_by_uid(uid, biz_type, self.db)
        for terminal in terminals:
            # 1: get terminal
            tid = terminal.tid

            group_info = get_group_info_by_tid(self.db, tid)

            terminal_info_key = get_terminal_info_key(tid)
            terminal_cache = self.redis.getvalue(terminal_info_key)
            if terminal_cache:
                terminal['gps'] = terminal_cache['gps']
                terminal['gsm'] = terminal_cache['gsm']
                terminal['pbat'] = terminal_cache['pbat']

            mobile = terminal['mobile']
            terminal['keys_num'] = 0
            if terminal['login'] == GATEWAY.TERMINAL_LOGIN.SLEEP:
                terminal['login'] = GATEWAY.TERMINAL_LOGIN.ONLINE
            # NOTE: if alias is null, provide cnum or sim instead
            terminal['alias'] = QueryHelper.get_alias_by_tid(
                tid, self.redis, self.db)
            fobs = self.db.query("SELECT fobid FROM T_FOB"
                                 "  WHERE tid = %s", tid)
            terminal['fob_list'] = [fob.fobid for fob in fobs]
            terminal['sim'] = terminal['mobile']

            # 2: get location
            location = QueryHelper.get_location_info(tid, self.db, self.redis)
            if location and not (location.clatitude or location.clongitude):
                location_key = get_location_key(str(tid))
                locations = [location, ]
                locations = get_locations_with_clatlon(locations, self.db)
                location = locations[0]
                self.redis.setvalue(
                    location_key, location, EVENTER.LOCATION_EXPIRY)

            if location and location['name'] is None:
                location['name'] = ''

            avatar_name, avatar_path, avatar_full_path, avatar_time = self.get_avatar_info(
                mobile)
            service_status = QueryHelper.get_service_status_by_tmobile(
                self.db, mobile)
            car_dct = {}
            if location and location['type'] == 1:  # cellid
                location['locate_error'] = 500  # mile

            car_info = dict(defend_status=terminal['defend_status'] if terminal['defend_status'] is not None else 1,
                            service_status=service_status,
                            mannual_status=terminal['mannual_status'] if terminal['mannual_status'] is not None else 1,
                            fob_status=terminal['fob_status'] if terminal['fob_status'] is not None else 0,
                            timestamp=location['timestamp'] if location else 0,
                            speed=location.speed if location else 0,
                            # NOTE: degree's type is Decimal, float() it before json_encode
                            degree=float(location.degree) if location else 0.00,
                            locate_error=location.get('locate_error', 20) if location else 20,
                            bt_name=terminal['bt_name'] if terminal.get('bt_name', None) is not None else '',
                            bt_mac=terminal['bt_mac'] if terminal.get('bt_mac', None) is not None else '',
                            dev_type=terminal['dev_type'] if terminal.get('dev_type', None) is not None else 'A',
                            name=location.name if location else '',
                            type=location.type if location else 1,
                            latitude=location['latitude'] if location else 0,
                            longitude=location['longitude'] if location else 0,
                            clatitude=location['clatitude'] if location else 0,
                            clongitude=location['clongitude'] if location else 0,
                            login=terminal['login'] if terminal['login'] is not None else 0,
                            gps=terminal['gps'] if terminal['gps'] is not None else 0,
                            gsm=terminal['gsm'] if terminal['gsm'] is not None else 0,
                            pbat=terminal['pbat'] if terminal['pbat'] is not None else 0,
                            mobile=terminal['mobile'],
                            owner_mobile=terminal['owner_mobile'],
                            alias=terminal['alias'],
                            #keys_num=terminal['keys_num'] if terminal['keys_num'] is not None else 0,
                            keys_num=0,
                            group_id=group_info['group_id'],
                            group_name=group_info['group_name'],
                            icon_type=terminal['icon_type'],
                            avatar_path=avatar_path,
                            avatar_time=avatar_time,
                            fob_list=terminal['fob_list'] if terminal['fob_list'] else [])

            
            car_dct[tid] = car_info
            cars_info.update(car_dct)

        #push_info = NotifyHelper.get_push_info()

        push_id = uid
        push_key = NotifyHelper.get_push_key(push_id, self.redis)

        version_info = get_version_info("android")
        lastinfo_time_key = get_lastinfo_time_key(uid)
        lastinfo_time = self.redis.getvalue(lastinfo_time_key)

        push = dict(id='',
                    key='')
        t = int(time.time()) * 1000
        push_key = get_push_key(uid, t)
        json_data = WSPushHelper.register_wspush(uid, self.redis)
        data = json_data['data']
        if data:
            id = data.get('push_id', '')
            key = data.get('psd', '')
            push['id'] = id
            push['key'] = key

        if version_type >= 1:
            terminals = []
            for k, v in cars_info.iteritems():
                v.update({'tid': k})
                terminals.append(v)

            self.write_ret(status,
                           dict_=DotDict(wspush=push,
                                         push_id=push_id,
                                         push_key=push_key,
                                         name=user_info.name if user_info else username,
                                         user_type=UWEB.USER_TYPE.PERSON,
                                         lastinfo_time=lastinfo_time,
                                         terminals=terminals))

        else:
            self.write_ret(status,
                           dict_=DotDict(wspush=push,
                                         push_id=push_id,
                                         # app_key=push_info.app_key,
                                         push_key=push_key,
                                         name=user_info.name if user_info else username,
                                         user_type=UWEB.USER_TYPE.PERSON,
                                         cars_info=cars_info,
                                         lastinfo_time=lastinfo_time,
                                         cars=terminals,))


class LogoutHandler(BaseHandler):

    @authenticated
    @tornado.web.removeslash
    def get(self):
        """Clear the cookie and return to login.html."""
        self.clear_cookie(self.app_name)
        self.redirect(self.get_argument("next", "/"))


class IOSLogoutHandler(BaseHandler):

    @authenticated
    @tornado.web.removeslash
    def post(self):
        """Clear the cookie and set defend."""
        try:
            data = DotDict(json_decode(self.request.body))
            iosid = data.get("iosid", "")
            logging.info("[UWEB] logout request: %s, uid: %s",
                         data, self.current_user.uid)
        except:
            self.write_ret(ErrorCode.ILLEGAL_DATA_FORMAT)
            logging.error("[UWEB] illegal format, body:%s", self.request.body)
        else:
            # 1: if there are tids, set defend
            for tid in data.tids:
                update_mannual_status(
                    self.db, self.redis, tid, UWEB.DEFEND_STATUS.YES)

            # 2: remove ios from push_list
            ios_push_list_key = get_ios_push_list_key(self.current_user.uid)
            ios_push_list = self.redis.getvalue(ios_push_list_key)
            ios_push_list = ios_push_list if ios_push_list else []
            if iosid in ios_push_list:
                ios_push_list.remove(iosid)
                self.redis.set(ios_push_list_key, ios_push_list)
            ios_badge_key = get_ios_badge_key(iosid)
            self.redis.delete(ios_badge_key)
            logging.info("[UWEB] uid:%s, ios_push_lst: %s", 
                         self.current_user.uid, ios_push_list)
        finally:
            # 3: clear cookie
            self.clear_cookie(self.app_name)
            self.write_ret(ErrorCode.SUCCESS)


class AndroidLogoutHandler(BaseHandler):

    @authenticated
    @tornado.web.removeslash
    def post(self):
        """Clear the cookie and set defend."""
        try:
            data = DotDict(json_decode(self.request.body))
            devid = data.get("devid", "")
            logging.info("[UWEB] logout request: %s, uid: %s",
                         data, self.current_user.uid)
        except:
            self.write_ret(ErrorCode.ILLEGAL_DATA_FORMAT)
            logging.error("[UWEB] illegal format, body:%s", self.request.body)
        else:
            # 1: if there are tids, set defend
            for tid in data.tids:
                update_mannual_status(self.db, self.redis, tid, UWEB.DEFEND_STATUS.YES)

            # 2: remove devid from android_push_list
            android_push_list_key = get_android_push_list_key(
                self.current_user.uid)
            android_push_list = self.redis.getvalue(android_push_list_key)
            android_push_list = android_push_list if android_push_list else []
            if devid in android_push_list:
                android_push_list.remove(devid)
                self.redis.set(android_push_list_key, android_push_list)
            logging.info("[UWEB] uid:%s, android_push_lst: %s",
                         self.current_user.uid, android_push_list)
        finally:
            # 3: clear cookie
            self.clear_cookie(self.app_name)
            self.write_ret(ErrorCode.SUCCESS)
