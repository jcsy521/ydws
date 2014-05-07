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
    ILLEGAL_EXCEL_FILE = 130
    ILLEGAL_MOBILE = 131
    ILLEGAL_LABEL = 132
    ILLEGAL_FILE = 133

    LOGIN_FAILED = 200
    LOGIN_AGAIN = 201
    WRONG_CAPTCHA = 202
    WRONG_PASSWORD = 203 
    WRONG_OLD_PASSWORD = 204
    NO_CAPTCHA = 205
    TEST_NOT_PERMITED = 206

    USER_NOT_ORDERED = 213 
    TERMINAL_NOT_ORDERED = 214
    TERMINAL_ORDERED = 215
    TERMINAL_SET_FAILED= 216
    TERMINAL_NOT_EXISTED = 217
    EC_MOBILE_EXISTED = 218
    EC_NAME_EXISTED = 219
    CNUM_EXISTED = 220
    MOBILE_NOT_ORDERED = 221
    TRACK_POINTS_TOO_MUCH = 222
    USER_NOT_EXIST = 223
    TERMINAL_EXIST = 224
    TERMINAL_BINDED = 225
    
    GROUP_HAS_TERMINAL = 226
    GROUP_EXIST = 227

    LOCATION_NAME_NONE = 300
    LOCATION_FAILED = 301
    LOCATION_CELLID_FAILED = 302
    LOCATION_OFFSET_FAILED = 303
    TRACKER_POWER_FULL = 304
    TRACKER_POWER_LOW = 305
    TRACKER_POWER_OFF = 306
    FOB_POWER_LOW = 307
    
    CREATE_USER_FAILURE = 400
    SELECT_CONDITION_ILLEGAL = 401
    SEARCH_BUSINESS_FAILURE = 402
    EDIT_CONDITION_ILLEGAL = 403
    CREATE_CONDITION_ILLEGAL = 404
    EDIT_USER_FAILURE = 405

    QUERY_TRACK_FORBID = 700
    QUERY_INTERVAL_EXCESS = 701
    REGION_ADDITION_EXCESS = 702
    REGION_NOT_EXISTED = 703 

    TERMINAL_OFFLINE = 800
    TERMINAL_OTHER_ERRORS = 802
    TERMINAL_TIME_OUT = 801

    UNKNOWN_COMMAND = 901
    SERVER_ERROR = 903
    SERVER_BUSY = 904
    FEEDBACK_FAILED = 907

    REGISTER_FAILED = 908
    TINYURL_EXPIRED = 909

    EXPORT_FAILED = 910
    
    DATA_EXIST = 911
    PASSENGER_EXIST = 912
    OPERATOR_EXIST = 913
    CORP_EXIST = 914

    ACTIVITY_EXISTED = 1001 
    ACTIVITY_NAME_ILLEGAL = 1002

    ACCOUNT_NOT_MATCH = 1101

    # for ajt
    AJT_ORDERED = 1201
    AJT_NOT_ORDERED = 1202

    ERROR_MESSAGE  = {
        SUCCESS:                       u"操作成功。",
        FAILED:                        u"操作失败。",
        ILLEGAL_DATA_FORMAT:           u"错误的数据格式。",
        ILLEGAL_ALIAS:                 u"定位器别名中含有非法字符，请重新输入。",
        ILLEGAL_CNUM:                  u"定位器名称只能由汉字、数字、大写英文组成。",
        ILLEGAL_WHITELIST:             u"SOS联系人中含有非法字符，请重新输入。",
        ILLEGAL_NAME:                  u"用户姓名只能是由数字、英文、中文组成.",
        ILLEGAL_ADDRESS:               u"地址中含有非法字符，请重新输入。",
        ILLEGAL_EMAIL:                 u"E-MAIL中含有非法字符，请重新输入。",
        ILLEGAL_REMARK:                u"备注内容中含有非法字符，请重新输入。",
        ILLEGAL_PASSWORD:              u"密码中含有非法字符，密码为不少于6位的字母或数字组成，请重新输入。",
        ILLEGAL_CONTENT:               u"反馈内容中含有非法字符，请重新输入。",
        ILLEGAL_EXCEL_FILE:            u"非法的文件，请选择excel表。",
        ILLEGAL_MOBILE:                u"非法的手机号。",
        ILLEGAL_LABEL:                 u"对不起，只允许输入数字和字母。",
        ILLEGAL_FILE:                  u"文件导入失败，请检查导入文件。",
        WRONG_CAPTCHA:                 u"验证码输入错误。",
        WRONG_PASSWORD:                u"密码错误，请重新输入。",
        WRONG_OLD_PASSWORD:            u"原始密码错误，请重新输入。",
        NO_CAPTCHA:                    u"验证码已失效，请重新获取。",
        LOGIN_FAILED:                  u"用户名或密码输入错误。",
        LOGIN_AGAIN:                   u"业务信息发生变更，请重新登录。",
        TEST_NOT_PERMITED:             u"对不起，该账号是体验账号，不能使用该功能。",
        USER_NOT_ORDERED:              u"对不起, 该号码尚未订购移动卫士业务。",
        TRACK_POINTS_TOO_MUCH:         u"对不起，您的网速太慢，数据太多了，请缩小查询范围。",
        USER_NOT_EXIST:                u"对不起，当前用户不存在。",
        SERVER_ERROR:                  u"服务器错误。",
        SERVER_BUSY:                   u"服务器忙，请稍后重试。",
        QUERY_TRACK_FORBID:            u"您使用的是简易版移动卫士，不支持轨迹查询功能。",
        QUERY_INTERVAL_EXCESS:         u"对不起，只能查询一个星期之内的记录！",
        REGION_ADDITION_EXCESS:        u"对不起，电子围栏数已超过上限。",
        REGION_NOT_EXISTED:            u"对不起，该围栏已经不存在。",
        TERMINAL_NOT_ORDERED:          u"对不起，该号码尚未绑定定位器。",
        MOBILE_NOT_ORDERED:            u"%s不是移动卫士白名单号码，请联系客服。",
        TERMINAL_NOT_EXISTED:          u"对不起，该终端不存在。",
        LOCATION_NAME_NONE:            u"无法解析经纬度对应的地址",
        LOCATION_FAILED:               u"定位不成功",
        LOCATION_CELLID_FAILED:        u"定位失败,请尝试将定位器移至室外再次定位!",
        LOCATION_OFFSET_FAILED :       u"经纬度偏转失败，请稍后重试。",
        TRACKER_POWER_FULL:            u"定位器电池充满，剩余电量100%",
        TRACKER_POWER_LOW:             u"定位器电量低，剩余电量%s%%",
        TRACKER_POWER_OFF:             u"定位器电量低于5%，即将关机",
        FOB_POWER_LOW:                 u"定位器挂件“%s”电量低",
        TERMINAL_OFFLINE:              u"定位器不在线，请确认定位器处于开机状态。",
        TERMINAL_TIME_OUT:             u"定位器响应超时，请稍后重试。",
        TERMINAL_OTHER_ERRORS:         u"连接定位器失败，请稍后重试。",
        TERMINAL_ORDERED:              u"该定位器号码已被绑定，请尝试输入其他定位器号码进行绑定。",
        #TERMINAL_ORDERED:              u"定位器手机号已被注册，请检查确认后重试！",
        EC_MOBILE_EXISTED:             u"集团手机号已被注册，请检查确认后重试！",
        EC_NAME_EXISTED:               u"该集团已被注册，请检查确认后重试！",
        CNUM_EXISTED:                  u"该定位器名称被使用！",
        TERMINAL_SET_FAILED:           u"定位器参数设置失败，请稍后重试。",
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
        EXPORT_FAILED:                 u"导出数据失败，请稍后重试。", 
        DATA_EXIST:                    u"数据已存在。",
        PASSENGER_EXIST:               u"乘客已存在。",
        OPERATOR_EXIST:                u"集团操作员已存在。",
        CORP_EXIST:                    u"集团管理员已存在。",
        TERMINAL_EXIST:                u"该定位器已经存在。",
        TERMINAL_BINDED:               u"该定位器已经存在，请输入其他定位器号码进行绑定。",

        GROUP_HAS_TERMINAL:            u"该分组下有定位器,不能删除。",
        GROUP_EXIST:                   u"该分组已存在。", 

        ACTIVITY_EXISTED:              u"文件已经存在，请先删除。",
        ACTIVITY_NAME_ILLEGAL:         u"文件名只能包含字母、数字、下划线、点。",

        ACCOUNT_NOT_MATCH:             u"账号不符，请联系客户人员。",

        AJT_ORDERED:                   u"%s已经是安捷通白名单号码。",
        AJT_NOT_ORDERED:               u"%s不是安捷通白名单号码，请联系客服。",

    }
