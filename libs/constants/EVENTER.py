# -*- coding: utf-8 -*-

from utils.dotdict import DotDict

# async report info type
INFO_TYPE = DotDict(POSITION="POSITION",
                    REPORT="REPORT",
                    STATISTICS="STATISTICS",
                    UNKNOWN="UNKNOWN")

# PositionInfo
TRIGGERID = DotDict(CALL="CALL",
                    CELLID="CELLID",
                    UNKNOWN="UNKNOWN")

# report info
RNAME = DotDict(POWEROFF="POWEROFF",
                POWERLOW="POWERLOW",
                REGION_OUT="REGION_OUT",
                SPEED_OUT="SPEED_OUT",
                ILLEGALMOVE="ILLEGALMOVE",
                HEARTBEAT_LOST="HEARTBEAT_LOST",
                UNKNOWN="UNKNOWN")

# statistics info
STATISTICS = DotDict(MILEAGE="MILEAGE")

# match definitions in db.
CATEGORY = DotDict(UNKNOWN=0,
                   REALTIME=1,
                   POWERLOW=2,
                   POWEROFF=3,
                   REGION_OUT=4,
                   SPEED_OUT=5,
                   ILLEGALMOVE=6,
                   HEARTBEAT_LOST=7)

# The location name will be cached for 7 days
LOCATION_NAME_EXPIRY = 60*60*24*7

# location of target keep 15s 
LOCATION_EXPIRY = 15 
