# -*- coding: utf-8 -*-

"""This module is designed for regions.
"""

import logging

import tornado.web
from tornado.escape import json_encode, json_decode

from utils.dotdict import DotDict
from utils.misc import DUMMY_IDS, str_to_list, get_region_status_key
from utils.public import add_region, delete_region
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
            region = QueryHelper.get_region(rid, self.db)
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
            regions = QueryHelper.get_regions(tid, self.db)
            for region in regions:
               if region.region_shape == UWEB.REGION_SHAPE.CIRCLE:
                   r = DotDict(region_id=region.region_id,
                               region_name=region.region_name,
                               region_shape=region.region_shape,
                               circle=DotDict(latitude=region.region_latitude,
                                              longitude=region.region_longitude,
                                              radius=region.region_radius),
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
            logging.exception("[UWEB] Get regions failed. tid: %s，Exception: %s",
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
            regions = QueryHelper.get_regions(tid, self.db)
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
                region_info = dict(region_name=region_name,
                                   longitude=longitude,
                                   latitude=latitude,
                                   radius=radius,
                                   shape=region_shape,
                                   uid=self.current_user.uid,
                                   tid=tid)                 
                rid = add_region(region_info, self.db, self.redis)
            elif region_shape == UWEB.REGION_SHAPE.POLYGON:
                polygon = data.polygon
                points_lst = [] 
                points = ''
                for p in polygon:
                    tmp = ','.join([str(p['latitude']), str(p['longitude'])])
                    points += tmp
                    points_lst.append(tmp)
                points = ':'.join(points_lst) 

                region_info = dict(region_name=region_name,
                                   points=points,                                  
                                   shape=region_shape,
                                   uid=self.current_user.uid,
                                   tid=tid)                 
                rid = add_region(region_info, self.db, self.redis) 
            else: 
                logging.error("[UWEB] Add region failed, unknown region_shape: %s, uid: %s",
                              region_shape, self.current_user.uid)          
            self.write_ret(status,
                           dict_=DotDict(rid=rid))
        except Exception as e:
            logging.exception("[UWEB] Create region failed. uid: %s, tid: %s. Exception: %s",
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
            delete_region(delete_ids, self.db, self.redis)           
            self.write_ret(status)
        except Exception as e:
            logging.exception("[UWEB] cid: %s delete region failed. Exception: %s", 
                              self.current_user.cid, e.args) 
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)
