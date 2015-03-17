# -*- coding: utf-8 -*-

import time

class BaseComposer(object):
    """Basic composer

    It provide current_time and add [] for the packet.
    """

    def __init__(self):
        self.time = str(int(time.time()))

    def format_packet(self, packet):
        format = "[%s]"
        return format % packet
