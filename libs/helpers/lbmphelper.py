# -*- coding: utf-8 -*-

import logging
from math import sin, cos, pi, acos 
import time

from tornado.escape import json_decode

from helpers.lbmpsenderhelper import LbmpSenderHelper
from utils.misc import get_location_cache_key, get_alarm_status_key
from utils.dotdict import DotDict
from constants import EVENTER, GATEWAY, UWEB
from constants.MEMCACHED import ALIVED

def get_clocation_from_ge(location):
    response = LbmpSenderHelper.forward(LbmpSenderHelper.URLS.GE, location)
    response = json_decode(response)
    if response['success'] == 0:
        location.cLat = response['position']['clat']
        location.cLon = response['position']['clon']
    else:
        logging.info("Get clocation from GE error: %s, location: %s",
                     response['info'], location)
        location.cLat = 0 
        location.cLon = 0 

    return location.cLat, location.cLon

def get_latlon_from_cellid(location):
    if location.cellid:
        try:
            cellid_info = [int(item) for item in location.cellid.split(":")]
            args = dict(mcc=cellid_info[0], mnc=cellid_info[1],
                        lac=cellid_info[2], cid=cellid_info[3])
            response = LbmpSenderHelper.forward(LbmpSenderHelper.URLS.LE, args)
            response = json_decode(response) 
            if response['success'] == 0:
                location.lat = response['position']['lat']
                location.lon = response['position']['lon']
                location.valid = GATEWAY.LOCATION_STATUS.SUCCESS 
            else:
                logging.info("Get clocation from GE error: %s, locaton: %s",
                             response['info'], location)
        except:
            logging.exception("Parse cellid: %s error.", location.cellid)

    return location

def get_location_name(location, redis):
    key = get_location_cache_key(int(location.cLon), int(location.cLat))
    location.name = redis.getvalue(key)
    if not location.name:
        args = dict(lon=(float(location.cLon)/3600000),
                    lat=(float(location.cLat)/3600000))
        response = LbmpSenderHelper.forward(LbmpSenderHelper.URLS.GV, args)
        response = json_decode(response)
        if response['success'] == 0:
            location.name = response.get('address')
            if location.name:
                redis.setvalue(key, location.name, EVENTER.LOCATION_NAME_EXPIRY)
        else:
            logging.error("Get location name error: %s, %s",
                          response.get('info'), location.dev_id)

    return location.name 

def get_last_degree(location, redis, db):
    # if the car is still(speed < min_speed) or location is cellid, the degree is suspect.
    # use degree of last usable location
    is_alived = redis.getvalue('is_alived')
    if is_alived == ALIVED:
        last_location = redis.getvalue(str(location.dev_id))
    else:
        last_location = db.get("SELECT degree FROM T_LOCATION"
                               "  WHERE tid = %s"
                               "    AND type = 0"
                               "    AND (%s BETWEEN timestamp - %s"
                               "                AND timestamp + %s)"
                               "  ORDER BY timestamp DESC"
                               "  LIMIT 1",
                               location.dev_id, location.timestamp,
                               EVENTER.LOCATION_EXPIRY * 1000,
                               EVENTER.LOCATION_EXPIRY * 1000)
    if last_location:
        location.degree = last_location.degree

    return float(location.degree)

