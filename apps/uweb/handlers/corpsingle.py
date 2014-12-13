# -*- coding: utf-8 -*-

"""This module is designed for single.
"""

import logging

import tornado.web
from tornado.escape import json_encode, json_decode

from utils.dotdict import DotDict
from utils.misc import DUMMY_IDS, str_to_list, get_single_status_key
from constants import UWEB, LIMIT
from utils.public import add_single, delete_single
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
            cid = self.current_user.cid
        except Exception as e:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            logging.exception("[UWEB] uid: %s get region data format illegal. Exception: %s",
                              self.current_user.uid, e.args)
            self.write_ret(status)
            return

        try:
            res = []
            singles = QueryHelper.get_singles_by_cid(self.current_user.cid, self.db)
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
                        dct = {'latitude': latlon[0],
                               'longitude': latlon[1]}
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
            singles = QueryHelper.get_singles_by_cid(self.current_user.cid, self.db)
            if len(singles) > LIMIT.REGION - 1:
                self.write_ret(ErrorCode.REGION_ADDITION_EXCESS)
                return

            status = ErrorCode.SUCCESS
            single_id = -1  # default value
            single_name = data.single_name
            single_shape = int(data.single_shape)
            if single_shape == UWEB.REGION_SHAPE.CIRCLE:
                circle = DotDict(data.circle)
                longitude = circle.longitude
                latitude = circle.latitude
                radius = circle.radius
                # create new region
                single_info = dict(single_name=single_name,
                                   longitude=longitude,
                                   latitude=latitude,
                                   radius=radius,
                                   shape=single_shape,
                                   cid=self.current_user.cid)
                single_id = add_single(single_info, self.db, self.redis)
            elif single_shape == UWEB.REGION_SHAPE.POLYGON:
                polygon = data.polygon
                points_lst = []
                points = ''
                for p in polygon:
                    tmp = ','.join([str(p['latitude']), str(p['longitude'])])
                    points += tmp
                    points_lst.append(tmp)
                points = ':'.join(points_lst)
                single_info = dict(single_name=single_name,
                                   points=points,
                                   shape=single_shape,
                                   cid=self.current_user.cid)
                single_id = add_single(single_info, self.db, self.redis)
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

    @authenticated
    @tornado.web.removeslash
    def delete(self):
        """Delete single.
        """
        try:
            delete_ids = map(
                int, str_to_list(self.get_argument('single_ids', None)))
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

            delete_single(delete_ids, self.db, self.redis)

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
            pagecnt = int(data.pagecnt)

            logging.info("[UWEB] Single list request: %s, cid: %s",
                         data, self.current_user.cid)
        except Exception as e:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            logging.exception("[UWEB] cid: %s single list  data format illegal. Exception: %s",
                              self.current_user.cid, e.args)
            self.write_ret(status)
            return

        try:
            # NOTE: we need return the event count to GUI at first time query
            if pagecnt == -1:
                res = QueryHelper.get_single_event(
                    tid, start_time, end_time, self.db)

                count = res.count
                d, m = divmod(count, page_size)
                pagecnt = (d + 1) if m else d

            res = QueryHelper.get_single_event_paged(
                tid, start_time, end_time, page_number * page_size, page_size, self.db)

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
        se_id = self.get_argument("se_id", '')
        single_event = QueryHelper.get_single_event_by_se_id(se_id, self.db)

        terminal = QueryHelper.get_terminal_info(
            single_event['tid'], self.db, self.redis)
        self.render("single_point.html",
                    single_id=single_event['sid'],
                    alias=terminal['alias'],
                    tid=single_event.get('tid', ''),
                    start_time=single_event.get('start_time'),
                    end_time=single_event.get('end_time'))
