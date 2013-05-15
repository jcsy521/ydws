# -*- coding: utf-8 -*-

import logging
from math import sin, cos, pi, acos 
import time
import random

from tornado.escape import json_decode

from helpers.lbmpsenderhelper import LbmpSenderHelper
from helpers.queryhelper import QueryHelper
from utils.misc import get_location_cache_key, get_location_key
from utils.dotdict import DotDict
from constants import EVENTER, GATEWAY, UWEB
from constants.MEMCACHED import ALIVED

def get_clocation_from_ge(lat, lon):
    """@params: lat, degree*3600000
                lon, degree*3600000
       @return: clat, degree
                clon, degree
    """
    clat = 0 
    clon = 0 
    try: 
        args = DotDict(lat=lat,
                       lon=lon)
        response = LbmpSenderHelper.forward(LbmpSenderHelper.URLS.GE, args)
        response = json_decode(response)
        if response['success'] == 0:
            clat = response['position']['clat']
            clon = response['position']['clon']
        else:
            clat = lat
            clon = lon
            logging.info("Get clocation from GE failed, used lat and lon for clat and clon, response: %s, args: %s",
                         response['info'], args)
    except Exception as e:
        logging.exception("Get latlon from GE failed. Exception: %s", e.args)
    return clat, clon

def get_latlon_from_cellid(mcc, mnc, lac, cid, sim):
    """@params: mcc, mobile country code 
                mnc, mobile network code 
                lac, location area code 
                cid, cellid
       @return: lat, degree
                lon, degree
    """
    lat = 0
    lon = 0
    try:
        args = dict(mcc=mcc, mnc=mnc,
                    lac=lac, cid=cid, sim=sim)
        response = LbmpSenderHelper.forward(LbmpSenderHelper.URLS.LE, args)
        response = json_decode(response) 
        if response['success'] == 0:
            lat = response['position']['lat']
            lon = response['position']['lon']
        else:
            logging.info("Get latlon from LE failed, response: %s, args: %s",
                         response['info'], args)
    except Exception as e:
        logging.exception("Get latlon from LE failed. Exception: %s", e.args)
    return lat, lon 

def handle_latlon_from_cellid(lat, lon, tid, redis, db):
    """Check the laton from cellid whether varied widely from the latlon from gps. 
       If the distance between them is less than a constant, modify the
       latlon of cellid to the latlon of last credible latlon of gps

       @params: lat, degree * 3600000
                lon, degree * 3600000
       @return: lat, degree * 3600000
                lon, degree * 3600000
    """
    distance = 0

    clat, clon = get_clocation_from_ge(lat, lon)
    location_key = get_location_key(tid)
    location = redis.getvalue(location_key)
    if location and location.get('type',None) == UWEB.LOCATE_FLAG.GPS: 
        distance = get_distance(int(clon), int(clat), int(location.clongitude), int(location.clatitude))
    else: 
        location = db.get("SELECT latitude, longitude, clatitude, clongitude FROM T_LOCATION"
                          "  WHERE tid = %s AND type = %s"
                          "    AND NOT (clatitude = 0 AND clongitude = 0)" 
                          " ORDER BY timestamp DESC" 
                          " LIMIT 1",
                          tid, UWEB.LOCATE_FLAG.GPS)
        if location: 
            distance = get_distance(int(clon), int(clat), int(location.clongitude), int(location.clatitude))

    logging.info("The distance :%s, tid:%s", distance, tid)
    if 0 < distance < UWEB.CELLID_MAX_OFFSET: 
        lon, lat = location.longitude, location.latitude
        logging.info("The distance: %s beteen cellid-latlon(%s, %s) and gps-latlon(%s, %s) is "
                     "lesser than %s, so change the cellid-latlon to gps-latlon",
                     distance, lat, lon, location.longitude, location.latitude, UWEB.CELLID_MAX_OFFSET)
    return lat, lon 

def get_location_name(clat, clon, redis):
    """@params: clat, degree*3600000
                clon, degree*3600000
                redis
       @return: name
    """
    name = ''
    try: 
        key = get_location_cache_key(int(clon), int(clat))
        name = redis.getvalue(key)
        if not name:
            args = dict(lon=(float(clon)/3600000),
                        lat=(float(clat)/3600000))
            response = LbmpSenderHelper.forward(LbmpSenderHelper.URLS.GV, args)
            response = json_decode(response)
            if response['success'] == 0:
                name = response.get('address')
                if name:
                    redis.setvalue(key, name, EVENTER.LOCATION_NAME_EXPIRY)
            else:
                logging.error("Get location name failed, response: %s, args: %s",
                              response.get('info'), args)
    except Exception as e:
        logging.exception("Get location name from GV failed. Exception: %s", e.args)
    return name 

