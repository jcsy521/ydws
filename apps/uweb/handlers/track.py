# -*- coding: utf-8 -*-

import logging
import datetime
import re
import hashlib
from os import SEEK_SET
import xlwt
from cStringIO import StringIO

from tornado.escape import json_decode, json_encode
import tornado.web

from utils.dotdict import DotDict
from utils.misc import str_to_list, utc_to_date, seconds_to_label,\
     get_terminal_sessionID_key, get_track_key, get_lqgz_key, get_lqgz_interval_key
from constants import UWEB, SMS
from helpers.queryhelper import QueryHelper
from helpers.smshelper import SMSHelper
from helpers.lbmphelper import get_distance, get_locations_with_clatlon
from helpers.confhelper import ConfHelper
from codes.errorcode import ErrorCode
from codes.smscode import SMSCode
from constants import UWEB, EXCEL

from base import BaseHandler, authenticated
from mixin.base import  BaseMixin

class TrackLQHandler(BaseHandler, BaseMixin):

    @authenticated
    @tornado.web.removeslash
    def post(self):
        """Turn on tracing."""
        status = ErrorCode.SUCCESS
        try:
            data = DotDict(json_decode(self.request.body))
            tid = data.get('tid',None) 
            tids = data.get('tids', None)
            flag = int(data.get('flag', 1))
            # check tid whether exist in request and update current_user
            self.check_tid(tid)
            logging.info("[UWEB] track LQ request: %s, uid: %s, tid: %s, tids: %s, flag: %s", 
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

                    ##NOTE: just send lqgz temporary
                    terminal = QueryHelper.get_terminal_by_tid(tid, self.db)
                    lqgz_key = get_lqgz_key(tid)
                    lqgz_value = self.redis.getvalue(lqgz_key)
                    lqgz_interval_key = get_lqgz_interval_key(tid)
                    if not lqgz_value:
                        interval = 30 # in minute
                        sms = SMSCode.SMS_LQGZ % interval
                        SMSHelper.send_to_terminal(terminal.mobile, sms)
                        self.redis.setvalue(lqgz_key, True, SMS.LQGZ_SMS_INTERVAL)
                        self.redis.setvalue(lqgz_interval_key, True, SMS.LQGZ_INTERVAL * 2)
                    # END

                    track_key = get_track_key(tid)
                    track = self.redis.get(track_key)
                    logging.info("[UWEB] Get track: %s from redis", track)
                    if track and int(track) == 1:
                        # turn on track already
                        logging.info("[UWEB] Terminal: %s turn on track already.", tid)
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
                              self.current_user.uid, self.current_user.tid, e.args )
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)

