# -*- coding: utf-8 -*-

from utils.dotdict import DotDict

CATEGORY = DotDict(RECEIVE=10,
                   SEND=20)

SMS_EXPIRY=24*60*60

LQ = DotDict(WEB=30,
             SMS=10)

LQ_INTERVAL = 3 * 60 # 3mins
