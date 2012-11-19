# -*- coding: utf-8 -*-

from base import BaseComposer
from constants.GATEWAY import S_MESSAGE_TYPE
from constants import UWEB

class UNBindComposer(BaseComposer):
 
    def __init__(self, args):
        BaseComposer.__init__(self)
        self.buf = self.compose(args)

    def compose(self, args):
        """
        eg: [1343278800,S24] 
        """
        packet = "%s,%s" % (self.time, S_MESSAGE_TYPE.UNBIND) 
        request = self.format_packet(packet)
        
        return request

