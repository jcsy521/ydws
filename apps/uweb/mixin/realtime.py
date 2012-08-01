# -*- coding: utf-8 -*-

import logging
import time

from tornado.escape import json_decode, json_encode

from helpers.gfsenderhelper import GFSenderHelper
from helpers.seqgenerator import SeqGenerator
from codes.errorcode import ErrorCode
from codes.clwcode import CLWCode
from utils.dotdict import DotDict
from helpers.lbmphelper import handle_location
from constants import UWEB, EVENTER
from constants.MEMCACHED import ALIVED
from base import BaseMixin


class RealtimeMixin(BaseMixin):
    """Mix-in for realtime related functions."""

    def insert_location(self, location):
        """Insert the location into mysql and keep it in memcached.
        """
        lid = self.db.execute("INSERT INTO T_LOCATION"
                              "  VALUES (NULL, %s, %s, %s, %s, %s, %s, %s,"
                              "          %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                              location.dev_id, location.lat,
                              location.lon, 0, location.cLat, location.cLon,
                              location.timestamp, location.name,
                              EVENTER.CATEGORY.REALTIME,
                              location.type, location.speed, 0,
                              location.degree, location.status,
                              location.cellid, 0, 0)
        is_alived = self.memcached.get('is_alived')
        if (is_alived == ALIVED and location.valid == CLWCode.LOCATION_SUCCESS):
            mem_location = DotDict({'id':lid,
                                    'latitude':location.lat,
                                    'longitude':location.lon,
                                    'type':location.type,
                                    'clatitude':location.cLat,
                                    'clongitude':location.cLon,
                                    'timestamp':location.timestamp,
                                    'name':location.name,
                                    'degree':location.degree,
                                    'speed':location.speed})
            self.memcached.set(str(location.dev_id), mem_location, EVENTER.LOCATION_EXPIRY)

    def request_realtime(self, query, callback=None):
        """
        All realtime requests in REALTIME_VALID_INTERVAL will be considered as
        only one. If not, invoke gf and use handle_location of lbmphelper. 
        """
        is_alived = self.memcached.get('is_alived')
        if is_alived == ALIVED:
            location = self.memcached.get(str(self.current_user.tid))
            if location and (time.time() * 1000 - location.timestamp) > UWEB.REALTIME_VALID_INTERVAL:
                location = None
        else:
            # we should eventually search location from T_LOCATION
            location = self.db.get("SELECT id, clatitude, clongitude, latitude,"
                                   "       longitude, name, timestamp, type, degree"
                                   "  FROM T_LOCATION"
                                   "  WHERE tid = %s"
                                   "    AND NOT (clatitude = 0 AND clongitude = 0)"
                                   "    AND (%s BETWEEN timestamp - %s"
                                   "                AND timestamp + %s)"
                                   "  ORDER BY timestamp DESC"
                                   "  LIMIT 1",
                                   self.current_user.tid, query.timestamp,
                                   UWEB.REALTIME_VALID_INTERVAL, UWEB.REALTIME_VALID_INTERVAL)
                
        ret = DotDict(status=ErrorCode.SUCCESS,
                      message='',
                      location=location)

        location = None
        if (location and location.clatitude and location.clongitude):
            
            location['degree'] = int(round(float(location.degree)/36))
            if callback:
                callback(ret)
        else:
            def _on_finish(response):
                ret = DotDict(status=ErrorCode.SUCCESS,
                              message='',
                              location=DotDict())
                response = json_decode(response)
                if response['success'] == 0:
                    location = DotDict(response['position'])
                    location = handle_location(location, self.memcached, cellid=True if query.cellid_status == UWEB.CELLID_STATUS.ON else False)
                    if location.get('cLat') and location.get('cLon'):
                        ret.location.latitude = location.lat
                        ret.location.longitude = location.lon
                        ret.location.clongitude = location.cLon
                        ret.location.clatitude = location.cLat
                        ret.location.timestamp = location.timestamp
                        ret.location.name = location.name
                        ret.location.speed = location.speed
                        ret.location.type = location.type
                        ret.location.degree = int(round(float(location.degree)/36))
                    else: 
                        ret.status = ErrorCode.LOCATION_FAILED 
                        ret.message = ErrorCode.ERROR_MESSAGE[ret.status]
                        logging.error("[UWEB] realtime failed. status: %s, message: %s", ret.status, ret.message)

                    self.insert_location(location)
                else:
                    ret.status = response['success']
                    ret.message = response['info']
                    logging.error("[UWEB] realtime failed. status: %s, message: %s", ret.status, ret.message)
                
                if callback:
                    callback(ret)

            args = DotDict(seq=SeqGenerator.next(self.db),
                           tid=self.current_user.tid)
            GFSenderHelper.async_forward(GFSenderHelper.URLS.REALTIME, args,
                                         _on_finish)
        return ret
