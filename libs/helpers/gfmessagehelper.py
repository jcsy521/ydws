# -*- coding: utf-8 -*-

import logging

from codes.errorcode import ErrorCode


class GFMessageHelper(object):

    @staticmethod
    def format_gf_message(errorcode):
        """
        @param errorcode: errorcode returned from GF.
        """
        status = ErrorCode.FAILED
        if errorcode == '0000':
            status = ErrorCode.SUCCESS
        elif errorcode == '0001':
            status = ErrorCode.ILLEGAL_COMMAND_FORMAT
        elif errorcode == '0005':
            status = ErrorCode.TERMINAL_OFFLINE
        else:
            status = ErrorCode.TERMINAL_OTHER_ERRORS

        message = ErrorCode.ERROR_MESSAGE[status]
        return status, message 
