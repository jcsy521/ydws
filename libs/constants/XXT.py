# -*- coding: utf-8 -*-

from utils.dotdict import DotDict

STATUS = DotDict(SUBSCRIBE=10,
                 PLAN_CHANGE=20,
                 UNSUBSCRIBE=30,
                 TO_BE_REMOVE=0)

VALID = DotDict(VALID=1,
                INVALID=0,
                AFFILIATED=100)

ROLE =DotDict(PARENT=1,
              CHILD=2,
              UNKNOWN=3)

DEFAULT_QQ_NUM = 4

OPER_TYPE = DotDict(CREATE=1,
                    SUSPEND=2,
                    RESUME=3,
                    UPDATE=4,
                    CANCEL=5)

USER_TYPE =DotDict(PARENT='1',
                   CHILD='3')

MARK =DotDict(CORP="CORPBIND",
              MEMBER="STAFFBIND")   
