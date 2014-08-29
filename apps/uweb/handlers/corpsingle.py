# -*- coding: utf-8 -*-

import logging

import tornado.web
from tornado.escape import json_encode, json_decode

from utils.dotdict import DotDict
from utils.misc import DUMMY_IDS, str_to_list, get_single_status_key
from constants import UWEB, LIMIT
from helpers.queryhelper import QueryHelper
from codes.errorcode import ErrorCode
from base import BaseHandler, authenticated

class CorpSingleHandler(BaseHandler):

    @authenticated
    @tornado.web.removeslash
    def get(self):
        """ Get singles by cid"""
        status = ErrorCode.SUCCESS
        try:
            cid = self.get_current_user()['cid']
        except Exception as e:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            logging.exception("[UWEB] uid: %s get region data format illegal. Exception: %s",
                              self.current_user.uid, e.args)
            self.write_ret(status)
            return

        try:
            res = []
            singles = self.db.query("SELECT id AS single_id, name AS single_name,"
                                    "       longitude, latitude, radius,"
                                    "       points, shape AS single_shape"
                                    "  FROM T_SINGLE"
                                    "  WHERE cid = %s",
                                    cid)
            for single in singles:
               if single.single_shape == UWEB.REGION_SHAPE.CIRCLE:
                   r = DotDict(single_id=single.single_id,
                               single_name=single.single_name,
                               single_shape=single.single_shape,
                               circle=DotDict(latitude=single.latitude,
                                              longitude=single.longitude,
                                              radius=single.radius),
                               )
               elif single.single_shape == UWEB.REGION_SHAPE.POLYGON:
                   polygon = []
                   points = single.points
                   point_lst = points.split(':')
                   for point in point_lst:
                       latlon = point.split(',')
                       dct = {'latitude':latlon[0],
                              'longitude':latlon[1]}
                       polygon.append(dct)
                   
                   r = DotDict(single_id=single.single_id,
                               single_name=single.single_name,
                               single_shape=single.single_shape,
                               polygon=polygon)
               res.append(r)
            self.write_ret(status,
                           dict_=DotDict(res=res))
        except Exception as e:
            logging.exception("[UWEB] cid: %s get singles failed. Exception: %s",
                              cid, e.args)
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)

    @authenticated
    @tornado.web.removeslash
    def post(self):
        """Create a new corp single. 
        """
        try:
            data = DotDict(json_decode(self.request.body))
            logging.info("[UWEB] add single request: %s, cid: %s",
                         data, self.current_user.cid)
        except Exception as e:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            logging.exception("[UWEB] cid: %s create single data format illegal. Exception: %s",
                              self.current_user.cid, e.args)
            self.write_ret(status)
            return

        try:
            singles = self.db.query("SELECT id"
                                    "  FROM T_SINGLE"
                                    "  WHERE cid = %s",
                                    self.current_user.cid)
            #TODO: how many single?
            if len(singles) > LIMIT.REGION - 1:
                self.write_ret(ErrorCode.REGION_ADDITION_EXCESS)
                return

            status = ErrorCode.SUCCESS
            single_id = -1 # default value
            single_name = data.single_name
            single_shape = int(data.single_shape)
            if single_shape == UWEB.REGION_SHAPE.CIRCLE:
                circle = DotDict(data.circle)
                longitude = circle.longitude 
                latitude = circle.latitude 
                radius = circle.radius
                # create new region
                single_id= self.db.execute("INSERT T_SINGLE(name, longitude, latitude, radius, shape, cid)"
                                           "  VALUES(%s, %s, %s, %s, %s, %s)",
                                           single_name, longitude, latitude,
                                           radius, single_shape, self.current_user.cid)
            elif single_shape == UWEB.REGION_SHAPE.POLYGON:
                polygon = data.polygon
                points_lst = [] 
                points = ''
                for p in polygon:
                    tmp = ','.join([str(p['latitude']), str(p['longitude'])])
                    points += tmp
                    points_lst.append(tmp)
                points = ':'.join(points_lst) 
                single_id = self.db.execute("INSERT T_SINGLE(name, points, shape, cid)"
                                            "  VALUES(%s, %s, %s, %s)",
                                            single_name, points, single_shape, self.current_user.cid)
            else: 
                logging.error("[UWEB] Add single failed, unknown single_shape: %s, uid: %s",
                              region_shape, self.current_user.uid)
                pass

            self.write_ret(status,
                           dict_=DotDict(single_id=single_id))
        except Exception as e:
            logging.exception("[UWEB] cid: %s create single failed. Exception: %s",
                              self.current_user.cid, e.args)
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)

    #TODO:
    @authenticated
    @tornado.web.removeslash
    def delete(self):
        """Delete single.
        """
        try:
            delete_ids = map(int, str_to_list(self.get_argument('single_ids', None)))
            logging.info("[UWEB] delete single: %s, cid: %s", 
                         delete_ids, self.current_user.cid)
        except Exception as e:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            logging.exception("[UWEB] cid: %s delete single illegal. Exception: %s",
                              self.current_user.cid, e.args)
            self.write_ret(status)
            return

        try:
            status = ErrorCode.SUCCESS
            #1: delete redis region status
            for single_id in delete_ids:
                terminals = self.db.query("SELECT tid"
                                          "  FROM T_SINGLE_TERMINAL"
                                          "  WHERE sid = %s",
                                          single_id)
                for terminal in terminals:
                    single_status_key = get_single_status_key(terminal.tid, single_id)
                    self.redis.delete(single_status_key)
            
            #2: delete region, region event and region terminal relation
            self.db.execute("DELETE FROM T_SINGLE WHERE id IN %s",
                            tuple(delete_ids + DUMMY_IDS)) 

            # rid: region_id, single_id
            self.db.execute("DELETE FROM T_EVENT WHERE rid IN %s",
                            tuple(delete_ids + DUMMY_IDS))

            self.db.execute("DELETE FROM T_SINGLE_TERMINAL WHERE sid IN %s",
                            tuple(delete_ids + DUMMY_IDS))
            
            self.write_ret(status)
        except Exception as e:
            logging.exception("[UWEB] cid: %s delete single failed. Exception: %s", 
                              self.current_user.cid, e.args) 
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)


