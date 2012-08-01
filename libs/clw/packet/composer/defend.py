# -*- coding: utf-8 -*-

from base import BaseComposer
from constants.GATEWAY import S_MESSAGE_TYPE
from constants import UWEB

class DefendComposer(BaseComposer):
 
    def __init__(self, args):
        BaseComposer.__init__(self)
        self.buf = self.compose(args)

    def compose(self, args):
        if args['defend_status'] == UWEB.DEFEND_STATUS.YES:
            defend = S_MESSAGE_TYPE.DEFENDON
        else:
            defend = S_MESSAGE_TYPE.DEFENDOFF
        packet = "%s,%s" % (self.time, defend) 
        request = self.format_packet(packet)
        
        return request

