# -*- coding: utf-8 -*-

"""This module is designed for recording the fob-info of a terminal.

#NOTE: deprecatd

"""

from base import BaseComposer
from constants.GATEWAY import S_MESSAGE_TYPE

class FobInfoRespComposer(BaseComposer):
 
    def __init__(self, args):
        BaseComposer.__init__(self)
        self.buf = self.compose(args)

    def compose(self, args):
        """
        :arg args: dict
        :return request: str
        
        eg: [1343278800,S19,0]
        """
        packet = "%s,%s,%s" % (self.time, S_MESSAGE_TYPE.FOBINFO, args['success'])
        request = self.format_packet(packet)

        return request
