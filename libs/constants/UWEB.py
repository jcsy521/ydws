# -*- coding: utf-8 -*-

from utils.dotdict import DotDict

# the priority is same with abt
PRIORITY = DotDict(SMS=40, )

SPEED_DIFF = 3 # if speed < 3km/h, be considered as still point.

DUMMY_CID = u'dummy_cid'
DUMMY_OID = u'dummy_oid'
DUMMY_UID = u'dummy_uid'
DUMMY_TID = u'dummy_tid'
DUMMY_MOBILE = u'dummy_mobile'

REALTIME_VALID_INTERVAL = 60 * 60 * 12 # 12 hours. in seconds.
LOCATION_VALID_INTERVAL = 5 * 60 # 5 mins

STATISTIC_INTERVAL = 10 * 60 # 10 mins

MILEAGE_STATISTIC_INTERVAL = 10 * 60 # 10 mins

SMS_CAPTCHA_INTERVAL = 60*5 # 5 minutes. in seconds.

IOS_ID_INTERVAL = 30 * 24 * 60 * 60 # one month. in seconds.

IOS_MAX_SIZE = 100 # in bytes. 

CELLID_MAX_OFFSET = 2000 # in metre

IDLE_INTERVAL = 5 * 60 # 5 minutes, in second. 
IDLE_DISTANCE  = 200 # in metre 

REGION_SHAPE=DotDict(CIRCLE=0,
                     POLYGON=1)

SINGLE_SHAPE=DotDict(CIRCLE=0,
                     POLYGON=1)


USER_TYPE=DotDict(PERSON='individual',
                  CORP='enterprise',
                  OPERATOR='operator')

APK_TYPE=DotDict(YDWS=1,
                 YDWQ_MONITOR=2,
                 YDWQ_MONITORED=3,
                 YDWS_ANJIETONG=4)

GROUP_TYPE=DotDict(BUILTIN=0,
                   NEW=1)

OP_TYPE=DotDict(ADD=1,
                DEL=2)

STATISTIC_USER_TYPE=DotDict(INDIVIDUAL=0,
                            ENTERPRISE=1,
                            TOTAL=2)


STATISTICS_TYPE=DotDict(YEAR=1,
                        MONTH=2,
                        QUARTER=3)

VEHICLE_TYPE=DotDict(ELECTROCAR=0,
                     CAR=1)

BIZ_TYPE=DotDict(YDWS=0,
                 YDWQ=1)

QUERY_TYPE=DotDict(JUNIOR=0,
                   SENIOR=1)

LOGIN_WAY=DotDict(WEB=u"WEB",
                  WAP=u"WAP",
                  ANDROID=u"Android客户端",
                  IOS=u"IOS客户端")

LIMIT=DotDict(PAGE_SIZE=10, # you can have up to 10 records in one page
              PAGE_SIZE_STATISTICS=16, # you can have up to 16 records in statistics page
              TERMINAL=2,# one user have 2 terminal at most.
              REGION=10,# a terminal has up to 10 regions.
              ) 

CATEGORY=DotDict(UNKNOWN=0,
                 WEB=10,
                 SMS=11)

CHECK_TERMINAL=DotDict(TID=u'tid',
                       MOBILE=u'mobile')

DEFEND_STATUS=DotDict(NO=0,
                      YES=1,
                      SMART=2)

LOCATE_FLAG=DotDict(GPS=0,
                    CELLID=1)

SERVICE_STATUS=DotDict(OFF=0,
                       ON=1,
                       TO_BE_UNBIND=2,
                       TO_BE_ACTIVATED=3)


TERMINAL_INFO_CATEGORY=DotDict(R=u'r',
                               W=u'w',
                               F=u'f')


TERMINAL_CATEGORY = DotDict(ESPECIAL_GPS_TERMINAL=1,
                            ESPECIAL_NO_GPS_TERMINAL=2, 
                            GENERAL_TERMINAL=3)

UPLOAD_CATEGORY = DotDict(HEARTBEAT=0,
                          LOCATION=1, 
                          POWER=2,
                          ATTENDANCE=3)

# the interval of query event, track, event: one week. in seconds.
QUERY_INTERVAL = 7 * 24 * 60 * 60

# the interval of wake up, 5 minutes, in seconds.
WAKEUP_INTERVAL = 5 * 60


REMOTE_EVENT_COMMAND = DotDict(REBOOT='REBOOT', 
                               LOCK='LOCK')

SMS_OPTION = DotDict(SEND=1,
                     UNSEND=0)

TERMINAL_STATUS = DotDict(JHING=0,
                          UNJH=1,
                          EXISTED=2,
                          INVALID=3,
                          MOBILE_NOT_ORDERED=4)

SIMPLE_YDCWS_PATTERN = r"^(1477874\d{4})$"

# turn on track for 10mins  
TRACK_INTERVAL = 10 * 60  

AVATAR_SIZE = DotDict(WIDTH=320,
                    HEIGHT=320)

AVATAR_QUALITY = 50

# The acc_status will be cached for 90 seconds
ACC_STATUS_EXPIRY = 90*2

# The acc_status will be cached for 90 seconds
MASS_POINT_LIMIT = 90*2

# The acc_status will be cached for 90 seconds
MASS_POINT_ = 90*2
