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
RNAME = DotDict(POWERLOW="POWERLOW",
                ILLEGALMOVE="ILLEGALMOVE",
                ILLEGALSHAKE="ILLEGALSHAKE",
                EMERGENCY="EMERGENCY",
                HEARTBEAT_LOST="HEARTBEAT_LOST",
                UNKNOWN="UNKNOWN")

# sms option 
SMS_CATEGORY = DotDict(LOGIN="LOGIN",
                       POWERLOW="POWERLOW",
                       ILLEGALMOVE="ILLEGALMOVE",
                       ILLEGALSHAKE="ILLEGALSHAKE",
                       EMERGENCY="SOS",
                       HEARTBEAT_LOST="HEARTBEAT_LOST",
                       CHARGE="CHARGE")

# match definitions in db.
CATEGORY = DotDict(UNKNOWN=0,
                   REALTIME=1,
                   POWERLOW=2,
                   ILLEGALSHAKE=3,
                   ILLEGALMOVE=4,
                   EMERGENCY=5,
                   HEARTBEAT_LOST=6)
                   

# The location name will be cached for 7 days
LOCATION_NAME_EXPIRY = 60*60*24*7

# location of target keep 24 hours. in seconds.
LOCATION_EXPIRY = 60 * 60 * 24

# tinyurl keep 3 days
TINYURL_EXPIRY = 3 * 24 * 60 * 60