def handle_location(location, redis, cellid=False, db=None):
    """
    @param location: position/report/locationdesc/pvt
           memcached
           cellid: if True issue cellid
    @return location
    """
    location = DotDict(location)
    if location.valid == GATEWAY.LOCATION_STATUS.SUCCESS:
        location.type = 0
        if location.get('speed') is not None and location.speed <= UWEB.SPEED_DIFF:
            location.degree = get_last_degree(location, redis, db)
    else:
        location.lat = 0
        location.lon = 0
        location.cLat = 0
        location.cLon = 0
        location.type = 0
        location.gps_time = int(time.time()) 
        if db:
            location.degree = get_last_degree(location, redis, db)
        if cellid:
            location.type = 1
            location = get_latlon_from_cellid(location)
            #if location.lat and location.lon:
            #    location = filter_location(location, memcached)


    if location and location.lat and location.lon:
        location.cLat, location.cLon = get_clocation_from_ge(location)
        if (location['t'] == EVENTER.INFO_TYPE.REPORT or
            location['command'] == GATEWAY.T_MESSAGE_TYPE.LOCATIONDESC):
            location.name = get_location_name(location, redis)

    if location['t'] == EVENTER.INFO_TYPE.POSITION:
        location.category = EVENTER.CATEGORY.REALTIME
    elif location['t'] == EVENTER.INFO_TYPE.REPORT:
        location.category = EVENTER.CATEGORY[location.rName]
    else:
        location.category = EVENTER.CATEGORY.UNKNOWN

    #alarm_key = get_alarm_status_key(location.dev_id)
    #alarm_status = redis.getvalue(alarm_key)
    #if alarm_status != location.category:
    #    redis.setvalue(alarm_key, location.category)

    return location


def get_distance(lon1, lat1, lon2, lat2): 
    """
    Receive a couple of longitude and latitude, and return the distance
    of the tow location.
    Principle:  
    1. distance = R * radian = R * degree * pi / 180 
    2. degree = arcos(c) = arcos(cos(lat1)cos(lat2)cos(lon1-lon2)+sin(lat1)sin(lat2)) 

    @params: lon1, lat1, lon2, lat2 #degree*3600000, type=int
    @retuns: d, metre
    """
    if (lon1 == lon2) and (lat1 == lat2):
        return 0 
    EARTH_RADIUS_METER = 6370000.0 # metre. keep same with front-end.
    def deg2rad(d):
        """degree to radian"""
        return d*pi/180.0
    lon1 = deg2rad(lon1/3600000.0)
    lon2 = deg2rad(lon2/3600000.0)
    lat1 = deg2rad(lat1/3600000.0)
    lat2 = deg2rad(lat2/3600000.0)
    c = cos(lat1) * cos(lat2) * cos(lon1-lon2) + sin(lat1) * sin(lat2) 
    d = EARTH_RADIUS_METER * acos(c) 

    return d 

def filter_location(location, redis):
    """
    workflow:
    if old_location:
        if distance <= MIN_DISTANCE:
            just a little migration cause by lbmp
        else:
            if distance > MAX_DISTANCE or speed > MAX_SPEED:
                odd location 
            elif old_location.speed:
                if (speed > HIGH_SPEED and ratio > MAX_RATIO):
                    odd location
            else:
                pass 
    else:
        first location, save it!
    """
    MIN_DISTANCE = 50  # m
    MAX_DISTANCE = 10000 # m
    HIGH_SPEED = 60 # km/h
    MAX_SPEED = 320 # km/h
    MAX_RATIO = 50 # ratio of two speed

    odd_flag = False
    speed = 0
    ratio = 0
    distance = 0

    old_location = redis.getvalue(str(location.dev_id))
    if old_location:
        # not first location, need to check distance and speed
        interval = location.timestamp - old_location.timestamp
        distance = get_distance(location.lon, 
                                location.lat, 
                                old_location.longitude,
                                old_location.latitude)
        if distance <= MIN_DISTANCE:
            # a little migration between two points cause by lbmp, not to filter
            speed = old_location.speed if old_location.speed else 0
        else:
            if interval != 0:
                speed = float(distance / interval) * 3600 #km/h

            if distance > MAX_DISTANCE or speed > MAX_SPEED:
                odd_flag = True
            elif old_location.speed:
                ratio = float(speed / float(old_location.speed))
                if speed > HIGH_SPEED and ratio > MAX_RATIO:
                    # speed change too fast, check it!
                    odd_flag = True
            else:
                pass

        if odd_flag:
            logging.warn("[EVENTER] Receive odd location: %s, distance: %sm, speed: %skm/h,"
                         " ratio: %s, and drop it!  The last location: %s",
                         location, distance, speed, ratio, old_location)
            return None

    location['speed'] = speed
    return location

