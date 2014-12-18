# -*- coding: utf-8 -*-

import os.path
import site
import math

TOP_DIR_ = os.path.abspath(os.path.join(__file__, "../../.."))
site.addsitedir(os.path.join(TOP_DIR_, "libs"))

import time
import datetime
from dateutil.relativedelta import relativedelta
import functools
import random
import logging

# import some modules for VG
from dotdict import DotDict
import checker
from constants import UWEB, GATEWAY, EVENTER

def get_token():
    """A string consist of digits and upercase, whose length is 10.
    Do not include number 0.
    """
    token = ''
    base_str = '123456789ABCDEFGHJKMNPQRSTUVWXYZ'
    token = ''.join(random.choice(base_str) for x in range(10))

    return token 

       
