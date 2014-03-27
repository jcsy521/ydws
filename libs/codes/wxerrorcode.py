# -*- coding: utf-8 -*-
class WXErrorCode(object):
    """definitions for various Error Code."""
    SUCCESS = 0
    FAILED = -1

    USER_BIND = 100     

    ERROR_MESSAGE = {
        SUCCESS:                       u"操作成功。",
        FAILED:                        u"操作失败。",
        USER_BIND:                     u"对不起，您没有绑定位置账户和移动车卫士账户",
        }
