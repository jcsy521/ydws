# -*- coding: utf-8 -*-

class SMSCode(object):
    """Definitions for various SMS literal strings"""
    # TO terminal
    SMS_TSIM = u":T_SIM %s"
    SMS_USIM = u":U_SIM %s"
    SMS_DOMAIN = u":DOMAIN %s"
    SMS_LQ = u":LQ %s"
    SMS_REGISTER = SMS_TSIM + SMS_USIM 

    # TO user
    SMS_TRACKER_POWERLOW = u"定位器%s后备电池电量不足，当前电量为%d%%；时间：%s"
    SMS_FOB_POWERLOW = u"定位器挂件%s电池电量不足，当前电量为%d%%；时间：%s"
    SMS_POWEROFF = u"定位器%s断电，定位器在：%s，时间：%s"
    SMS_REGION_OUT = u"定位器%s越界，定位器在：%s，时间：%s"
    SMS_SPEED_OUT= u"定位器%s超速，定位器在：%s，时间：%s"
    SMS_ILLEGALMOVE = u"定位器%s非法移动，定位器在：%s，时间：%s"
    SMS_HEARTBEAT_LOST = u"车主您好，定位器%s与平台通讯可能出现异常，请检查，时间：%s"
    SMS_SOS = u"定位器%s发起SOS请求，定位器在：%s，时间：%s"
    SMS_REALTIME_RESULT = u"实时定位结果：定位器%s在：%s，时间：%s"
    SMS_LOGIN_REMIND = u"尊敬的车主，您于%s通过%s登陆车联网平台，车主号码为%s，所关注定位器号码为%s。"
    SMS_CHARGE = u"尊敬的车主，定位器%s，%s，时间：%s"
    SMS_SERVICE_STOP = u"尊敬的车主，定位器%s已经停止服务。"

