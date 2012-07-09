# -*- coding: utf-8 -*-

import time

class BaseComposer(object):

    def __init__(self):
        self.time = time.strftime("%Y-%m-%d %H:%M:%S")

    def format_packet(self, packet):
        format = "[%s]"
        return format % packet
