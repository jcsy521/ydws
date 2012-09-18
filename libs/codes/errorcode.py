# -*- coding: utf-8 -*-

class ErrorCode(object):
    """definitions for various Error Code."""

    # 000 : success
    SUCCESS = 0
    FAILED = -1

    ILLEGAL_DATA_FORMAT = 120

    LOGIN_FAILED = 200
    LOGIN_AGAIN = 201
    WRONG_CAPTCHA = 202
    WRONG_PASSWORD = 203 

    REGISTER_EXIST = 205
    USER_MOBILE_EXIST = 206
    USER_UID_EXIST = 207
    NO_TERMINAL = 208
    TERMINAL_MOBILE_EXIST = 209
    TERMINAL_TID_EXIST = 210
    USER_NOT_EXIST = 211
    USER_EXCESS = 212
    USER_NOT_ORDER = 213
    

    PARENT_NOT_ORDERED = 214
    TERMINAL_NOT_ORDERED = 215
    TERMINAL_ORDERED = 216
    TERMINAL_SET_FAILED= 217

    LOCATION_NAME_NONE = 300
    LOCATION_FAILED = 301
    LOCATION_CELLID_FAILED = 302
    LOCATION_OFFSET_FAILED = 303
    
    CREATE_USER_FAILURE = 400
    SELECT_CONDITION_ILLEGAL = 401
    SEARCH_BUSINESS_FAILURE = 402
    EDIT_CONDITION_ILLEGAL = 403
    CREATE_CONDITION_ILLEGAL = 404
    EDIT_USER_FAILURE = 405

    ADDITION_EXCESS = 700
    QUERY_INTERVAL_EXCESS = 701

    TERMINAL_OFFLINE = 800
    TERMINAL_OTHER_ERRORS = 802
    TERMINAL_TIME_OUT = 801

    UNKNOWN_COMMAND = 901
    SERVER_ERROR = 903
    SERVER_BUSY = 904
    DOWNLOAD_FAILED = 906
    FEEDBACK_FAILED = 907

    ERROR_MESSAGE  = {
        SUCCESS:                    u"操作成功。",
        FAILED:                     u"操作失败。",
        ILLEGAL_DATA_FORMAT:        u"错误的数据格式。",
        WRONG_CAPTCHA:              u"验证码错误。",
        WRONG_PASSWORD:             u"密码错误",
        LOGIN_FAILED:               u"用户名或密码错误。",
        LOGIN_AGAIN:                u"业务信息发生变更，请重新登录。",
        USER_MOBILE_EXIST:          u"手机号已被关联。",
        USER_UID_EXIST:             u"该用户名已被使用。",
        REGISTER_EXIST:             u"用户已存在。",
        TERMINAL_MOBILE_EXIST:      u"爱车保号码已被关联。",
        TERMINAL_TID_EXIST:         u"爱车保已被关联。",
        USER_NOT_EXIST:             u"用户不存在。",
        USER_NOT_ORDER:             u"该手机号未订购爱车保业务。",
        USER_EXCESS:                u'用户已达到定位器的上限，不能再订购新的定位器。', 
        NO_TERMINAL:                u"您尚未关联车辆。",
        SERVER_ERROR:               u"服务器错误。",
        SERVER_BUSY:                u"服务器忙，请稍后重试。",
        ADDITION_EXCESS:            u'该功能设置已超过上限，本次操作失败。',
        QUERY_INTERVAL_EXCESS:      u'对不起，只能查询一个星期之内的记录！',
        PARENT_NOT_ORDERED:         u'您输入的用户名或密码有误，请重新输入！',
        TERMINAL_NOT_ORDERED:       u'对不起，该号码尚未订购"爱车保"业务！',
        LOCATION_NAME_NONE:         u"无法解析经纬度对应的地址",
        LOCATION_FAILED:            u"无法获取爱车保当前位置，请稍后重试。",
        LOCATION_CELLID_FAILED:     u"爱车保基站定位失败，请稍后重试。",
        LOCATION_OFFSET_FAILED :    u"经纬度偏转失败，请稍后重试。",
        TERMINAL_OFFLINE:           u'您的爱车保不在线。',
        TERMINAL_TIME_OUT:          u'连接爱车保超时，请稍后重试。',
        TERMINAL_OTHER_ERRORS:      u'连接爱车保失败，请稍后重试。',
        TERMINAL_ORDERED:           u'终端手机已被注册，请检查确认后再重试！',
        TERMINAL_SET_FAILED:        u'终端参数设置失败，请稍后重试。',
        UNKNOWN_COMMAND:            u"您好，你输入的指令爱车保系统不识别，请输入标准指令。",
        CREATE_USER_FAILURE:        u"添加用户失败。",
        SELECT_CONDITION_ILLEGAL:   u"您输入的查询条件非法。",
        SEARCH_BUSINESS_FAILURE:    u"查询普通用户业务失败。",
        EDIT_CONDITION_ILLEGAL:     u"您输入的编辑内容非法。",
        CREATE_CONDITION_ILLEGAL:   u"您输入的创建内容非法。",
        EDIT_USER_FAILURE:          u"编辑普通用户业务失败。",
        DOWNLOAD_FAILED:            u'对不起，下载失败，请稍后重试。',
        FEEDBACK_FAILED:            u'对不起，反馈失败，请稍后重试。',
    }
