# -*- coding: utf-8 -*-

class ErrorCode(object):
    """definitions for various Error Code."""

    FAILED = -1 
    SUCCESS = 0
    SID_NOT_EXISTED = 1
    SIGN_ILLEGAL = 2
    MOBILE_NOT_EXISTED = 3
    TOKEN_EXPIRED = 4
    DATA_FORMAT_INVALID = 5
    LOCATION_EXCEED = 6


    ERROR_MESSAGE  = {

        FAILED:                        u"操作失败。",
        SUCCESS:                       u"操作成功。",
        SID_NOT_EXISTED:               u"Sid 不存在。",
        SIGN_ILLEGAL:                  u"Sign 错误。",
        MOBILE_NOT_EXISTED:            u"Mobile 不存在。",
        TOKEN_EXPIRED:                 u"Token 已过期。",
        DATA_FORMAT_INVALID:           u"请求参数格式错误。",
        LOCATION_EXCEED:               u"轨迹查询时间范围过长。",

    }
