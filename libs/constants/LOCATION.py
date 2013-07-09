# -*- coding: utf-8 -*-

from utils.dotdict import DotDict


# The location name will be cached for 7 days
MEMCACHE_EXPIRY = 60*60*24*7

# location of target keep 1h+3min 
LOCATION_EXPIRY = 60*60 + 3*60
