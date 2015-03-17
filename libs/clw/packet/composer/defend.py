# -*- coding: utf-8 -*-

"""This module is designed for defend a terminal.

#NOTE: deprecatd

"""

from base import BaseComposer
from constants.GATEWAY import S_MESSAGE_TYPE
from constants import UWEB

class DefendComposer(BaseComposer):
 
    def __init__(self, args):
        BaseComposer.__init__(self)
        self.buf = self.compose(args)

    def compose(self, args):
        """
        :arg args: dict
        :return request: str
        
        eg: [1343278800,S8] 
        """
        if args['defend_status'] == UWEB.DEFEND_STATUS.YES:
            defend = S_MESSAGE_TYPE.DEFENDON
        else:
            defend = S_MESSAGE_TYPE.DEFENDOFF
        packet = "%s,%s" % (self.time, defend) 
        request = self.format_packet(packet)
        
        return request

