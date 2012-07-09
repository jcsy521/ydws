# -*- coding: utf-8 -*-

class CLWCode(object):
    """definitions for various GF status Code."""

    SUCCESS = 1 
    FAILED = 0

    #LOGIN_FAILED = 10
    #LOGIN_SUCCESS = 11
    #LOGIN_NO_REGIST = 12
    #LOGIN_SERVICE_EXPIRE = 13
    #LOGIN_CHANGE_SIM = 14

    # report location valid
    LOCATION_FAILED = 10
    LOCATION_SUCCESS = 11
    LOCATION_LAST = 12

    # defend status
    DEFEND_FAILED = 20
    DEFEND_SUCCESS = 21
    DEFEND_NO_HOST_SUCCESS = 22
    DEFEND_NO_HOST_FAILED = 23

    ERROR_MESSAGE  = {
        SUCCESS:           u"成功",
        FAILED:            u"失败",

        #LOGIN_FAILED:      u"登录失败",
        #LOGIN_SUCCESS:     u"登录成功",
        #LOGIN_NO_REGIST:   u"终端未注册"
        #LOGIN_SERVICE_EXPIRE: u"服务到期",
        #LOGIN_CHANGE_SIM:  u"终端已注册，但更换了非法SIM卡",

        LOCATION_FAILED:   u"定位失败",
        LOCATION_SUCCESS:  u"定位成功",
        LOCATION_LAST:     u"最近定位信息",

        DEFEND_FAILED:     u"设防失败",
        DEFEND_SUCCESS:    u"设防成功",
        DEFEND_NO_HOST_SUCCESS:   u"无主电设防成功",
        DEFEND_NO_HOST_FAILED:    u"无主电设防失败"
    }

