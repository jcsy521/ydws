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
from utils.geometry import PtInPolygon, DM_ZJGS_POLYGON 
from constants import EVENTER, GATEWAY, UWEB
from constants.MEMCACHED import ALIVED

#def get_last_location(tid, redis, db):
#    location_key = get_location_key(tid)
#    location = redis.getvalue(location_key)
#    if not location:
#        location = db.get("SELECT latitude, longitude, clatitude, clongitude FROM T_LOCATION"
#                          "  WHERE tid = %s"
#                          "    AND NOT (clatitude = 0 AND clongitude = 0)"
#                          " ORDER BY timestamp DESC"
#                          " LIMIT 1",
#                          tid)
#    return location

#def get_clocation_from_ge(lat, lon):
#    """@params: lat, degree*3600000
#                lon, degree*3600000
#       @return: clat, degree
#                clon, degree
#    """
#    clat = 0 
#    clon = 0 
#    try: 
#        args = DotDict(lat=lat,
#                       lon=lon)
#        response = LbmpSenderHelper.forward(LbmpSenderHelper.URLS.GE, args)
#        response = json_decode(response)
#        if response['success'] == 0:
#            clat = response['position']['clat']
#            clon = response['position']['clon']
#        else:
#            logging.info("Get clocation from GE failed, used 0,0 for clat and clon, response: %s, args: %s",
#                         response['info'], args)
#    except Exception as e:
#        logging.exception("Get latlon from GE failed. Exception: %s", e.args)
#    return clat, clon

def get_clocation_from_ge(lats, lons):
    """@params: lats, [degree*3600000, ...]
                lons, [degree*3600000, ...]
       @return: clats,[degree*3600000, ...]
                clons, [degree*3600000, ...]
    """
    # send 20 items for getting offset latlon every time.
    MAX_COUNT = 20 
    clats = [] 
    clons = [] 
    try: 
        # NOTE: if lats and lons has different number of items, or either
        # is a empty list, return clats and clons directly 
        if (len(lats) != len(lons)) or (not (lats and lons)):
            logging.error("[LBMPHELPER] Invalid data. len(lats)=%s, len(lons)=%s, lats: %s, lons: %s", 
                          len(lats), len(lons), lats, lons)
            return clats, clons

        #NOTE: when there are too many lats and lons, send 20 pairs one time till all is sent.
        d, m = divmod(len(lats), MAX_COUNT)
        rounds = (d + 1) if m else d
        for i in xrange(rounds):
            lats_item = lats[(i * MAX_COUNT) : ((i+1) * MAX_COUNT)]
            lons_item = lons[(i * MAX_COUNT) : ((i+1) * MAX_COUNT)]

            args = DotDict(lats=lats_item,
                           lons=lons_item)
            response = LbmpSenderHelper.forward(LbmpSenderHelper.URLS.GE, args)
            response = json_decode(response)
            if response['success'] == 0:
                clats_item = response['position']['clats']
                clons_item = response['position']['clons']
            else:
                # NOTE: porvide a dummy list
                clats_item = [0,] * len(lats_item)
                clons_item = [0,] * len(lons_item)
                logging.info("[LBMPHELPER] Get clocation from GE failed, response: %s, args: %s",
                             response['info'], args)
            clats.extend(clats_item)
            clons.extend(clons_item)
    except Exception as e:
        logging.exception("[LBMPHELPER] Get latlon from GE failed. Exception: %s", e.args)
    return clats, clons

