# -*- coding: utf-8 -*-

from utils.dotdict import DotDict

# the priority is same with abt
PRIORITY = DotDict(SMS=40, )

SPEED_DIFF = 3 # if speed < 3km/h, be considered as still point.

DUMMY_CID = u'dummy_cid'

REALTIME_VALID_INTERVAL = 60 * 60 * 12 # 12 hours. in seconds.
LOCATION_VALID_INTERVAL = 5 * 60 # 5 mins

SMS_CAPTCHA_INTERVAL = 60*5 # 5 minutes. in seconds.

IOS_ID_INTERVAL = 7 * 24 * 60 * 60 # one week. in seconds.

IOS_MAX_SIZE = 180 # in bytes. 

USER_TYPE=DotDict(CORP='corp',
                  PERSON='person')

LOGIN_WAY=DotDict(WEB=u"WEB",
                  WAP=u"WAP",
                  ANDROID=u"Android客户端",
                  IOS=u"IOS客户端")

LIMIT=DotDict(PAGE_SIZE=10, # you can have up to 10 records in one page
              TERMINAL=2) # one user have 2 terminal at most.

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
                       ON=1)


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

