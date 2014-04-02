# -*- coding: utf-8 -*-
class WXErrorCode(object):
    """definitions for various Error Code."""
    SUCCESS = 0
    FAILED = -1

    USER_BIND = 100     
    USER_EXIST = 101    
    USER_BINDED = 102  
    USER_FLUSH =  103   
    OUTSERVICE = 104

    ILLEGAL_DATA_FORMAT = 120

    ERROR_MESSAGE = {
        SUCCESS:                       u"操作成功。",
        FAILED:                        u"操作失败。",
        USER_BIND:                     u"对不起，您没有绑定微信账户和移动车卫士账户",
        USER_EXIST:                    u"对不起，您填写的移动车卫士用户名或者密码不正确",
        USER_BINDED:                   u"对不起，您微信已经绑定移动车卫士帐号，如需要更改请先解绑",
        ILLEGAL_DATA_FORMAT:           u"错误的数据格式。",
        USER_FLUSH:                    u"对不起，不支持刷新,请您点击菜单再次操作",
        OUTSERVICE:                    u"对不起， 服务繁忙请稍后重试",
        }
