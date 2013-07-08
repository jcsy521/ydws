# -*- coding: utf-8 -*-


class MiscParser(object):

    def __init__(self, packet, ret):
        self.ret = self.parse(packet, ret)

    def parse(self, packet, ret):
        keys = ["misc"]
        for i, key in enumerate(keys):
            ret[key] = packet[i]

        return ret 

