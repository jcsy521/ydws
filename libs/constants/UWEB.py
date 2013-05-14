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

IOS_MAX_SIZE = 160 # in bytes. 

CELLID_MAX_OFFSET = 1000 # in metre

IDLE_INTERVAL = 5 * 60 # 5 minutes, in second. 
IDLE_DISTANCE  = 100 # in metre 

USER_TYPE=DotDict(PERSON='individual',
                  CORP='enterprise',
                  OPERATOR='operator')

GROUP_TYPE=DotDict(BUILTIN=0,
                   NEW=1)

STATISTICS_TYPE=DotDict(YEAR=1,
                        MONTH=2,
                        QUARTER=3)

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
                      YES=1)

LOCATE_FLAG=DotDict(GPS=0,
                    CELLID=1)

SERVICE_STATUS=DotDict(OFF=0,
                       ON=1,
                       TO_BE_UNBIND=2)


TERMINAL_INFO_CATEGORY=DotDict(R=u'r',
                               W=u'w',
                               F=u'f')


TERMINAL_CATEGORY = DotDict(ESPECIAL_GPS_TERMINAL=1,
                            ESPECIAL_NO_GPS_TERMINAL=2, 
                            GENERAL_TERMINAL=3)

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
