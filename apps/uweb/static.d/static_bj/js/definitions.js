/*
*此文件来用定义URL及静态数据
*/

/* ---------------------- URL --------------------------*/
var TRACK_URL = '/track'; //轨迹
var REALTIME_URL = '/realtime'; //实时
var DEFEND_URL = '/defend'; //设防
var TERMINAL_URL = '/terminal'; //终端设置
var EVENT_URL = '/event'; //报警事件
var PWD_URL = '/password'; //密码修改
var PERSON_URL = '/profile'; //个人信息
var SWITCHCAR_URL = '/switchcar'; //车辆切换
var REMOTE_URL = '/remote'; //远程终端
var TERMINALLIST_URL = '/terminallist'; //终端列表
var LASTINFO_URL = '/lastinfo'; //动态更新当前终端数据
var LOGIN_URL = '/login'; // 登录
var SMS_URL = '/smsoption'; // 短信告警参数
/*常量*/
var CHECK_INTERVAL = 1000; // 每N秒
var CHECK_PERIOD = 60000; // 总共执行的时间
var INFOTIME = 15000; //动态更新的时间
var CURRENT_TIMMER = null; // 定时器对象 
var GPS_TYPE = 0; /*GPS*/ 
var CELLID_TYPE = 1; /*基站*/
var DEFEND_OFF = 0; // 未设防
var DEFEND_ON = 1; // 已设防
var EVENT_NO = 0; // 无报警
var LOCK_ON = 1; // 车被锁定
var LOCK_OFF = 0; // 车未被锁定
var LOGINST = 1; //终端连接到平台
var NUMLNGLAT = 3600000; /*int->lnglat num值*/ 
var WEEKMILISECONDS = 24*60*60*6; // 一个星期的毫秒数
/*
*终端参数的正则
*1: 开启  0: 关闭
*calllock: 1: 呼叫设防撤防  0: 呼叫定位
*/

