# -*- coding: utf-8 -*-

import hashlib
import time
import logging
from hashlib import md5

import tornado.web
from tornado.escape import json_encode, json_decode

from utils.dotdict import DotDict
from utils.misc import get_ios_push_list_key, get_ios_id_key, get_ios_badge_key,\
     get_android_push_list_key, get_terminal_info_key, get_location_key, get_lastinfo_time_key, DUMMY_IDS
from utils.checker import check_sql_injection, check_phone
from utils.public import get_group_info_by_tid
from codes.errorcode import ErrorCode
from constants import UWEB, EVENTER, GATEWAY
from base import BaseHandler, authenticated
from helpers.notifyhelper import NotifyHelper
from helpers.queryhelper import QueryHelper 
from helpers.lbmphelper import get_locations_with_clatlon
from helpers.downloadhelper import get_version_info 
from helpers.confhelper import ConfHelper
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
        username = self.get_argument("username", "")
        password = self.get_argument("password", "")
        captcha = self.get_argument("captcha", "")
        user_type = self.get_argument("user_type", UWEB.USER_TYPE.PERSON)
        captchahash = self.get_argument("captchahash", "")

        logging.info("[UWEB] Browser login request, username: %s, password: %s, user_type: %s", username, password, user_type)

        # must check username and password avoid sql injection.
        if not (username.isalnum() and password.isalnum()):
            self.render("login.html",
                        username='',
                        password='',
                        user_type=user_type,
                        message_captcha=None,
                        message=ErrorCode.ERROR_MESSAGE[ErrorCode.ILLEGAL_LABEL])
            return

        #if not (check_sql_injection(username) and check_sql_injection(password)):
        #    self.render("login.html",
        #                username="",
        #                password="",
        #                user_type=user_type,
        #                message_captcha=None,
        #                message=ErrorCode.ERROR_MESSAGE[ErrorCode.LOGIN_FAILED])
        #    return

        m = hashlib.md5()
        m.update(captcha.lower())
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
        cid, oid, uid, terminals, user_type, status = self.login_passwd_auth(username, password, user_type)
        if status == ErrorCode.SUCCESS: 
            ## role: 0: person; 1: operator; 2: enterprise
            ## method 0: web; 1: android; 2: ios 
            role = None
            user_id = None
            if user_type == UWEB.USER_TYPE.PERSON:
                role = 0
                user_id = uid
            elif user_type == UWEB.USER_TYPE.OPERATOR:
                role = 1
                user_id = oid
            elif user_type == UWEB.USER_TYPE.CORP:
                role = 2
                user_id = cid
            else:
                logging.error("[UWEB] invalid user_type: %s", user_type)
                pass
            if (role is not None) and (user_id is not None):
                # keep the login log
                self.login_log(user_id, role, 0)

            self.bookkeep(dict(cid=cid,
                               oid=oid,
                               uid=uid if uid else cid,
                               tid=terminals[0].tid,
                               sim=terminals[0].sim))
            user_info = QueryHelper.get_user_by_uid(uid, self.db)
            if user_info:
                #NOTE: if alias is null, provide cnum or sim instead
                for terminal in terminals:
                    terminal['alias'] = QueryHelper.get_alias_by_tid(terminal.tid, self.redis, self.db)
                self.login_sms_remind(uid, user_info.mobile, terminals, login="WEB")
            else:
                # corp maybe has no user 
                pass

            self.clear_cookie('captchahash')
            self.redirect(self.get_argument("next","/"))
        else:
            logging.info("[UWEB] username: %s login failed, message: %s", username, ErrorCode.ERROR_MESSAGE[status])
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
        self.clear_cookie('captchahash')
        self.redirect(self.get_argument("next","/"))

