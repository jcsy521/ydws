# -*- coding: utf-8 -*-

import logging

import tornado.web
from tornado.escape import json_encode, json_decode

from utils.dotdict import DotDict
from utils.misc import DUMMY_IDS, str_to_list, get_region_status_key
from utils.checker import check_sql_injection
from constants import UWEB, LIMIT
from codes.errorcode import ErrorCode
from base import BaseHandler, authenticated


class RegionDetailHandler(BaseHandler):

    @authenticated
    @tornado.web.removeslash
    def get(self):
        """Get the detail of a region. 
        """ 
        status = ErrorCode.SUCCESS
        try:
            rid = self.get_argument('rid')
        except Exception as e:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            logging.exception("[UWEB] cid: %s get report region data format illegal. Exception: %s", 
                              self.current_user.cid, e.args) 
            self.write_ret(status)
            return
        
        try:
            region = self.db.get("SELECT id AS region_id, name AS region_name, longitude, latitude,"
                                 "  radius, points, shape AS region_shape"
                                 "  FROM T_REGION"
                                 "  WHERE id = %s",
                                 rid)
            if not region:
                status = ErrorCode.REGION_NOT_EXISTED
                self.write_ret(status)
                return

            if region.region_shape == UWEB.REGION_SHAPE.CIRCLE:
                res = DotDict(region_id=region.region_id,
                            region_name=region.region_name,
                            region_shape=region.region_shape,
                            circle=DotDict(latitude=region.latitude,
                                           longitude=region.longitude,
                                           radius=region.radius),
                            )
            elif region.region_shape == UWEB.REGION_SHAPE.POLYGON:
                polygon = []
                points = region.points
                point_lst = points.split(':')
                for point in point_lst:
                    latlon = point.split(',')
                    dct = {'latitude':latlon[0],
                           'longitude':latlon[1]}
                    polygon.append(dct)
                
                res = DotDict(region_id=region.region_id,
                            region_name=region.region_name,
                            region_shape=region.region_shape,
                            polygon=polygon)
 
            self.write_ret(status,
                           dict_=DotDict(res=res))
        except Exception as e:
            logging.exception("[UWEB] cid: %s get report region failed. Exception: %s", 
                              self.current_user.cid, e.args) 
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)
       
