# -*- coding: utf-8 -*-


class DefendParser(object):

    def __init__(self, packet, ret):
        self.ret = self.parse(packet, ret)

    def parse(self, packet, ret):
        ret['status'] =  packet[0] 

        return ret

