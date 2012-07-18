# -*- coding: utf-8 -*-

from utils.dotdict import DotDict

# match definitions in db.
# T_LOCATION, T_BOUND_EVENT, T_BOUND_CWT, T_POWER_EVENT
CATEGORY = DotDict(UNKNOWN=0,
                   
                   REALTIME=10,
                   SCHEDULE=11,
                   CUSTOM=12,
                   
                   POWERLOW=20,
                   POWEROFF=21,

                   REGION_ENTER=30,
                   REGION_OUT=31,

                   EMERGENCY=5)

# PositionInfo
TRIGGERID = DotDict(CALL="CALL",
                    CELLID="CELLID",
                    PRST="PRST",
                    CUST="CUST",
                    POWEROFF="POWEROFF",
                    POWERLOW="POWERLOW",
                    EMERGENCY="EMERGENCY",
                    REGION_ENTER="REGION_ENTER",
                    REGION_OUT="REGION_OUT",
                    UNKNOWN="UNKNOWN")

# The location name will be cached for 7 days
MEMCACHE_EXPIRY = 60*60*24*7

# location of target keep 1h+3min 
LOCATION_EXPIRY = 60*60 + 3*60
