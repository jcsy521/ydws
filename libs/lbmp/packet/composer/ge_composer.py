# -*- coding: utf-8 -*-

import time
from datetime import datetime

from base import BaseComposer

class GeComposer(BaseComposer):
    GE_TEMPLATE = """<?xml version="1.0" encoding="GB2312"?><Envelope><Header><id>%(username)s</id><pwd>%(password)s</pwd></Header><Body><request><property key="lng">%(lon)s</property><property key="lat">%(lat)s</property><property key="heit">0</property><property key="week">%(week)s</property><property key="time">%(times)s</property></request></Body></Envelope>"""

    def __init__(self, args):
        
        self.args = args
        username = args['username']
        password = args['password']
        lon = int(float(args['lon']) * 1.024)
        lat = int(float(args['lat']) * 1.024)
        local_time = time.localtime()
        y,m,d = local_time[0:3]
        current_time = datetime(y, m, d)
        start_time = datetime(1980, 01, 06)
        days = (current_time - start_time).days
        # GPS week, from 1980-01-06
        week = days / 7
        times = (((days % 7) * 24 + local_time[3]) * 60 * 60  + local_time[4] * 60 + local_time[5]) * 1000
        self.template = self.GE_TEMPLATE % locals()
