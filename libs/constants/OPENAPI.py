# -*- coding: utf-8 -*-

from utils.dotdict import DotDict


LIMIT=DotDict(REQUEST=100, # you can have up to 100 requests in one minutee.
              TRACK=1000) # you can have up to 1000 locations one time.

TOKEN_EXPIRES = 3 * 60 * 60 # in seconds, 3 hours
