# -*- coding: utf-8 -*-

class SMSCode(object):
    """Definitions for various SMS literal strings"""
    SMS_TSIM = u":T_SIM %s"
    SMS_USIM = u":U_SIM %s"
    SMS_DOMAIN = u":DOMAIN %s"
    SMS_LQ = u":LQ %s"
    SMS_REGISTER = SMS_TSIM + SMS_USIM 
