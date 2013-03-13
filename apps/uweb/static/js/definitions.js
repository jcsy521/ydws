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
var CORP_LASTINFO_URL = '/lastinfo/corp';
var LOGIN_URL = '/login'; // 登录
var SMS_URL = '/smsoption'; // 短信告警参数
var WAKEUP_URL = '/wakeup'; // 唤醒定位器
var BEGINTRACK_URL = '/tracklq';        // 开启追踪 
var GROUPS_URL = '/group';	// 分组
var GROUPTRANSFER_URL = '/changegroup';	// 组移动
var CORP_URL = '/corp';	// 集团
var CORPPERSON_URL = '/profile/corp';	// 集团资料
var TERMINALCORP_URL = '/terminal/corp';	// 集团终端
var STATICS_URL = '/statistic';	// 告警统计
var CHECKMOBILE_URL = '/checktmobile';	// 终端手机号验证
var CHECKCNAME_URL = '/checkcname';	// 验证集团名
var CORPPWD_URL = '/password/corp';	// 集团密码
/*常量*/
var CHECK_INTERVAL = 10000; // 每N秒
var CHECK_ROUNDNUM = 3; // 经纬度显示小数位截取
var CHECK_PERIOD = 60000; // 总共执行的时间
var INFOTIME = 15000; //动态更新的时间
var CURRENT_TIMMER = null; // 定时器对象 
var GPS_TYPE = 0; /*GPS*/ 
var CELLID_TYPE = 1; /*基站*/
var DEFEND_OFF = 0; // 未设防
var DEFEND_ON = 1; // 已设防
var FOB_ON = 1;	// 挂件在附近
var FOB_OFF = 0;	// 挂件不在附近
var EVENT_NO = 0; // 无报警
var LOCK_ON = 1; // 车被锁定
var LOCK_OFF = 0; // 车未被锁定
var LOGINST = 1; //终端连接到平台
var LOGINOUT = 0; //终端连接到平台
var LOGINWAKEUP = 2; //终端连接到平台
var NUMLNGLAT = 3600000; /*int->lnglat num值*/ 
var WEEKMILISECONDS = 24*60*60*6; // 一个星期的毫秒数
var LASTINFOCACHE = 0;	// 0: 首次访问lastinfo  1: 不是首次访问
var WAITIMG = '...<img src="/static/images/blue-wait.gif" width="12px" />';	// 正在查询中 图标
var BASEIMGURL = '/static/images/';	// 图片的默认路径
var CORPIMGURL = BASEIMGURL + 'corpImages/';	// 集团默认图片路径
var MOBILEREG =  /^(\+86){0,1}1(3[0-9]|5[012356789]|8[02356789]|47)\d{8}$/;	// 手机号正则表达