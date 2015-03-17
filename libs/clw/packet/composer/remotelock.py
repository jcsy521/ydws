# -*- coding: utf-8 -*-

"""This module is designed for remote-locking a terminal.

#NOTE: deprecated

"""

from base import BaseComposer
from constants.GATEWAY import S_MESSAGE_TYPE

class RemoteLockComposer(BaseComposer):
 
    def __init__(self, args):
        BaseComposer.__init__(self)
        self.buf = self.compose(args)

    def compose(self, args):
        """
        :arg args: dict
        :return request: str
        """
        lock = args['lock_status']
        packet = "%s,%s,%s" % (self.time, S_MESSAGE_TYPE.REMOTELOCK, lock)
        request = self.format_packet(packet)
        
        return request
