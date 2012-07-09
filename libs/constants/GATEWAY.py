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
                         REMOTELOCK="T10",
                         ILLEAGALMOVE="T11",
                         POWEROFF="T12",
                         POWERLOW="T13",
                         BOUND="T14",
                         OVERSPEED="T15",
                         MILEAGE="T16"
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
                         REMOTELOCK="S10",
                         ILLEAGALMOVE="S11",
                         POWEROFF="S12",
                         POWERLOW="S13",
                         BOUND="S14",
                         OVERSPEED="S15",
                         MILEAGE="S16"
                         )

T_REGIST_STATUS = DotDict(REGIST="1",
                          UN_REGIST="0"
                          )

LOGIN_SUCCESS = "1"
LOGIN_FAILD = "0"

HEARTBEAT_INTERVAL = 2*60
SLEEP_HEARTBEAT_INTERVAL = 2*60*60
DUMMY_FD = "-1"
