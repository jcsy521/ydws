# -*- coding: utf-8 -*-

import logging
import time

from helpers.queryhelper import QueryHelper 
from codes.errorcode import ErrorCode
from utils.dotdict import DotDict
from helpers.lbmphelper import (get_locations_with_clatlon, 
     get_latlon_from_cellid, get_location_name, get_clocation_from_ge)
from utils.misc import get_location_key 
from utils.public import insert_location
from constants import EVENTER
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
                                    'degree':float(location.degree),
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
        location = QueryHelper.get_location_info(self.current_user.tid, self.db, self.redis)

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
        location = QueryHelper.get_location_info(self.current_user.tid, self.db, self.redis)
        if location and location['name'] is None:
            location['name'] = '' 
                
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
                return

        lat, lon = get_latlon_from_cellid(0,0,0,0, self.current_user.sim)
        clat, clon = get_clocation_from_ge([lat,],[lon,]) 
        clat = int(clat[0]) if len(clat)>0 else 0 
        clon = int(clon[0]) if len(clon)>0 else 0 
        name = get_location_name(clat, clon, self.redis)
        
        location = DotDict(category = 1, # cellid
                           dev_id = self.current_user.tid, 
                           lat = lat, 
                           lon = lon, 
                           cLat = clat, 
                           cLon = clon, 
                           alt = 0,
                           gps_time = int(time.time()), 
                           type = 1, 
                           speed = 0.0, 
                           degree = 0.0, 
                           name = name, 
                           cellid = None,
                           locate_error = 20)
        if clat and clon:
            ret.location = DotDict()
            ret.location.latitude = lat
            ret.location.longitude = lon
            ret.location.clongitude = clon
            ret.location.clatitude = clat
            ret.location.timestamp = int(time.time()) 
            ret.location.name = name
            ret.location.speed = 0
            ret.location.type = 1
            ret.location.tid = self.current_user.tid
            ret.location.degree = 0.0 
            ret.location.locte_error = 20 
            insert_location(location, self.db, self.redis)
            logging.info("[UWEB] tid %s cellid query success", self.current_user.tid)
        else:
            ret.status = ErrorCode.LOCATION_CELLID_FAILED 
            ret.message = ErrorCode.ERROR_MESSAGE[ret.status]
            logging.info("[UWEB] Do not find any location, and cellid query failed. tid: %s", 
                         self.current_user.tid)

        if callback:
            callback(ret)