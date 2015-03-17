# -*- coding: utf-8 -*-

"""This module is designed for locate a terminal.

#NOTE: deprecatd

"""

from base import BaseComposer
from constants.GATEWAY import S_MESSAGE_TYPE

class RealtimeComposer(BaseComposer):
 
    def __init__(self):
        BaseComposer.__init__(self)
        self.buf = self.compose()

    def compose(self):
        """
        :arg args: dict
        :return request: str

        eg: [1343278800,S4]
        """
        packet = "%s,%s" % (self.time, S_MESSAGE_TYPE.REALTIME)
        request = self.format_packet(packet)

        return request
