# -*- coding: utf-8 -*-

import logging
from utils.dotdict import DotDict

class HeartbeatParser(object):

    def __init__(self, packet):
        self.ret = self.parse(packet)

    def parse(self, packet):
        heartbeat_info = DotDict()
        keys = ['GPS', 'GSM', 'POWER']
        for i, key in enumerate(keys):
            heartbeat_info[key] = str(packet[0])[i]

        return heartbeat_info
