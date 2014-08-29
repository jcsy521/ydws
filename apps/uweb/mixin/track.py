# -*- coding: utf-8 -*-

import logging
import time

from tornado.escape import json_decode, json_encode

from helpers.gfsenderhelper import GFSenderHelper
from helpers.seqgenerator import SeqGenerator
from helpers.queryhelper import QueryHelper 
from codes.errorcode import ErrorCode
from utils.dotdict import DotDict
from helpers.lbmphelper import handle_location, get_locations_with_clatlon, get_latlon_from_cellid, get_location_name, get_distance
from utils.misc import get_location_key 
from utils.public import insert_location
from constants import UWEB, EVENTER, GATEWAY, SMS
from constants.MEMCACHED import ALIVED
from base import BaseMixin


class TrackMixin(BaseMixin):
    """Mix-in for track related functions."""

    def get_track(self, tid, start_time, end_time, cellid=False):
        """NOTE: Now, only return gps point.
        """
        if cellid:
            track = self.db.query("SELECT id, latitude, longitude, clatitude,"
                                  "       clongitude, timestamp, name, type, speed, degree, locate_error"
                                  "  FROM T_LOCATION"
                                  "  WHERE tid = %s"
                                  "    AND NOT (latitude = 0 OR longitude = 0)"
                                  "    AND (timestamp BETWEEN %s AND %s)"
                                  "    GROUP BY timestamp"
                                  "    ORDER BY timestamp",
                                  tid, start_time, end_time)
        else:
            track = self.db.query("SELECT id, latitude, longitude, clatitude,"
                                  "       clongitude, timestamp, name, type, speed, degree, locate_error"
                                  "  FROM T_LOCATION"
                                  "  WHERE tid = %s"
                                  "    AND NOT (latitude = 0 OR longitude = 0)"
                                  "    AND (timestamp BETWEEN %s AND %s)"
                                  "    AND type = 0"
                                  "    GROUP BY timestamp"
                                  "    ORDER BY timestamp",
                                  tid, start_time, end_time)
        return track 

    def get_track_distance(self, track):
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

    def get_track_name(self, location):
        """Get name of a location which comes from a track.
        """
        if not location:
            return ''
        if not location['name']:
            name = get_location_name(location['clatitude'], location['clongitude'], self.redis)
            if name:
                location['name'] = name 
                self.db.execute("UPDATE T_LOCATION SET name = %s WHERE id = %s",
                                name, location['lid'])
        return location['name']

