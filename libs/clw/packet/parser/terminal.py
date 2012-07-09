# -*- coding: utf-8 -*-

import logging
from utils.dotdict import DotDict

class TerminalParser(object):

    def __init__(self, ret, packet):
        self.ret = self.parse(ret, packet)

    def parse(self, ret, packet):
        info = self.get_info(packet)

        ret.update(info)

        return ret

    def get_info(self, packet):
        info = DotDict()
        keys = ['name', 'status']
        for i, key in enumerate(keys):
            info[key] = packet[i]

        return info 

