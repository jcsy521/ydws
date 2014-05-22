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
    SMS_KQLY = u":KQLY %s"
    SMS_CQ = u":CQ"

    # TO user
    SMS_TRACKER_POWERLOW = u"尊敬的客户：您的定位器“%s”电量不足，当前电量为%d%%，地址：%s，时间：%s。"
    SMS_TRACKER_POWERLOW_NOLOC = u"尊敬的客户：您的定位器“%s”电量不足，当前电量为%d%%，地址：因定位信号弱，当前暂时无法定位，请关注定位器状态，时间：%s。"
    SMS_FOB_POWERLOW = u"尊敬的客户：您的定位器挂件“%s”电量不足，当前电量为20%%，时间：%s。"
    SMS_POWEROFF_TIMEOUT = u"尊敬的客户：您的定位器“%s”已经关机，为了安全请及时充电并保持开机状态。"
    SMS_POWERLOW_OFF = u"尊敬的客户：您的定位器“%s”电量过低，即将关机，为了安全请及时充电并保持开机状态。地址：%s，时间：%s。"
    SMS_POWERLOW_OFF_NOLOC = u"尊敬的客户：您的定位器“%s”电量过低，即将关机，为了安全请及时充电并保持开机状态。地址：因定位信号弱，当前暂时无法定位，请关注定位器状态，时间：%s。"
    SMS_POWERFULL = u"尊敬的客户：您的定位器“%s”已经充电完成，请拔下电源。"
    SMS_POWERDOWN = u"尊敬的客户：您的定位器“%s”已检测到断电告警。地址：%s，时间：%s。"
    SMS_POWERDOWN_NOLOC = u"尊敬的客户：您的定位器“%s”已检测到断电告警。地址：因定位信号弱，当前暂时无法定位，请关注定位器状态，时间：%s。"
    SMS_ILLEGALMOVE = u"尊敬的客户：您的定位器“%s”发生移动，地址：%s，时间：%s。如需取消短信提醒，请执行撤防操作。"
    SMS_ILLEGALMOVE_NOLOC = u"尊敬的客户：您的定位器“%s”发生移动，地址：因定位信号弱，当前暂时无法定位，请关注定位器状态，时间：%s。如需取消短信提醒，请执行撤防操作。"
    SMS_ILLEGALSHAKE= u"尊敬的客户：您的定位器“%s”发生震动，请关注定位器状态，地址：%s，时间：%s。如需取消短信提醒，请执行撤防操作。"
    SMS_ILLEGALSHAKE_NOLOC = u"尊敬的客户：您的定位器“%s”发生震动，请关注定位器状态，地址：因定位信号弱，当前暂时无法定位，请关注定位器状态，时间：%s。如需取消短信提醒，请执行撤防操作。"
    SMS_HEARTBEAT_LOST = u"尊敬的客户：您的定位器“%s”与平台通讯可能出现异常，请检查定位器是否处于正常状态，时间：%s。"
    SMS_HEARTBEAT_LOST_YDWQ = u"尊敬的客户：您的移动卫士(位置上报)“%s”与平台通讯可能出现异常，请检查是否处于正常状态，时间：%s。"
    SMS_SOS = u"您的定位器“%s”发起的应急救援请求，【移动卫士】平台已收到，地址：%s，时间：%s。"
    SMS_SOS_NOLOC = u"您的定位器“%s”发起的应急救援请求，【移动卫士】平台已收到，地址：因定位信号弱，当前暂时无法定位，请关注定位器状态，时间：%s。"
    SMS_SOS_OWNER = u"您的定位器“%s”发起应急救援请求，已通知%s，地址：%s，时间：%s。"
    SMS_SOS_OWNER_NOLOC = u"您的定位器“%s”发起应急救援请求，已通知%s，地址：因定位信号弱，当前暂时无法定位，请关注定位器状态，时间：%s。"
    SMS_SOS_WHITE = u"您的定位器“%s”发起应急救援请求，当前所在位置：%s，时间：%s。"
    SMS_SOS_WHITE_NOLOC = u"您的定位器“%s”发起应急救援请求，地址：因定位信号弱，当前暂时无法定位，请关注定位器状态，时间：%s。"
    SMS_LOGIN_REMIND = u"尊敬的客户：您于%s通过%s登录【移动卫士】平台，用户号码为%s，所关联的定位器为“%s”。"
    SMS_CHARGE = u"尊敬的客户：您的定位器“%s”当前帐户信息：%s"
    SMS_CHARGE_REMIND = u"尊敬的客户：为了不影响移动卫士业务的正常使用，请您及时为您的移动卫士账号：%s进行充值，如已经缴费或者已经合并账号缴费请不用理会此短信。【移动卫士】"
    SMS_SERVICE_STOP = u"尊敬的客户：您的定位器“%s”已经停止服务。"
    SMS_RETRIEVE_PASSWORD = u"尊敬的客户：您刚才使用了【移动卫士】密码找回功能，新的登录密码为：%s，请妥善保管。如需修改密码，请登录【移动卫士】网站或手机客户端进行修改。" 
    SMS_RESET_PASSWORD = u"尊敬的客户：您的密码刚才被【移动卫士】客服人员进行了重置，新的登录密码为：%s，请妥善保管。如需修改密码，请登录【移动卫士】网站或手机客户端进行修改。" 
    SMS_CAPTCHA = u"尊敬的客户：您【移动卫士】找回密码所需的验证码为：%s，请5分钟内进行修改。若非您本人或授权操作，请联系【移动卫士】客服。" 
    SMS_REG = u"尊敬的客户：您的【移动卫士】验证码为：%s，请5分钟内进行激活。若非您本人或授权操作，请联系【移动卫士】客服。" 
    SMS_IOS_CAPTCHA = u"尊敬的客户：您的【智能班车】业务验证码为：%s，请5分钟内进行激活。若非您本人或授权操作，请联系【智能班车】客服。" 
    SMS_DW_SUCCESS = u"尊敬的客户：您的定位器“%s”%s定位成功，地址：%s，时间：%s。"
    SMS_DW_FAILED = u"尊敬的客户：您的定位器“%s”%s定位失败。"
    SMS_DEFEND_SUCCESS = u"尊敬的客户：您的定位器“%s”%s成功。"

    SMS_ACTIVATE = u"尊敬的客户：您要监控的账号已经被激活。【移动外勤】"
    SMS_JH_SUCCESS = u"尊敬的客户：您的定位器“%s”激活成功，平台网址：%s，用户名：%s，密码：%s"
    SMS_JH_FAILED = u"激活失败，请确认手机号是否正确，或联系【移动卫士】客服。"
    SMS_TERMINAL_HK = u"尊敬的客户：您的定位器“%s”已经换卡，请先激活该号码。"
    SMS_TERMINAL_REGISTER = u"尊敬的客户：您的定位器“%s”的短信接收号设置失败，请重新激活该定位器。"
    SMS_NOT_JH = u"尊敬的客户：您的定位器号码%s未激活，请先激活该号码。"
    SMS_USER_HK_SUCCESS = u"尊敬的客户：已成功更换用户号码，新用户号码：%s，平台网址：%s，用户名：%s，密码：%s"
    SMS_TERMINAL_HK_SUCCESS = u"尊敬的客户：您的定位器“%s”换卡成功，新卡号码：%s"
    SMS_USER_ADD_TERMINAL = u"尊敬的客户：您的帐号已绑定了新的定位器号码%s。请使用原有的用户名和密码登录平台网址：%s 查看。"
    SMS_PSD_WRONG = u"尊敬的客户：您输入的密码错误，请重新确认！"
    SMS_TID_EXIST = u"尊敬的客户：该定位器序列号%s冲突，请联系【移动卫士】客服。"
    SMS_TMOBILE_EXIST = u"尊敬的客户：卡号%s已被使用，请先执行解绑操作。"
    SMS_TID_NOT_EXIST = u"尊敬的客户：该定位器未激活，请执行激活短信指令：‘JH(空格)定位器号码’到定位器号码。例如：JH 13900000000"
    SMS_MOBILE_NOT_WHITELIST = u"尊敬的客户：您的定位器号码%s不是指定移动卫士号码，请联系【移动卫士】客服。"
    SMS_DELETE_TERMINAL = u"尊敬的客户：您的定位器号码%s已经解绑。如非本人操作，请联系【移动卫士】客服。"
    SMS_UNUSUAL_ACTIVATE = u"尊敬的客户：该定位器%s已经被使用，原用户解绑后方可使用。"


    #SMS_DOWNLOAD_REMIND = u"尊敬的客户：请手机登录中山无线城市手机网站 gd.wxcs.cn/zs 进入‘下载’-‘移动卫士’ 下载安装【移动卫士】客户端。"
    SMS_DOWNLOAD_REMIND = u"尊敬的客户：请点击 http://www.ydcws.com/download?category=2 下载安装【移动卫士】客户端。"
    SMS_DOWNLOAD_REMIND = u"尊敬的客户：请点击 http://www.ydcws.com/download?category=2 下载安装【移动卫士】客户端。"
    #SMS_REGISTER_YDWQ = u"尊敬的客户：您将加入贵企业/单位移动卫士位置管理群组中，请点击 http://www.ydcws.com/download?category=4 下载客户端，安装打开客户端后，同意加入请输入验证码 %s，成功加入群组后，您的位置将在贵企业/单位指定时间内上报到后台。 " 
    SMS_REGISTER_YDWQ = u"尊敬的客户：您将加入贵企业/单位移动卫士位置管理群组中，请点击 http://www.ichebao.net/clientdownload?category=2 下载客户端，安装打开客户端后，同意加入请输入激活码%s，成功加入群组后，您的位置将在贵企业/单位指定时间内上报到后台。 " 

    SMS_NEW_OPERATOR = u"尊敬的客户：您已经成为移动卫士集团用户管理员，平台网址：%s，用户名：%s，密码：%s"
    SMS_SERVICE_EXCEPTION_REPORT = u"管理员你好，平台%s，不能检测到模拟终端的位置更新，服务可能发生异常，请检查！！！"
    SMS_EVENTER_QUEUE_REPORT = u"管理员你好，平台%s，检测到EVENTER模块队列长度超过上限，服务可能发生异常，请检查！！！"
    
    SMS_REGION_ENTER = u"尊敬的客户：您的定位器“%s”已进入电子围栏“%s”，地址：%s，时间：%s。"
    SMS_REGION_ENTER_NOLOC = u"尊敬的客户：您的定位器“%s”已进入电子围栏“%s”，地址：因定位信号弱，当前暂时无法定位，请关注定位器状态， 时间：%s。"
    SMS_REGION_OUT = u"尊敬的客户：您的定位器“%s”已离开电子围栏“%s”，地址：%s，时间：%s。"
    SMS_REGION_OUT_NOLOC = u"尊敬的客户：您的定位器“%s”已离开电子围栏“%s”，地址：因定位信号弱，当前暂时无法定位，请关注定位器状态，时间：%s。"
    SMS_REGION_ENTER_NO_ADDRESS = u"尊敬的客户：您的定位器“%s”已进入电子围栏“%s”，时间：%s。"
    SMS_REGION_OUT_NO_ADDRESS = u"尊敬的客户：您的定位器“%s”已离开电子围栏“%s”，时间：%s。"
    
    SMS_RUNTIME_STATUS = u"尊敬的客户：您的定位器“%s”运行状态如下，\n通讯状态：%s，\n运行模式：%s，\n电量：%d%%，\nGSM信号强度：%s，\nGPS信号强度：%s。"

    SMS_NOTIFY = u"尊敬的客户，您的车辆行程已到达%s公里，请及时对车辆“%s”进行保养。若已保养，请登录网页或手机客户端重新设置“下次保养里程”【移动卫士】"
    SMS_NOTIFY_ASSIST = u"定位器:%s，车主号码：%s，车主姓名：%s。该车辆已经到达%s公里，该进行车辆保养。"