class RegionHandler(BaseHandler):

    @authenticated
    @tornado.web.removeslash
    def get(self):
        """ Get regions by tid"""
        status = ErrorCode.SUCCESS
        try:
            tid = self.get_argument('tid')
        except Exception as e:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            logging.exception("[UWEB] uid: %s get region bind data format illegal. Exception: %s",
                              self.current_user.uid, e.args)
            self.write_ret(status)
            return

        try:
            res = []
            regions = self.db.query("SELECT tr.id AS region_id, tr.name AS region_name,"
                                    "       tr.longitude, tr.latitude, tr.radius,"
                                    "       tr.points, tr.shape AS region_shape"
                                    "  FROM T_REGION tr, T_REGION_TERMINAL trt"
                                    "  WHERE tr.id = trt.rid"
                                    "  AND trt.tid = %s",
                                    tid)
            for region in regions:
               if region.region_shape == UWEB.REGION_SHAPE.CIRCLE:
                   r = DotDict(region_id=region.region_id,
                               region_name=region.region_name,
                               region_shape=region.region_shape,
                               circle=DotDict(latitude=region.latitude,
                                              longitude=region.longitude,
                                              radius=region.radius),
                               )
               elif region.region_shape == UWEB.REGION_SHAPE.POLYGON:
                   polygon = []
                   points = region.points
                   point_lst = points.split(':')
                   for point in point_lst:
                       latlon = point.split(',')
                       dct = {'latitude':latlon[0],
                              'longitude':latlon[1]}
                       polygon.append(dct)
                   
                   r = DotDict(region_id=region.region_id,
                               region_name=region.region_name,
                               region_shape=region.region_shape,
                               polygon=polygon)
 
               res.append(r)
            self.write_ret(status,
                           dict_=DotDict(res=res))
        except Exception as e:
            logging.exception("[UWEB] tid: %s get regions failed. Exception: %s",
                              tid, e.args)
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)

    @authenticated
    @tornado.web.removeslash
    def post(self):
        """Create a new region.
        """
        try:
            data = DotDict(json_decode(self.request.body))
            tid = data.tid
            region_name = data.region_name
            region_shape = int(data.region_shape)
            logging.info("[UWEB] Add region request: %s, uid: %s",
                         data, self.current_user.uid)
        except Exception as e:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            logging.exception("[UWEB] uid: %s create region data format illegal. Exception: %s",
                              self.current_user.uid, e.args)
            self.write_ret(status)
            return

        try:
            regions = self.db.query("SELECT id"
                                    "  FROM T_REGION_TERMINAL"
                                    "  WHERE tid = %s",
                                    tid)
            if len(regions) > LIMIT.REGION - 1:
                self.write_ret(ErrorCode.REGION_ADDITION_EXCESS)
                return

            status = ErrorCode.SUCCESS
            rid = -1

            if region_shape == UWEB.REGION_SHAPE.CIRCLE:
                circle = DotDict(data.circle)
                longitude = circle.longitude 
                latitude = circle.latitude 
                radius = circle.radius
                rid = self.db.execute("INSERT T_REGION(name, longitude, latitude, radius, shape, uid)"
                                      "  VALUES(%s, %s, %s, %s, %s, %s)",
                                      region_name, longitude, latitude, radius, region_shape, self.current_user.uid)

                self.db.execute("INSERT INTO T_REGION_TERMINAL(rid, tid)"
                                "  VALUES(%s, %s)",
                                rid, tid)
            elif region_shape == UWEB.REGION_SHAPE.POLYGON:
                polygon = data.polygon
                points_lst = [] 
                points = ''
                for p in polygon:
                    tmp = ','.join([str(p['latitude']), str(p['longitude'])])
                    points += tmp
                    points_lst.append(tmp)
                points = ':'.join(points_lst) 
                rid = self.db.execute("INSERT T_REGION(name, points, shape, uid)"
                                      "  VALUES(%s, %s, %s, %s)",
                                      region_name, points, region_shape, self.current_user.uid)

                self.db.execute("INSERT INTO T_REGION_TERMINAL(rid, tid)"
                                "  VALUES(%s, %s)",
                                rid, tid)
 
            else: 
                logging.error("[UWEB] Add region failed, unknown region_shape: %s, uid: %s",
                              region_shape, self.current_user.uid)
                pass
            
            self.write_ret(status,
                           dict_=DotDict(rid=rid))
        except Exception as e:
            logging.exception("[UWEB] uid: %s create region for tid: %s failed. Exception: %s",
                              self.current_user.uid, data.tid, e.args)
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)


    @authenticated
    @tornado.web.removeslash
    def delete(self):
        """Delete region.
        """
        try:
            delete_ids = map(int, str_to_list(self.get_argument('ids', None)))
            logging.info("[UWEB] delete region: %s, cid: %s", 
                         delete_ids, self.current_user.cid)
        except Exception as e:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            self.write_ret(status)

        try:
            status = ErrorCode.SUCCESS
            #1: delete redis region status
            for region_id in delete_ids:
                terminals = self.db.query("SELECT tid"
                                          "  FROM T_REGION_TERMINAL"
                                          "  WHERE rid = %s",
                                          region_id)
                for terminal in terminals:
                    region_status_key = get_region_status_key(terminal.tid, region_id)
                    self.redis.delete(region_status_key)
            
            #2: delete region, region event and region terminal relation
            self.db.execute("DELETE FROM T_REGION WHERE id IN %s",
                            tuple(delete_ids + DUMMY_IDS)) 

            self.db.execute("DELETE FROM T_EVENT WHERE rid IN %s",
                            tuple(delete_ids + DUMMY_IDS))

            self.db.execute("DELETE FROM T_REGION_TERMINAL WHERE rid IN %s",
                            tuple(delete_ids + DUMMY_IDS))
            
            self.write_ret(status)
        except Exception as e:
            logging.exception("[UWEB] cid: %s delete region failed. Exception: %s", 
                              self.current_user.cid, e.args) 
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)