def get_locations_with_clatlon(locations, db):
    # NOTE: if latlons are legal, but clatlons are illlegal, offset them
    # and update them in db. 
    if not locations:
        return []
    #modify_locations= []
    lats = []
    lons = []
    index_lst = []
    lids = []
    for i, location in enumerate(locations): 
        if location and not (location['clatitude'] and location['clongitude']):
            index_lst.append(i)
            lats.append(location['latitude'])
            lons.append(location['longitude'])
            lids.append(location['id'])
        else:
            #NOTE: the location has legal clatlon, there is noneed to offset.
            pass

    if not (lats and lons):
        return locations
    
    #NOTE:
    raw_locations = zip(lids, lats, lons, index_lst)
    logging.info("[LBMPHELPER] Raw location, num:%s, data:%s",
                 len(raw_locations), raw_locations)
    
    MAX_COUNT = 20
    d, m = divmod(len(index_lst), MAX_COUNT)
    rounds = (d + 1) if m else d 
    for i in xrange(rounds):
        modify_locations = []
        index_lst_ = index_lst[(i * MAX_COUNT) : ((i+1) * MAX_COUNT)]
        lats_ = lats[(i * MAX_COUNT) : ((i+1) * MAX_COUNT)]
        lons_ = lons[(i * MAX_COUNT) : ((i+1) * MAX_COUNT)] 
        clats, clons = get_clocation_from_ge(lats_, lons_) 
        if clats and clons:
            clatlons = zip(index_lst_, clats, clons)
            # NOTE: clatlons, a list like [(index, clat, clon,),
            #                              (index, clat, clon,), 
            #                              ...]
            for clatlon in clatlons:
                index = clatlon[0]
                clat = clatlon[1]
                clon = clatlon[2]
                if clat and clon:
                    locations[index]['clatitude'] = clat
                    locations[index]['clongitude'] = clon
                    modify_locations.append(dict(lid=locations[index]['id'], 
                                                 clat=clat, 
                                                 clon=clon,
                                                 index=index))
                else:
                    # BIG NOTE: if offset failed. set the clatlon as latlon 
                    logging.error("[LBMPHELPER] get clatlon failed, lat: %s, lon: %s", 
                                  locations[index]['latitude'],
                                  locations[index]['longitude'])
                    locations[index]['clatitude'] = 0 
                    locations[index]['clongitude'] = 0 

        if modify_locations:
            logging.info("[LBMPHELPER] Modify location, num:%s, data:%s",
                         len(modify_locations), modify_locations)
            db.executemany("UPDATE T_LOCATION"
                           "  SET clatitude = %s,"
                           "      clongitude = %s"
                           "  WHERE id = %s",
                           [(item['clat'], item['clon'], item['lid']) 
                           for item in modify_locations])
    return locations

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
            logging.info("[LBMPHELPER] Get latlon from LE failed, response: %s, args: %s",
                         response['info'], args)
    except Exception as e:
        logging.exception("[LBMPHELPER] Get latlon from LE failed. Exception: %s", e.args)
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

    clats, clons = get_clocation_from_ge([lat,], [lon,])
    clat, clon = clats[0], clons[0]
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

    logging.info("[LBMPHELPER] The distance :%s, tid:%s", distance, tid)
    if 0 < distance < 2000: 
        lon, lat = location.longitude, location.latitude
        logging.info("[LBMPHELPER] The distance: %s beteen cellid-latlon(%s, %s) and gps-latlon(%s, %s) is "
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
                logging.error("[LBMPHELPER] Get location name failed, response: %s, args: %s",
                              response.get('info'), args)
    except Exception as e:
        logging.exception("[LBMPHELPER] Get location name from GV failed. Exception: %s", e.args)
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
    logging.info("[LBMPHELPER] %s Issue cellid...", location.dev_id)
    location.gps = 0
    location.type = 1
    location.degree = random.randint(0, 360)
    # 1: get latlon through cellid
    cellid_info = [int(item) for item in location.cellid.split(":")]
    #NOTE: Check version of terminal: If version if 2.3.x, do not issue cellid
    terminal = db.get("SELECT id, tid, mobile, softversion FROM T_TERMINAL_INFO WHERE tid = %s", location.dev_id)
    if terminal and str(terminal['softversion'][0:3]) == '2.3':
        logging.info("[LBMPHELPER] %s softversion: %s is 2.3.x, do not issue cellid", location.dev_id, terminal['softversion'])
        location.lat, location.lon = 0, 0
    else:
        sim = QueryHelper.get_tmobile_by_tid(location.dev_id, redis, db)
        location.lat, location.lon = get_latlon_from_cellid(cellid_info[0],cellid_info[1],cellid_info[2],cellid_info[3], sim)

    logging.info("[LBMPHELPER] %s cellid result, lat:%s, lon:%s", location.dev_id, location.lat, location.lon)

    return location

def handle_location(location, redis, cellid=False, db=None):
    """
    @param location: position/report/locationdesc/pvt
           memcached
           cellid: if True issue cellid
    @return location
    """
    location = DotDict(location)
    if location.valid == GATEWAY.LOCATION_STATUS.SUCCESS: # 1
        location.type = 0
        if location.get('speed') is not None and location.speed <= UWEB.SPEED_DIFF:
            location.degree = get_last_degree(location, redis, db)
    elif location.valid == GATEWAY.LOCATION_STATUS.UNMOVE: # 4
        logging.info("[LBMPHELPER] Tid:%s gps locate flag :%s", location.dev_id, location.valid)
        #last_location = QueryHelper.get_location_info(location.dev_id, db, redis)
        last_location = QueryHelper.get_gps_location_info(location.dev_id, db, redis)
        if last_location:
            current_time = int(time.time())
            diff = current_time - last_location.timestamp
            logging.info("[LBMPHELPER] current time:%s, last locaiton time:%s, diff time:%s", current_time, last_location.timestamp, diff)
            if (current_time - last_location.timestamp) < 60 * 60 * 24 * 30: # 30 days. in seconds 
                logging.info("[LBMPHELPER] Tid:%s, current_time - last_location.timestamp  < 30 days, so use last location time:%s", 
                             location.dev_id, last_location.timestamp)
                location.gps_time = last_location.timestamp
                location.lat = last_location.latitude
                location.lon = last_location.longitude
                location.cLat = last_location.clatitude
                location.cLon = last_location.clongitude
                location.type = 0 
                location.gps = 0
            else:
                location.type = 0 
                logging.info("[LBMPHELPER] Tid:%s, current_time - last_location.timestamp >= 600s, so use location itself: %s.", location.dev_id, location)
                pass
        else:
            location.type = 0 
            logging.info("[LBMPHELPER] Tid:%s, found no location before, so use location itself: %s.", location.dev_id, location)
            pass
        
        #    location.lat = last_location.latitude
        #    if (current_time - last_location.timestamp) > 600:
        #        location.gps_time = current_time 
        #        logging.info("Tid:%s, current_time - last_location.timestamp  > 600s, so use current time:%s", location.dev_id, current_time)
        #    else:
        #        logging.info("Tid:%s, current_time - last_location.timestamp  <= 600s, so use last location time:%s", location.dev_id, last_location.timestamp)
        #        location.gps_time = last_location.timestamp
        #    location.lat = last_location.latitude
        #    location.lon = last_location.longitude
        #    location.cLat = last_location.clatitude
        #    location.cLon = last_location.clongitude
        #    location.type = 0 
        #    location.gps = 0
        #else:
        #    location.lat = 0
        #    location.lon = 0
        #    location.cLat = 0
        #    location.cLon = 0
        #    location.type = 0
        #    location.gps_time = int(time.time()) 
        #    location.degree = 0.00
        #    location.gps = 0
        #    #if cellid:
        #    #    location = issue_cellid(location, db, redis)
    elif location.valid == GATEWAY.LOCATION_STATUS.MOVE: # 6
        logging.info("[LBMPHELPER] tid:%s gps locate flag :%s", location.dev_id, location.valid)
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
    else: # 0,2,5
        logging.info("[LBMPHELPER] tid:%s gps locate flag :%s", location.dev_id, location.valid)
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
                last_location = QueryHelper.get_location_info(location.dev_id, db, redis)
                if last_location:
                    distance = get_distance(location.lon,
                                            location.lat,
                                            last_location.longitude,
                                            last_location.latitude)
                    if distance > 5000: 
                        login_time = QueryHelper.get_login_time_by_tid(location.dev_id, db, redis)
                        if last_location.timestamp < login_time:
                            logging.info("[LBMPHELPER] tid: %s distance:%s > 5000m, and last login time: %s, after last location timestamp: %s, use cellid location.",
                                         location.dev_id, distance, login_time, last_location.timestamp) 
                        else:
                            location.lat, location.lon = (last_location.latitude, last_location.longitude)
                            logging.info("[LBMPHELPER] tid:%s, distance:%s > 5000m, use last location: %s ",
                                         location.dev_id, distance, last_location)
                    elif distance < 2000:
                        location.lat, location.lon = (last_location.latitude, last_location.longitude)
                        logging.info("[LBMPHELPER] tid:%s distance:%s < 2000m, use last location:%s", location.dev_id, distance, last_location)
                    else:
                        logging.info("[LBMPHELPER] tid:%s 2000m < distance:%s < 5000m, use cellid location", location.dev_id, distance)
                else:
                    logging.info("[LBMPHELPER] tid:%s last location is none, use cellid location", location.dev_id)

    if location and location.lat and location.lon:
        clats, clons = get_clocation_from_ge([location.lat,], [location.lon,])
        location.cLat, location.cLon = clats[0], clons[0] 
        # drop some odd cellid location
        if location.type == 1 and location.cLat and location.cLon:
            if PtInPolygon(location, DM_ZJGS_POLYGON):
                location.lat = 0
                location.lon = 0
                location.cLat = 0
                location.cLon = 0

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

