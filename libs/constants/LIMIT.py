# -*- coding: utf-8 -*-

"""Some limitations.
"""

# A user has up to 4 trackers.
TRACKER = 4

# a terminal has up to 10 regions.
REGION = 10

# if the number of track is more than 1000, it's a mass point
MASS_POINT_NUMBER = 1000

# a week. if mass_point interval is more than 7 days, it's a mass point
MASS_POINT_INTERVAL = 60*60*24*7 

# if speed is > 5, it is moving, else may be motionless 
SPEED_LIMIT = 5 

# a week. before 2014.08.01, if query interval about mass-point exceeds one week, it is invalid
MASS_POINT_QUERY_INTERVAL = 60*60*24*7 

# 2014.08.01. before 2014.08.01, if query interval about mass-point exceeds one week, it is invalid
MASS_POINT_QUERY_TIME = 1406822400 



