# -*- coding: utf-8 -*-

from base import BaseComposer
from constants.GATEWAY import S_MESSAGE_TYPE

class RebootComposer(BaseComposer):
 
    def __init__(self, args):
        BaseComposer.__init__(self)
        self.buf = self.compose(args)

    def compose(self, args):
        packet = "%s,%s" % (self.time, S_MESSAGE_TYPE.REBOOT)
        request = self.format_packet(packet)
        
        return request
