# -*- coding: utf-8 -*-

class SMSCode(object):
    """Definitions for various SMS literal strings"""
    # TO terminal
    SMS_TSIM = u":T_SIM %s"
    SMS_USIM = u":U_SIM %s"
    SMS_DOMAIN = u":DOMAIN %s"
    SMS_LQ = u":LQ %s"
    SMS_REGISTER = u":SIM %s:%s" 
    SMS_UNBIND = u":JB" 
    SMS_CF = u":CF"
    SMS_SF = u":SF"
    SMS_LQGZ = u":LQGZ %s"

    # TO user
    SMS_TRACKER_POWERLOW = u"尊敬的客户：您的定位器“%s”电量不足，当前电量为%d%%，地址：%s，时间：%s。"
    SMS_FOB_POWERLOW = u"尊敬的客户：您的定位器挂件“%s”电量不足，当前电量为20%%，时间：%s。"
    SMS_POWEROFF_TIMEOUT = u"尊敬的客户：您的定位器“%s”已经关机，为了安全请及时充电并保持开机状态。"
    SMS_POWERLOW_OFF = u"尊敬的客户：您的定位器“%s”电量过低，即将关机，为了安全请及时充电并保持开机状态。地址：%s，时间：%s。"
    SMS_POWERFULL = u"尊敬的客户：您的定位器“%s”已经充电完成，请拔下电源。"
    SMS_ILLEGALMOVE = u"尊敬的客户：您的车辆“%s”发生移动，地址：%s，时间：%s。如需取消短信提醒，请执行撤防操作。"
    SMS_ILLEGALSHAKE= u"尊敬的客户：您的车辆“%s”发生震动，请关注车辆状态，地址：%s，时间：%s。如需取消短信提醒，请执行撤防操作。"
    SMS_HEARTBEAT_LOST = u"尊敬的客户：您的定位器“%s”与平台通讯可能出现异常，请检查定位器是否处于正常状态，时间：%s。"
    SMS_SOS = u"您的定位器“%s”发起的应急救援请求，【移动车卫士】平台已收到，地址：%s，时间：%s。"
    SMS_SOS_OWNER = u"您的定位器“%s”发起应急救援请求，已通知%s，当前所在位置：%s，时间：%s。"
    SMS_SOS_WHITE = u"您的定位器“%s”发起应急救援请求，当前所在位置：%s，时间：%s。"
    SMS_LOGIN_REMIND = u"尊敬的客户：您于%s通过%s登陆【移动车卫士】平台，车主号码为%s，所关联的定位器为“%s”。"
    SMS_CHARGE = u"尊敬的客户：您的定位器“%s”当前剩余GPRS流量为：%s，敬请留意。"
    SMS_CHARGE_REMIND = u"尊敬的客户：为了不影响移动车卫士业务的正常使用，请您及时为您的移动车卫士账号：%s进行充值，如已经缴费或者已经合并账号缴费请不用理会此短信。【移动车卫士】"
    SMS_SERVICE_STOP = u"尊敬的客户：您的定位器“%s”已经停止服务。"
    SMS_RETRIEVE_PASSWORD = u"尊敬的客户：您刚才使用了【移动车卫士】密码找回功能，新的登陆密码为：%s，请妥善保管。如需修改密码，请登录【移动车卫士】网站或手机客户端进行修改。" 
    SMS_REG = u"尊敬的客户：您刚才绑定了【移动车卫士】定位器，验证码为：%s，请5分钟内进行激活。若非您本人或授权操作，请联系【移动车卫士】客服。" 
    SMS_DW_SUCCESS = u"尊敬的客户：您的定位器“%s”%s定位成功，地址：%s，时间：%s。"
    SMS_DW_FAILED = u"尊敬的客户：您的定位器“%s”%s定位失败。"
    SMS_DEFEND_SUCCESS = u"尊敬的客户：您的定位器“%s”%s成功。"

    SMS_JH_SUCCESS = u"尊敬的客户：您的定位器“%s”激活成功，平台网址：%s，用户名：%s，密码：%s"
    SMS_JH_FAILED = u"激活失败，请确认手机号是否正确，或联系【移动车卫士】客服。"
    #SMS_TERMINAL_HK = u"尊敬的客户：您的定位器“%s”已经换卡，请发送换卡短信指令：‘HK(空格)新定位器号码(空格)平台登录密码’到新定位器号码。例如：HK 13900000000 111111"
    SMS_TERMINAL_HK = u"尊敬的客户：您的定位器“%s”已经换卡，请先执行解绑操作。"
    SMS_USER_HK_SUCCESS = u"尊敬的客户：已成功更换车主号码，新车主号码：%s，平台网址：%s，用户名：%s，密码：%s"
    SMS_TERMINAL_HK_SUCCESS = u"尊敬的客户：您的定位器“%s”换卡成功，新卡号码：%s"
    SMS_USER_ADD_TERMINAL = u"尊敬的客户：您的号码已绑定了新的定位器号码%s。请登录平台网址：%s查看。"
    SMS_PSD_WRONG = u"尊敬的客户：您输入的密码错误，请重新确认！"
    SMS_TID_EXIST = u"尊敬的客户：该定位器序列号%s冲突，请联系【移动车卫士】客服。"
    SMS_TID_NOT_EXIST = u"尊敬的客户：该定位器未激活，请执行激活短信指令：‘JH(空格)定位器号码’到定位器号码。例如：JH 13900000000"
    SMS_MOBILE_NOT_WHITELIST = u"尊敬的客户：您的终端号码%s不合法，不是指定移动车卫士号码，请联系【移动车卫士】客服。"


    SMS_DOWNLOAD_REMIND = u"尊敬的客户：请手机登录中山无线城市手机网站 gd.wxcs.cn/zs 进入‘下载’-‘移动车卫士’ 下载安装【移动车卫士】客户端。"

    SMS_NEW_OPERATOR = u"尊敬的客户：您已经成为移动车卫士集团用户管理员，平台网址：%s，用户名：%s，密码：%s"
    SMS_SERVICE_EXCEPTION_REPORT = u"管理员你好，平台%s，不能检测到模拟终端的位置更新，服务可能发生异常，请检查！！！"
    
    SMS_REGION_ENTER = u"尊敬的客户：您的定位器%s已进入电子围栏“%s”，位置在：%s，时间：%s"
    SMS_REGION_OUT = u"尊敬的客户：您的定位器%s已离开电子围栏“%s”，位置在：%s，时间：%s"
