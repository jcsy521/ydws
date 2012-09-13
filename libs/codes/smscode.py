# -*- coding: utf-8 -*-

class SMSCode(object):
    """Definitions for various SMS literal strings"""
    # TO terminal
    SMS_TSIM = u":T_SIM %s"
    SMS_USIM = u":U_SIM %s"
    SMS_DOMAIN = u":DOMAIN %s"
    SMS_LQ = u":LQ %s"
    SMS_REGISTER = u":SIM %s:%s" 
    SMS_CF = u":CF"
    SMS_SF = u":SF"

    # TO user
    SMS_TRACKER_POWERLOW = u"您的爱车保%s电量不足，当前电量为%d%%，地址：%s，时间：%s"
    SMS_FOB_POWERLOW = u"您的爱车保挂件%s电量不足，当前电量为%d%%，地址：%s，时间：%s"
    SMS_POWEROFF = u"您的爱车保%s断电，地址：%s，时间：%s"
    SMS_REGION_OUT = u"您的爱车保%s越界，地址：%s，时间：%s"
    SMS_SPEED_OUT= u"您的爱车保%s超速，地址：%s，时间：%s"
    SMS_ILLEGALMOVE = u"您的爱车保%s非法移动，地址：%s，时间：%s"
    SMS_HEARTBEAT_LOST = u"车主您好，您的爱车保%s与平台通讯可能出现异常，请检查，时间：%s"
    SMS_SOS = u"您的爱车保%s发起SOS请求，地址：%s，时间：%s"
    SMS_REALTIME_RESULT = u"实时定位结果：您的爱车保%s在：%s，时间：%s"
    SMS_LOGIN_REMIND = u"尊敬的车主，您于%s通过%s登陆爱车保平台，车主号码为%s，所关注的爱车保为%s。"
    SMS_CHARGE = u"爱车保%s余额信息：%s"
    SMS_SERVICE_STOP = u"尊敬的车主，您的爱车保%s已经停止服务。"
    SMS_RETRIEVE_PASSWORD = u"尊敬的车主,您刚才使用了爱车保网站的密码找回功能，新的登陆密码为：%s，请妥善保管。" 

    SMS_JH_SUCCESS = u"您的爱车保%s激活成功，平台网址：%s，用户名：%s，密码：%s。"
    SMS_JH_FAILED = u"激活失败，请确认手机号是否正确，或联系爱车保客服：400-xxxx-xxxx。"
    SMS_TERMINAL_HK = u"您的爱车保%s已经换卡，请发送换卡短信指令：‘HK+新爱车保号码+平台登录密码’到新爱车保号码。例如：HK 13900000000 111111"
    SMS_USER_HK_SUCCESS = u"车主号码换卡成功，新卡号码：%s，平台网址：%s，用户名：%s，密码：%s。"
    SMS_TERMINAL_HK_SUCCESS = u"您的爱车保%s换卡成功，新卡号码：%s！"
    SMS_USER_ADD_TERMINAL = u"您的号码绑定了新的爱车保号码%s。请登录平台网址：%s查看。"
    SMS_PSD_WRONG = u"密码错误，请重新确认！"
