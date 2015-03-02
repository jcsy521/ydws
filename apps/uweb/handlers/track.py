# -*- coding: utf-8 -*-

"""This module is designed for tracking terminal.

#NOTE: deprecated.
"""

import logging
import time
import hashlib
from os import SEEK_SET
import xlwt
from cStringIO import StringIO

from tornado.escape import json_decode
import tornado.web

from utils.dotdict import DotDict
from utils.misc import (str_to_list, utc_to_date, 
     get_terminal_sessionID_key, get_track_key, get_lqgz_key, 
     seconds_to_label, get_lqgz_interval_key)
from constants import UWEB, SMS, EXCEL
from helpers.queryhelper import QueryHelper
from helpers.smshelper import SMSHelper
from helpers.lbmphelper import get_distance, get_locations_with_clatlon
from helpers.confhelper import ConfHelper
from codes.errorcode import ErrorCode
from codes.smscode import SMSCode

from base import BaseHandler, authenticated
from mixin.base import BaseMixin


class TrackLQHandler(BaseHandler, BaseMixin):

    @authenticated
    @tornado.web.removeslash
    def post(self):
        """Turn on tracing."""
        status = ErrorCode.SUCCESS
        try:
            data = DotDict(json_decode(self.request.body))
            tid = data.get('tid', None)
            tids = data.get('tids', None)
            flag = int(data.get('flag', 1))
            # check tid whether exist in request and update current_user
            self.check_tid(tid)
            logging.info("[UWEB] track LQ request: %s, "
                         "  uid: %s, tid: %s, tids: %s, flag: %s",
                         data, self.current_user.uid, tid, tids, flag)
        except Exception as e:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            self.write_ret(status)
            return

        try:
            tids = str_to_list(tids)
            tids = tids if tids else [self.current_user.tid, ]
            tids = [str(tid) for tid in tids]

            if int(flag) == 1:
                for tid in tids:
                    # NOTE: just send lqgz temporary
                    terminal = QueryHelper.get_terminal_by_tid(tid, self.db)
                    lqgz_key = get_lqgz_key(tid)
                    lqgz_value = self.redis.getvalue(lqgz_key)
                    lqgz_interval_key = get_lqgz_interval_key(tid)
                    if not lqgz_value:
                        interval = 30  # in minute
                        biz_type = QueryHelper.get_biz_type_by_tmobile(
                            terminal.mobile, self.db)
                        if biz_type != UWEB.BIZ_TYPE.YDWS:
                            self.write_ret(status)
                            return
                        sms = SMSCode.SMS_LQGZ % interval
                        SMSHelper.send_to_terminal(terminal.mobile, sms)
                        self.redis.setvalue(
                            lqgz_key, True, SMS.LQGZ_SMS_INTERVAL)
                        self.redis.setvalue(
                            lqgz_interval_key, True, SMS.LQGZ_INTERVAL * 2)
                    # END

                    track_key = get_track_key(tid)
                    track = self.redis.get(track_key)
                    logging.info("[UWEB] Get track: %s from redis", track)
                    if track and int(track) == 1:
                        # turn on track already
                        logging.info(
                            "[UWEB] Terminal: %s turn on track already.", tid)
                    else:
                        self.db.execute("UPDATE T_TERMINAL_INFO SET track = %s"
                                        "  WHERE tid = %s",
                                        flag, tid)
                        self.redis.setvalue(track_key, 1, UWEB.TRACK_INTERVAL)
                        sessionID_key = get_terminal_sessionID_key(tid)
                        self.redis.delete(sessionID_key)
            self.write_ret(status)
        except Exception as e:
            logging.exception("[UWEB] uid: %s, tid: %s send lqgz failed. Exception: %s. ",
                              self.current_user.uid, self.current_user.tid, e.args)
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)


