# -*- coding: utf-8 -*-

from base import BaseComposer
from constants.GATEWAY import S_MESSAGE_TYPE

class MileageRespComposer(BaseComposer):
 
    def __init__(self):
        packet = ",%s" % S_MESSAGE_TYPE.MILEAGE
        self.buf = self.format_packet(packet)
