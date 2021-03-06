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
                REGION_ENTER="REGION_ENTER",
                REGION_OUT="REGION_OUT",
                POWERDOWN="POWERDOWN",
                STOP="STOP",
                SPEED_LIMIT="SPEED_LIMIT",
                SINGLE_ENTER="SINGLE_ENTER",
                SINGLE_OUT="SINGLE_OUT",
                UNKNOWN="UNKNOWN")

# sms option 
SMS_CATEGORY = DotDict(LOGIN="LOGIN",
                       POWERLOW="POWERLOW",
                       ILLEGALMOVE="ILLEGALMOVE",
                       ILLEGALSHAKE="ILLEGALSHAKE",
                       EMERGENCY="SOS",
                       HEARTBEAT_LOST="HEARTBEAT_LOST",
                       CHARGE="CHARGE",
                       REGION_ENTER="REGION_ENTER",
                       REGION_OUT="REGION_OUT",
                       POWERDOWN="POWERDOWN",
                       STOP="STOP",
                       SPEED_LIMIT="SPEED_LIMIT",
                       SINGLE_ENTER="SINGLE_ENTER",
                       SINGLE_OUT="SINGLE_OUT",) 

# category for eventer. match definitions in db.
CATEGORY = DotDict(UNKNOWN=0,
                   REALTIME=1,
                   POWERLOW=2,
                   ILLEGALSHAKE=3,
                   ILLEGALMOVE=4,
                   EMERGENCY=5,
                   HEARTBEAT_LOST=6,
                   REGION_ENTER=7, # 进围栏
                   REGION_OUT=8, # 出围栏
                   POWERDOWN=9, # 低电
                   STOP=10, # 停留
                   SPEED_LIMIT=11, # 超速
                   SINGLE_ENTER=12, # 进单程
                   SINGLE_OUT=13) # 出单程
                   

# The location name will be cached for 7 days
LOCATION_NAME_EXPIRY = 60 * 60 * 24 *7

# location of target keep 24 hours. in seconds.
#LOCATION_EXPIRY = 60 * 60 * 24 * 7
LOCATION_EXPIRY = 60 * 60 * 24 * 365 * 2 # two years 


SPEED_LIMIT_EXPIRY = 60 * 60 * 24 * 365 * 2 # two years 

STOP_EXPIRY = 60 * 60 * 24 * 365 * 2 # two years 

# tinyurl keep 3 days
TINYURL_EXPIRY = 3 * 24 * 60 * 60

# The alarm will be cached for 1 days
ALARM_EXPIRY = 60 * 60 * 24  

