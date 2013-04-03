/*
*辅助处理相关操作方法
*/

/**
* mapObj: 地图对象
* actionMarker: 轨迹的动态marker 
* currentLastInfo: 动态更新的定时器对象
* str_currentPersonalTid: 上次lastinfo的选中个人用户定位器tid
* arr_infoPoint: 通过动态更新获取到的车辆数据进行轨迹显示
* f_infoWindowStatus: 吹出框是否显示
* obj_localSearch: 周边查询对象 
* wakeupInterval： 唤醒定位器计时器
* obj_polylines： 保存所有的开启追踪轨迹
* obj_actionTrack：保存开启追踪
* obj_selfmarkers：所有车辆的marker对象
*/
var mapObj = null,
	actionMarker = null, 
	viewControl = null,
	currentLastInfo = null,
	arr_infoPoint = [],
	f_infoWindowStatus = true,
	obj_localSearch = null,
	wakeupInterval = null,
	trackInterval  = null,
	str_currentPersonalTid = '',
	obj_polylines = {},
	obj_actionTrack = {},
	obj_selfmarkers = {};
	
	
if ( !window.dlf ) { window.dlf = {}; }

(function () {
/**
* 窗口关闭事件
*/
window.dlf.fn_closeWrapper = function() {
	var obj_close = $('.j_close');
	
	obj_close.click(function() {
		var str_whoDialog = $(this).attr('who');
		
		/* if ( str_whoDialog == 'statics' || str_whoDialog == 'mileage' ) {
			dlf.fn_clearNavStatus('recordCount');
		} else {
		*/
			dlf.fn_clearNavStatus(str_whoDialog);
		//}
		dlf.fn_closeJNotifyMsg('#jNotifyMessage');
		dlf.fn_closeDialog(); // 窗口关闭
	});
}

/**
* 主动关闭窗口
*/
var b_eventSearchStatus = false;

window.dlf.fn_closeDialog = function() {
	var f_eventSearchWpST = $('#eventSearchWrapper').is(':visible'),  //告警窗口是否在打开状态
		b_trackStatus = $('#trackHeader').is(':visible'), // 轨迹是否打开
		b_trackClass = $('#trackHeader').data('trackST'); // 轨迹是否有操作

	b_eventSearchStatus = f_eventSearchWpST;
	if ( f_eventSearchWpST ) {
		if ( b_trackClass ) {
			dlf.fn_closeTrackWindow(false);	// 关闭轨迹查询 不操作lastinfo
			dlf.fn_setMapContainerZIndex(0);
		} else {
			dlf.fn_closeTrackWindow(true);	// 关闭轨迹查询 清除lastinfo
		}
	} else {
		if ( b_trackStatus ) {
			dlf.fn_closeTrackWindow(true);	// 关闭轨迹查询 清除lastinfo
		}
		dlf.fn_unLockScreen(); // 去除页面遮罩
		dlf.fn_unLockContent(); // 清除内容区域的遮罩
	}
	dlf.fn_clearAllMenu();
	$('.wrapper').hide();
}

// 清除所有的menu的操作样式
window.dlf.fn_clearAllMenu = function() {
	$('.menu a').each(function() {
		var obj_this = $(this),
			str_id = obj_this.attr('id');
			
		dlf.fn_clearNavStatus(str_id);
	});
}

/**
* 清除导航功能的选中状态
* str_who: 要清除的导航ID
*/
window.dlf.fn_clearNavStatus = function(str_who) {
	$('#'+ str_who).removeClass(str_who +'Hover'); 
}

window.dlf.fn_setMapContainerZIndex = function(n_num) {
	$('.mapContainer').css('zIndex', n_num);
}
/**
* 处理请求服务器错误
*/
window.dlf.fn_serverError = function(XMLHttpRequest) {
	if ( XMLHttpRequest && XMLHttpRequest.status > 200 ) {
		dlf.fn_jNotifyMessage('请求失败，请重新操作！', 'message', false, 3000);		
		if ( window == window.parent ) {
			window.location.replace('/');
		} else {
			document.jxq_refresh.action = document.referrer;
			document.jxq_refresh.submit();
		}
	}
}

/**
* 页面添加透明遮罩
*/
window.dlf.fn_lockScreen = function(str_body) {
	var n_height = $(window).height(), 
		obj_body = ''; 
		
	if ( !str_body ) {
		obj_body = $('.j_body');
		obj_body.data('layer', true);
	} else {
		obj_body = $('.'+str_body);
	}
	
	$('#maskLayer').addClass('layer').css({
			'display': 'block',
			'height': n_height+'px',
			'width': obj_body.width()+'px'
		});
}

/**
* 去除页面的透明遮罩
*/
window.dlf.fn_unLockScreen = function() {
	$('#maskLayer').removeClass().css({'display': 'none','height': '0px','width': '0px'});
	$('.j_body').removeData('layer');
}

/**
* 添加内容区域的遮罩
* obj_who 要进行内容区域遮罩的内容ID
*/
window.dlf.fn_lockContent = function(obj_who) {
	var obj_offset = obj_who.offset();

	$('#jContentLock').css({
		'display': 'block',
		'height': obj_who.height()+5,
		'left': obj_offset.left,
		'top': obj_offset.top,
		'width': obj_who.width()+5
	});
}

/**
* 移除内容区域的遮罩
*/
window.dlf.fn_unLockContent = function() {
	$('#jContentLock').css('display', 'none');
}

/**
* 转化日期字符串为整数
* dateString格式有两种2011-11-11 20:20:20, 20:20
* 如果直传第二中小时和分钟，则在使用今天日期构造数据
* 返回秒
*/
window.dlf.fn_changeDateStringToNum = function(dateString) {
    var year = '',
        month = '', 
        day = '', 
        hour = '', 
        min = '', 
        seconds = '00', 
        timeArr = '';

	if ( dateString.search('-') != -1 ) {
		var tmpArr = dateString.split(' '), 
            dateArr = tmpArr[0].split('-');

		year = dateArr[0], 
        month = dateArr[1]-1, 
        day = dateArr[2],
		timeArr = tmpArr[1].split(':'), 
        hour = timeArr[0], 
        min = timeArr[1], 
        seconds = timeArr[2];
	} else {
        var date = new Date();
			year = date.getFullYear(),
			month = date.getMonth(),
			day = date.getDate();
        
        month = month < 10 ? '0'+month : month;
        day = day < 10 ? '0'+day : day;
        
        timeArr = dateString.split(':'),
        hour = timeArr[0], 
        min = timeArr[1];
    }
	return new Date(year,month,day,hour,min,seconds).getTime()/1000; // Your timezone!
}

/**
* 将整数时间转换成正常时间
* 如果传入str_isYear不是： 时分秒(sfm)、年月日(ymd)、date  整数时间*1000转换成毫秒
* 返回正常时间
*/
window.dlf.fn_changeNumToDateString = function(myEpoch, str_isYear) {
	var n_myEpoch = '';
	
	if ( str_isYear == 'sfm' ||   str_isYear == 'date' || str_isYear == 'ymd'  ) {
		n_myEpoch = myEpoch;
	} else {
		n_myEpoch = myEpoch*1000;
	}
	var	myDate = new Date(n_myEpoch),
        year = myDate.getFullYear(), 
        month = myDate.getMonth()+1,
	    day = myDate.getDate(), 
        hours = myDate.getHours(), 
        min = myDate.getMinutes(),
	    seconds = myDate.getSeconds();
	
    month = month < 10 ? '0'+month : month;
	day = day < 10 ? '0'+day : day;
	hours = hours < 10 ? '0'+hours : hours;
	min = min < 10 ? '0'+min : min;
	seconds = seconds < 10 ? '0'+seconds : seconds;
	
	if ( str_isYear == 'sfm' ) {
		return hours +':'+ min +':'+ seconds;
	} else if ( str_isYear == 'date' ) {
		return new Date(year, month - 1, day);
	} else if ( str_isYear == 'ymd' ) {
		return year +'-'+ month +'-'+ day;
	} else {
		return year +'-'+ month +'-'+ day +' '+ hours +':'+ min +':'+ seconds;
	}
}

/**
	* 页面显示提示信息,替代alert
	* messages:要显示的消息内容
	* type: error,message
	* f_permanent: 消息是否总显示
	* showTime: 消息显示时间
*/
window.dlf.fn_jNotifyMessage = function(messages, types, f_permanent, showTime) {
	var pf = ($(window).width()-447)/2,
        displayTime = 6000,
        f_perMan_type = f_permanent ? f_permanent : false,
	    displayTime = showTime ? showTime : displayTime;

	$('#jNotifyMessage').css({
		'display': 'block',
        'left': pf
    }).jnotifyAddMessage({
		text: messages,
		permanent: f_perMan_type,
		type: types,
        disappearTime: displayTime
	});
}

/**
* 扩展jnotify的删除方法
* id：调用jnotify的元素id
*/
window.dlf.fn_closeJNotifyMsg = function(id) {
    $(id).hide().children().remove();
}
/**
* 绑定车辆列表的各项
*/
window.dlf.fn_bindCarListItem = function() {
	$('.j_carList .j_terminal').unbind('mousedown').mousedown(function(event) {
		var n_tid = $(this).attr('tid'), 
			obj_currentCar = $(this), 
			str_className = obj_currentCar.attr('class'), 
			n_mouseWhick = event.which;
			
		if (n_mouseWhick == 1 ) {
			if ( str_className.search('j_currentCar') != -1 || str_className.search(JSTREECLICKED) != -1 ) { // 如果用户点击当前车辆不做操作
				return;
			}
			dlf.fn_switchCar(n_tid, obj_currentCar); // 车辆列表切换
		}
	});
}

/**
* 车辆列表的切换方法
* n_tid: 定位器序列号
* obj_currentItem: 当前车辆对象
*/
window.dlf.fn_switchCar = function(n_tid, obj_currentItem) {
	var obj_carA = $('.j_carList a[tid='+n_tid+']');
	
	$.get_(SWITCHCAR_URL + '/' + n_tid, '', function (data) {	// 向后台发送切换请求
		if ( data.status == 0 ) { 
			// 更新当前车辆的详细信息显示
			var	obj_carDatas = $('.j_carList').data('carsData'),
				obj_terminals = $('.j_carList .j_terminal'),
				f_trackSt = $('#trackHeader').is(':visible'), 
				f_eventSearchWpST = $('#eventSearchWrapper ').is(':visible'),
				n_len = obj_terminals.length;

			obj_terminals.removeClass('j_currentCar');	// 其他车辆移除样式
			obj_currentItem.addClass('j_currentCar');	// 当前车添加样式
			
			if ( !dlf.fn_userType() ) {	// 如果是个人用户添加当前车样式
				obj_terminals.removeClass('currentCarCss');	// 其他车辆移除样式
				obj_currentItem.addClass('currentCarCss');	// 当前车添加样式
				
				// 个人用户操作成功保存当前车tid 
				str_currentPersonalTid = n_tid;
				if ( obj_carDatas ) {
					var obj_currentCarData = obj_carDatas[n_tid];
					if ( obj_currentCarData ) {
						dlf.fn_updateTerminalInfo(obj_carDatas[n_tid]);	// 更新车辆信息
						dlf.fn_moveMarker(n_tid);
					}
					if ( f_trackSt || f_eventSearchWpST  ) {	// 如果告警查询,告警统计 ,里程统计 ,轨迹是打开并操作的,不进行数据更新
						return;
					}
				} else {
					if ( f_trackSt || f_eventSearchWpST  ) {	// 如果告警查询,告警统计 ,里程统计 ,轨迹是打开并操作的,不进行数据更新
						return;
					} else {
						dlf.fn_getCarData('first');
					}
				}
			} else {
				obj_terminals.removeClass(JSTREECLICKED);
				obj_currentItem.addClass(JSTREECLICKED);
				
				/* 
				str_checkedNodeId = '#leafNode_' + n_tid;
				$('#corpTree').jstree('check_node', str_checkedNodeId);	  // 单击同时选中定位器
				*/
				str_currentTid = n_tid;
				if ( obj_carDatas ) {
					dlf.fn_updateTerminalInfo(obj_carDatas[n_tid]);	// 更新车辆信息
				}
				dlf.fn_moveMarker(n_tid);
				/*集团用户切换变换轨迹要显示的终端 并清除地图*/
				var str_trackStatus = $('#trackHeader').is(':visible'),  
					str_currentCarAlias = $('.j_currentCar').text().substr(2, 11);
	
				if ( str_trackStatus ) {	
					dlf.fn_clearTrack('inittrack');	// 初始化清除数据;
					$('#trackTerminalAliasLabel').html(str_currentCarAlias);
				}
			}
			dlf.fn_closeJNotifyMsg('#jNotifyMessage');  // 关闭消息提示
			dlf.fn_updateLastInfo();
		} else if ( data.status == 201 ) {	// 业务变更
			dlf.fn_showBusinessTip();
		} else {
			dlf.fn_jNotifyMessage(data.message, 'message'); // 查询状态不正确,错误提示
		}
	}, 
	function (XMLHttpRequest, textStatus, errorThrown) {
		dlf.fn_serverError(XMLHttpRequest);
	});
}

/**
*动态更新定位器相关数据
*/
window.dlf.fn_updateLastInfo = function() {
	dlf.fn_clearInterval(currentLastInfo); // 清除定时器
	currentLastInfo = setInterval(function () { // 每15秒启动
		if ( !dlf.fn_userType() ) {
			dlf.fn_getCarData();
		} else {
			dlf.fn_corpGetCarData();
		}		
	}, INFOTIME);
}

/**
* 每隔15秒获取数据
*/
window.dlf.fn_getCarData = function(str_flag) {
	var str_currentTid = $($('.j_carList a[class*=j_currentCar]')).attr('tid'),	//当前车tid
		obj_carListLi = $('.j_carList li'),
		n_length = obj_carListLi.length, 	//车辆总数
		n_count = 0, 
		arr_tids = [], 
		obj_tids= {'tids': [str_currentTid], 'cache': 0};	//所有车的tid集合、是否是第一次lastinfo
	
	for( var i = 0; i < n_length; i++ ) {	//遍历每辆车获取tid
		var str_tempTid = obj_carListLi.eq(i).children().attr('tid');	
		if ( str_tempTid ) {
			arr_tids[n_count++] = str_tempTid;
		}
	}
	obj_tids.tids = arr_tids;
	$.post_(LASTINFO_URL, JSON.stringify(obj_tids), function (data) {	// 向后台发起lastinfo请求
			if ( data.status == 0 ) {
				var obj_cars = data.cars_info,
					obj_tempData = {},
					arr_locations = [],
					n_pointNum = 0;
				
				if ( !dlf.fn_isEmptyObj(obj_cars) ) {
					return;
				}
				
				// 重新生成终端列表
				fn_createTerminalList(obj_cars);
				for ( var param in obj_cars ) {
					var obj_carInfo = obj_cars[param], 
						str_tid = param,
						n_enClon = obj_carInfo.clongitude,
						n_enClat = obj_carInfo.clatitude,
						n_clon = n_enClon/NUMLNGLAT,	
						n_clat = n_enClat/NUMLNGLAT;
						
					obj_carInfo.tid = str_tid; 
					obj_carInfo.name = '';
					obj_tempData[str_tid] = obj_carInfo;
					
					if ( n_clon != 0 && n_clat != 0 ) {
						n_pointNum ++;
						arr_locations.push({'clongitude': n_enClon, 'clatitude': n_enClat});
						if ( obj_carInfo ) {
							//obj_carA.data('carData', obj_carInfo);
							dlf.fn_updateInfoData(obj_carInfo, str_flag); // 工具箱动态数据
						}
					}
					
					if ( str_currentTid == str_tid ) {	// 更新当前车辆信息
						dlf.fn_updateTerminalInfo(obj_carInfo);
					}
				}
				if ( str_flag == 'first' && arr_locations.length > 0 ) {
					dlf.fn_caculateBox(arr_locations);
				}
				$('.j_carList').data('carsData', obj_tempData);
				// 如果无终端或终端都无位置  地图设置为全国地图
				if ( n_pointNum <= 0 ) {
					mapObj.setZoom(5);
				}
			} else if ( data.status == 201 ) {	// 业务变更
				dlf.fn_showBusinessTip();
			} else {
				dlf.fn_jNotifyMessage(data.message, 'message'); // 查询状态不正确,错误提示
			}
		}, 
		function (XMLHttpRequest, textStatus, errorThrown) {
			dlf.fn_serverError(XMLHttpRequest);
		});
}

/**
* lastinfo第一次 计算最大点和最小点 让所有点放在一个盒子中
* arr_locations: 所有点数组
*/
window.dlf.fn_caculateBox = function (arr_locations) {
	n_tempMax = 0;
	obj_tempMaxPoint = arr_locations[0];
	obj_tempFirstPoint = arr_locations[0];
	
	var	n_locLength = arr_locations.length;
	
	for (var i = 0; i < n_locLength; i++) {
		var obj_currentLoc = arr_locations[i], 
			obj_firstPoint = dlf.fn_createMapPoint(obj_currentLoc.clongitude, obj_currentLoc.clatitude);
			
		for ( var j = i + 1; j < n_locLength; j++ ) {
			var obj_itemLoc = arr_locations[j], 
				obj_tempPoint = dlf.fn_createMapPoint(obj_itemLoc.clongitude, obj_itemLoc.clatitude);
				
			dlf.fn_tempDist(obj_firstPoint, obj_tempPoint); // 计算与第一个点距离
		}
	}
	if ( n_tempMax <= 0 ) {
		dlf.fn_setOptionsByType('centerAndZoom', dlf.fn_createMapPoint(obj_tempFirstPoint.clongitude, obj_tempFirstPoint.clatitude), 18);
	} else {
		dlf.fn_setOptionsByType('viewport', [obj_tempFirstPoint, obj_tempMaxPoint]);
	}
}


/**
* 对定位器的最新数据进行页面填充
* obj_carInfo: 车辆的信息
* type: 是否是实时定位
*/
window.dlf.fn_updateTerminalInfo = function (obj_carInfo, type) {
	var str_tmobile = obj_carInfo.mobile,
		n_defendStatus = obj_carInfo.mannual_status, 
		str_dStatus = n_defendStatus == DEFEND_ON ? '已设防' : '未设防', 
		str_dStatusTitle =  n_defendStatus == DEFEND_ON ? '设防状态：已设防' : '设防状态：未设防',
		str_dImg= n_defendStatus == DEFEND_ON ? 'defend_status1.png' : 'defend_status0.png',
		str_type = obj_carInfo.type == GPS_TYPE ? 'GPS定位' : '基站定位',
		str_speed = obj_carInfo.speed + ' km/h',
		n_degree = obj_carInfo.degree,
		str_degree = dlf.fn_changeData('degree', n_degree), //方向角处理
		str_degreeTip = '方向角：' + Math.round(n_degree),
		str_eStatus = dlf.fn_eventText(obj_carInfo.event_status),  // 报警状态
		str_address = '',	// 位置描述		
		str_time = obj_carInfo.timestamp > 0 ? dlf.fn_changeNumToDateString(obj_carInfo.timestamp) : '-',
		n_clon = obj_carInfo.clongitude/NUMLNGLAT,	
		str_clon = '',
		n_clat = obj_carInfo.clatitude/NUMLNGLAT,
		str_clat = '';	// 经纬度
		
	if ( n_clat == 0 || n_clon == 0 ) {	// 经纬度为0 不显示位置信息
		str_address = '-';
		str_degree = '-';
		str_type = '-';
		str_clon += '-';
		str_clat += '-';
		str_speed = '-';
	} else {
		str_address = $('.j_carList a[tid='+ obj_carInfo.tid +']').data('address');
		str_clon += 'E ' + n_clon.toFixed(CHECK_ROUNDNUM);
		str_clat += 'N ' + n_clat.toFixed(CHECK_ROUNDNUM);
	}
	if ( !type ) {	// lastinfo: 更新车辆信息和定位器信息  realtime: 只更新位置信息
		var n_power = parseInt(obj_carInfo.pbat),
			str_power =  n_power + '%',	// 电池电量 0-100
			str_pImg = dlf.fn_changeData('power', n_power), // 电量图标
			n_gsm = obj_carInfo.gsm,	// gsm 值
			str_gsm = dlf.fn_changeData('gsm', n_gsm),	// gsm信号
			n_gps = obj_carInfo.gps,	// gps 值
			str_gps = dlf.fn_changeData('gps', n_gps);	// gps信号
			
		$('#powerContent').html(str_power);// 电池电量填充
		$('#gsmContent').html(str_gsm);	// gsm 
		$('#gpsContent').html(str_gps);	// gps
		$('#defendContent').html(str_dStatus).data('defend', n_defendStatus);	// defend status
		$('#defendStatus').css('background-image', 'url("' + dlf.fn_getImgUrl() + str_dImg + '")');	//.attr('title', str_dStatusTitle);
		//$('#tmobile').attr('title', '定位器号码：' + str_tmobile );	// 定位器手机号
		$('#tmobileContent').html(str_tmobile);
	}
	//$('.j_updateTime').attr('title', str_time)
	$('#locationTime').html(str_time); // 最后一次定位时间
	$('#address').html(str_address); // 最后一次定们地址
	$('#degree').html(str_degree);	// .attr('title', str_degreeTip);
	$('#type').html(str_type); // 车辆定位类型
	$('#lng').html(str_clon); // 车辆经度
	$('#lat').html(str_clat);	// 车辆纬度
	$('#speed').html(str_speed); // 定位器最后一次定位速度
}
/*
* 重新生成终端列表
* obj_carDatas: 终端数据
*/
function fn_createTerminalList(obj_carDatas) {
	var str_carListHtml = '', 
		obj_carListUl = $('.j_carList'), 
		obj_tempSelfMarker = {};
	
	for(var param in obj_carDatas) {
		var obj_carInfo = obj_carDatas[param], 
			str_tid = param, // 终端 tid
			str_loginStatus = obj_carInfo.login, //终端状态
			str_alias = obj_carInfo.alias, // 终端车牌号
			str_carLoginClass = 'carlogin ', 
			str_carLoginImg = 'car1',
			str_carLoginColor = 'green',
			str_carLoginText = '在线', 
			str_carClass = 'j_terminal', 
			obj_currentSelfMarker = obj_selfmarkers[str_tid];
		
		if ( str_loginStatus == LOGINOUT ) { // 终端离线
			str_carLoginClass = 'carlogout ';
			str_carLoginImg = 'carout1';
			str_carLoginColor = 'gray',
			str_carLoginText = '离线';
		}
		if ( str_currentPersonalTid == str_tid ) { // 如果是当前终端
			str_carClass = ' j_currentCar currentCarCss ' + str_carClass;
		} 
		str_carListHtml += '<li>'
						+'<a clogin="'+ str_loginStatus +'" tid="'+ str_tid +'" class="'+ str_carLoginClass +str_carClass +'" title="'+ str_alias +'" href="#"><img src="/static/images/'+ str_carLoginImg +'.png"></a>'
						+'<div class="'+ str_carLoginColor +'" title="'+ str_alias +'">'+ str_alias +'</div>'
						+'<div class="'+ str_carLoginColor +'">('+ str_carLoginText +')</div></li>';
						
						
		if ( obj_currentSelfMarker ) {
			obj_tempSelfMarker[str_tid] = obj_currentSelfMarker; 
			obj_selfmarkers[str_tid] = undefined;
		}
		dlf.fn_checkTrackDatas(str_tid);
	}
	
	obj_carListUl.html(str_carListHtml); // 将新生成的终端列表进行填充到页面上
	
	// 将不使用的终端的marker信息并从地图上清除
	for ( var param in  obj_selfmarkers ) {
		var str_tempTSelfMarker = obj_selfmarkers[param];
		
		if ( str_tempTSelfMarker ) {
			dlf.fn_clearMapComponent(str_tempTSelfMarker);
			if ( param == str_currentPersonalTid ) { // 如果当前车被 删除 
				var obj_tempCurrentCar = $('#carList a ').eq(0),
					str_tempTid = obj_tempCurrentCar.attr('tid');
					
				dlf.fn_switchCar(str_tempTid, obj_tempCurrentCar); // 车辆列表切换
			}
		}
	}
	obj_selfmarkers = obj_tempSelfMarker;
	dlf.fn_bindCarListItem(); //绑定终端 点击事件
}
/*
* 追踪效果的数据存储判断
*/
window.dlf.fn_checkTrackDatas = function (str_tid) {
	var obj_tempTrack = obj_actionTrack[str_tid];

	if ( !obj_tempTrack ) {
		obj_actionTrack[str_tid] = {'status': '', 'interval': ''}
	}
}
/** 
* 转换GPS,GSM,power,degree 为相应的值
* str_key: gsm、gps、power、degree
* str_val: 对应的值
*/
window.dlf.fn_changeData = function(str_key, str_val) {
	var str_return = '';
	
	if ( str_key == 'gsm' ) { // gsm 
		var str_gsmImg = '',
			obj_gsm = $('#gsm');
			
		if ( str_val >= 0 && str_val < 3 ) {
			str_return = '弱';
			str_gsmImg = 'gsm1.png';
		} else if ( str_val >= 3 && str_val < 6 ) {
			str_return = '较弱';
			str_gsmImg = 'gsm2.png';
		} else {
			str_return = '强';
			str_gsmImg = 'gsm3.png';
		}
		if ( obj_gsm ) {
			obj_gsm.css('background-image', 'url("'+ BASEIMGURL + str_gsmImg +'")').attr('title', 'GSM 信号强度：' + str_val);;
		}
	} else if ( str_key == 'gps' ) {	// gps 
		var str_gpsImg = '',
			obj_gps = $('#gps'),
			str_imgUrl = ''
			
		if ( str_val >= 0 && str_val < 10 ) {
			str_return = '弱';
			str_gpsImg = 'gps0.png';
		} else if ( str_val >= 10 && str_val < 20 ) {
			str_return = '较弱';
			str_gpsImg = 'gps1.png';
		} else if ( str_val >= 20 && str_val < 30 ) {
			str_return = '较强';
			str_gpsImg = 'gps2.png';
		} else if ( str_val >= 30 ) {
			str_return = '强';
			str_gpsImg = 'gps3.png';
		}
		str_imgUrl = dlf.fn_getImgUrl() + str_gpsImg;
		if ( obj_gps ) {
			obj_gps.css('background-image', 'url("'+ str_imgUrl +'")').attr('title', 'GPS信号：' + str_val);
		}
	} else if ( str_key == 'power' ) {	// 电池电量
		var arr_powers = [0,10,20,30,40,50,60,70,80,90,100],
			arr_img = ['power0.png','power1.png','power2.png','power3.png','power4.png','power5.png','power6.png','power7.png','power8.png','power9.png','power10.png'];
			
		for ( var i = 0; i < arr_powers.length; i++ ) {
			if ( str_val >= 0 && str_val <= 10 ) {
				str_return = 'power0.png';
				break;
			} else if ( str_val == 100 ) {
				str_return = 'power10.png';
				break;
			} else if ( str_val > arr_powers[i] && str_val <= arr_powers[i+1] ) {
				str_return = arr_img[i];
				break;
			}
		}
		$('#power').css('background-image', 'url("'+ BASEIMGURL + str_return +'")');	//.attr('title', '剩余电量：' + str_val + '%' );
	} else if ( str_key == 'degree' ) {	// 方向角
		var arr_degree = [355,5,40,50,85,95,130,140,175,185,220,230,265,275,310,320,355],
			arr_desc  = ['正北','北偏东','东北','东偏北','正东','东偏南','东南','南偏东','正南','南偏西','西南','西偏南','正西','西偏北','西北','北偏西','正北'];
			
		for ( var i = 0; i < arr_degree.length; i++ ) {
			if ( str_val >= 355 || str_val <= 5 ) {
				str_return = '正北';
				break;
			} else if ( str_val >= arr_degree[i] && str_val <= arr_degree[i+1] ) {
				str_return = arr_desc[i];
				break;
			}	
		}
	}
	return str_return;
}

window.dlf.fn_getImgUrl = function() {
	if ( dlf.fn_userType() ) {
		return CORPIMGURL;
	} else {
		return BASEIMGURL;
	}
}

/**
* 查找相应tid下的数据
* str_tid: 定位器序列号
*/
window.dlf.fn_checkCarVal = function(str_tid) {
	var len = arr_infoPoint.length;
	for ( var i = 0; i < len; i++ ) {
		var str_tempKey = arr_infoPoint[i].key;
		if ( str_tempKey == str_tid ) {
			arr_infoPoint[i].cNum = i;
			return arr_infoPoint[i];
		}
	}
	return null;
}

/**
* 清除定时器
*/
window.dlf.fn_clearInterval = function(obj_interval) {
	if ( obj_interval ) {
		clearInterval(obj_interval); 
	}
}

/**
* 方向角处理
* n_degree: 方向角度
*/
window.dlf.fn_processDegree = function(n_degree) {
	var n_roundDegree = Math.round(n_degree/10);
	
	return n_roundDegree != 0 ? n_roundDegree : 36;
}

/**
* 判断object对象是否有属性
*/
window.dlf.fn_isEmptyObj = function (obj){
    return ((function(){for(var k in obj)return k})()!=null?true:false)
}
/**
* 判断object对象有数据属性的个数
*/
window.dlf.fn_getObjNums = function (obj){
	var n_nums = 0;
	for(var k in obj) {
		if ( obj[k] ) {
			n_nums ++;
		}
	}
	return n_nums;
}

/**
* 根据相应的报警状态码显示相应的报警提示
*/
window.dlf.fn_eventText = function(n_eventNum) {
	var str_text = '无法获取';
	
	switch (n_eventNum) {
		case 2:
			str_text = '电量告警';
			break;
		case 3:
			str_text = '震动';
			break;
		case 4:
			str_text = '移动';
			break;
		case 5:
			str_text = 'SOS';
			break;
		case 6:
			str_text = '通讯异常';
			break;
	}
	return str_text;
}

/**
*修改元素的mouseover mouseout  css样式 
* obj_who: 要进行设置的标签
* arr_png: 要更改的图片的名称
* str_cursor: 要修改的鼠标指针状态
* 根据typeof来判断用户所传的参数进行相应操作
*/
window.dlf.fn_setItemMouseStatus = function(obj_who, str_cursor, arr_png) {
	var obj_type = typeof(arr_png);
	if ( obj_type == 'string' ) {
		obj_who.css({
			'cursor': str_cursor, 
			'background-image': 'url("/static/images/'+arr_png+'.png")'
		}).unbind('mouseover mouseout');
	} else {
		obj_who.css({
			'cursor': str_cursor, 
			'background-image': 'url("/static/images/'+arr_png[0]+'.png")'
		}).mouseover(function(event) {
			$(this).css('background-image', 'url("/static/images/'+arr_png[1]+'.png")');
		}).mouseout(function(event){
			$(this).css('background-image', 'url("/static/images/'+arr_png[0]+'.png")');
		});
	}
}

/**
* 定位器开启追踪倒计时初始化 
*/
window.dlf.fn_clearRealtimeTrack = function(str_tid) { 
	$('#trackTimer').html('0');
	$('#trackWrapper').hide();
	if ( str_tid ) { 
		var obj_carTrackInterval = obj_actionTrack[str_tid].interval;
		
		dlf.fn_clearInterval(obj_carTrackInterval);
	} else { 
		$('.j_carList a').each(function(e){
			var obj_tempActionTrack = obj_actionTrack[str_tid];
			
			if ( obj_tempActionTrack ) {
				var str_tempTid = $(this).attr('tid');
				
				dlf.fn_clearInterval(obj_tempActionTrack.interval);
				obj_actionTrack[str_tempTid].status = 'yes';
			}
		});
	}
}

/**
* 向后台发送开始跟踪请求，前台倒计时5分钟，5分钟后自动取消跟踪
*/
window.dlf.fn_openTrack = function(str_tid, selfItem) {
	// 向后台发送开启追踪请求
	var obj_param = {'interval': 10};
	
	$.post_(BEGINTRACK_URL, JSON.stringify(obj_param), function(data) {
		if ( data.status == 0 ) {
			var obj_trackMsg = $('#trackMsg'),
				obj_trackWrapper = $('#trackWrapper'),	// 定位器唤醒提示容器
				obj_trackTimer = $('#trackTimer'),	// 定位器提示框计时器容器
				n_timer = parseInt(obj_trackTimer.html()),
				n_left = ($(window).width()-400)/2, 
				str_terminalAlias = '',
				f_userType = dlf.fn_userType();
				
			// 关闭jNotityMessage,dialog
			dlf.fn_closeJNotifyMsg('#jNotifyMessage'); 
			dlf.fn_closeDialog();
			if ( f_userType ) { //根据角色不同取不同位置的终端别名
				str_terminalAlias = $('.leat_'+ str_tid).text();
			} else {
				str_terminalAlias = $('#carList a[tid='+ str_tid +']').next().text();
			}
			/**
			* 10分钟
			*/
			obj_trackMsg.html('定位器：'+ str_terminalAlias +' 已开启追踪，10分钟后将自动取消追踪。');
			obj_trackWrapper.css('left', n_left + 'px').show();
			setTimeout(function() {
				obj_trackWrapper.hide();
			}, 4000);
			trackInterval = setInterval(function() {
				if ( n_timer > 600 ) {
					dlf.fn_clearInterval(obj_actionTrack[str_tid].interval);
					obj_trackWrapper.show();
					obj_trackMsg.html('定位器：'+ str_terminalAlias +'，追踪时间已到，将取消追踪。');
					setTimeout(function() { 
						dlf.setTrack(str_tid, selfItem);
					}, 3000);
				}
				n_timer++;
			}, 1000);
			obj_actionTrack[str_tid].interval = trackInterval;
		} else {
			dlf.setTrack(str_tid, selfItem);
			dlf.fn_jNotifyMessage(data.message, 'message', false, 4000);
		}
	});
}
/*
* 通过tid取得当前tid的actiontrack状态
*/      
window.dlf.fn_getActionTrackStatus = function(str_tid) {
	var obj_tempActionTrack = obj_actionTrack[str_tid];
	
	if ( obj_tempActionTrack ) {
		return 	obj_tempActionTrack.status;
	} else {
		return 'no';
	}
}
/**
* 业务变更提示 
* str_type: event
*/
window.dlf.fn_showBusinessTip = function(str_type) {
	dlf.fn_clearInterval(currentLastInfo); // 清除lastinfo定时器
	dlf.fn_closeJNotifyMsg('#jNotifyMessage'); // 关闭消息提示
	if ( !str_type ) {
		dlf.fn_closeDialog(); // 窗口关闭 去除遮罩
	}
	// 遮罩
	dlf.fn_lockScreen(); 
	dlf.fn_dialogPosition('business');
	$('#businessBtn').click(function() {
		window.location.replace('/logout');
	});
}

/**
* 文本框获得焦点事件
*/
window.dlf.fn_onInputBlur = function() {
	$('.j_onInputBlur').unbind('blur').bind('blur', function() {
		var $this = $(this),
			obj_wrapper = $('#' + $this.attr('parent')),
			str_status = obj_wrapper.is(':hidden'),
			str_val = $this.val(),
			str_msg = $this.attr('msg'),
			n_maxLength = $this.attr('max'),
			str_who = $this.attr('who'),
			n_valLength = str_val.length;
			
		$this.removeClass('bListR_text_mouseFocus');
		
		/*if ( str_who == 'mobile' ) {
			if ( str_val == '' ) {
				$this.val('请输入手机号').css({'color': '#888'});
			}
		}*/		
		if ( str_status ) {
			dlf.fn_closeJNotifyMsg('#jNotifyMessage');
		} else {
			switch (str_who) {
				case  'validateLength':
					if ( n_valLength > n_maxLength ) {	// 验证长度
						dlf.fn_jNotifyMessage(str_msg, 'message', false, 4000);
					} else {
						dlf.fn_closeJNotifyMsg('#jNotifyMessage');
					}
					break;
				case 'mobile':
					var str_whitelist1 = $('#t_white_list_1').val(),	// 车主号码
						str_msg = '';
					
					if ( n_valLength == 0 ) {	// 手机号验证长度
						str_msg = '';
					} else if ( n_valLength > 14 || n_valLength < 11 ) {
						str_msg = '您设置的SOS联系人号码不合法，请重新输入！'
					} else {
						if ( !MOBILEREG.test(str_val) ) {	// 手机号合法性验证
							str_msg = '您设置的SOS联系人号码不合法，请重新输入！';
						}
					}
					if ( str_msg != '' ) {
						dlf.fn_jNotifyMessage(str_msg, 'message', false, 4000);
					} else {
						dlf.fn_closeJNotifyMsg('#jNotifyMessage');
					}
					break;
				case 'name':
					var reg =  /^[a-zA-Z0-9_\u4e00-\u9fa5 ]+$/,
						str_msg = '';
						
					if ( n_valLength > n_maxLength ) {	// 车主姓名验证长度
						str_msg = '车主姓名最大长度是20个汉字或字符！'
					} else {
						if ( !reg.test(str_val) ) {
							str_msg = '车主姓名只能是由数字、英文、下划线或中文组成！';
						}
					}
					if ( str_msg != '' ) {
						dlf.fn_jNotifyMessage(str_msg, 'message', false, 4000);
					} else {
						dlf.fn_closeJNotifyMsg('#jNotifyMessage');
					}
					break;
				case 'cMobile': 
					var str_msg = '';
					
					if ( n_valLength > 14 || n_valLength < 11 ) {
						str_msg = '定位器手机号输入不合法，请重新输入！'
					} else {
						if ( !MOBILEREG.test(str_val) ) {	// 手机号合法性验证
							str_msg = '定位器手机号输入不合法，请重新输入';
						}
					}
					if ( str_msg != '' ) {
						dlf.fn_jNotifyMessage(str_msg, 'message', false, 4000);
					} else {
						if ( $this.attr('id') == 'c_tmobile' ) {
							dlf.fn_checkTMobile(str_val);
						}
						dlf.fn_closeJNotifyMsg('#jNotifyMessage');
					}
					break;
				case 'uMobile': 
					var str_msg = '';
					
					if ( n_valLength > 0 ) {
						if ( n_valLength > 14 || n_valLength < 11 ) {
							str_msg = '短信接收号码输入不合法，请重新输入！'
						} else {
							if ( !MOBILEREG.test(str_val) ) {	// 手机号合法性验证
								str_msg = '短信接收号码输入不合法，请重新输入！';
							}
						}
						if ( str_msg != '' ) {
							dlf.fn_jNotifyMessage(str_msg, 'message', false, 4000);
						} else {
							dlf.fn_closeJNotifyMsg('#jNotifyMessage');
						}
					}
					break;
				case 'operatorMobile': // 操作员手机号验证
					var str_msg = '', 
						str_oldOperatorMobile = $(this).data('oldmobile');
					
					if ( str_oldOperatorMobile && str_oldOperatorMobile == str_val ) {
						$('#hidOperatorMobile').val('');
						return; // 如果操作员手机号编辑时没有修改
					}
					if ( n_valLength > 14 || n_valLength < 11 ) {
						str_msg = '操作员手机号输入不合法，请重新输入！'
					} else {
						if ( !MOBILEREG.test(str_val) ) {	// 手机号合法性验证
							str_msg = '操作员手机号输入不合法，请重新输入';
						}
					}
					if ( str_msg != '' ) {
						dlf.fn_jNotifyMessage(str_msg, 'message', false, 4000);
					} else {
						if ( $this.attr('id') == 'txt_operatorMobile' ) {
							dlf.fn_checkOperatorMobile(str_val);
						}
						dlf.fn_closeJNotifyMsg('#jNotifyMessage');
					}
					break;
			}
		}
 	});
 }
 
/**
* dialog弹出框的位置计算并显示
* str_wrapperId: 弹出框对象的ID
*/ 
dlf.fn_dialogPosition = function ( str_wrapperId ) {
	var obj_wrapper = $('#'+ str_wrapperId+'Wrapper'), 
		n_wrapperWidth = obj_wrapper.width(),
		n_width = ($(window).width() - n_wrapperWidth)/2;

	dlf.fn_closeDialog();	// 关闭所有dialog
	$('#'+ str_wrapperId).addClass(str_wrapperId +'Hover');
	dlf.fn_clearNavStatus('home');	// 移除菜单车辆位置的样式
	
	if ( str_wrapperId == 'eventSearch' ) {
		dlf.fn_setMapPosition(true);	// 如果打开的是告警查询  设置地图位置
	} else {
		if ( str_wrapperId != 'mileage' && str_wrapperId != 'operator' ) {
			dlf.fn_showOrHideMap(true);
			if ( b_eventSearchStatus ) {	// 如果选择的非告警查询 并且告警查询打开着  则初始化地图
				dlf.fn_setMapPosition(false);
				b_eventSearchStatus = false;
			}
			dlf.fn_clearNavStatus('eventSearch'); // 移除告警导航操作中的样式
			obj_wrapper.css({left: n_width});
		} else {
			// 隐藏地图
			dlf.fn_showOrHideMap(false);
		}
		dlf.fn_setMapContainerZIndex(0);	// 除告警外的其余操作都设置地图zIndex：0
	}
	obj_wrapper.show();
}

/**
* 设置地图的显示状态
* b_flag: true: 显示  false: 隐藏
*/
window.dlf.fn_showOrHideMap = function(b_flag) {
	var obj_map = $('#mapObj'),
		b_mapStatus = obj_map.is(':hidden'),
		str_display  = 'none';
	
	if ( b_flag ) {
		str_display = 'inline-block';
	}
	obj_map.css('display', str_display);
}

/**
* 判断是个人用户还是集团用户
*/
window.dlf.fn_userType = function() {
	var str_flag = $('.j_body').attr('userType');
	
	if ( str_flag == USER_PERSON ) { // 个人用户
		return false;
	}
	return true;
}

/**
*POST方法的整合 defend
*url: 要请求的URL地址
*obj_data: 需要向后台发送的数据
*str_who: 发起此次操作的源头
*str_msg: 发送中的消息提示
*/
window.dlf.fn_jsonPost = function(url, obj_data, str_who, str_msg) {
	var obj_cWrapper = $('#'+str_who+'Wrapper'), 
		obj_content = $('.'+str_who+'Content'), 
		f_closeWrapper = true;
		
	dlf.fn_jNotifyMessage(str_msg + WAITIMG, 'message', true);
	if ( obj_content.length > 0 ) {
		dlf.fn_lockContent(obj_content); // 添加内容区域的遮罩	
	}
	
	$.post_(url, JSON.stringify(obj_data), function (data) {
		var f_warpperStatus = !obj_cWrapper.is(':hidden');
		
		if ( f_warpperStatus ) { // 如果查到结束后,用户关闭的窗口,不进行后续操作
			if ( data.status == 0 ) {
				if ( str_who == 'defend' || str_who == 'batchDefend' ) {	// 如果是设防撤防操作					
					dlf.fn_jNotifyMessage(str_successMsg, 'message', false, 3000);
					var arr_tids = obj_data.tids.split(','),
						n_length = arr_tids.length,
						obj_carList = $('.j_carList'),
						obj_carsData = obj_carList.data('carsData'),
						obj_currentCar = $('.j_currentCar'),
						str_tid = obj_currentCar.attr('tid'),
						n_status = obj_data.mannual_status,
						str_defendMsg = n_status == 1 ? '已设防' : '未设防',
						str_poDefendMsg = n_status == 0 ? '已设防' : '未设防',
						arr_datas = data.res;
					
					if ( n_length > 0 ) {	// 批量设防撤防
						for ( var i in arr_tids ) {
							var str_tempTid = arr_tids[i];
							
							obj_carsData[str_tempTid].mannual_status = n_status;
							if ( str_tid == str_tempTid ) {	// 如果批量中有当前定位器
								// todo 如果是集团用户 1、修改cardata里的数据  2、批量设防撤防如果有当前定位器要修改页面状态
								var str_defendStatus = parseInt(n_status),
									str_html = '',
									str_dImg = '',
									str_successMsg = '',
									n_defendStatus = 0,
									str_imgUrl = '';
								if ( str_defendStatus == DEFEND_OFF ) { 
									n_defendStatus = 0;
									str_html = '未设防';
									str_successMsg = '撤防成功';
									str_dImg=  'defend_status0.png';			
								} else {
									n_defendStatus = 1;
									str_html = '已设防';
									str_successMsg = '设防成功';
									str_dImg= 'defend_status1.png';	
								}
								$('#defendContent').html(str_html).data('defend', n_defendStatus);
								$('#defendStatus').css('background-image', 'url("'+ dlf.fn_getImgUrl() + str_dImg + '")');	//.attr('title', str_html);
							}
						}
						if ( str_who == 'batchDefend' ) {	// 如果是批量设防撤防
							for ( var x = 0; x < arr_datas.length; x++ ) {
								var obj_result = arr_datas[x],
									n_resultStatus = obj_result.status,
									str_resTid = obj_result.tid,
									obj_updateStatusTd = $('.batchDefendTable tbody td[tid='+ str_resTid +']'),
									str_msg = '',
									obj_updateDefendTd = obj_updateStatusTd.prev();
								
								if ( n_resultStatus == 0 ) {
									obj_updateStatusTd.html('操作成功').addClass('fileStatus4');
									obj_updateDefendTd.html(str_defendMsg);
								} else {
									obj_updateStatusTd.html('操作失败').addClass('fileStatus3');
									obj_updateDefendTd.html(str_poDefendMsg);
								}
							}
						}				
						obj_carList.data('carData', obj_carsData);
						dlf.fn_clearNavStatus('defend');
						$('.j_batchDefend').removeClass('operationBtn').addClass('btn_delete').attr('disabled', true);	// 批量按钮变成灰色并且不可用
						dlf.fn_closeJNotifyMsg('#jNotifyMessage');  // 关闭消息提示
					}
				} else if ( str_who == 'cTerminal' ) {	// 新增定位器
					// todo 添加节点到对应group上    或者重新加载lastinfo
					$('#corpTree').jstree("create", $('#group_'+ obj_data.group_id), 'first', obj_data.tmobile); 
					dlf.fn_closeDialog(); // 窗口关闭 去除遮罩
					dlf.fn_corpGetCarData();
					str_currentTid = obj_data.tmobile;
					b_createTerminal = true;	// 标记 是新增定位器操作 以便switchcar到新增车辆
					dlf.fn_jNotifyMessage(data.message, 'message', false, 3000);
				} else if ( str_who == 'operator' ) {
					var obj_header = $('#operatorTableHeader'), 
						n_operatorId = data.id ,
						str_name = obj_data.name, 
						str_mobile = obj_data.mobile,
						str_address = obj_data.address, 
						str_email = obj_data.email, 
						str_groupId = obj_data.group_id,
						str_groupName = obj_data.group_name;
					
					obj_header.after('<tr id='+ n_operatorId +'>' +
										'<td groupId ='+ str_groupId +'>'+ str_groupName +'</td>'+
										'<td>' + str_name + '</td>' + 
										'<td>' + str_mobile + '</td>' + 
										'<td>' + str_address + '</td>' + 
										'<td>' + str_email + '</td>' + 
										'<td><a href="#" onclick=dlf.fn_editOperator('+ n_operatorId +')>编辑</a></td>' +
										'<td><a href="#" onclick=dlf.fn_deleteOperator('+ n_operatorId +')>删除</a></td>' +
										'</tr>'); 
					
					$('#addOperatorDialog').dialog("close");	// 关闭dialog
					dlf.fn_jNotifyMessage(data.message, 'message', false, 3000); 
					f_closeWrapper = false; //操作员管理不关闭弹出框 
				} else {
					dlf.fn_jNotifyMessage(data.message, 'message', false, 3000); 
				}
				if ( f_closeWrapper ) {
					dlf.fn_closeDialog(); // 窗口关闭 去除遮罩
					$('#exitWrapper').hide();	// 退出dialog隐藏
				}
			} else if ( data.status == 201 ) {	// 业务变更
				dlf.fn_showBusinessTip();
			} else {
				dlf.fn_jNotifyMessage(data.message, 'message', false, 5000);
			}
		}
		dlf.fn_unLockContent(); // 清除内容区域的遮罩
	}, 
	function(XMLHttpRequest, textStatus, errorThrown) {
		dlf.fn_serverError(XMLHttpRequest);
	});
}

/**
*PUT方法的整合 personal,pwd,terminal
*url: 要请求的URL地址
*obj_data: 需要向后台发送的数据
*str_who: 发起此次操作的源头
*msg: 发送中的消息提示
*str_tid: 集团用户的右键菜单参数设置
*/
window.dlf.fn_jsonPut = function(url, obj_data, str_who, str_msg, str_tid) {
	var obj_cWrapper = $('#'+str_who+'Wrapper'), 
		obj_content = $('.'+str_who+'Content');
	
	if ( str_who != 'whitelistPop' ) {
		dlf.fn_jNotifyMessage(str_msg + WAITIMG, 'message', true);
		if ( obj_content.length > 0 ) {
			dlf.fn_lockContent(obj_content); // 添加内容区域的遮罩	
		}
	}
	$.put_(url, JSON.stringify(obj_data), function (data) {
		var f_warpperStatus = !obj_cWrapper.is(':hidden');
		if ( f_warpperStatus ) { // 如果查到结束后,用户关闭的窗口,不进行后续操作
			if ( data.status == 0 ) {
				if ( str_who == 'personal') {	// 个人资料修改
					var str_name = obj_data.name,
						str_newName = str_name;
						
					if ( str_name ) {	// 用户名回填
						if ( str_name.length > 4 ) {
							str_newName = str_name.substr(0,4)+'...';
						}
						$('#spanWelcome').html('欢迎您，'+ str_newName).attr('title', str_name);
					}
					for(var param in obj_data) {	// 修改保存成功的原始值
						if ( param == 'cnum' ) {
							dlf.fn_updateAlias();
						}
						$('#' + param ).data(param, obj_data[param]);
					}
					dlf.fn_jNotifyMessage(data.message, 'message', false, 3000);
				} else if ( str_who == 'corp' ) {	// 集团资料
					var str_cName = obj_data.c_name,
						str_linkman = obj_data.c_linkman,
						str_newName = str_linkman;
						
					if ( str_linkman ) {	// 用户名回填
						if ( str_linkman.length > 4 ) {
							str_newName = str_linkman.substr(0,4)+'...';
						}
						$('#spanWelcome').html('欢迎您，'+ str_newName).attr('title', str_linkman);
					}
					$('.corpNode').html('<ins class="jstree-icon">&nbsp;</ins>' + str_cName).children('ins').css('background', 'url("/static/images/corpImages/corp.png")');;
					for(var param in obj_data) {	// 修改保存成功的原始值
						if ( param == 'cnum' ) {
							dlf.fn_updateAlias();
						}
						$('#' + param ).data(param, obj_data[param]);
					}
					dlf.fn_jNotifyMessage(data.message, 'message', false, 3000);
				} else if ( str_who == 'cTerminalEdit' ) {
					var str_cnum = obj_data.corp_cnum;
					
					if ( str_cnum ) {
						$('#leaf_' + obj_data.tid).html('<ins class="jstree-icon" style="background: '+ $('#leaf_' + obj_data.tid).children('ins').css('background-image') +'">&nbsp;</ins>' + str_cnum);
					}
					dlf.fn_jNotifyMessage(data.message, 'message', false, 3000);
					dlf.fn_closeDialog(); // 窗口关闭 去除遮罩
				} else if ( str_who == 'terminal' ) {	// 定位器参数设置修改
					for(var param in obj_data) {	// 修改保存成功的原始值
						var str_val = obj_data[param];
						
						if ( param == 'white_list' ) { // 白名单特殊处理
							var n_length = obj_data[param].length;
							
							if ( n_length > 1 ) {
								for ( var x = 0; x < n_length; x++ ) {
									var str_name = param  + '_' + (x+1),
										obj_whitelist = $('#t_' + str_name),
										obj_oriWhitelist = $('#' + str_name),
										str_value = str_val[x];
										
									obj_whitelist.val(str_value);	
									obj_oriWhitelist.attr('t_val', str_value);	
								}
							} else {
								$('#white_list_2').attr('t_val', '');
							}
						} else {
							$('#' + param ).attr('t_val', str_val);
						}
					}
					dlf.fn_jNotifyMessage(data.message, 'message', false, 3000);
				} else if ( str_who == 'corpTerminal' ) {	// 定位器参数设置修改
					for(var param in obj_data) {	// 修改保存成功的原始值
						var str_val = obj_data[param];
						
						if ( param == 'white_list' ) { // 白名单特殊处理
							var n_length = obj_data[param].length;
							
							if ( n_length > 1 ) {
								for ( var x = 0; x < n_length; x++ ) {
									var str_name = param  + '_' + (x+1),
										obj_whitelist = $('#t_' + str_name),
										obj_oriWhitelist = $('#' + str_name),
										str_value = str_val[x];
										
									obj_whitelist.val(str_value);	
									obj_oriWhitelist.attr('t_val', str_value);	
								}
							} else {
								$('#white_list_2').attr('t_val', '');
							}
						} else {
							if ( param == 'corp_cnum' ) {
								dlf.fn_updateCorpCnum(obj_data[param]);
								$('#corp_corp_cnum' ).attr('t_val', str_val);
							}
							$('#corp_' + param ).attr('t_val', str_val);
						}
					}
					dlf.fn_jNotifyMessage(data.message, 'message', false, 3000);
				} else if ( str_who == 'whitelistPop' ) {	// 白名单提示框
					$('#whitelistPopWrapper').hide();
				} else if ( str_who == 'sms' ) {	// 短信设置修改
					for ( var param in obj_data ) {
						var str_val = obj_data[param];
						
						$('#' + param).attr('t_checked', str_val).attr('t_val', str_val);
					}
					dlf.fn_jNotifyMessage(data.message, 'message', false, 3000);
				} else if ( str_who == 'operator' ) {
					var n_operatorId = obj_data.id ,
						str_name = obj_data.name, 
						str_mobile = obj_data.mobile,
						str_address = obj_data.address, 
						str_email = obj_data.email, 
						str_groupId = obj_data.group_id,
						str_groupName = obj_data.group_name;
					
					$('tr[id='+ n_operatorId +']').empty().append(
										'<td groupId ='+ str_groupId +'>'+ str_groupName +'</td>'+
										'<td>' + str_name + '</td>' + 
										'<td>' + str_mobile + '</td>' + 
										'<td>' + str_address + '</td>' + 
										'<td>' + str_email + '</td>' + 
										'<td><a href="#" onclick=dlf.fn_editOperator('+ n_operatorId +') class="blacklistLink">编辑</a></td>' +
										'<td><a href="#" onclick=dlf.fn_deleteOperator('+ n_operatorId +') class="blacklistLink">删除</a></td>'
										);
					$('#addOperatorDialog').dialog('close');	// 关闭dialog
					dlf.fn_jNotifyMessage(data.message, 'message', false, 3000);
				} else {
					if ( str_who == 'corpTerminal' ) {
						dlf.fn_clearNavStatus('corpTerminal');
					}
					dlf.fn_jNotifyMessage(data.message, 'message', false, 3000);
					dlf.fn_closeDialog(); // 窗口关闭 去除遮罩
				}
			} else if ( data.status == 201 ) {	// 业务变更
				dlf.fn_showBusinessTip();
			} else {
				dlf.fn_jNotifyMessage(data.message, 'message', false, 5000);
			}
		}
		if ( str_who != 'whitelistPop' ) {
			dlf.fn_unLockContent(); // 清除内容区域的遮罩
		}
	}, 
	function(XMLHttpRequest, textStatus, errorThrown) {
		dlf.fn_serverError(XMLHttpRequest);
	});
}

/**
* 周边查询事件绑定
*/
window.dlf.fn_POISearch = function(n_clon, n_clat) {
	// 文本框获取/失去焦点
	$('.j_blur').blur(function() {
		var obj_this = $(this),
			str_id = obj_this.attr('id'),
			str_val = obj_this.val();
		obj_this.css('color', '#808080');
		if ( str_val == '' ) {
			if ( str_id == 'txtKeywords' ) {
				obj_this.val('查找其他关键词');
			 } else {
				$('#boundsTip').html('1000');
			 }
		} else {
			if ( str_id != 'txtKeywords' ) {
				var regex = new RegExp("^[1-9][0-9]*$");
					str_bounds = obj_this.val();
				if ( !regex.test(str_bounds) ) {
					obj_this.val('1000');
					$('#boundsTip').html('必须是大于0的整数');
				} else {
					$('#boundsTip').html('');
				}
			}
		}
	}).focus(function() {
		var obj_this = $(this);
		if ( obj_this.attr('id') == 'txtKeywords' ) {
			if( obj_this.val() == '查找其他关键词' ) {
				obj_this.val('');
			}
		}
		obj_this.css('color', '#000');
	});
	$('#POISClose').click(function() {
		$('#POISearchWrapper').hide();
	});
	/**
	* 关键字点击事件
	*/
	$('.siv_list li a').unbind('click').bind('click', function() {
		dlf.fn_searchPoints($(this), n_clon, n_clat);
	});
	/**
	* 搜索点击事件 
	*/
	$('#btnSearch').click(function() {
		dlf.fn_searchPoints('',n_clon, n_clat);
	});
	/**
	* 显示窗口
	*/
	$('#POISearchWrapper').css({'right': '10px', 'top': '205px'}).show();
}

/**
* 无钥匙挂件:无定位操作
*/
window.dlf.fn_showOrHideLocation = function(n_keys_num) {
	if ( n_keys_num == 0 ) {
		$('#defend').parent().hide();
	} else {
		$('#defend').parent().show();
	}
}
})();

