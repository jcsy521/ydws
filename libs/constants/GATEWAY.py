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
                         ILLEGALSHAKE="T15",
                         EMERGENCY="T16",
                         CONFIG="T17",
                         DEFENDSTATUS="T18",
                         FOBINFO="T19",
                         FOBOPERATE="T20",
                         SLEEPSTATUS="T21",
                         FOBSTATUS="T22",
                         RUNTIMESTATUS="T23",
                         UNBIND="T24",
                         UNBINDSTATUS="T25",
                         POWERDOWN="T26",
                         UNUSUALACTIVATE="T27",
                         MISC="T28",
                         STOP="T29",
                         ACC_STATUS="T30",
                         ACC_STATUS_REPORT="T31",
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
                         ILLEGALSHAKE="S15",
                         EMERGENCY="S16",
                         CONFIG="S17",
                         DEFENDSTATUS="S18",
                         FOBINFO="S19",
                         FOBOPERATE="S20",
                         SLEEPSTATUS="S21",
                         FOBSTATUS="S22",
                         RUNTIMESTATUS="S23",
                         UNBIND="S24",
                         UNBINDSTATUS="S25",
                         POWERDOWN="S26",
                         UNUSUALACTIVATE="S27",
                         MISC="S28",
                         STOP="S29",
                         ACC_STATUS="S30",
                         ACC_STATUS_REPORT="S31",
                         AGPS="S100"
                         )

LON_LAT = DotDict(default=(114.17, 30.45),
                  A00=(83, 15.5),
                  A01=(103, 15.5),
                  A02=(123, 15.5),
                  A10=(83, 40.5),
                  A11=(103, 40.5),
                  A12=(123, 40.5))

LOGIN_STATUS = DotDict(SUCCESS="0",
                       UNREGISTER="1",
                       EXPIRED="2",
                       ILLEGAL_SIM="3",
                       PSD_WRONG="4",
                       ILLEGAL_DEVID="5",
                       NOT_WHITELIST="6")

LOCATION_STATUS = DotDict(FAILED="0",
                          SUCCESS="1",
                          UNREALTIME="2",
                          REALTIME_RESP="3",
                          UNMOVE="4",
                          MOVE_OR_NOT="5", # old version, can not ensure it is move
                          MOVE="6")

RESPONSE_STATUS = DotDict(SUCCESS="0",
                          INVALID_SESSIONID="1",
                          CELLID_FAILED="2" # only T10
                          )

SERVICE_STATUS = DotDict(ON=1,
                         OFF=0)

DEFEND_STATUS = DotDict(SUCCESS="0",
                        FAILED="1")

# login status of termianl
TERMINAL_LOGIN = DotDict(OFFLINE=0,
                         ONLINE=1,
                         SLEEP=2,
                         WAKEUP=3)

FOB_OPERATE = DotDict(ADD=0,
                      REMOVE=1)

STATUS = DotDict(SUCCESS="0",
                 FAILED="1")

# 30 min 
YDWQ_HEARTBEAT_INTERVAL = 30 * 60 

# 30 second 
HEARTBEAT_INTERVAL = 30 
# 30 min 
SLEEP_HEARTBEAT_INTERVAL = 30 * 60
DUMMY_FD = "-1"

POWEROFF_TIMEOUT_SMS = DotDict(SEND=1,
                               UNSEND=0)

# check report resend
RESEND_EXPIRY = 2 * 60
