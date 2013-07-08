# -*- coding: utf-8 -*-

import logging
import time

from tornado.escape import json_decode, json_encode

from helpers.gfsenderhelper import GFSenderHelper
from helpers.seqgenerator import SeqGenerator
from helpers.queryhelper import QueryHelper 
from codes.errorcode import ErrorCode
from utils.dotdict import DotDict
from helpers.lbmphelper import handle_location, get_locations_with_clatlon
from utils.misc import get_location_key 
from utils.public import insert_location
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
            self.db.execute("UPDATE T_TERMINAL_INFO SET " + set_clause + " WHERE tid = %s", 
                            location.dev_id)
    
    def update_location(self, location):
        self.db.execute("UPDATE T_LOCATION"
                        "  SET name = %s,"
                        "      latitude = %s,"
                        "      longitude = %s,"
                        "      clatitude = %s,"
                        "      clongitude = %s,"
                        "      type = %s,"
                        "      timestamp = %s"
                        "  WHERE id = %s",	
                        location.name, location.lat, location.lon,
                        location.cLat, location.cLon, location.type,
                        location.gps_time, location.id)
        is_alived = self.redis.getvalue('is_alived')
        if (is_alived == ALIVED and location.cLat and location.cLon):
            mem_location = DotDict({'id':location.id,
                                    'latitude':location.lat,
                                    'longitude':location.lon,
                                    'type':location.type,
                                    'clatitude':location.cLat,
                                    'clongitude':location.cLon,
                                    'timestamp':location.gps_time,
                                    'name':location.name,
                                    'degree':location.degree,
                                    'speed':location.speed})
            location_key = get_location_key(str(location.dev_id))
            self.redis.setvalue(location_key, mem_location, EVENTER.LOCATION_EXPIRY)

    def get_realtime(self, uid, sim):
        """Get the location of the current realtime request.
        workflow:
        if there is alive memcached, we can get location from it,
        else get location from db
        return result to user browser
        """
        ret = DotDict(status=ErrorCode.SUCCESS,
                      message='',
                      location=None)

        is_alived = self.redis.getvalue('is_alived')
        if is_alived == ALIVED:
            location_key = get_location_key(str(self.current_user.tid))
            location = self.redis.getvalue(location_key)
            # after 1 minute, the location is invalid, get it again.
            if location and abs(time.time() - int(location.timestamp)) > UWEB.REALTIME_VALID_INTERVAL:
                location = None
        else:
            query_time = int(time.time())
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
                                   self.current_user.tid, query_time,
                                   UWEB.REALTIME_VALID_INTERVAL, UWEB.REALTIME_VALID_INTERVAL)

        locations = [location,] 
        locations = get_locations_with_clatlon(locations, self.db) 
        location = locations[0]

        if (location and location.clatitude and location.clongitude):
            if not location.name:
                location.name = ''
            if location.has_key('id'):
                del location['id']

            location['degree'] = float(location.degree)
            location['tid'] = self.current_user.tid
            ret.location = location

        return ret

    def request_realtime(self, query, callback=None):
        """
        All realtime requests in REALTIME_VALID_INTERVAL will be considered as
        only one. If not, invoke gf and use handle_location of lbmphelper. 
        """
        is_alived = self.redis.getvalue('is_alived')
        if is_alived == ALIVED:
            location_key = get_location_key(str(self.current_user.tid))
            location = self.redis.getvalue(location_key)
            # after 1 minute, the location is invalid, get it again.
            if location and abs(time.time() - int(location.timestamp)) > UWEB.REALTIME_VALID_INTERVAL:
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
            if (location and not location.name):
                location.name = ''

                
        ret = DotDict(status=ErrorCode.SUCCESS,
                      message='',
                      location=None)

        locations = [location,] 
        locations = get_locations_with_clatlon(locations, self.db) 
        location = locations[0]

        if (location and location.clatitude and location.clongitude):
            if location.has_key('id'):
                del location['id']
            
            location['degree'] = float(location.degree)
            location['tid'] = self.current_user.tid
            ret.location = location
            if callback:
                callback(ret)
                #NOTE: after callback(ret), callback must be setted as null, and do not callback again.
                callback=None

        if query.locate_flag == UWEB.LOCATE_FLAG.CELLID:
            loc = self.db.get("SELECT id, cellid, degree, speed"
                              "  FROM T_LOCATION WHERE tid = %s"
                              "  AND cellid IS NOT NULL "
                              "  AND cellid <> '' "
                              #"  AND clongitude = 0"
                              #"  AND clatitude = 0"
                              #"  AND (%s BETWEEN timestamp - %s"
                              #"              AND timestamp + %s)"
                              "  ORDER BY timestamp DESC"
                              "  LIMIT 1",
                              self.current_user.tid)
                              #query.timestamp,
                              #UWEB.LOCATION_VALID_INTERVAL,
                              #UWEB.LOCATION_VALID_INTERVAL)
            if loc:
                location = DotDict(id=loc.id,
                                   valid=GATEWAY.LOCATION_STATUS.FAILED,
                                   t=EVENTER.INFO_TYPE.POSITION, 
                                   dev_id=self.current_user.tid,
                                   lat=0,
                                   lon=0,
                                   cLat=0,
                                   cLon=0,
                                   gps_time=int(time.time()),
                                   type=1,
                                   speed=float(loc.speed) if loc else 0.0,
                                   degree=float(loc.degree) if loc else 0.0,
                                   name='',
                                   cellid=loc.cellid if loc else None)

                location = handle_location(location, self.redis,
                                           cellid=True,
                                           db=self.db)

                if location.get('cLat') and location.get('cLon'):
                    ret.location = DotDict()
                    ret.location.latitude = location.lat
                    ret.location.longitude = location.lon
                    ret.location.clongitude = location.cLon
                    ret.location.clatitude = location.cLat
                    ret.location.timestamp = location.gps_time
                    ret.location.name = location.name if location.name else ''
                    ret.location.speed = location.speed
                    ret.location.type = location.type
                    ret.location.tid = self.current_user.tid
                    ret.location.degree = float(location.degree)
                    self.update_location(location)
                else:
                    ret.status = ErrorCode.LOCATION_CELLID_FAILED 
                    ret.message = ErrorCode.ERROR_MESSAGE[ret.status]
            else:
                logging.info("[UWEB] do not find any cellid info from db. tid: %s", self.current_user.tid)
                ret.status = ErrorCode.LOCATION_CELLID_FAILED 
                ret.message = ErrorCode.ERROR_MESSAGE[ret.status]

            if callback:
                callback(ret)
        else: 
            def _on_finish(response):
                ret = DotDict(status=ErrorCode.SUCCESS,
                              message='',
                              location=None)
                response = json_decode(response)
                if response['success'] == ErrorCode.SUCCESS:
                    location = DotDict(response['position'])

                    location = handle_location(location, self.redis,
                                               cellid=False,
                                               db=self.db)

                    insert_location(location, self.db, self.redis)
                    if location.get('cLat') and location.get('cLon'):
                        ret.location = DotDict()
                        ret.location.latitude = location.lat
                        ret.location.longitude = location.lon
                        ret.location.clongitude = location.cLon
                        ret.location.clatitude = location.cLat
                        ret.location.timestamp = location.gps_time
                        ret.location.name = location.name if location.name else ''
                        ret.location.speed = location.speed
                        ret.location.type = location.type
                        ret.location.tid = self.current_user.tid
                        ret.location.degree = float(location.degree)
                        self.update_terminal_status(location)
                else:
                    if response['success'] in (ErrorCode.TERMINAL_OFFLINE, ErrorCode.TERMINAL_TIME_OUT): 
                        self.send_lq_sms(self.current_user.sim, self.current_user.tid, SMS.LQ.WEB)
                    ret.status = response['success']
                    ret.message = response['info']
                    logging.error("[UWEB] realtime failed. tid: %s, status: %s, message: %s",
                                  self.current_user.tid, ret.status, ret.message)
                
                if callback:
                    callback(ret)

            seq = str(int(time.time()*1000))[-4:]
            args = DotDict(seq=seq,
                           tid=self.current_user.tid)
            GFSenderHelper.async_forward(GFSenderHelper.URLS.REALTIME, args,
                                         _on_finish)
