# -*- coding: utf-8 -*-

import logging
from utils.dotdict import DotDict

class HeartbeatParser(object):

    def __init__(self, packet, ret):
        self.ret = self.parse(packet, ret)

    def parse(self, packet, ret):
        ggp = packet[0].split(':')
        keys = ['gps', 'gsm', 'pbat']
        for i, key in enumerate(keys):
            ret[key] = ggp[i]

        return ret
