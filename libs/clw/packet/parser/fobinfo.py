# -*- coding: utf-8 -*-

import logging

class FobInfoParser(object):

    def __init__(self, packet, ret):
        self.ret = self.parse(packet, ret)

    def parse(self, packet, ret):
        keys = ['fobid', 'operate'] 
        for i, key in enumerate(keys):
            ret[key] = packet[i]

        return ret

