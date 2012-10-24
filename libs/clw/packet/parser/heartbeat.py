# -*- coding: utf-8 -*-

import logging

from utils.dotdict import DotDict
from constants import GATEWAY

class HeartbeatParser(object):

    def __init__(self, packet, ret):
        self.ret = self.parse(packet, ret)

    def parse(self, packet, ret):
        keys = ['ggp', 'sleep_status', 'fob_status']
        for i, key in enumerate(keys):
            ret[key] = packet[i]

        keys = ['gps', 'gsm', 'pbat']
        ggp = ret['ggp'].split(':')
        for i, key in enumerate(keys):
            ret[key] = ggp[i]
        del ret['ggp']

        return ret