class IOSHandler(BaseHandler, LoginMixin, AvatarMixin):

    @tornado.web.removeslash
    def post(self):
        username = self.get_argument("username")
        password = self.get_argument("password")
        iosid = self.get_argument("iosid",'')
        user_type = self.get_argument("user_type", UWEB.USER_TYPE.PERSON)
        biz_type = self.get_argument("biz_type", UWEB.BIZ_TYPE.YDWS)
        versionname = self.get_argument("versionname", "")
        logging.info("[UWEB] IOS login request, username: %s, password: %s, iosid: %s, user_type: %s",
                     username, password, iosid, user_type)
        # must check username and password avoid sql injection.
        if not (username.isalnum() and password.isalnum()):
            status= ErrorCode.ILLEGAL_LABEL
            self.write_ret(status)
            return
        #if not (check_sql_injection(username) and check_sql_injection(password)):
        #    status= ErrorCode.LOGIN_FAILED
        #    self.write_ret(status)
        #    return

        # check the user, return uid, tid, sim and status
        cid, oid, uid, terminals, user_type, status = self.login_passwd_auth(username, password, user_type)
        logging.info("[UWEB] Login auth, cid:%s, oid:%s, uid:%s, user_type:%s", cid, oid, uid, user_type)
        if status == ErrorCode.SUCCESS: 
            # keep the login log
            self.login_log(uid, 0, 2, versionname)
            self.bookkeep(dict(cid=cid,
                               oid=oid,
                               uid=uid,
                               tid=terminals[0].tid,
                               sim=terminals[0].sim))
            user_info = QueryHelper.get_user_by_uid(uid, self.db) 

            # NOTE: add cars_info, it's same as lastinfo
            cars_info = {} 

            #NOTE: the code here is ugly, maybe some day the unwanted field is removed, the code canbe refactored.

            if user_type == UWEB.USER_TYPE.PERSON:
                terminals = self.db.query("SELECT tid, mobile, owner_mobile, login, keys_num"
                                          "    gsm, gps, pbat, login, defend_status,"
                                          "    mannual_status, fob_status, icon_type, bt_name, bt_mac"
                                          "  FROM T_TERMINAL_INFO"
                                          "  WHERE (service_status = %s"
                                          "         OR service_status = %s)"
                                          "    AND biz_type = %s"
                                          "    AND owner_mobile = %s"
                                          "    AND login_permit = 1"
                                          "    ORDER BY LOGIN DESC",
                                          UWEB.SERVICE_STATUS.ON, 
                                          UWEB.SERVICE_STATUS.TO_BE_ACTIVATED,
                                          biz_type,
                                          uid)

            elif user_type == UWEB.USER_TYPE.OPERATOR:
                groups = self.db.query("SELECT group_id FROM T_GROUP_OPERATOR WHERE oper_id = %s", oid)
                gids = [g.group_id for g in groups]
                terminals = self.db.query("SELECT tid, mobile, owner_mobile, login, keys_num"
                                          "    gsm, gps, pbat, login, defend_status,"
                                          "    mannual_status, fob_status, icon_type, bt_name, bt_mac"
                                          "  FROM T_TERMINAL_INFO"
                                          "  WHERE (service_status = %s"
                                          "         OR service_status = %s)"
                                          "    AND biz_type = %s"
                                          "    AND group_id IN %s"
                                          "    ORDER BY LOGIN DESC",
                                          UWEB.SERVICE_STATUS.ON, 
                                          UWEB.SERVICE_STATUS.TO_BE_ACTIVATED,
                                          biz_type,
                                          tuple(DUMMY_IDS + gids))
            elif user_type == UWEB.USER_TYPE.CORP:
                groups = self.db.query("SELECT id gid, name FROM T_GROUP WHERE corp_id = %s", cid)
                gids = [g.gid for g in groups]
                terminals = self.db.query("SELECT tid, mobile, owner_mobile, login, keys_num"
                                          "    gsm, gps, pbat, login, defend_status,"
                                          "    mannual_status, fob_status, icon_type, bt_name, bt_mac"
                                          "  FROM T_TERMINAL_INFO"
                                          "  WHERE (service_status = %s"
                                          "         OR service_status = %s)"
                                          "    AND biz_type = %s"
                                          "    AND group_id IN %s"
                                          "    ORDER BY LOGIN DESC",
                                          UWEB.SERVICE_STATUS.ON, 
                                          UWEB.SERVICE_STATUS.TO_BE_ACTIVATED,
                                          biz_type,
                                          tuple(DUMMY_IDS + gids))
            else:
                logging.error("[UWEB] invalid user_type: %s", user_type)
                pass

            for terminal in terminals:
                # 1: get terminal
                tid = terminal.tid

                group_info = get_group_info_by_tid(self.db, tid)

                terminal_info_key = get_terminal_info_key(tid)
                terminal_cache = self.redis.getvalue(terminal_info_key)
                if terminal_cache:
                    terminal['gps'] =  terminal_cache['gps']
                    terminal['gsm'] =  terminal_cache['gsm']
                    terminal['pbat'] =  terminal_cache['pbat']

                mobile = terminal['mobile'] 
                terminal['keys_num'] = 0
                if terminal['login'] == GATEWAY.TERMINAL_LOGIN.SLEEP:
                    terminal['login'] = GATEWAY.TERMINAL_LOGIN.ONLINE
                #NOTE: if alias is null, provide cnum or sim instead
                terminal['alias'] = QueryHelper.get_alias_by_tid(tid, self.redis, self.db)
                fobs = self.db.query("SELECT fobid FROM T_FOB"
                                     "  WHERE tid = %s", tid)
                terminal['fob_list'] = [fob.fobid for fob in fobs]
                terminal['sim'] = terminal['mobile'] 

                # 2: get location
                location = QueryHelper.get_location_info(tid, self.db, self.redis)
                if location and not (location.clatitude or location.clongitude):
                    location_key = get_location_key(str(tid))
                    locations = [location,] 
                    locations = get_locations_with_clatlon(locations, self.db) 
                    location = locations[0]
                    self.redis.setvalue(location_key, location, EVENTER.LOCATION_EXPIRY)

                if location and location['name'] is None:
                    location['name'] = ''

                avatar_name, avatar_path, avatar_full_path, avatar_time = self.get_avatar_info(mobile)
                service_status = QueryHelper.get_service_status_by_tmobile(self.db, mobile)
                car_dct = {}

                if location and location['type'] == 1: # cellid 
                    location['locate_error'] = 500  # mile
                car_info=dict(defend_status=terminal['defend_status'] if terminal['defend_status'] is not None else 1,
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

                car_dct[tid]=car_info
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
                pass # corp maybe no user_info

            if version_type >= 1:
                terminals = []
                for k, v in cars_info.iteritems():
                    v.update({'tid':k})
                    terminals.append(v)

                self.write_ret(status,
                               dict_=DotDict(name=user_info.name if user_info else username, 
                                             user_type=user_type,
                                             terminals=terminals))
            else:
                self.write_ret(status,
                               dict_=DotDict(name=user_info.name if user_info else username, 
                                             user_type=user_type,
                                             cars_info=cars_info,
                                             cars=terminals))
        else:
            logging.info("[UWEB] username: %s login failed, message: %s", username, ErrorCode.ERROR_MESSAGE[status])
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

        self.bookkeep(dict(cid=cid,
                           oid=oid,
                           uid=uid,
                           tid=tid,
                           sim=sim))
        user_info = QueryHelper.get_user_by_uid(uid, self.db) 

        # NOTE: add cars_info, it's same as lastinfo
        cars_info = {} 

        #NOTE: the code here is ugly, maybe some day the unwanted field is removed, the code canbe refactored.
        terminals = self.db.query("SELECT tid, mobile, owner_mobile, login, keys_num"
                                  "    gsm, gps, pbat, login, defend_status,"
                                  "    mannual_status, fob_status, icon_type, bt_name, bt_mac"
                                  "  FROM T_TERMINAL_INFO"
                                  "  WHERE service_status = %s"
                                  "    AND owner_mobile = %s"
                                  "    AND login_permit = 1"
                                  "    ORDER BY LOGIN DESC",
                                  UWEB.SERVICE_STATUS.ON, uid)


        for terminal in terminals:
            # 1: get terminal
            tid = terminal.tid

            group_info = get_group_info_by_tid(self.db, tid)

            terminal_info_key = get_terminal_info_key(tid)
            terminal_cache = self.redis.getvalue(terminal_info_key)
            if terminal_cache:
                terminal['gps'] =  terminal_cache['gps']
                terminal['gsm'] =  terminal_cache['gsm']
                terminal['pbat'] =  terminal_cache['pbat']

            mobile = terminal['mobile']
            terminal['keys_num'] = 0
            if terminal['login'] == GATEWAY.TERMINAL_LOGIN.SLEEP:
                terminal['login'] = GATEWAY.TERMINAL_LOGIN.ONLINE
            #NOTE: if alias is null, provide cnum or sim instead
            terminal['alias'] = QueryHelper.get_alias_by_tid(tid, self.redis, self.db)
            fobs = self.db.query("SELECT fobid FROM T_FOB"
                                 "  WHERE tid = %s", tid)
            terminal['fob_list'] = [fob.fobid for fob in fobs]
            terminal['sim'] = terminal['mobile'] 

            # 2: get location
            location = QueryHelper.get_location_info(tid, self.db, self.redis)
            if location and not (location.clatitude or location.clongitude):
                location_key = get_location_key(str(tid))
                locations = [location,] 
                locations = get_locations_with_clatlon(locations, self.db) 
                location = locations[0]
                self.redis.setvalue(location_key, location, EVENTER.LOCATION_EXPIRY)

            if location and location['name'] is None:
                location['name'] = ''


            avatar_name, avatar_path, avatar_full_path, avatar_time = self.get_avatar_info(mobile) 

            service_status = QueryHelper.get_service_status_by_tmobile(self.db, mobile)
            car_dct = {}
            if location and location['type'] == 1: # cellid 
                location['locate_error'] = 500  # mile
            car_info=dict(defend_status=terminal['defend_status'] if terminal['defend_status'] is not None else 1,
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

            car_dct[tid]=car_info
            cars_info.update(car_dct)

        if version_type >= 1:
            terminals = []
            for k, v in cars_info.iteritems():
                v.update({'tid':k})
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
            status= ErrorCode.ILLEGAL_LABEL
            self.write_ret(status)
            return
        #if not (check_sql_injection(username) and check_sql_injection(password)):
        #    status= ErrorCode.LOGIN_FAILED
        #    self.write_ret(status)
        #    return

        # check the user, return uid, tid, sim and status
        cid, oid, uid, terminals, user_type, status = self.login_passwd_auth(username, password, user_type)
        logging.info("[UWEB] Login auth, cid:%s, oid:%s, uid:%s, user_type:%s", cid, oid, uid, user_type)
        if status == ErrorCode.SUCCESS: 
            ## role: 0: person; 1: operator; 2: enterprise
            ## method 0: web; 1: android; 2: ios 
            self.login_log(uid, 0, 1, versionname)

            self.bookkeep(dict(cid=cid,
                               oid=oid,
                               uid=uid,
                               tid=terminals[0].tid,
                               sim=terminals[0].sim))

            user_info = QueryHelper.get_user_by_uid(uid, self.db)

            # NOTE: add cars_info, it's same as lastinfo
            cars_info = {} 

            if user_type == UWEB.USER_TYPE.PERSON:
                terminals = self.db.query("SELECT tid, mobile, owner_mobile, login, keys_num"
                                          "    gsm, gps, pbat, login, defend_status,"
                                          "    mannual_status, fob_status, icon_type, bt_name, bt_mac"
                                          "  FROM T_TERMINAL_INFO"
                                          "  WHERE (service_status = %s"
                                          "         OR service_status = %s)"
                                          "    AND biz_type = %s"
                                          "    AND owner_mobile = %s"
                                          "    AND login_permit = 1"
                                          "    ORDER BY LOGIN DESC",
                                          UWEB.SERVICE_STATUS.ON, 
                                          UWEB.SERVICE_STATUS.TO_BE_ACTIVATED,
                                          biz_type, uid)

            elif user_type == UWEB.USER_TYPE.OPERATOR:
                groups = self.db.query("SELECT group_id FROM T_GROUP_OPERATOR WHERE oper_id = %s", oid)
                gids = [g.group_id for g in groups]
                terminals = self.db.query("SELECT tid, mobile, owner_mobile, login, keys_num"
                                          "    gsm, gps, pbat, login, defend_status,"
                                          "    mannual_status, fob_status, icon_type, bt_name, bt_mac"
                                          "  FROM T_TERMINAL_INFO"
                                          "  WHERE (service_status = %s"
                                          "         OR service_status = %s)"
                                          "    AND biz_type = %s"
                                          "    AND group_id IN %s"
                                          "    ORDER BY LOGIN DESC",
                                          UWEB.SERVICE_STATUS.ON, 
                                          UWEB.SERVICE_STATUS.TO_BE_ACTIVATED,
                                          biz_type, tuple(DUMMY_IDS + gids))
            elif user_type == UWEB.USER_TYPE.CORP:
                groups = self.db.query("SELECT id gid, name FROM T_GROUP WHERE corp_id = %s", cid)
                gids = [g.gid for g in groups]
                terminals = self.db.query("SELECT tid, mobile, owner_mobile, login, keys_num"
                                          "    gsm, gps, pbat, login, defend_status,"
                                          "    mannual_status, fob_status, icon_type, bt_name, bt_mac"
                                          "  FROM T_TERMINAL_INFO"
                                          "  WHERE (service_status = %s"
                                          "         OR service_status = %s)"
                                          "    AND biz_type = %s"
                                          "    AND group_id IN %s"
                                          "    ORDER BY LOGIN DESC",
                                          UWEB.SERVICE_STATUS.ON, 
                                          UWEB.SERVICE_STATUS.TO_BE_ACTIVATED,
                                          biz_type, tuple(DUMMY_IDS + gids))
            else:
                logging.error("[UWEB] Invalid user_type: %s", user_type)
                pass

            for terminal in terminals:
                # 1: get terminal
                tid = terminal.tid

                group_info = get_group_info_by_tid(self.db, tid)

                terminal_info_key = get_terminal_info_key(tid)
                terminal_cache = self.redis.getvalue(terminal_info_key)
                if terminal_cache:
                    terminal['gps'] =  terminal_cache['gps']
                    terminal['gsm'] =  terminal_cache['gsm']
                    terminal['pbat'] =  terminal_cache['pbat']

                mobile = terminal['mobile']
                terminal['keys_num'] = 0
                if terminal['login'] == GATEWAY.TERMINAL_LOGIN.SLEEP:
                    terminal['login'] = GATEWAY.TERMINAL_LOGIN.ONLINE
                #NOTE: if alias is null, provide cnum or sim instead
                terminal['alias'] = QueryHelper.get_alias_by_tid(tid, self.redis, self.db)
                fobs = self.db.query("SELECT fobid FROM T_FOB"
                                     "  WHERE tid = %s", tid)
                terminal['fob_list'] = [fob.fobid for fob in fobs]
                terminal['sim'] = terminal['mobile'] 

                # 2: get location
                location = QueryHelper.get_location_info(tid, self.db, self.redis)
                if location and not (location.clatitude or location.clongitude):
                    location_key = get_location_key(str(tid))
                    locations = [location,] 
                    locations = get_locations_with_clatlon(locations, self.db) 
                    location = locations[0]
                    self.redis.setvalue(location_key, location, EVENTER.LOCATION_EXPIRY)

                if location and location['name'] is None:
                    location['name'] = ''

                avatar_name, avatar_path, avatar_full_path, avatar_time = self.get_avatar_info(mobile)

                service_status = QueryHelper.get_service_status_by_tmobile(self.db, mobile)
                car_dct = {}

                if location and location['type'] == 1: # cellid 
                    location['locate_error'] = 500  # mile

                car_info=dict(defend_status=terminal['defend_status'] if terminal['defend_status'] is not None else 1,
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

                car_dct[tid]=car_info
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
                old_android_push_list = self.redis.getvalue(old_android_push_list_key)
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
                pass # corp maybe no user_info

            if version_type >= 1:
                terminals = []
                for k, v in cars_info.iteritems():
                    v.update({'tid':k})
                    terminals.append(v)

                self.write_ret(status,
                               dict_=DotDict(push_id=push_id,
                                             push_key=push_key,
                                             name=user_info.name if user_info else username, 
                                             user_type=user_type,
                                             terminals=terminals,
                                             lastinfo_time=lastinfo_time,))
            else:
                self.write_ret(status,
                               dict_=DotDict(push_id=push_id,
                                             #app_key=push_info.app_key,
                                             push_key=push_key,
                                             name=user_info.name if user_info else username, 
                                             user_type=user_type,
                                             cars_info=cars_info,
                                             lastinfo_time=lastinfo_time,
                                             cars=terminals))
        else:
            logging.info("[UWEB] username: %s login failed, message: %s", username, ErrorCode.ERROR_MESSAGE[status])
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

        self.bookkeep(dict(cid=cid,
                           oid=oid,
                           uid=uid,
                           tid=tid,
                           sim=sim))

        user_info = QueryHelper.get_user_by_uid(uid, self.db)

        # NOTE: add cars_info, it's same as lastinfo
        cars_info = {} 
        terminals = self.db.query("SELECT tid, mobile, owner_mobile, login, keys_num"
                                  "    gsm, gps, pbat, login, defend_status,"
                                  "    mannual_status, fob_status, icon_type, bt_name, bt_mac"
                                  "  FROM T_TERMINAL_INFO"
                                  "  WHERE service_status = %s"
                                  "    AND owner_mobile = %s"
                                  "    AND login_permit = 1"
                                  "    ORDER BY LOGIN DESC",
                                  UWEB.SERVICE_STATUS.ON, uid)
        for terminal in terminals:
            # 1: get terminal
            tid = terminal.tid

            group_info = get_group_info_by_tid(self.db, tid)

            terminal_info_key = get_terminal_info_key(tid)
            terminal_cache = self.redis.getvalue(terminal_info_key)
            if terminal_cache:
                terminal['gps'] =  terminal_cache['gps']
                terminal['gsm'] =  terminal_cache['gsm']
                terminal['pbat'] =  terminal_cache['pbat']

            mobile = terminal['mobile']
            terminal['keys_num'] = 0
            if terminal['login'] == GATEWAY.TERMINAL_LOGIN.SLEEP:
                terminal['login'] = GATEWAY.TERMINAL_LOGIN.ONLINE
            #NOTE: if alias is null, provide cnum or sim instead
            terminal['alias'] = QueryHelper.get_alias_by_tid(tid, self.redis, self.db)
            fobs = self.db.query("SELECT fobid FROM T_FOB"
                                 "  WHERE tid = %s", tid)
            terminal['fob_list'] = [fob.fobid for fob in fobs]
            terminal['sim'] = terminal['mobile'] 

            # 2: get location
            location = QueryHelper.get_location_info(tid, self.db, self.redis)
            if location and not (location.clatitude or location.clongitude):
                location_key = get_location_key(str(tid))
                locations = [location,] 
                locations = get_locations_with_clatlon(locations, self.db) 
                location = locations[0]
                self.redis.setvalue(location_key, location, EVENTER.LOCATION_EXPIRY)

            if location and location['name'] is None:
                location['name'] = ''


            avatar_name, avatar_path, avatar_full_path, avatar_time = self.get_avatar_info(mobile)
            service_status = QueryHelper.get_service_status_by_tmobile(self.db, mobile)
            car_dct = {}
            if location and location['type'] == 1: # cellid 
                location['locate_error'] = 500  # mile
            car_info=dict(defend_status=terminal['defend_status'] if terminal['defend_status'] is not None else 1,
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

            car_dct[tid]=car_info
            cars_info.update(car_dct)

        #push_info = NotifyHelper.get_push_info()
        
        push_id =  uid 
        push_key = NotifyHelper.get_push_key(push_id, self.redis)

        version_info = get_version_info("android")
        lastinfo_time_key = get_lastinfo_time_key(uid)
        lastinfo_time = self.redis.getvalue(lastinfo_time_key)

        if version_type >= 1: 
            terminals = []
            for k, v in cars_info.iteritems():
                v.update({'tid':k})
                terminals.append(v)

            self.write_ret(status,
                           dict_=DotDict(push_id=push_id,
                                         push_key=push_key,
                                         name=user_info.name if user_info else username, 
                                         user_type=UWEB.USER_TYPE.PERSON,
                                         lastinfo_time=lastinfo_time,
                                         terminals=terminals))

        else:
            self.write_ret(status,
                           dict_=DotDict(push_id=push_id,
                                         #app_key=push_info.app_key,
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
        #uid = self.current_user.uid
        #terminals = self.db.query("SELECT uid, default_status, defend_status FROM T_TERMINAL_INFO WHERE uid=%s", uid)
        #for terminal in termianls:
        #    if terminal["default_status"] != termianl["mannual_status"]:
        #        self.db.update("UPDATE T_TERMINAL_INFO SET mannual_status=%s WHERE tid=%s",terminal["default_status"], terminal["tid"])
        #        logging.info("[UWEB] terminal %s logout and change mannual status %s, uid is %s", terminal["tid"], terminal["default_status"], uid)
        self.clear_cookie(self.app_name)
        self.redirect(self.get_argument("next", "/"))

class IOSLogoutHandler(BaseHandler):

    #@authenticated
    #@tornado.web.removeslash
    #def get(self):
    #    """Clear the cookie, ios_id and ios_badge. """
    #    ios_id_key = get_ios_id_key(self.current_user.uid)
    #    ios_badge_key = get_ios_badge_key(self.current_user.uid)
    #    keys = [ios_id_key, ios_badge_key]
    #    self.redis.delete(*keys)
    #    self.clear_cookie(self.app_name)

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
                terminal = QueryHelper.get_terminal_by_tid(tid, self.db)
                if not terminal:
                    status = ErrorCode.LOGIN_AGAIN
                    logging.error("The terminal with tid: %s does not exist, check it ", tid)
                    continue
                #terminal = self.db.get("SELECT uid, default_status, defend_status FROM T_TERMINAL_INFO WHERE tid=%s", tid)
                #if terminal["default_status"] != termianl["mannual_status"]:
                #    self.db.update("UPDATE T_TERMINAL_INFO SET mannual_status=%s WHERE tid=%s",terminal["default_status"], terminal["tid"])
                #    logging.info("[UWEB] terminal %s logout and change mannual status %s, uid is %s", terminal["tid"], terminal["default_status"], terminal["uid"])
                #self.keep_waking(self.current_user.sim, self.current_user.tid)
                self.db.execute("UPDATE T_TERMINAL_INFO"
                                "  SET mannual_status = %s"
                                "  WHERE tid = %s",
                                UWEB.DEFEND_STATUS.YES, tid)

                terminal_info_key = get_terminal_info_key(tid)
                terminal_info = self.redis.getvalue(terminal_info_key)
                if terminal_info:
                    terminal_info['mannual_status'] = UWEB.DEFEND_STATUS.YES
                    self.redis.setvalue(terminal_info_key, terminal_info)
                logging.info("[UWEB] uid:%s, tid:%s set mannual status  successfully", 
                             self.current_user.uid, tid)

            # 2: remove ios from push_list 
            ios_push_list_key = get_ios_push_list_key(self.current_user.uid) 
            ios_push_list = self.redis.getvalue(ios_push_list_key) 
            ios_push_list = ios_push_list if ios_push_list else []
            if iosid in ios_push_list: 
                ios_push_list.remove(iosid) 
                self.redis.set(ios_push_list_key, ios_push_list) 
            ios_badge_key = get_ios_badge_key(iosid) 
            self.redis.delete(ios_badge_key) 
            logging.info("[UWEB] uid:%s, ios_push_lst: %s", self.current_user.uid, ios_push_list)
        finally:
            # 3: clear cookie
            self.clear_cookie(self.app_name)
            self.write_ret(ErrorCode.SUCCESS)


class AndroidLogoutHandler(BaseHandler):

    #@authenticated
    #@tornado.web.removeslash
    #def get(self):
    #    """Clear the cookie ."""
    #    self.clear_cookie(self.app_name)

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
                terminal = QueryHelper.get_terminal_by_tid(tid, self.db)
                if not terminal:
                    status = ErrorCode.LOGIN_AGAIN
                    logging.error("The terminal with tid: %s does not exist, check it ", tid)
                    continue
               # terminal = self.db.get("SELECT uid, default_status, defend_status FROM T_TERMINAL_INFO WHERE tid=%s", tid)
               # if terminal["default_status"] != termianl["mannual_status"]:
               #     self.db.update("UPDATE T_TERMINAL_INFO SET mannual_status=%s WHERE tid=%s",terminal["default_status"], terminal["tid"])
               #     logging.info("[UWEB] terminal %s logout and change mannual status %s, uid is %s", terminal["tid"], terminal["default_status"], terminal["uid"])
                #self.keep_waking(self.current_user.sim, self.current_user.tid)
                self.db.execute("UPDATE T_TERMINAL_INFO"
                                "  SET mannual_status = %s"
                                "  WHERE tid = %s",
                                UWEB.DEFEND_STATUS.YES, tid)

                terminal_info_key = get_terminal_info_key(tid)
                terminal_info = self.redis.getvalue(terminal_info_key)
                if terminal_info:
                    terminal_info['mannual_status'] = UWEB.DEFEND_STATUS.YES
                    self.redis.setvalue(terminal_info_key, terminal_info)
                logging.info("[UWEB] uid:%s, tid:%s set mannual status  successfully", 
                             self.current_user.uid, tid)
            # 2: remove devid from android_push_list 
            android_push_list_key = get_android_push_list_key(self.current_user.uid) 
            android_push_list = self.redis.getvalue(android_push_list_key) 
            android_push_list = android_push_list if android_push_list else []
            if devid in android_push_list: 
                android_push_list.remove(devid) 
                self.redis.set(android_push_list_key, android_push_list) 
            logging.info("[UWEB] uid:%s, android_push_lst: %s", self.current_user.uid, android_push_list)
        finally:
            # 3: clear cookie
            self.clear_cookie(self.app_name)
            self.write_ret(ErrorCode.SUCCESS)
