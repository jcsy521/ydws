# -*- coding: utf-8 -*-

import logging

from dotdict import DotDict

DM_ZJGS_POLYGON = {'name': u"斗门区珠江高速公路",
                   'points': [{'lat': 22.348998999999999, 'lon': 113.211752},
                              {'lat': 22.364241, 'lon': 113.238198},
                              {'lat': 22.353545, 'lon': 113.27183100000001}, 
                              {'lat': 22.325196999999999, 'lon': 113.30000200000001}, 
                              {'lat': 22.292563000000001, 'lon': 113.309488},
                              {'lat': 22.271159999999998, 'lon': 113.331335},
                              {'lat': 22.246274, 'lon': 113.358068}, 
                              {'lat': 22.220848, 'lon': 113.38164}, 
                              {'lat': 22.195952999999999, 'lon': 113.40147399999999}, 
                              {'lat': 22.180425, 'lon': 113.38164}, 
                              {'lat': 22.195150000000002, 'lon': 113.35231899999999}, 
                              {'lat': 22.242795000000001, 'lon': 113.305176},
                              {'lat': 22.264202999999998, 'lon': 113.272406}, 
                              {'lat': 22.303799000000001, 'lon': 113.233886}, 
                              {'lat': 22.304065999999999, 'lon': 113.233312}]
                 }

def PtInPolygon(location, *polygons):
    """
    function: judge point is in polygon or not.
    method: get num of intersection point which cross each side of polygon
            and the horizontal line which through point.
    return: True/False, if num is odd, point is in polygon.

    graphical representation:
             ----------                
            /          \               
           /            \              
           \     p------/------        
            \          /               
             ----------                
    """

    point = DotDict(location)
    point.lat = point.cLat/3600000.0
    point.lon = point.cLon/3600000.0
    is_in = False

    for polygon in polygons:
        polygon_pts = polygon['points']
        polygon_name = polygon['name']
        # side num of polygon
        sides = len(polygon_pts) - 1
        # num of intersection point, if nCross is odd, point is in polygon 
        nCross = 0
        for i in range(sides):
            p1 = polygon_pts[i]
            p2 = polygon_pts[(i+1)%sides]
            p1 = DotDict(p1)
            p2 = DotDict(p2)

            if p1.lat == p2.lat: # horizontal line
                continue

            if (point.lat < min(p1.lat, p2.lat)): # cross point is in extension line of p1p2
                continue

            if (point.lat >= max(p1.lat, p2.lat)): # cross point is in extension line of p1p2
                continue;

            # get lon of cross point
            lon = (point.lat - p1.lat) * (p2.lon - p1.lon) / (p2.lat - p1.lat) + p1.lon
            if lon > point.lon: # on the right side of point, intersect 
                nCross += 1

        is_in |= (nCross % 2 == 1)
        if is_in:
            logging.info("Point: %s is in polygon: %s", point, polygon_name)
        else:
            logging.info("Point: %s is out polygon: %s", point, polygon_name)

    return is_in 