class TrackHandler(BaseHandler):

    KEY_TEMPLATE = "track_%s_%s"

    @authenticated
    @tornado.web.removeslash
    @tornado.web.asynchronous
    def post(self):
        """Get track through tid in some period."""
        status = ErrorCode.SUCCESS
        try:
            data = DotDict(json_decode(self.request.body))
            tid = data.get('tid', None)
            # check tid whether exist in request and update current_user
            self.check_tid(tid)
            logging.info("[UWEB] track request: %s, uid: %s, tid: %s",
                         data, self.current_user.uid, self.current_user.tid)
        except Exception as e:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            logging.exception(
                "[UWEB] Invalid data format. Exception: %s", e.args)
            self.write_ret(status)
            self.finish()
            return

        try:

            start_time = data.start_time
            end_time = data.end_time
            cellid_flag = data.get('cellid_flag', 0)
            network_type = data.get('network_type', 1)
        except Exception as e:
            logging.exception("[UWEB] uid: %s, tid: %s get track failed. Exception: %s. ",
                              self.current_user.uid, self.current_user.tid, e.args)
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)
            self.finish()
            return

        def _on_finish(db):
            self.db = db
            if cellid_flag == 1:
                # gps track and cellid track
                track = self.db.query("SELECT id, latitude, longitude, clatitude,"
                                      "       clongitude, timestamp, name,"
                                      "       type, speed, degree, locate_error"
                                      "  FROM T_LOCATION"
                                      "  WHERE tid = %s"
                                      "    AND NOT (latitude = 0 OR longitude = 0)"
                                      "    AND (timestamp BETWEEN %s AND %s)"
                                      "    GROUP BY timestamp"
                                      "    ORDER BY timestamp",
                                      self.current_user.tid, start_time, end_time)

            else:
                # cellid_flag is None or 0, only gps track
                track = self.db.query("SELECT id, latitude, longitude, clatitude,"
                                      "       clongitude, timestamp, name, "
                                      "       type, speed, degree, locate_error"
                                      "  FROM T_LOCATION"
                                      "  WHERE tid = %s"
                                      "    AND NOT (latitude = 0 OR longitude = 0)"
                                      "    AND (timestamp BETWEEN %s AND %s)"
                                      "    AND type = 0"
                                      "    GROUP BY timestamp"
                                      "    ORDER BY timestamp",
                                      self.current_user.tid, start_time, end_time)

            # check track point count
            if track and len(track) > 500 and network_type == 0:
                logging.info("[UWEB] The %s track points length is: %s, "
                             "  and the newtork type is too low, so return error.", 
                             tid, len(track))
                self.write_ret(ErrorCode.TRACK_POINTS_TOO_MUCH)
                self.finish()
                return

            # NOTE: if latlons are legal, but clatlons are illlegal, offset
            # them and update them in db.
            _start_time = time.time()
            track = get_locations_with_clatlon(track, self.db)
            _now_time = time.time()
            if _now_time - _start_time > 3:  # 3 seconds
                logging.info("[UWEB] Track offset used time: %s s, tid: %s, cid: %s",
                             _now_time - _start_time, self.current_user.tid, self.current_user.cid)

            # NOTE: filter point without valid clat and clon
            _track = []
            for t in track:
                if t['clongitude'] and ['clatitude']:
                    _track.append(t)
                else:
                    logging.info("[UWEB] Invalid point: %s, drop it, cid: %s",
                                 t, self.current_user.cid)
            track = _track

            # add idle_points
            # track1, track2, track3,...
            # when the distance between two points is larger than 10 meters and the interval is less than 5 minutes,
            # they are regarded as idle_points
            idle_lst = []
            idle_points = []
            for i, item_start in enumerate(track):
                is_idle = False
                if i in idle_lst:
                    continue
                for j in range(i + 1, len(track)):
                    item_end = track[j]
                    distance = get_distance(
                        item_start.clongitude, item_start.clatitude, item_end.clongitude, item_end.clatitude)
                    if distance >= UWEB.IDLE_DISTANCE:
                        break
                    else:
                        idle_time = item_end[
                            'timestamp'] - item_start['timestamp']
                        item_start['idle_time'] = idle_time
                        item_start['start_time'] = item_start['timestamp']
                        item_start['end_time'] = item_end['timestamp']
                        idle_lst.append(j)
                        is_idle = True
                if is_idle and item_start['idle_time'] > UWEB.IDLE_INTERVAL:
                    idle_points.append(item_start)

            # modify name & degere
            for item in track:
                item['degree'] = float(item['degree'])
                if item.name is None:
                    item['name'] = ''

            # organize and store the data to be downloaded
            m = hashlib.md5()
            m.update(self.request.body)
            hash_ = m.hexdigest()
            mem_key = self.KEY_TEMPLATE % (self.current_user.uid, hash_)

            res = []
            if idle_lst:
                point_begin = dict(label=u'起点',
                                   start_time=utc_to_date(
                                       track[0]['timestamp']),
                                   end_time='',
                                   name=track[0]['name'])
                point_idle = []
                for idle_point in idle_points:
                    idle_label = seconds_to_label(idle_point['idle_time'])
                    label = u'停留' + idle_label
                    point = dict(label=label,
                                 start_time=utc_to_date(
                                     idle_point['start_time']),
                                 end_time=utc_to_date(idle_point['end_time']),
                                 name=idle_point['name'])
                    point_idle.append(point)
                point_end = dict(label=u'终点',
                                 start_time=utc_to_date(
                                     track[-1]['timestamp']),
                                 end_time='',
                                 name=track[-1]['name'])
                res.append(point_begin)
                res.append(point_end)
                res.extend(point_idle)

                self.redis.setvalue(mem_key, res, time=UWEB.STATISTIC_INTERVAL)

            logging.info(
                "[UEB] Tid:%s track query, returned %s points.", self.current_user.tid, len(track))
            self.write_ret(status,
                           dict_=DotDict(track=track,
                                         idle_points=idle_points,
                                         hash_=hash_))
            self.finish()
        self.queue.put((10, _on_finish))


