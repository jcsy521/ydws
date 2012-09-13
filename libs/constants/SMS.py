# -*- coding: utf-8 -*-

from utils.dotdict import DotDict


SMS_EXPIRY=24*60*60

LQ = DotDict(WEB=30, # 30 minutes
             SMS=30) # 30 minutes 

LQ_INTERVAL = 3 * 60 # 3mins

#modify
CATEGORY = DotDict(MO=1,
                   MT=2)

SENDSTATUS = DotDict(PREPARING=-1,
                     SUCCESS=0,
                     FAILURE=1)

USERSTATUS = DotDict(NOSYNC=-1,
                     SUCCESS=0,
                     FAILURE=1)

RETRYSTATUS = DotDict(NO=0,
                      YES=1)
                     
OPTION = DotDict(SEND=1,
                 NOSEND=0)
