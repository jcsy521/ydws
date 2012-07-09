# -*- coding: utf-8 -*-

import logging
from codes.clwcode import CLWCode

class QueryParser(object):

    def __init__(self, ret, packet):
        self.ret = self.parse(ret, packet)

    def parse(self, ret, packet):
        p = packet[0].split('=')
        ret['f_key'] = p[0]  
        ret['f_value'] = p[1]

        return ret

