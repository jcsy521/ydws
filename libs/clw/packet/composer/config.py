# -*- coding: utf-8 -*-

"""This module is designed for configure a terminal.
"""

from base import BaseComposer
from constants.GATEWAY import S_MESSAGE_TYPE

class ConfigRespComposer(BaseComposer):
 
    def __init__(self, args):
        BaseComposer.__init__(self)
        self.buf = self.compose(args)

    def compose(self, args):
        """
        eg: [1343278800,1q2w3e45,S17,0,1q2w3e45,DOMAIN=www.pinganbb.info:8002,FREQ=0,TRACE=1,STATIC_VAL=3,MOVE_VAL=3,TRACE_PARA=5:10,VIBL=1,USE_SCENE=3,STOP_INTERVAL=1800,TEST=1,GPS_ENHANCED=1,TRACKING_INTERVAL=5]
        """
        packet = "%s,%s,%s" % (self.time, S_MESSAGE_TYPE.CONFIG,
                               args['success']) 
        for key in ['domain', 'freq', 'trace', 'static_val', 'move_val',
                    'trace_para', 'vibl','use_scene', 'stop_interval', 
                    'test', 'gps_enhanced', 'tracking_interval']:
            if args.has_key(key):
                packet += ",%s=%s" % (key.upper(), args[key])
        request = self.format_packet(packet)
        
        return request
