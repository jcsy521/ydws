# -*- coding: utf-8 -*-

from utils.dotdict import DotDict


SMS_EXPIRY=24*60*60

LQ = DotDict(WEB=30,
             SMS=10)

LQ_INTERVAL = 3 * 60 # 3mins

CATEGORY = DotDict(RECEIVE=10,
                   SEND=20)

SENDSTATUS = DotDict(PENDING=0,
                     SUCCESS=1,
                     FAILURE=2)

USERSTATUS = DotDict(NOSYNC=-1,
                     SUCCESS=0,
                     FAILURE=1)

