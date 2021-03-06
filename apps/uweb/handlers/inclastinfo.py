# -*- coding: utf-8 -*-

"""This module is designed for inclastinfo.
"""

import logging
import time
from copy import deepcopy

import tornado.web
from tornado.ioloop import IOLoop
from tornado.escape import json_decode

from utils.dotdict import DotDict
from utils.misc import (get_alarm_info_key, get_location_key,
                        DUMMY_IDS, get_track_key, get_corp_info_key, get_group_info_key,
                        get_group_terminal_info_key, get_group_terminal_detail_key)
from codes.errorcode import ErrorCode
from helpers.queryhelper import QueryHelper 
from constants import UWEB, EVENTER, GATEWAY
from base import BaseHandler, authenticated


class IncLastInfoCorpHandler(BaseHandler):

    """Get the newest info of terminal from database.

    :url /inclastinfo/corp

    NOTE:It just retrieves data from db, not get info from terminal. 
    """

    @authenticated
    @tornado.web.removeslash
    @tornado.web.asynchronous
    def post(self):
        _start_time = time.time()

        def _on_finish(db):
            self.db = db
            try:
                data = DotDict(json_decode(self.request.body))
                track_lst = data.get('track_lst', [])
                # NOTE: nearly all timestamp's len is 10, here use 13
                current_time = int(time.time() * 1000)
                lastinfo_time = data.get('lastinfo_time')
            except Exception as e:
                status = ErrorCode.ILLEGAL_DATA_FORMAT
                logging.info("[UWEB] inlastfinfo for corp failed, message: %s, Exception: %s, request: \n%s",
                             ErrorCode.ERROR_MESSAGE[status], e.args, self.request.body)
                self.write_ret(status)
                IOLoop.instance().add_callback(self.finish)
                return

            try:
                status = ErrorCode.SUCCESS
                REMOVE_GID_TID = []  # [(gid, tid),(gid,tid),]
                res_type = 0
                # NOTE: first time, lastinfo_time = -1, set the lsstinfo_time
                # as current_time
                if lastinfo_time == -1:
                    #logging.info("[UWEB] res_type=2, first time, cid:%s", self.current_user.cid)
                    res_type = 2
                    lastinfo_time = current_time

                corp = self.db.get(
                    "SELECT cid, name, mobile FROM T_CORP WHERE cid = %s", self.current_user.cid)
                if self.current_user.oid == UWEB.DUMMY_OID:
                    uid = self.current_user.cid
                    groups = self.db.query("SELECT id gid, name FROM T_GROUP WHERE corp_id = %s"
                                           "  ORDER BY id", uid)
                else:
                    uid = self.current_user.oid
                    groups = self.db.query(
                        "SELECT group_id FROM T_GROUP_OPERATOR WHERE oper_id = %s", uid)
                    gids = [g.group_id for g in groups]
                    groups = self.db.query("SELECT id gid, name FROM T_GROUP WHERE id IN %s"
                                           "  ORDER BY id", tuple(DUMMY_IDS + gids))

                corp_info = dict(name=corp['name'] if corp else '',
                                 cid=corp['cid'] if corp else '')

                corp_info_key = get_corp_info_key(uid)

                corp_info_tuple = self.redis.getvalue(corp_info_key)
                if corp_info_tuple:
                    corp_info_old, corp_info_time = corp_info_tuple
                else:
                    corp_info_old, corp_info_time = None, None

                if corp_info_old is not None:
                    if corp_info_old != corp_info:
                        #logging.info("[UWEB] res_type=2, corp_info changed, cid:%s", self.current_user.cid)
                        res_type = 2
                        self.redis.setvalue(
                            corp_info_key, (corp_info, current_time))
                    else:
                        if lastinfo_time < corp_info_time:
                            # logging.info("[UWEB] res_type=2, corp_info time changed, lastinfo_time:%s < corp_info_time:%s, cid:%s",
                            # lastinfo_time, corp_info_time,
                            # self.current_user.cid)
                            res_type = 2
                else:
                    self.redis.setvalue(
                        corp_info_key, (corp_info, current_time))

                _now_time = time.time()
                if (_now_time - _start_time) > 5:
                    logging.info("[UWEB] Inclastinfo step1_corp used time: %s > 5s, cid: %s",
                                 _now_time - _start_time, self.current_user.cid)

                res = DotDict(name=corp_info['name'],
                              cid=corp_info['cid'],
                              online=0,
                              offline=0,
                              groups=[],
                              lastinfo_time=current_time)

                group_info_key = get_group_info_key(uid)
                group_info_tuple = self.redis.getvalue(group_info_key)
                if group_info_tuple:
                    group_info_old, group_info_time = group_info_tuple
                else:
                    group_info_old, group_info_time = None, None
                if group_info_old is not None:
                    if group_info_old != groups:
                        #logging.info("[UWEB] res_type=2, group_info changed, cid:%s", self.current_user.cid)
                        res_type = 2
                        self.redis.setvalue(
                            group_info_key, (groups, current_time))
                    else:
                        if lastinfo_time < group_info_time:
                            # logging.info("[UWEB] res_type=2, group_info time changed, lastinfo_time:%s < group_info_time:%s, cid:%s",
                            # lastinfo_time, group_info_time,
                            # self.current_user.cid)
                            res_type = 2
                else:
                    self.redis.setvalue(group_info_key, (groups, current_time))

                for group in groups:
                    group['trackers'] = {}
                    terminals = QueryHelper.get_terminals_by_group_id(
                        group.gid, db)
                    tids = [str(terminal.tid) for terminal in terminals]
                    _now_time = time.time()
                    if (_now_time - _start_time) > 5:
                        logging.info("[UWEB] Inclastinfo step1_group_sql used time: %s > 5s, cid: %s, gid: %s",
                                     _now_time - _start_time, self.current_user.cid, group.gid)

                    terminal_info_key = get_group_terminal_info_key(
                        uid, group.gid)
                    terminal_info_tuple = self.redis.getvalue(
                        terminal_info_key)
                    if terminal_info_tuple:
                        terminal_info_old, terminal_info_time = terminal_info_tuple
                    else:
                        terminal_info_old, terminal_info_time = None, None
                    if terminal_info_old is not None:
                        if terminal_info_old != tids:
                            #logging.info("[UWEB] res_type=2, terminal_info changed, cid:%s", self.current_user.cid)
                            res_type = 2
                            self.redis.setvalue(
                                terminal_info_key, (tids, current_time))
                        else:
                            if lastinfo_time < terminal_info_time:
                                # logging.info("[UWEB] res_type=2, terminal_info time changed, lastinfo_time:%s < terminal_info_time:%s, cid:%s",
                                # lastinfo_time, terminal_info_time,
                                # self.current_user.cid)
                                res_type = 2
                    else:
                        self.redis.setvalue(
                            terminal_info_key, (tids, current_time))
                    _now_time = time.time()
                    if (_now_time - _start_time) > 5:
                        logging.info("[UWEB] Inclastinfo step1_group used time: %s > 5s, cid: %s, gid: %s",
                                     _now_time - _start_time, self.current_user.cid, group.gid)
                    for tid in tids:
                        _now_time = time.time()
                        if (_now_time - _start_time) > 5:
                            logging.info("[UWEB] Inclastinfo step2 used time: %s > 5s, cid: %s",
                                         _now_time - _start_time, self.current_user.cid)

                        group['trackers'][tid] = {}
                        # 1: get terminal info
                        terminal = QueryHelper.get_terminal_info(
                            tid, self.db, self.redis)
                        if terminal['login'] == GATEWAY.TERMINAL_LOGIN.SLEEP:
                            terminal['login'] = GATEWAY.TERMINAL_LOGIN.ONLINE

                        if terminal['login'] == GATEWAY.TERMINAL_LOGIN.ONLINE:
                            res['online'] += 1
                        else:
                            res['offline'] += 1

                        # 2: get location
                        location = QueryHelper.get_location_info(
                            tid, self.db, self.redis)
                        if location and not (location.clatitude or location.clongitude):
                            location_key = get_location_key(str(tid))
                            locations = [location, ]
                            # NOTE: offset latlon
                            #locations = get_locations_with_clatlon(locations, self.db)
                            location = locations[0]
                            self.redis.setvalue(
                                location_key, location, EVENTER.LOCATION_EXPIRY)

                        if location and location['name'] is None:
                            location['name'] = ''

                        if location and location['type'] == 1:  # cellid
                            location['locate_error'] = 500  # mile

                        acc_status_info = QueryHelper.get_acc_status_info_by_tid(
                            self.client_id, tid, self.db, self.redis)
                        acc_message = acc_status_info['acc_message']
                        op_status = acc_status_info['op_status']

                        # 1: build the basic_info
                        basic_info = dict(defend_status=terminal['defend_status'] if terminal['defend_status'] is not None else 1,
                                          mannual_status=terminal['mannual_status'] if terminal[
                            'mannual_status'] is not None else 1,
                            acc_message=acc_message,
                            op_status=op_status,
                            fob_status=terminal['fob_status'] if terminal[
                            'fob_status'] is not None else 0,
                            timestamp=location[
                            'timestamp'] if location else 0,
                            speed=location.speed if location else 0,
                            # NOTE: degree's type is Decimal,
                            # float() it before json_encode
                            degree=float(
                            location.degree) if location else 0.00,
                            locate_error=location.get(
                            'locate_error', 20) if location else 20,
                            name=location.name if location else '',
                            type=location.type if location else 1,
                            latitude=location[
                            'latitude'] if location else 0,
                            longitude=location['longitude'] if location else 0,
                            clatitude=location[
                            'clatitude'] if location else 0,
                            clongitude=location[
                                'clongitude'] if location else 0,
                            login=terminal['login'] if terminal[
                            'login'] is not None else 0,
                            bt_name=terminal.get(
                            'bt_name', '') if terminal else '',
                            bt_mac=terminal.get(
                            'bt_mac', '') if terminal else '',
                            dev_type=terminal['dev_type'] if terminal.get(
                            'dev_type', None) is not None else 'A',
                            gps=terminal['gps'] if terminal[
                            'gps'] is not None else 0,
                            gsm=terminal['gsm'] if terminal[
                            'gsm'] is not None else 0,
                            pbat=terminal['pbat'] if terminal[
                            'pbat'] is not None else 0,
                            mobile=terminal['mobile'],
                            owner_mobile=terminal['owner_mobile'],
                            alias=terminal['alias'],
                            #keys_num=terminal['keys_num'] if terminal['keys_num'] is not None else 0,
                            keys_num=0,
                            icon_type=terminal['icon_type'] if terminal.get(
                            'icon_type', None) is not None else 0,
                            fob_list=terminal['fob_list'] if terminal['fob_list'] else [])

                        _now_time = time.time()
                        if (_now_time - _start_time) > 5:
                            logging.info("[UWEB] Inclastinfo step2_basic used time: %s > 5s, cid: %s",
                                         _now_time - _start_time, self.current_user.cid)
                        # 2: build track_info
                        track_info = []
                        for item in track_lst:
                            if tid == item['track_tid']:
                                track_key = get_track_key(tid)
                                self.redis.setvalue(
                                    track_key, 1, UWEB.TRACK_INTERVAL)
                                #endtime = int(basic_info['timestamp'])-1 if basic_info['timestamp'] else (current_time/1000)-1
                                endtime = int(basic_info['timestamp']) - 1
                                points_track = []

                                logging.info("[UWEB] tid: %s, track_time, %s, %s", tid, int(
                                    item['track_time']) + 1, endtime)
                                # NOTE: offset latlon
                                #points_track = get_locations_with_clatlon(points_track, self.db)
                                for point in points_track:
                                    if point['clatitude'] and point['clongitude']:
                                        t = dict(latitude=point['latitude'],
                                                 longitude=point['longitude'],
                                                 clatitude=point['clatitude'],
                                                 clongitude=point[
                                                     'clongitude'],
                                                 type=point['type'],
                                                 timestamp=point['timestamp'])
                                        track_info.append(t)
                                break

                        _now_time = time.time()
                        if (_now_time - _start_time) > 5:
                            logging.info("[UWEB] Inclastinfo step2_track used time: %s > 5s, cid: %s",
                                         _now_time - _start_time, self.current_user.cid)
                        # 3: build trace_info
                        trace_info = []
                        points_trace = []
                        points_trace = points_trace[-5:]
                        #points_trace = get_locations_with_clatlon(points_trace, self.db)
                        len_trace = 0
                        if points_trace:
                            for point in points_trace:
                                if len_trace >= 5:
                                    break
                                if point['clatitude'] and point['clongitude']:
                                    trace_info.append(point['clatitude'])
                                    trace_info.append(point['clongitude'])
                                    len_trace += 1
                                else:
                                    continue

                        _now_time = time.time()
                        if (_now_time - _start_time) > 5:
                            logging.info("[UWEB] Inclastinfo step2_trace used time: %s > 5s, cid: %s",
                                         _now_time - _start_time, self.current_user.cid)

                        # 4: build alert_info
                        alarm_info_key = get_alarm_info_key(tid)
                        alarm_info_all = self.redis.getvalue(alarm_info_key)
                        alarm_info_all = alarm_info_all if alarm_info_all else []
                        alarm_info = []

                        if alarm_info_all:
                            for alarm in alarm_info_all:
                                # NOTE: here, check alarm's keeptime when kept
                                # in reids, not timestamp alarm occurs
                                if alarm.get('keeptime', None) is None:
                                    alarm['keeptime'] = alarm['timestamp']
                                if alarm['keeptime'] >= lastinfo_time / 1000:
                                    alarm_info.append(alarm)

                        for alarm in alarm_info:
                            alarm['alias'] = terminal['alias']

                        _now_time = time.time()
                        if (_now_time - _start_time) > 5:
                            logging.info("[UWEB] Inclastinfo step2_alarm used time: %s > 5s, cid: %s",
                                         _now_time - _start_time, self.current_user.cid)
                        group['trackers'][tid]['basic_info'] = basic_info
                        group['trackers'][tid]['track_info'] = track_info
                        group['trackers'][tid]['trace_info'] = trace_info
                        group['trackers'][tid]['alarm_info'] = alarm_info

                        terminal_detail_key = get_group_terminal_detail_key(
                            uid, group.gid, tid)
                        terminal_detail_tuple = self.redis.getvalue(
                            terminal_detail_key)
                        if terminal_detail_tuple:
                            terminal_detail_old, terminal_detail_time = terminal_detail_tuple
                        else:
                            terminal_detail_old, terminal_detail_time = None, None

                        if res_type != 2:
                            if terminal_detail_old is not None:
                                if terminal_detail_old != group['trackers'][tid]:
                                    self.redis.setvalue(
                                        terminal_detail_key, (group['trackers'][tid], current_time))
                                    #logging.info("[UWEB] res_type=1, terminal detail changed cid:%s", self.current_user.cid)
                                    res_type = 1
                                else:
                                    if lastinfo_time < terminal_detail_time:
                                        #logging.info("[UWEB] res_type=1, terminal detail time changed cid:%s", self.current_user.cid)
                                        res_type = 1
                                    else:
                                        #logging.info("[UWEB] res_type=0, terminal detail no changed cid:%s", self.current_user.cid)
                                        REMOVE_GID_TID.append((group.gid, tid))
                            else:
                                self.redis.setvalue(
                                    terminal_detail_key, (group['trackers'][tid], current_time))
                        else:
                            pass
                    res.groups.append(group)

                if res_type == 0:
                    res = DotDict(lastinfo_time=current_time)
                    self.write_ret(status,
                                   dict_=DotDict(res=res,
                                                 res_type=res_type))
                else:
                    if res_type == 1:
                        for gid, tid in REMOVE_GID_TID:
                            # logging.info("[UWEB] res_type=1, gid: %s, tid: %s is tobe removed. cid:%s",
                            #             gid, tid, self.current_user.cid)
                            for index, group in enumerate(res.groups):
                                if gid == group['gid']:
                                    del res.groups[index]['trackers'][tid]
                                    # logging.info("[UWEB] res_type=1, gid: %s, tid: %s is removed. cid:%s",
                                    # gid, tid, self.current_user.cid)

                        _groups = deepcopy(res.groups)
                        for index, group in enumerate(_groups):
                            if not group['trackers']:
                                res.groups.remove(group)
                                # logging.info("[UWEB] res_type=1, gid: %s, has no tracker, remove it. cid:%s",
                                #             gid, self.current_user.cid)

                    self.write_ret(status,
                                   dict_=DotDict(res=res,
                                                 res_type=res_type))

                _now_time = time.time()
                if (_now_time - _start_time) > 5:
                    logging.info("[UWEB] Inclastinfo step3 used time: %s > 5s, cid: %s",
                                 _now_time - _start_time, self.current_user.cid)
            except Exception as e:
                logging.exception("[UWEB] cid: %s get corp lastinfo failed. Exception: %s",
                                  self.current_user.cid, e.args)
                status = ErrorCode.SERVER_BUSY
                self.write_ret(status)
            IOLoop.instance().add_callback(self.finish)

        self.queue.put((10, _on_finish))
