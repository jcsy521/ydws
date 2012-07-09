# -*- coding: utf-8 -*-
import logging
from codes.errorcode import ErrorCode

class LBMPMessageHelper(object):
    """ Provide different methods to format different kinds of messages 
    """

    @staticmethod
    def format_lbmp_response(response):
        """
        @param response: response returned from LBMP.
        """
        
        status = ErrorCode.FAILED
        errorcode = int(response['success'])
        logging.error("[LBMP]: %s", response['info'])

        if errorcode == 0:
            status = ErrorCode.SUCCESS
        elif errorcode == 11195:
            status = ErrorCode.TERMINAL_OFFLINE
        elif errorcode == 9990242:
            status = ErrorCode.CELLID_REMIND_WEB
        elif errorcode == 9993002:
            status = ErrorCode.TERMINAL_TIME_OUT
        elif errorcode in (9999256, 9990240):
            status = ErrorCode.CELLID_NOT_ORDERED
        else: 
            status = ErrorCode.TERMINAL_OTHER_ERRORS
        message = ErrorCode.ERROR_MESSAGE[status]

        return status, message
