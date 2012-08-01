# -*- coding: utf-8 -*-

import logging
from utils.dotdict import DotDict

class TerminalParser(object):

    def __init__(self, packet, ret):
        self.ret = self.parse(packet, ret)

    def parse(self, packet, ret):
        params = self.get_info(packet)
        ret['params'] = params

        return ret

    def get_info(self, packet):
        dct = {}
        for p in packet:
            res = p.split('=')
            dct[res[0]] = res[1]

        return dct 