class TrackDownloadHandler(TrackHandler):

    @authenticated
    @tornado.web.removeslash
    def get(self):
        """Provide some report about track.
        """
        try:
            hash_ = self.get_argument('hash_', None)

            mem_key = self.KEY_TEMPLATE % (self.current_user.uid, hash_)

            results = self.redis.getvalue(mem_key)

            if not results:
                logging.exception(
                    "[UWEB] mileage statistic export excel failed, find no res by hash_:%s", hash_)
                self.render("error.html",
                            message=ErrorCode.ERROR_MESSAGE[
                                ErrorCode.EXPORT_FAILED],
                            home_url=ConfHelper.UWEB_CONF.url_out)
                return

            wb = xlwt.Workbook()
            ws = wb.add_sheet(EXCEL.TRACK_SHEET)

            start_line = 0
            for i, head in enumerate(EXCEL.TRACK_HEADER):
                ws.write(0, i, head)
                #ws.col(0).width = 4000
            ws.col(0).width = 4000 * 2
            ws.col(1).width = 4000 * 2
            ws.col(2).width = 4000 * 2
            ws.col(3).width = 4000 * 3
            start_line += 1
            for i, result in zip(range(start_line, len(results) + start_line), results):
                ws.write(i, 0, result['label'])
                ws.write(i, 1, result['start_time'])
                ws.write(i, 2, result['end_time'])
                ws.write(i, 3, result['name'])

            _tmp_file = StringIO()
            wb.save(_tmp_file)
            filename = self.generate_file_name(EXCEL.TRACK_FILE_NAME)

            self.set_header('Content-Type', 'application/force-download')
            self.set_header(
                'Content-Disposition', 'attachment; filename=%s.xls' % (filename,))

            # move the the begging.
            _tmp_file.seek(0, SEEK_SET)
            self.write(_tmp_file.read())
            _tmp_file.close()

        except Exception as e:
            logging.exception(
                "[UWEB] track report export excel failed, Exception: %s", e.args)
            self.render("error.html",
                        message=ErrorCode.ERROR_MESSAGE[
                            ErrorCode.EXPORT_FAILED],
                        home_url=ConfHelper.UWEB_CONF.url_out)