def get_last_degree(location, redis, db):
    # if the car is still(speed < min_speed) or location is cellid, the degree is suspect.
    # use degree of last usable location
    is_alived = redis.getvalue('is_alived')
    if is_alived == ALIVED:
        location_key = get_location_key(location.dev_id)
        last_location = redis.getvalue(location_key)
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

def issue_cellid(location, db, redis):
    logging.info("%s Issue cellid...", location.dev_id)
    location.gps = 0
    location.type = 1
    location.degree = random.randint(0, 360)
    # 1: get latlon through cellid
    cellid_info = [int(item) for item in location.cellid.split(":")]
    sim = QueryHelper.get_tmobile_by_tid(location.dev_id, redis, db)
    location.lat, location.lon = get_latlon_from_cellid(cellid_info[0],cellid_info[1],cellid_info[2],cellid_info[3], sim)

    return location

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
    elif location.valid == GATEWAY.LOCATION_STATUS.UNMOVE:
        location_key = get_location_key(location.dev_id)
        last_location = redis.getvalue(location_key)
        if last_location:
            location.lat = last_location.latitude
            location.lon = last_location.longitude
            location.cLat = last_location.clatitude
            location.cLon = last_location.clongitude
            location.type = 1
            location.gps_time = int(time.time())
            location.gps = 0
        else:
            location.lat = 0
            location.lon = 0
            location.cLat = 0
            location.cLon = 0
            location.type = 0
            location.gps_time = int(time.time()) 
            location.degree = 0.00
            location.gps = 0
            if cellid:
                location = issue_cellid(location, db, redis)
    elif location.valid == GATEWAY.LOCATION_STATUS.MOVE:
        location.lat = 0
        location.lon = 0
        location.cLat = 0
        location.cLon = 0
        location.type = 0
        location.gps_time = int(time.time()) 
        location.degree = 0.00
        location.gps = 0
        if cellid:
            location = issue_cellid(location, db, redis)
    else:
        location.lat = 0
        location.lon = 0
        location.cLat = 0
        location.cLon = 0
        location.type = 0
        location.gps_time = int(time.time()) 
        location.degree = 0.00
        #if db:
        #    location.degree = get_last_degree(location, redis, db)
        location.gps = 0
        if cellid:
            # 1: issue cellid
            location = issue_cellid(location, db, redis)
            if location.lon and location.lat:
                # 2: check the location whether is odd 
                location_key = get_location_key(location.dev_id)
                old_location = redis.getvalue(location_key)
                if old_location:
                    distance = get_distance(location.lon,
                                            location.lat,
                                            old_location.longitude,
                                            old_location.latitude)
                    if distance > 10000 and (location.gps_time - old_location.timestamp <= 60*60):
                        location.lat, location.lon = (old_location.latitude, old_location.longitude)
                        logging.info("[LBMPHELPER] drop odd location, new location: %s, old location: %s, distance: %s",
                                     location, old_location, distance)

                # 3: if there is a close gps-latlon, modify the cellid-latlon
                location.lat, location.lon = handle_latlon_from_cellid(location.lat, location.lon, location.dev_id, redis, db)

                #if location.lat and location.lon:
                #    location = filter_location(location, memcached)


    if location and location.lat and location.lon:
        location.cLat, location.cLon = get_clocation_from_ge(location.lat, location.lon)
        #if (location['t'] == EVENTER.INFO_TYPE.REPORT or
        #    location['command'] == GATEWAY.T_MESSAGE_TYPE.LOCATIONDESC):
        # NOTE: change it temporarily: in platform get loction name of all
        if location.cLat and location.cLon:
            location.name = get_location_name(location.cLat, location.cLon, redis)

    if location['t'] == EVENTER.INFO_TYPE.POSITION:
        location.category = EVENTER.CATEGORY.REALTIME
    elif location['t'] == EVENTER.INFO_TYPE.REPORT:
        location.category = EVENTER.CATEGORY[location.rName]
    else:
        location.category = EVENTER.CATEGORY.UNKNOWN

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

    location_key = get_location_key(location.dev_id)
    old_location = redis.getvalue(location_key)
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

