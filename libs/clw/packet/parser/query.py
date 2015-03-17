# -*- coding: utf-8 -*-

#NOTE: deprecated

import logging

class QueryParser(object):

    def __init__(self, packet, ret):
        self.ret = self.parse(packet, ret)

    def parse(self, packet, ret):
        params = {}
        for p in packet:
            res = p.split('=')
            params[res[0]] = res[1]

        ret['params'] = params

        return ret

