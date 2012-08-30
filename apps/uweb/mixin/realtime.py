# -*- coding: utf-8 -*-

import logging
import time

from tornado.escape import json_decode, json_encode

from helpers.gfsenderhelper import GFSenderHelper
from helpers.seqgenerator import SeqGenerator
from helpers.queryhelper import QueryHelper 
from codes.errorcode import ErrorCode
from utils.dotdict import DotDict
from utils.misc import get_alias_key
from helpers.lbmphelper import handle_location
from constants import UWEB, EVENTER, GATEWAY, SMS
from constants.MEMCACHED import ALIVED
from base import BaseMixin


class RealtimeMixin(BaseMixin):
    """Mix-in for realtime related functions."""
 
    def update_terminal_status(self, location): 
        fields = [] 
        keys = ['gps', 'gsm', 'pbat', 'defend_status'] 
        for key in keys: 
            if location[key] is not None: 
                fields.append(key + " = " + location[key]) 
        set_clause = ','.join(fields) 
        if set_clause: 
            self.db.execute("UPDATE T_TERMINAL_INFO" " SET " + set_clause + " WHERE tid = %s", 
            location.dev_id)
    
    def insert_location(self, location):
        """Insert the location into mysql and keep it in memcached.
        """
        lid = self.db.execute("INSERT INTO T_LOCATION"
                              "  VALUES (NULL, %s, %s, %s, %s, %s, %s, %s,"
                              "          %s, %s, %s, %s, %s, %s)",
                              location.dev_id, location.lat, location.lon, 
                              0, location.cLat, location.cLon,
                              location.gps_time, location.name,
                              EVENTER.CATEGORY.REALTIME,
                              location.type, location.speed,
                              location.degree, location.cellid)
        is_alived = self.redis.getvalue('is_alived')
        if (is_alived == ALIVED and location.valid == GATEWAY.LOCATION_STATUS.SUCCESS):
            mem_location = DotDict({'id':lid,
                                    'latitude':location.lat,
                                    'longitude':location.lon,
                                    'type':location.type,
                                    'clatitude':location.cLat,
                                    'clongitude':location.cLon,
                                    'timestamp':location.gps_time,
                                    'name':location.name,
                                    'degree':location.degree,
                                    'speed':location.speed})
            self.redis.setvalue(str(location.dev_id), mem_location, EVENTER.LOCATION_EXPIRY)

    def request_realtime(self, query, callback=None):
        """
        All realtime requests in REALTIME_VALID_INTERVAL will be considered as
        only one. If not, invoke gf and use handle_location of lbmphelper. 
        """
        is_alived = self.redis.getvalue('is_alived')
        alias_key = get_alias_key(self.current_user.sim) 
        alias = self.redis.getvalue(alias_key)
        if not alias:
            t = QueryHelper.get_terminal_by_tid(self.current_user.tid, self.db)
            if t.alias:
                alias = t.alias
                self.redis.setvalue(alias_key, alias)
            else:
                alias = self.current_user.sim

        if is_alived == ALIVED:
            location = self.redis.getvalue(str(self.current_user.tid))
            if location and (time.time() - int(location.timestamp)) > UWEB.REALTIME_VALID_INTERVAL:
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

        if (location and location.clatitude and location.clongitude):
            
            location['degree'] = float(location.degree)
            location['tid'] = self.current_user.tid
            location['alias'] = alias  

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
                    location = handle_location(location, self.redis,
                                               cellid=True if int(query.cellid_status) == UWEB.CELLID_STATUS.ON else False,
                                               db=self.db)
                    if location.get('cLat') and location.get('cLon'):
                        ret.location.latitude = location.lat
                        ret.location.longitude = location.lon
                        ret.location.clongitude = location.cLon
                        ret.location.clatitude = location.cLat
                        ret.location.timestamp = location.gps_time
                        ret.location.name = location.name
                        ret.location.speed = location.speed
                        ret.location.type = location.type
                        ret.location.tid = self.current_user.tid
                        ret.location.alias = alias 
                        #ret.location.degree = int(round(float(location.degree)/36))
                        # now, provide the orginal degree.
                        ret.location.degree = float(location.degree)
                        self.insert_location(location)
                        self.update_terminal_status(location)
                    else: 
                        ret.status = ErrorCode.LOCATION_FAILED 
                        ret.message = ErrorCode.ERROR_MESSAGE[ret.status]
                        logging.error("[UWEB] realtime failed. status: %s, message: %s", ret.status, ret.message)
                else:
                    if response['success'] in (ErrorCode.TERMINAL_OFFLINE, ErrorCode.TERMINAL_TIME_OUT): 
                        self.send_lq_sms(self.current_user.sim, SMS.LQ.WEB)
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
