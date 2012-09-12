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
                         EMERGENCY="T16",
                         CONFIG="T17",
                         DEFENDSTATUS="T18",
                         AGPS="T100"
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
                         EMERGENCY="S16",
                         CONFIG="S17",
                         DEFENDSTATUS="S18",
                         AGPS="S100"
                         )

LON_LAT = DotDict(default=(114.17, 30.45),
                  O1=(83, 15.5),
                  O2=(103, 15.5),
                  O3=(123, 15.5),
                  T1=(83, 40.5),
                  T2=(103, 40.5),
                  T3=(123, 40.5))

LOGIN_STATUS = DotDict(SUCCESS="0",
                       UNREGISTER="1",
                       EXPIRED="2",
                       ILLEGAL_SIM="3",
                       PSD_WRONG="4")

LOCATION_STATUS = DotDict(FAILED="0",
                          SUCCESS="1",
                          UNREALTIME="2")

RESPONSE_STATUS = DotDict(SUCCESS="0",
                          INVALID_SESSIONID="1",
                          CELLID_FAILED="2" # only T10
                          )

SERVICE_STATUS = DotDict(ON=1,
                         OFF=0)

DEFEND_STATUS = DotDict(SUCCESS="0",
                        FAILED="1")

TERMINAL_LOGIN = DotDict(LOGIN=1,
                         UNLOGIN=0)

# 10 second 
HEARTBEAT_INTERVAL = 30 
# 30 min 
SLEEP_HEARTBEAT_INTERVAL = 30 * 60
DUMMY_FD = "-1"
