# -*- coding: utf-8 -*-

from utils.dotdict import DotDict

# async report info type
INFO_TYPE = DotDict(POSITION="POSITION",
                    REPORT="REPORT",
                    CHARGE="CHARGE",
                    UNKNOWN="UNKNOWN")

# PositionInfo
TRIGGERID = DotDict(CALL="CALL",
                    CELLID="CELLID",
                    PVT="PVT",
                    UNKNOWN="UNKNOWN")

# report info
RNAME = DotDict(POWEROFF="POWEROFF",
                POWERLOW="POWERLOW",
                ILLEGALMOVE="ILLEGALMOVE",
                EMERGENCY="EMERGENCY",
                HEARTBEAT_LOST="HEARTBEAT_LOST",
                UNKNOWN="UNKNOWN")

# match definitions in db.
CATEGORY = DotDict(UNKNOWN=0,
                   REALTIME=1,
                   POWERLOW=2,
                   POWEROFF=3,
                   ILLEGALMOVE=4,
                   EMERGENCY=5,
                   HEARTBEAT_LOST=6)

# The location name will be cached for 7 days
LOCATION_NAME_EXPIRY = 60*60*24*7

# location of target keep 60 minutes 
LOCATION_EXPIRY = 60 * 60 