/**
* jquery 异步请求架构
* url: ajax请求的url
* data: ajax请求参数
* callback: 回调函数
* errorCallback: 出现错误的回调函数
* method： ajax请求方式get or post
*/
function _ajax_request(url, data, callback, errorCallback, method) {
	return jQuery.ajax({
		type : method,
		url : url,
		data : data,
		success : callback,
        error : errorCallback, // 出现错误
		dataType : 'json',
		contentType : 'application/json; charset=utf-8',
        complete: function (XMLHttpRequest, textStatus) { // 页面超时
            var stu = XMLHttpRequest.status;
            if ( stu == 200 && XMLHttpRequest.responseText.search('captchaimg') != -1 ) {
                //window.location.replace('/static/timeout.html'); // redirect to the index.
                return;
            }
        }
	});
}

/**
* 继承并重写jquery的异步方法
*/
jQuery.extend({
    put_: function(url, data, callback, errorCallback) {
        return _ajax_request(url, data, callback, errorCallback, 'PUT');
    },
    delete_: function(url, data, callback, errorCallback) {
        return _ajax_request(url, data, callback, errorCallback, 'DELETE');
    },
    post_: function(url, data, callback, errorCallback) {
        return _ajax_request(url, data, callback, errorCallback, 'POST');
    },
	get_: function(url, data, callback, errorCallback) {
        return _ajax_request(url, data, callback, errorCallback, 'GET');
    }
});

/**
* 初始化 jNotifyMessage
*/
$(function () {
	$('#jNotifyMessage').jnotifyInizialize({
		oneAtTime : true,
		appendType : 'append'
	});
})