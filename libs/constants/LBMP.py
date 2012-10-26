# -*- coding: utf-8 -*-

from utils.dotdict import DotDict

DUMMY = "DUMMY"

# the priority is same with abt
PRIORITY = DotDict(LE=100, 
                   GE=100, 
                   SUBSCRIPTION=100, 
                   GV=100)

MODULE=DotDict(LE="LE",
               GV="GV", 
               SUBSCRIPTION="SUBSCRIPTION", 
               GE="GE")

