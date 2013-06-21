# -*- coding: utf-8 -*-

from utils.dotdict import DotDict


SMS_EXPIRY=24*60*60

LQ = DotDict(WEB=5, # 5min 
             SMS=5) # 5min 

LQ_INTERVAL = 3 * 60 # 3mins
LQGZ_SMS_INTERVAL = 3* 60 # 3mins
LQGZ_INTERVAL = 10 * 60 # 10mins

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
