# -*- coding: utf-8 -*-

import logging
from codes.clwcode import CLWCode

class DefendParser(object):

    def __init__(self, ret, packet):
        self.ret = self.parse(ret, packet)

    def parse(self, ret, packet):
        if packet[0] == '0':
            ret['status'] = CLWCode.DEFEND_FAILED
        elif packet[0] == '1':
            ret['status'] = CLWCode.DEFEND_SUCCESS
        elif packet[0] == '2':
            ret['status'] = CLWCode.DEFEND_NO_HOST_SUCCESS
        else:
            ret['status'] = CLWCode.DEFEND_NO_HOST_FAILED

        return ret

