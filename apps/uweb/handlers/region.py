# -*- coding: utf-8 -*-

import logging

import tornado.web
from tornado.escape import json_encode, json_decode

from utils.dotdict import DotDict
from utils.misc import DUMMY_IDS, str_to_list, get_region_status_key
from utils.checker import check_sql_injection
from constants import UWEB
from codes.errorcode import ErrorCode
from base import BaseHandler, authenticated


class RegionEventHandler(BaseHandler):

    @authenticated
    @tornado.web.removeslash
    def get(self):
        """ """ 
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
            region = self.db.get("SELECT id AS region_id, name AS region_name, longitude, latitude, radius"
                                 "  FROM T_REGION"
                                 "  WHERE id = %s",
                                 rid)
            self.write_ret(status,
                           dict_=DotDict(region=region))
        except Exception as e:
            logging.exception("[UWEB] cid: %s get report region failed. Exception: %s", 
                              self.current_user.cid, e.args) 
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)
        
       
class RegionHandler(BaseHandler):

    @authenticated
    @tornado.web.removeslash
    def get(self):
        """ """ 
        try:
            status = ErrorCode.SUCCESS
            regions = self.db.query("SELECT id AS region_id, name AS region_name, longitude, latitude, radius "
                                    "  FROM T_REGION"
                                    "  WHERE cid = %s",
                                    self.current_user.cid)
            
            self.write_ret(status,
                           dict_=DotDict(regions=regions))
        except Exception as e:
            logging.exception("[UWEB] cid: %s get regions failed. Exception: %s", 
                              self.current_user.cid, e.args) 
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)


    @authenticated
    @tornado.web.removeslash
    def post(self):
        """Create a new region.
        """
        try:
            data = DotDict(json_decode(self.request.body))
            logging.info("[UWEB] add region request: %s, cid: %s", 
                         data, self.current_user.cid)
        except Exception as e:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            logging.exception("[UWEB] cid: %s create region data format illegal. Exception: %s", 
                              self.current_user.cid, e.args) 
            self.write_ret(status)
            return

        try:
            status = ErrorCode.SUCCESS
            region_name = data.region_name
            longitude = data.longitude
            latitude = data.latitude
            radius = data.radius
            
            self.db.execute("INSERT T_REGION(id, name, longitude, latitude, radius, cid)"
                            "  VALUES(NULL, %s, %s, %s, %s, %s)",
                            region_name, longitude, latitude, radius, self.current_user.cid)
            
            self.write_ret(status)
        except Exception as e:
            logging.exception("[UWEB] cid: %s create region failed. Exception: %s", 
                              self.current_user.cid, e.args) 
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
            return

        try:
            status = ErrorCode.SUCCESS
            # delete redis region status
            for region_id in delete_ids:
                terminals = self.db.query("SELECT tid"
                                          "  FROM T_REGION_TERMINAL"
                                          "  WHERE rid = %s",
                                          region_id)
                for terminal in terminals:
                    region_status_key = get_region_status_key(terminal.tid, region_id)
                    self.redis.delete(region_status_key)
            
            # delete region, region event and region terminal relation
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


