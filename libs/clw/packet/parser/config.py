# -*- coding: utf-8 -*-

import logging
from utils.dotdict import DotDict

class ConfigParser(object):

    def __init__(self, packet, ret):
        self.ret = self.parse(packet, ret)

    def parse(self, packet, ret):
        pass

        return ret

