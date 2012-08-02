# -*- coding: utf-8 -*-

import logging
from codes.clwcode import CLWCode

class RebootParser(object):

    def __init__(self, packet, ret):
        self.ret = self.parse(packet, ret)

    def parse(self, packet, ret):
        if packet[0] == '0':
            ret['status'] = CLWCode.FAILED
        elif packet[0] == '1':
            ret['status'] = CLWCode.SUCCESS

        return ret

