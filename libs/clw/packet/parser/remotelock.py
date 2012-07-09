# -*- coding: utf-8 -*-

import logging
from utils.dotdict import DotDict

class RemoteLockParser(object):

    def __init__(self, ret, packet):
        self.ret = self.parse(ret, packet)

    def parse(self, ret, packet):
        ret['status'] = packet[0]

        return ret

