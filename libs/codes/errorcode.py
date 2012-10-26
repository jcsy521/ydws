# -*- coding: utf-8 -*-

class ErrorCode(object):
    """definitions for various Error Code."""

    # 000 : success
    SUCCESS = 0
    FAILED = -1

    ILLEGAL_DATA_FORMAT = 120
    ILLEGAL_ALIAS = 121
    ILLEGAL_CNUM = 122
    ILLEGAL_WHITELIST = 123
    ILLEGAL_NAME = 124
    ILLEGAL_ADDRESS = 125
    ILLEGAL_EMAIL = 126
    ILLEGAL_REMARK = 127
    ILLEGAL_PASSWORD = 128
    ILLEGAL_CONTENT = 129

    LOGIN_FAILED = 200
    LOGIN_AGAIN = 201
    WRONG_CAPTCHA = 202
    WRONG_PASSWORD = 203 
    NO_CAPTCHA = 204

    USER_NOT_ORDERED = 213 
    TERMINAL_NOT_ORDERED = 214
    TERMINAL_ORDERED = 215
    TERMINAL_SET_FAILED= 216

    LOCATION_NAME_NONE = 300
    LOCATION_CELLID_FAILED = 302
    LOCATION_OFFSET_FAILED = 303
    
    CREATE_USER_FAILURE = 400
    SELECT_CONDITION_ILLEGAL = 401
    SEARCH_BUSINESS_FAILURE = 402
    EDIT_CONDITION_ILLEGAL = 403
    CREATE_CONDITION_ILLEGAL = 404
    EDIT_USER_FAILURE = 405

    QUERY_INTERVAL_EXCESS = 701

    TERMINAL_OFFLINE = 800
    TERMINAL_OTHER_ERRORS = 802
    TERMINAL_TIME_OUT = 801

    UNKNOWN_COMMAND = 901
    SERVER_ERROR = 903
    SERVER_BUSY = 904
    FEEDBACK_FAILED = 907

    REGISTER_FAILED = 908
    TINYURL_EXPIRED = 909

    ERROR_MESSAGE  = {
        SUCCESS:                       u"操作成功。",
        FAILED:                        u"操作失败。",
        ILLEGAL_DATA_FORMAT:           u"错误的数据格式。",
        ILLEGAL_ALIAS:                 u"追踪器别名中含有非法字符，请重新输入。",
        ILLEGAL_CNUM:                  u"车牌号中含有非法字符，请重新输入。",
        ILLEGAL_WHITELIST:             u"SOS联系人中含有非法字符，请重新输入。",
        ILLEGAL_NAME:                  u"姓名中含有非法字符，请重新输入。",
        ILLEGAL_ADDRESS:               u"地址中含有非法字符，请重新输入。",
        ILLEGAL_EMAIL:                 u"E-MAIL中含有非法字符，请重新输入。",
        ILLEGAL_REMARK:                u"备注内容中含有非法字符，请重新输入。",
        ILLEGAL_PASSWORD:              u"密码中含有非法字符，请重新输入。",
        ILLEGAL_CONTENT:               u"反馈内容中含有非法字符，请重新输入。",
        WRONG_CAPTCHA:                 u"验证码错误。",
        WRONG_PASSWORD:                u"原始密码错误，请重新输入。",
        NO_CAPTCHA:                    u"验证码失效，请重新获取。",
        LOGIN_FAILED:                  u"用户名或密码错误。",
        LOGIN_AGAIN:                   u"业务信息发生变更，请重新登录。",
        USER_NOT_ORDERED:              u"对不起, 该号码尚未订购移动车卫士业务。",
        SERVER_ERROR:                  u"服务器错误。",
        SERVER_BUSY:                   u"服务器忙，请稍后重试。",
        QUERY_INTERVAL_EXCESS:         u"对不起，只能查询一个星期之内的记录！",
        TERMINAL_NOT_ORDERED:          u"对不起，该号码尚未绑定追踪器。",
        LOCATION_NAME_NONE:            u"无法解析经纬度对应的地址",
        LOCATION_CELLID_FAILED:        u"追踪器基站定位失败，请稍后重试。",
        LOCATION_OFFSET_FAILED :       u"经纬度偏转失败，请稍后重试。",
        TERMINAL_OFFLINE:              u"追踪器不在线，请稍后重试。",
        TERMINAL_TIME_OUT:             u"追踪器响应超时，请稍后重试。",
        TERMINAL_OTHER_ERRORS:         u"连接追踪器失败，请稍后重试。",
        TERMINAL_ORDERED:              u"追踪器手机号已被注册，请检查确认后再重试！",
        TERMINAL_SET_FAILED:           u"追踪器参数设置失败，请稍后重试。",
        UNKNOWN_COMMAND:               u"您好，你输入的指令系统不识别，请输入标准指令。",
        CREATE_USER_FAILURE:           u"添加用户失败。",
        SELECT_CONDITION_ILLEGAL:      u"您输入的查询条件非法。",
        SEARCH_BUSINESS_FAILURE:       u"查询普通用户业务失败。",
        EDIT_CONDITION_ILLEGAL:        u"您输入的编辑内容非法。",
        CREATE_CONDITION_ILLEGAL:      u"您输入的创建内容非法。",
        EDIT_USER_FAILURE:             u"编辑普通用户业务失败。",
        FEEDBACK_FAILED:               u"对不起，添加反馈失败，请稍后重试。",
        REGISTER_FAILED:               u"对不起，注册失败，请稍后重试。",
        TINYURL_EXPIRED:               u"对不起，该链接已失效。",
    }
