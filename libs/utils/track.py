# -*- coding: utf-8 -*-

import logging
import time 

from helpers.queryhelper import QueryHelper
from helpers.lbmphelper import get_locations_with_clatlon, get_location_name, get_distance

from utils.dotdict import DotDict
from constants import EVENTER, UWEB, GATEWAY

def get_track(db, redis, tid, start_time, end_time, cellid=False):
    """NOTE: Now, only return gps point.
    """
    if cellid:
        track = db.query("SELECT id, latitude, longitude, clatitude,"
                         "       clongitude, timestamp, name, type, speed, degree, locate_error"
                         "  FROM T_LOCATION"
                         "  WHERE tid = %s"
                         "    AND NOT (latitude = 0 OR longitude = 0)"
                         "    AND (timestamp BETWEEN %s AND %s)"
                         "    GROUP BY timestamp"
                         "    ORDER BY timestamp",
                         tid, start_time, end_time)
    else:
        track = db.query("SELECT id, latitude, longitude, clatitude,"
                         "       clongitude, timestamp, name, type, speed, degree, locate_error"
                         "  FROM T_LOCATION"
                         "  WHERE tid = %s"
                         "    AND category = 1"
                         "    AND NOT (latitude = 0 OR longitude = 0)"
                         "    AND (timestamp BETWEEN %s AND %s)"
                         "    AND type = 0"
                         "    GROUP BY timestamp"
                         "    ORDER BY timestamp",
                         tid, start_time, end_time)
    track = get_locations_with_clatlon(track, db)
    #NOTE: handle the name 
    for t in track:
        if t['name'] is None:
            t['name'] = ''
        
    return track 

def get_track_distance(track):
    """Get distance of a section of track.
    """
    distance = 0 
    if not track:
        pass
    else:
        start_point = None
        for point in track:
            if not start_point: 
                start_point = point
                continue
            else:
                distance += get_distance(start_point["longitude"], start_point["latitude"], 
                                         point["longitude"], point["latitude"])
                start_point = point

    return distance

def get_stop_point(db, redis, tid, start_time, end_time):
    """Get stop points of a terminal in a period of time.
    """
    stop = db.query("SELECT ts.id, ts.lid, ts.start_time,"
                    "    ts.end_time, ts.distance,"
                    "    tl.latitude, tl.longitude, "
                    "    tl.clatitude, tl.clongitude, "
                    "    tl.name, tl.degree, tl.speed, tl.locate_error"
                    "  FROM T_STOP AS ts, T_LOCATION AS tl"
                    "  WHERE ts.tid = %s"
                    "  AND ts.lid = tl.id "
                    "  AND ts.start_time BETWEEN %s AND %s"
                    "  AND ts.end_time !=0"
                    "  AND ts.distance !=0"
                    "  ORDER BY ts.start_time ASC",
                    tid, start_time, end_time)
    return stop

def get_track_name(db, redis, location):
    """Get name of a location which comes from a track.

    @param: location, {'name':'',
                       'clatitude':'',
                       'clongitude':'',
                       }
    """
    if not location:
        return ''
    if not location['name']:
        if location['clatitude'] and location['clongitude']:
            pass
        else:
            track = get_locations_with_clatlon([location,], db)
            location = track[0] 
        name = get_location_name(location['clatitude'], location['clongitude'], redis)
        if name:
            location['name'] = name 
            db.execute("UPDATE T_LOCATION SET name = %s WHERE id = %s",
                       name, location['id'])

    return location['name'] if location['name'] else ''
