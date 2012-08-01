# -*- coding: utf-8 -*-

from base import BaseComposer
from constants.GATEWAY import S_MESSAGE_TYPE

class MileageRespComposer(BaseComposer):
 
    def __init__(self):
        BaseComposer.__init__(self)
        self.buf = self.compose(args)

    def compose(self):
        packet = "%s,%s" % (self.time, S_MESSAGE_TYPE.MILEAGE)
        request = self.format_packet(packet)

        return request
