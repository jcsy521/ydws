# -*- coding: utf-8 -*-

from utils.dotdict import DotDict

T_MESSAGE_TYPE = DotDict(LOGIN="T1",
                         HEARTBEAT="T2",
                         POSITION="T3",
                         REALTIME="T4",
                         QUERY="T5",
                         TERMINAL="T6",
                         REBOOT="T7",
                         DEFENDON="T8",
                         DEFENDOFF="T9",
                         LOCATIONDESC="T10",
                         MULTIPVT="T11",
                         CHARGE="T12",
                         ILLEGALMOVE="T13",
                         POWERLOW="T14",
                         POWEROFF="T15",
                         EMERGENCY="T16"
                         )

S_MESSAGE_TYPE = DotDict(LOGIN="S1",
                         HEARTBEAT="S2",
                         POSITION="S3",
                         REALTIME="S4",
                         QUERY="S5",
                         TERMINAL="S6",
                         REBOOT="S7",
                         DEFENDON="S8",
                         DEFENDOFF="S9",
                         LOCATIONDESC="S10",
                         MULTIPVT="S11",
                         CHARGE="S12",
                         ILLEGALMOVE="S13",
                         POWERLOW="S14",
                         POWEROFF="S15",
                         EMERGENCY="S16"
                         )

LOGIN_STATUS = DotDict(SUCCESS="0",
                       UNREGISTER="1",
                       EXPIRED="2",
                       ILLEGAL_SIM="3")

LOCATION_STATUS = DotDict(FAILED="0",
                          SUCCESS="1",
                          UNREALTIME="2")

RESPONSE_STATUS = DotDict(SUCCESS="0",
                          INVALID_SESSIONID="1")

SERVICE_STATUS = DotDict(ON=1,
                         OFF=0)

DEFEND_STATUS = DotDict(FAILED="0",
                        SUCCESS="1",
                        NO_HOST_SUCCESS="2",
                        NO_HOST_FAILED="3")

TERMINAL_LOGIN = DotDict(LOGIN=1,
                         UNLOGIN=0)

# 30min
HEARTBEAT_INTERVAL = 30 * 60 
# no use
SLEEP_HEARTBEAT_INTERVAL = 2*60*60
DUMMY_FD = "-1"
