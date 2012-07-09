# -*- coding: utf-8 -*-

class GFCode(object):
    """definitions for various GF status Code."""

    SUCCESS = '0000'
    ILLEGAL_FORMAT = '0001'
    UNKNOWN_COMMAND = '0002'
    ILLEGAL_TERMINAL = '0003'
    GF_NOT_ORDERED = '0004'
    TERMINAL_OFFLINE = '0005'
    ILLEGAL_COMMAND = '0006'
    OTHER_ERROR = '0007'

    ERROR_MESSAGE  = {
        SUCCESS:           u"成功",
        ILLEGAL_FORMAT:    u"命令参数错误",
        UNKNOWN_COMMAND:   u"无此命令",
        ILLEGAL_TERMINAL:  u"部分终端非法",
        GF_NOT_ORDERED:    u"终端求订购业务",
        TERMINAL_OFFLINE:  u"终端不在线",
        ILLEGAL_COMMAND:   u"终端不支持下发命令",
        OTHER_ERROR:       u"当前无法下发"

    }

