# -*- coding: utf-8 -*-

from base import BaseComposer
from constants.GATEWAY import S_MESSAGE_TYPE, T_MESSAGE_TYPE

class AsyncRespComposer(BaseComposer):
 
    def __init__(self, args):
        BaseComposer.__init__(self)
        self.buf = self.compose(args)

    def compose(self, args):
        """
        eg: [1343278800,S3,0]
        """
        if args.command == T_MESSAGE_TYPE.POSITION:
            args.command = S_MESSAGE_TYPE.POSITION
        elif args.command == T_MESSAGE_TYPE.MULTIPVT:
            args.command = S_MESSAGE_TYPE.MULTIPVT
        elif args.command == T_MESSAGE_TYPE.CHARGE:
            args.command = S_MESSAGE_TYPE.CHARGE
        elif args.command == T_MESSAGE_TYPE.ILLEGALMOVE:
            args.command = S_MESSAGE_TYPE.ILLEGALMOVE
        elif args.command == T_MESSAGE_TYPE.POWERLOW:
            args.command = S_MESSAGE_TYPE.POWERLOW
        elif args.command == T_MESSAGE_TYPE.ILLEGALSHAKE:
            args.command = S_MESSAGE_TYPE.ILLEGALSHAKE
        elif args.command == T_MESSAGE_TYPE.EMERGENCY:
            args.command = S_MESSAGE_TYPE.EMERGENCY
        elif args.command == T_MESSAGE_TYPE.DEFENDSTATUS:
            args.command = S_MESSAGE_TYPE.DEFENDSTATUS
        elif args.command == T_MESSAGE_TYPE.SLEEPSTATUS:
            args.command = S_MESSAGE_TYPE.SLEEPSTATUS
        elif args.command == T_MESSAGE_TYPE.FOBSTATUS:
            args.command = S_MESSAGE_TYPE.FOBSTATUS
        elif args.command == T_MESSAGE_TYPE.RUNTIMESTATUS:
            args.command = S_MESSAGE_TYPE.RUNTIMESTATUS
        elif args.command == T_MESSAGE_TYPE.UNBINDSTATUS:
            args.command = S_MESSAGE_TYPE.UNBINDSTATUS
        else:
            args.command = None
        
        packet = "%s,%s,%s" % (self.time, args['command'], args['success'])
        request = self.format_packet(packet)

        return request 