class CorpSingleListHandler(BaseHandler):

    @authenticated
    @tornado.web.removeslash
    def post(self):
        """Query all single event. 
        """
        status = ErrorCode.SUCCESS
        try:
            data = DotDict(json_decode(self.request.body))
            start_time = data.start_time
            end_time = data.end_time
            tid = data.tid

            # For paging
            page_size = int(data.get('pagesize', UWEB.LIMIT.PAGE_SIZE))
            page_number = int(data.pagenum) 
            page_count = int(data.pagecnt)

            logging.info("[UWEB] Single list request: %s, cid: %s",
                         data, self.current_user.cid)
        except Exception as e:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            logging.exception("[UWEB] cid: %s single list  data format illegal. Exception: %s",
                              self.current_user.cid, e.args)
            self.write_ret(status)
            return

        try:
            #NOTE: we need return the event count to GUI at first time query
            if page_count == -1:
                res = self.db.get("SELECT COUNT(*) AS count"
                                  "  FROM T_SINGLE_EVENT AS tse, T_SINGLE AS ts"
                                  "  WHERE tse.tid = %s"
                                  "  AND tse.sid = ts.id"
                                  "  AND end_time != 0"
                                  "  AND (start_time between %s and %s)",
                                  tid, start_time, end_time)

                count = res.count 
                d, m = divmod(count, page_size) 
                pagecnt = (d + 1) if m else d


            res = self.db.query("SELECT tse.id as se_id, tse.start_time, tse.end_time,  ts.name as single_name"
                                "  FROM T_SINGLE_EVENT AS tse, T_SINGLE AS ts"
                                "  WHERE tse.tid = %s"
                                "  AND tse.sid = ts.id"
                                "  AND end_time != 0"
                                "  AND (start_time between %s and %s)"
                                "  LIMIT %s, %s",
                                tid, start_time, end_time,
                                page_number * page_size, page_size)

            self.write_ret(status,
                           dict_=DotDict(res=res,
                                         pagecnt=pagecnt))
        except Exception as e:
            logging.exception("[UWEB] cid: %s single list failed. Exception: %s",
                              self.current_user.cid, e.args)
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)


class CorpSingleDetailHandler(BaseHandler):

    @authenticated
    @tornado.web.removeslash
    def get(self):
        """Just a new page. 
        """
        se_id = self.get_argument("se_id",'')
        single_event = self.db.get("SELECT sid, tid, start_time, end_time"
                                   "  FROM T_SINGLE_EVENT"
                                   "  WHERE id = %s",
                                   se_id)

        terminal = QueryHelper.get_terminal_info(single_event['tid'], self.db, self.redis) 
        self.render("single_point.html",
                    single_id=single_event['sid'],
                    alias=terminal['alias'],
                    tid=single_event.get('tid',''),
                    start_time=single_event.get('start_time'),
                    end_time=single_event.get('end_time'))
