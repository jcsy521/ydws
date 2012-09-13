# -*- coding: utf-8 -*-

import logging

class LocationDescParser(object):

    def __init__(self, packet, ret):
        self.ret = self.parse(packet, ret)

    def parse(self, packet, ret):
        keys = ['ew', 'lon', 'ns', 'lat', 'cellid', 'valid'] 
        for i, key in enumerate(keys):
            ret[key] = packet[i]
        ret['lon'] = int(float(ret['lon']) * 3600000)
        ret['lat'] = int(float(ret['lat']) * 3600000)

        return ret

