# -*- coding: utf-8 -*-

from base import BaseComposer
from constants.GATEWAY import S_MESSAGE_TYPE

class AgpsComposer(BaseComposer):
 
    def __init__(self, args):
        BaseComposer.__init__(self)
        self.buf = self.compose(args)

    def compose(self, args):
        """
        eg: [1343278800,S17,0,xxx]
        """
        packet = "%s,%s,%s,%s" % (self.time, S_MESSAGE_TYPE.AGPS, 
                                  args['success'], args['agps_data'])
        request = self.format_packet(packet)

        return request