class TrackHandler(BaseHandler):

    KEY_TEMPLATE = "track_%s_%s"

    @authenticated
    @tornado.web.removeslash
    def post(self):
        """Get track through tid in some period."""
        status = ErrorCode.SUCCESS
        try:
            data = DotDict(json_decode(self.request.body))
            tid = data.get('tid',None) 
            # check tid whether exist in request and update current_user
            self.check_tid(tid)
            logging.info("[UWEB] track request: %s, uid: %s, tid: %s", 
                         data, self.current_user.uid, self.current_user.tid)
        except Exception as e:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            self.write_ret(status)
            return 

        try:
            # check the tracker whether can be tracked
            # 13600335550 中山三乡谷都派出所
            # 15919176710  贾晓磊的测试账号
            if self.current_user.cid in ['15919176710','13600335550']:
                logging.info("cid: %s is no need check.", self.current_user.cid)
                pass
            else: 
                biz = QueryHelper.get_biz_by_mobile(self.current_user.sim, self.db)
                if biz: 
                    if biz.biz_type == UWEB.BIZ_TYPE.ELECTROCAR:
                        status = ErrorCode.QUERY_TRACK_FORBID
                        self.write_ret(status)
                        logging.info("[UWEB] sim:%s, biz_type:%s, track is not permited.", 
                                     self.current_user.sim, biz.biz_type)
                        return
                else:
                    # 1477874**** cannot query track
                    r = re.compile(UWEB.SIMPLE_YDCWS_PATTERN)
                    if r.match(self.current_user.sim):
                        status = ErrorCode.QUERY_TRACK_FORBID
                        self.write_ret(status)
                        logging.info("[UWEB] sim:%s, track is not permited.", 
                                     self.current_user.sim)
                        return

            start_time = data.start_time
            end_time = data.end_time
            cellid_flag = data.get('cellid_flag')
            # the interval between start_time and end_time is one week
            if (int(end_time) - int(start_time)) > UWEB.QUERY_INTERVAL:
                self.write_ret(ErrorCode.QUERY_INTERVAL_EXCESS)
                return

            if cellid_flag == 1:
                # gps track and cellid track
                track = self.db.query("SELECT id, latitude, longitude, clatitude,"
                                      "       clongitude, timestamp, name, type, speed, degree"
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
                                      "       clongitude, timestamp, name, type, speed, degree"
                                      "  FROM T_LOCATION"
                                      "  WHERE tid = %s"
                                      "    AND NOT (latitude = 0 OR longitude = 0)"
                                      "    AND (timestamp BETWEEN %s AND %s)"
                                      "    AND type = 0"
                                      "    GROUP BY timestamp"
                                      "    ORDER BY timestamp",
                                      self.current_user.tid, start_time, end_time)

            # NOTE: if latlons are legal, but clatlons are illlegal, offset
            # them and update them in db.  
            track = get_locations_with_clatlon(track, self.db)

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
               for j in range(i+1,len(track)):
                   item_end = track[j]
                   distance = get_distance(item_start.clongitude, item_start.clatitude, item_end.clongitude, item_end.clatitude) 
                   if distance >= UWEB.IDLE_DISTANCE:
                       break
                   else:
                       idle_time = item_end['timestamp'] - item_start['timestamp']
                       item_start['idle_time'] = idle_time
                       item_start['start_time'] = item_start['timestamp']
                       item_start['end_time'] = item_end['timestamp']
                       idle_lst.append(j)
                       is_idle = True
               if is_idle and item_start['idle_time'] > UWEB.IDLE_INTERVAL: 
                   idle_points.append(item_start)

            # modify name & degere 
            terminal = QueryHelper.get_terminal_by_tid(self.current_user.tid, self.db)
            for item in track:
                item['degree'] = float(item['degree'])
                if item.name is None:
                    item['name'] = ''

            # organize and store the data to be downloaded 
            m = hashlib.md5()
            m.update(self.request.body)
            hash_ = m.hexdigest()
            mem_key = self.KEY_TEMPLATE % (self.current_user.uid, hash_)
            
            res =  []
            if idle_lst:
                point_begin = dict(label=u'起点',
                                   start_time=utc_to_date(track[0]['timestamp']),
                                   end_time='',
                                   name=track[0]['name'])
                point_idle = []
                for idle_point in idle_points:
                    idle_label =  seconds_to_label(idle_point['idle_time'])
                    label = u'停留' + idle_label
                    point = dict(label=label,
                                 start_time=utc_to_date(idle_point['start_time']),
                                 end_time=utc_to_date(idle_point['end_time']),
                                 name=idle_point['name'])
                    point_idle.append(point)
                point_end = dict(label=u'终点',
                                 start_time=utc_to_date(track[-1]['timestamp']),
                                 end_time='',
                                 name=track[-1]['name'])
                res.append(point_begin)
                res.append(point_end)
                res.extend(point_idle)

                self.redis.setvalue(mem_key, res, time=UWEB.STATISTIC_INTERVAL)

            logging.info("[UEB] Tid:%s track query, returned %s points.", self.current_user.tid, len(track))
            self.write_ret(status,
                           dict_=DotDict(track=track,
                                         idle_points=idle_points,
                                         hash_=hash_))
        except Exception as e:
            logging.exception("[UWEB] uid: %s, tid: %s get track failed. Exception: %s. ", 
                              self.current_user.uid, self.current_user.tid, e.args )
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)

class TrackDownloadHandler(TrackHandler):

    @authenticated
    @tornado.web.removeslash
    def get(self):
        """Provide some report about track.
        """
        status = ErrorCode.SUCCESS
        try:
            hash_ = self.get_argument('hash_', None)

            mem_key = self.KEY_TEMPLATE % (self.current_user.uid, hash_)

            results = self.redis.getvalue(mem_key)

            if not results:
                logging.exception("[UWEB] mileage statistic export excel failed, find no res by hash_:%s", hash_)
                self.render("error.html",
                            message=ErrorCode.ERROR_MESSAGE[ErrorCode.EXPORT_FAILED],
                            home_url=ConfHelper.UWEB_CONF.url_out)
                return

            date_style = xlwt.easyxf(num_format_str='YYYY-MM-DD HH:mm:ss')
            
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
            self.set_header('Content-Disposition', 'attachment; filename=%s.xls' % (filename,))

            # move the the begging. 
            _tmp_file.seek(0, SEEK_SET)
            self.write(_tmp_file.read())
            _tmp_file.close()
 
        except Exception as e:
            logging.exception("[UWEB] track report export excel failed, Exception: %s", e.args)
            self.render("error.html",
                        message=ErrorCode.ERROR_MESSAGE[ErrorCode.EXPORT_FAILED],
                        home_url=ConfHelper.UWEB_CONF.url_out)