var ARR_TERMINAL_REG = {
	'speed': {
		'maxLen': 3,
		'regex': '/^(0?\\d{0,2}|100)$/',
		'alertText': '您设置的超速报警速度上限不正确，范围(0-100km/h)！' },
	'freq': {
		'maxLen': 4,
		'regex': '/^((5?|[1-9]{1}\\d{1,2}|[12]{1}\\d{3}|3[0-5]{1}\\d{2})|3600)$/', 
		'alertText': '您设置的上报频率不正确，范围(5-3600秒)！' },
	'vibl':{
		'maxLen': 2,
		'regex': '/^(0?\\d{1}|1?[0-5]{1})$/',
		'alertText': '您设置的车辆震动灵敏度不正确，范围(0-15)！'}, 
	'psw': {
		'maxLen': 6,
		'regex': '/^[a-zA-Z0-9]{6}$/',
		'alertText': '防盗器密码必须为6位字符！'},
	'domain': {
		'maxLen': 64,
		'regex': '/^(((25[0-5])|(2[0-4]\d)|(1\d\d)|([1-9]\d)|\d)(\.((25[0-5])|(2[0-4]\d)|(1\d\d)|([1-9]\d)|\d)){3}|^([a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,6})(:[0-9]{1,4})?$/',
		'alertText': '请设置正确的服务器地址和端口！'},
	'trace': {
		'maxLen': 1,
		'regex': '/^\\d{1}$/',
		'alertText': '设置防盗器的实时上报状态，是否开启追踪状态！',
		'radio': ['开启追踪', '关闭追踪']},
	'pulse': {
		'maxLen': 3,
		'regex': '/^(1|[1-9]{1}\\d{1}|1\\d{2}|2[0-3]{1}\\d{1}|240)$/',
		'alertText': '您设置的终端的心跳时间不正确，范围(1-240秒)！'},
	'phone': {
		'maxLen': 11,											
		'regex': '/^1(3[0-9]|5[012356789]|8[02356789]|47)\\d{8}$/', 
		'alertText': '您设置的防盗器内的SIM卡号码不正确，请输入正确的手机号！'},	
	'owner_mobile': {
		'maxLen': 11,
		'regex': '/^1(3[0-9]|5[012356789]|8[02356789]|47)\\d{8}$/',
		'alertText': '您设置的车主号码不正确，请输入正确的手机号！'},
	'radius': {
		'maxLen': 6,
		'regex': '/^([3-9]{1}\\d{2}|[1-9]{1}\\d{3,4}|100000)$/',
		'alertText': '您设置的GPS告警距离不正确，范围(300-100000)米！'},	
	'vib': {
		'maxLen': 1,
		'regex': '/^\\d{1}$/',
		'alertText': '开启非法移动告警短信！',
		'radio': ['开启非法移动告警', '关闭非法移动告警']},
	'vibl': {
		'maxLen': 2,
		'regex': '/^(0?\\d{1}|1?[0-5]{1})$/',
		'alertText': '您设置非法移动告警的感应灵敏度不正确，范围(0-15)！'},		
	'pof': {
		'maxLen': 1,
		'regex': '/^\\d{1}$/',
		'alertText': '断电和低电告警开关，是否开启！',
		'radio': ['开启低电告警', '关闭低电告警']},
	'lbv': {
		'maxLen': 3,
		'regex': '/^3\.[5-8]{1}$/',
		'alertText': '低电告警开阈值，范围(3.5-3.8)V！'},	
	'sleep': {
		'maxLen': 1,
		'regex': '/^\\d{1}$/',
		'alertText': '开启、关闭节电模式！',
		'radio': ['开启休眠节电模式', '关闭休眠节电模式']},
	'vibgps': {
		'maxLen': 1,
		'regex': '/^\\d{1}$/',
		'alertText': '开启、关闭GPS过滤功能！',
		'radio': ['开启GPS过滤功能', '关闭GPS过滤功能']},		
	'calllock': {
		'maxLen': 1,
		'regex': '/^\\d{1}$/',
		'alertText': '请设置防盗器内卡号的作用！',
		'radio': ['呼叫设防撤防', '呼叫定位']},	
	'calldisp': {
		'maxLen': 1,
		'regex': '/^\\d{1}$/',
		'alertText': '是否需要开通来显功能！',
		'radio': ['开通来电显示', '不开通来电显示']},	
	'vibcall': {
		'maxLen': 1,
		'regex': '/^\\d{1}$/',
		'alertText': '振动呼叫功能！',
		'radio': ['振动呼叫车主', '振动不呼叫车主']},	
	'sms': {
		'maxLen': 1,
		'regex': '/^\\d{1}$/',
		'alertText': '是否需要短信激活！',
		'radio': ['无须激活自动登陆', '防盗器激活才能登陆']},
	'vibchk': {
		'regex': '/^([1-9]{1}|[1-2]{1}\\d{1}|30:[1-9]{1}|[1-2]{1}\\d{1}|30)$/',
		'alertText': '配置在 X 秒时间内产生了Y次震动，才产生震动告警，范围(1:1--30:30)！'},
	'poft': {
		'maxLen': 1,
		'regex': '/^\\d{1}$/',
		'alertText': '单位：秒；默认 0 秒；决定熄火后等待多久开启断电告警功能，范围(0-9秒)！'},
	'wakeupt': {
		'maxLen': 4,
		'regex': '/^(\\d{1}|[1-9]{1}\\d{2}|1([1-3]{1}\\d{2}|4[0-3]\\d{2}|440))$/', 
		'alertText': '单位：分钟；默认 60分钟，决定休眠后多久自动唤醒，范围(0-1440分钟)！'},
	'sleept': {
		'maxLen': 4,
		'regex': '/^(\\d{1}|[1-9]{1}\\d{2}|1([1-3]{1}\\d{2}|4[0-3]\\d{2}|440))$/', 
		'alertText': '单位：分钟；默认 2 分钟；决定断电后多长时间进入休眠；或休眠唤醒后工作多久重新进入休眠，范围(0-1440分钟)！'},
	'acclt': {
		'maxLen': 4,
		'regex': '/^(\\d{1}|[1-9]{1}\\d{2}|1([1-7]{1}\\d{2}|800))$/',
		'alertText': '单位：秒;默认 120 秒；决定熄火后等待多久进入设防，范围(0-1800秒) ！'},
	'acclock': {
		'maxLen': 1,
		'regex': '/^\\d{1}$/',
		'alertText': 'ACC 状态自动设防功能，ACCLOCK=1 表示开启根据 ACC 状态自动设防功能，ACC=0 表示关闭自动设防功能 ！',
		'radio': ['开启自动设防功能', '关闭自动设防功能']},
	'stop_service': {
		'maxLen': 1,
		'regex': '/^\\d{1}$/',
		'alertText': '主动控制终端发起向控制器的注销动作，1 表示终端向控制器发起注销动作，0 表示取消终端向控制器发起的注销动作 ！',
		'radio': ['向控制器发起注销', '取消向控制器发起注销']},
	'cid': {
		'maxLen': 8,
		'regex': '/^([A-F0-9a-f]{8})$/',
		'alertText': '预制控制器序列号功能，CID = AABBCCDD （8 位16进制数据，表示对终端预制控制器序列号），CID=00000000 （表示清除终端本地的控制器序列号） ！'}
}
