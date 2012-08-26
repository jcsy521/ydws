/*
*辅助处理相关操作方法
*/

// 全局变量存放处 :)
var mapObj = null, // 地图对象
	actionMarker = null, // 轨迹的动态marker 
	viewControl = null, // 鹰眼对象 
	currentLastInfo = null,  //动态更新的定时器对象
	arr_infoPoint = [],  //通过动态更新获取到的车辆数据进行轨迹显示
	f_infoWindowStatus = true, // 吹出框是否显示
	obj_localSearch = null;
if ( !window.dlf ) { window.dlf = {}; }

(function () {
// 加载MAP
window.dlf.fn_loadMap = function() { 
	// 设置地图初始化参数对象
	mapObj = new BMap.Map('mapObj'); // 创建地图实例
	markerPoint = new BMap.Point(116.39825820922851 ,39.904600759441024); // 创建点坐标
	mapObj.centerAndZoom(markerPoint, 15); // 初始化地图，设置中心点坐标和地图级别 
	mapObj.enableScrollWheelZoom();  // 启用滚轮放大缩小。
	mapObj.addControl(new BMap.ScaleControl());  // 添加比例尺控件
	viewControl = new BMap.OverviewMapControl({isOpen: true});
	mapObj.addControl(viewControl); //添加缩略地图控件
	mapObj.addControl(new BMap.MapTypeControl({
												mapTypes: [BMAP_NORMAL_MAP,BMAP_SATELLITE_MAP], 
												offset: new BMap.Size(100, 10)
												}));	// 地图类型 自定义显示 普通地图和卫星地图
	mapObj.addControl(new BMap.NavigationControl({anchor: BMAP_ANCHOR_TOP_LEFT}));
	mapObj.addControl(new BMapLib.TrafficControl({anchor: BMAP_ANCHOR_TOP_RIGHT})); //添加路况信息控件
}	
// 窗口关闭事件
window.dlf.fn_closeWrapper = function() {
	// 弹出框的关闭按钮事件 
	var obj_close = $('.j_close');
	//dlf.fn_setItemMouseStatus(obj_close, 'pointer', new Array('close_default', 'close_hover', 'close_default'));
	obj_close.click(function() {
		dlf.fn_closeJNotifyMsg('#jNotifyMessage');
		dlf.fn_closeDialog(); // 窗口关闭
	});
}

// 主动关闭窗口
window.dlf.fn_closeDialog = function() {
	$('.wrapper').hide();
	dlf.fn_unLockScreen(); // 去除页面遮罩
	dlf.fn_unLockContent(); // 清除内容区域的遮罩
	//dlf.fn_clearMapComponent(); //清除地图上的图形
}
// 处理请求服务器错误
window.dlf.fn_serverError = function(XMLHttpRequest) {
	if ( XMLHttpRequest && XMLHttpRequest.status > 200 ) {
		//alert('请求失败，请重新操作！');	// httpRequest failed
		dlf.fn_jNotifyMessage('请求失败，请重新操作！', 'message', false, 3000);		
		if ( window == window.parent ) {
			window.location.replace('/'); // redirect to the index.
		} else {
			document.jxq_refresh.action = document.referrer;
			document.jxq_refresh.submit();
		}
	}
}

// 页面添加透明遮罩
window.dlf.fn_lockScreen = function(str_body) {
	var n_height = $(window).height(), 
		obj_body = ''; 
	if ( !str_body ) {;
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
// 去除页面的透明遮罩
window.dlf.fn_unLockScreen = function() {
	$('#maskLayer').removeClass().css({'display': 'none','height': '0px','width': '0px'});
	$('.j_body').removeData('layer');
}

/* 添加内容区域的遮罩
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
// 移除内容区域的遮罩
window.dlf.fn_unLockContent = function() {
	$('#jContentLock').css('display', 'none');
}

/**
    * 转化日期字符串为整数
    * dateString格式有两种2011-11-11 20:20:20, 20:20
    * 如果直传第二中小时和分钟，则在使用今天日期构造数据
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
	return parseInt(new Date(year,month,day,hour,min,seconds).getTime()); // Your timezone!
}

// 将日期整数转化为字符串
window.dlf.fn_changeNumToDateString = function(myEpoch, str_isYear) {
	var myEpoch = parseInt(myEpoch/1000)*1000,
		myDate = new Date(myEpoch),
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
	} if ( str_isYear == 'ymd' ) {
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
	var pf = ($(window).width()-400)/2,
        displayTime = 6000,
        f_perMan_type = f_permanent ? f_permanent : false,
	    displayTime = showTime ? showTime : displayTime;

	$('#jNotifyMessage').css({
		'display': 'block',
        'left': pf+'px'
    }).jnotifyAddMessage({
		text: messages,
		permanent: f_perMan_type,
		type: types,
        disappearTime: displayTime
	});
}

// 扩展jnotify的删除方法
// id：调用jnotify的元素id
window.dlf.fn_closeJNotifyMsg = function(id) {
    $(id).hide().children().remove();
}
// 绑定车辆列表的各项
window.dlf.fn_bindCarListItem = function() {
	// 车辆列表切换
	$('#carList a').unbind('mousedown').mousedown(function(event) {
		var n_tid = $(this).attr('tid'), 
			obj_currentCar = $(this), 
			str_className = obj_currentCar.attr('class'), 
			n_mouseWhick = event.which, 
			obj_offset = $(this).offset(), 
			obj_mDownItem = $('#terminalDownItem');
		// 右键点击,显示操作菜单
		if ( n_mouseWhick == 3 ) {
			obj_mDownItem.css({'left': obj_offset.left+20, 'top': obj_offset.top-3}).show();
			$('#terminalDownItem span').unbind('mouseout click').click(function(event) {
				dlf.fn_tlDel(obj_currentCar);
			}).mouseout(function(event) {
				obj_mDownItem.hide();
			});
		} else if (n_mouseWhick == 1 ) {
			if ( str_className.search('currentCar') != -1 ) { // 如果用户点击当前车辆不做操作
				return;
			}
			dlf.fn_switchCar(n_tid, obj_currentCar); // 车辆列表切换
		}
	});
}
// 车辆列表的切换方法
window.dlf.fn_switchCar = function(n_tid, obj_currentItem) {
	// 向后台发送切换请求
	$.get_(SWITCHCAR_URL + '/' + n_tid, '', function (data) {
		if ( data.status == 0 ) {
			$('#carList a').removeClass('currentCar').addClass('car1');
			obj_currentItem.removeClass('car1').addClass('currentCar');
			var obj_carLi = $('#carList li a[tid='+n_tid+']').parent(), 
				obj_carDatas = obj_carLi.data('carData');
			if ( obj_carDatas ) {
				var obj_selfMarker = obj_carLi.children().eq(0).data('selfmarker');
				dlf.fn_updateTerminalInfo(obj_carDatas); 	//更新当前车辆的详细信息显示
				//obj_selfMarker.openInfoWindow(obj_selfMarker.selfInfoWindow);
			} else {
				dlf.fn_getCarData(); // 启动动态获取数据
			}
			// 查找到当前车辆的信息
			var obj_toCentInterval = setInterval(function() {
				var obj_tempMarker = obj_currentItem.data('selfmarker');
				if ( obj_tempMarker ) {
					mapObj.panTo(obj_tempMarker.getPosition());
				var arr_overlays = $('#carList li a');
				for ( var i = 0; i < arr_overlays.length; i++ ) {
					var obj_marker = $(arr_overlays[i]).data('selfmarker');
					if ( obj_marker ) {
						obj_marker.setTop(false);
					}
				}
				obj_tempMarker.setTop(true);
					clearInterval(obj_toCentInterval);
				}
			}, 500);
			dlf.fn_closeJNotifyMsg('#jNotifyMessage'); // 关闭消息提示
			// 动态更新终端相关数据
			dlf.fn_updateLastInfo();
		} else { // 查询状态不正确,错误提示
			dlf.fn_jNotifyMessage(data.message, 'message');
		}
	}, 
	function (XMLHttpRequest, textStatus, errorThrown) {
		dlf.fn_serverError(XMLHttpRequest);
	});
}
/**
*动态更新终端相关数据
* n_tid: 当前正在进行操作的终端 
*/
window.dlf.fn_updateLastInfo = function() {
	dlf.fn_clearInterval(currentLastInfo); // 清除定时器
	currentLastInfo = setInterval(function () { // 每15秒启动
		dlf.fn_getCarData();
	}, INFOTIME);
}
	
window.dlf.fn_getCarData = function() {
	var str_currentTid = $($('#carList a[class*=currentCar]')).attr('tid'),	//当前车tid
		obj_carListLi = $('#carList li'), 
		n_length = obj_carListLi.length, 	//车辆总数
		n_count = 0, 
		arr_tids = [], 
		obj_tids= {'tids': [str_currentTid]};	//所有车的tid集合
	for( var i = 0; i < n_length; i++ ) {
		var str_tempTid = obj_carListLi.eq(i).children().attr('tid');	//遍历每辆车获取tid
		if ( str_tempTid ) {
			arr_tids[n_count++] = str_tempTid;
		}
	}
	obj_tids.tids = arr_tids;
	$.post_(LASTINFO_URL, JSON.stringify(obj_tids), function (data) {
			if ( data.status == 0 ) {
				var obj_cars = data.cars_info,
					n_len = obj_cars.length;
				for ( var i = 0; i < n_len; i++ ) {
					// 车辆详细信息更新
					var obj_carInfo = obj_cars[i], 
						str_tid = obj_carInfo.tid, 	//车辆tid
						str_loginst = obj_carInfo.login,
						obj_carA = $('#carList a[tid='+str_tid+']'),
						obj_carLi = obj_carA.parent(),
						n_clon = obj_carInfo.clongitude/NUMLNGLAT,	
						n_clat = obj_carInfo.clatitude/NUMLNGLAT;
					// 经纬度数据不正确不做处理
					if ( n_clon != 0 && n_clat != 0 ) {
						if ( obj_carInfo ) {
							obj_carLi.data('carData', obj_carInfo);
							dlf.fn_updateInfoData(obj_carInfo); // 工具箱动态数据
						}
					}
					// 动态修改车辆当前连接状态
					if ( str_loginst == LOGINST) {
						obj_carLi.children().eq(2).removeClass('carlogout').addClass('carlogin').html('在线');
					} else {
						obj_carLi.children().eq(2).removeClass('carlogin').addClass('carlogout').html('离线');
					}
					obj_carA.attr('clogin', str_loginst);
					// 更新当前车辆信息
					if ( str_currentTid == str_tid ) {
						dlf.fn_updateTerminalInfo(obj_carInfo);
					}
				}
			}
		}, 
		function (XMLHttpRequest, textStatus, errorThrown) {
			dlf.fn_serverError(XMLHttpRequest);
		});
}
/**
* 对终端的最新数据进行页面填充
* car_info: 车辆的信息
*/
window.dlf.fn_updateTerminalInfo = function (obj_carInfo, type) {
	var n_defendStatus = obj_carInfo.defend_status, 
		str_dStatus = n_defendStatus == DEFEND_ON ? '设防状态：  已设防' : '设防状态：  未设防', 
		str_dImg= n_defendStatus == DEFEND_ON ? '/static/images/defend_status1.png' : '/static/images/defend_status0.png',
		str_type = obj_carInfo.type == GPS_TYPE ? 'GPS定位' : '基站定位',
		str_speed = obj_carInfo.speed + ' km/h',
		n_degree = obj_carInfo.degree,
		str_degree = dlf.fn_changeData('degree', n_degree), //方向角处理
		str_degreeTip = '方向角：' + Math.round(n_degree),
		str_eStatus = dlf.fn_eventText(obj_carInfo.event_status),  // 报警状态
		str_address = obj_carInfo.name,
		n_power = parseInt(obj_carInfo.pbat),
		str_power = '剩余电量：   ' + n_power + '%',	// 电池电量 0-100
		str_pImg = dlf.fn_changeData('power', n_power), // 电量图标
		str_time = obj_carInfo.timestamp > 0 ? dlf.fn_changeNumToDateString(obj_carInfo.timestamp*1000) : '-',
		n_gsm = obj_carInfo.gsm,	// gsm 值
		str_gsm = 'GSM 信号：    ' + dlf.fn_changeData('gsm', n_gsm),	// gsm信号
		n_gps = obj_carInfo.gps,	// gps 值
		str_gps = 'GPS 信号：   ' + dlf.fn_changeData('gps', n_gps),	// gps信号
		n_clon = obj_carInfo.clongitude/NUMLNGLAT,	
		str_clon = '经度： ',
		n_clat = obj_carInfo.clatitude/NUMLNGLAT,
		str_clat = '纬度： ';	// 经纬度
		
	if ( str_address == '' || str_address == null ) {
		str_address = '暂无';
	}
	// 经纬度为0 不显示位置信息
	if ( n_clat == 0 || n_clon == 0 ) {
		str_address = '-';
		str_degree = '-';
		str_type = '-';
		str_clon += '-';
		str_clat += '-';
		str_speed = '-';
	} else {
		str_clon += 'E ' + Math.floor(obj_carInfo.clongitude/NUMLNGLAT*CHECK_INTERVAL)/CHECK_INTERVAL;
		str_clat += 'N ' + Math.floor(obj_carInfo.clatitude/NUMLNGLAT*CHECK_INTERVAL)/CHECK_INTERVAL;
	}
	// lastinfo 更新车辆信息和终端信息  realtime: 只更新位置信息
	if ( !type ) {
		// 终端状态
		$('#power').css('background-image', str_pImg).html(str_power);
		$('#power').attr('title', str_power );	// 电池电量填充
		$('#GSM').html(str_gsm).attr('title', 'GSM 信号强度：' + n_gsm);
		$('#g_word').html(str_gps);
		//$('#GPS').html(str_gps).attr('title', 'GPS 信号强度：' + n_gps);
		$('#defend_word').html(str_dStatus).data('defend', n_defendStatus);
		$('#defendStatus').attr('title', str_dStatus);
		$('#defend_status').attr('src', str_dImg); // 终端最后一次设防状态
	}
	// 车辆信息/位置信息
	$('.updateTime').html('更新时间： ' + str_time); // 最后一次定位时间
	$('#address').html('位置：   ' + str_address); // 最后一次定们地址
	$('#degree').html('方向：   ' + str_degree).attr('title', str_degreeTip);
	$('#type').html('定位类型：   ' + str_type); // 车辆定位类型
	$('#lng').html(str_clon); // 车辆经度
	$('#lat').html(str_clat);	// 车辆纬度
	$('#speed').html( '速度： ' + str_speed); // 终端最后一次定位速度
}
/*对动态数据做更新*/
window.dlf.fn_updateInfoData = function(obj_carInfo, str_type) {
	var obj_tempData = [], 
		str_currentTid = $('#carList a[class*=currentCar]').attr('tid'),
		str_tid = obj_carInfo.tid,
		n_clon = obj_carInfo.clongitude/NUMLNGLAT,
		n_clat = obj_carInfo.clatitude/NUMLNGLAT,
		n_degree = obj_carInfo.degree,
		obj_tempVal = dlf.fn_checkCarVal(str_tid), // 查询缓存中是否有当前车辆信息
		obj_tempPoint = new BMap.Point(n_clon, n_clat),
		obj_carA = $('#carList a[tid='+str_tid+']'),	// 要更新的车辆
		actionPolyline = null, // 轨迹线对象
		str_actionTrack = obj_carA.attr('actiontrack'), 
		obj_selfMarker = obj_carA.data('selfmarker'), 
		n_imgDegree = dlf.fn_processDegree(n_degree),	// 方向角处理
		obj_selfPolyline = obj_carA.data('selfpolyline');
	// 存储车辆信息
	if ( obj_tempVal ) { // 追加
		if ( str_actionTrack == 'yes' ) { 
			obj_tempVal.val.push(obj_tempPoint);
		} else { 
			obj_tempVal.val = [];
			obj_tempVal.val[0] = obj_tempPoint;
		}
		obj_tempData = obj_tempVal;
		mapObj.removeOverlay(obj_selfPolyline); // 删除相应轨迹线
	} else { // 新增
		obj_tempData = {'key': str_tid, 'val': [obj_tempPoint]};
		arr_infoPoint.push(obj_tempData);
	}
	
	actionPolyline = new BMap.Polyline(obj_tempData.val); 
	mapObj.addOverlay(actionPolyline);//向地图添加覆盖物 
	obj_carA.data('selfpolyline', actionPolyline);
	if ( obj_selfMarker ) {
		obj_selfMarker.selfInfoWindow.setContent(dlf.fn_tipContents(obj_carInfo, 'actiontrack'));
		obj_selfMarker.setPosition(obj_tempPoint);
		obj_carA.data('selfmarker', obj_selfMarker);
		//方向角
		obj_selfMarker.setIcon(new BMap.Icon('/static/images/'+n_imgDegree+'.png', new BMap.Size(34, 34)));
		f_infoWindowStatus = obj_selfMarker.selfInfoWindow.isOpen();	
	} else {
		dlf.fn_addMarker(obj_carInfo, 'actiontrack', obj_carA.parent().index(), true); // 添加标记
	}
	// 实时定位
	/*if ( str_type ) {
		obj_selfMarker.openInfoWindow(obj_selfMarker.selfInfoWindow);
	}
	*/
	// 查找到当前车辆的信息
	if ( str_type == 'current' ) {
		f_infoWindowStatus = true;
	}
	var obj_toWindowInterval = setInterval(function() {
		var obj_tempMarker = obj_carA.data('selfmarker');
		if (( str_currentTid == str_tid ) && f_infoWindowStatus ) { 
			if ( obj_tempMarker ) {
				obj_tempMarker.openInfoWindow(obj_tempMarker.selfInfoWindow);
				clearInterval(obj_toWindowInterval);
			}
		}
	}, 500);
}
/** 转换GPS信号和GSM信号 为相应的强度**/
window.dlf.fn_changeData = function(str_key, str_val) {
	var str_return = '';
	if ( str_key == 'gsm' ) { // gsm 
		var str_gsmImg = '',
			obj_gsm = $('#GSM');
		if ( str_val >= 0 && str_val < 3 ) {
			str_return = '弱';
			str_gsmImg = 'url("/static/images/gsm1.png")';
		} else if ( str_val >= 3 && str_val < 6 ) {
			str_return = '较弱';
			str_gsmImg = 'url("/static/images/gsm2.png")';
		} else {
			str_return = '强';
			str_gsmImg = 'url("/static/images/gsm3.png")';
		}
		if ( obj_gsm ) {
			obj_gsm.css('background-image', str_gsmImg);
		}
	} else if ( str_key == 'gps' ) {	// gps 
		var str_gpsImg = '',
			obj_gps = $('#GPS');
		if ( str_val >= 0 && str_val < 10 ) {
			str_return = '弱';
			str_gpsImg = '/static/images/gps0.png';
		} else if ( str_val >= 10 && str_val < 20 ) {
			str_return = '较弱';
			str_gpsImg = '/static/images/gps1.png';
		} else if ( str_val >= 20 && str_val < 30 ) {
			str_return = '较强';
			str_gpsImg = '/static/images/gps2.png';
		} else {
			str_return = '强';
			str_gpsImg = '/static/images/gps3.png';
		}
		if ( obj_gps ) {
			obj_gps.attr('src', str_gpsImg); // 终端最后一次设防状态
			$('#gps').attr('title', 'GPS信号：' + str_val);
		}
	} else if ( str_key == 'power' ) {
		if ( str_val == 0 ) {
			str_return = 'url("/static/images/power.png")';
		} else if ( str_val > 0 && str_val <= 25 ) {
			str_return = 'url("/static/images/power0.png")';
		} else if ( str_val > 25 && str_val <= 50 ) {
			str_return = 'url("/static/images/power3.png")';
		} else if ( str_val > 50 && str_val <= 75 ) {
			str_return = 'url("/static/images/power6.png")';
		} else if ( str_val > 75 && str_val <= 100 ) {
			str_return = 'url("/static/images/power9.png")';
		}
	} else if ( str_key == 'degree' ) {
		if ( str_val == 0 || str_val == 360 ) {
			str_return = '正北';
		} else if ( str_val > 0 && str_val < 90) {
			str_return = '东北';
		} else if ( str_val == 90) {
			str_return = '正东';
		} else if ( str_val > 90 && str_val < 180) {
			str_return = '东南';
		} else if ( str_val == 180) {
			str_return = '正南';
		} else if ( str_val > 180 && str_val < 270) {
			str_return = '西南';
		} else if ( str_val == 270) {
			str_return = '正西';
		} else if ( str_val > 270 && str_val < 360) {
			str_return = '西北';
		}
	}
	return str_return;
}
/**查找相应tid下的数据*/
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
// 清除定时器
window.dlf.fn_clearInterval = function(obj_interval) {
	clearInterval(obj_interval); 
}
// 方向角处理
window.dlf.fn_processDegree = function(n_degree) {
	var n_roundDegree = Math.floor(n_degree/36);
	return n_roundDegree != 0 ? n_roundDegree : 10;
}
/**根据相应的报警状态码显示相应的报警提示*/
window.dlf.fn_eventText = function(n_eventNum) {
	var str_text = '无法获取';
	switch (n_eventNum) {
		case 2:
			str_text = '低电';
			break;
		case 3:
			str_text = '断电';
			break;
		case 4:
			str_text = '非法移动';
			break;
		case 5:
			str_text = 'SOS';
			break;
		case 6:
			str_text = '心跳丢失';
			break;
	}
	return str_text;
}

/**
*修改元素的mouseover mouseout  css样式 
*obj_who: 要进行设置的标签
*arr_png: 要更改的图片的名称
*str_cursor: 要修改的鼠标指针状态
*根据typeof来判断用户所传的参数进行相应操作
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
			$(this).css('background-image', 'url("/static/images/'+arr_png[2]+'.png")');
		});
	}
}
/**设置是否要启动追踪效果*/
window.dlf.setTrack = function(str_tid, selfItem) {
	var obj_carLi = $('#carList a[tid='+str_tid+']'), 
		str_actionTrack = obj_carLi.attr('actiontrack'),
		obj_selfMarker = obj_carLi.data('selfmarker'), 
		obj_selfInfoWindow = obj_selfMarker.selfInfoWindow,  // 获取吹出框
		str_content = obj_selfInfoWindow.getContent(), // 吹出框内容
		str_tempAction = 'yes';
		str_tempOldMsg = '',
		str_tempMsg = '取消跟踪';
	
	if ( str_actionTrack == 'yes' ) {
		str_tempAction = 'no';
		str_tempMsg = '开始跟踪';
		str_tempOldMsg = '取消跟踪';
	} else {
		str_tempAction = 'yes';
		str_tempMsg = '取消跟踪';
		str_tempOldMsg = '开始跟踪';
	}
	
	str_content = str_content.replace(str_tempOldMsg, str_tempMsg);
	obj_selfInfoWindow.setContent(str_content);
	obj_selfMarker.selfInfoWindow = obj_selfInfoWindow;
	
	obj_carLi.attr('actiontrack', str_tempAction).data('selfmarker', obj_selfMarker);
	$(selfItem).html(str_tempMsg);
}
/**
*POST方法的整合 defend,remote: lock,reboot
*url: 要请求的URL地址
*obj_data: 需要向后台发送的数据
*str_who: 发起此次操作的源头
*str_msg: 发送中的消息提示
*/
window.dlf.fn_jsonPost = function(url, obj_data, str_who, str_msg) {
	var obj_cWrapper = $('#'+str_who+'Wrapper'), 
		obj_content = $('.'+str_who+'Content');

	dlf.fn_jNotifyMessage(str_msg+'...<img src="/static/images/blue-wait.gif" />', 'message', true);
	dlf.fn_lockContent(obj_content); // 添加内容区域的遮罩
	
	$.post_(url, JSON.stringify(obj_data), function (data) {
		var f_warpperStatus = !obj_cWrapper.is(':hidden');
		if ( f_warpperStatus ) { // 如果查到结束后,用户关闭的窗口,不进行后续操作
			if ( data.status == 0 ) {
				if ( str_who == 'defend' ) {
					// 修改设防状态
					var str_defendStatus = $('#defend_word').data('defend'),
						str_html = '',
						str_dImg = '',
						n_defendStatus = 0;
					if ( str_defendStatus == DEFEND_ON ) { 
						// 修改成功 状态改为：撤防
						n_defendStatus = 0;
						str_html = '设防状态：  未设防';
						str_dImg=  '/static/images/defend_status0.png';
					} else {
						n_defendStatus = 1;
						str_html = '设防状态：  已设防';
						str_dImg= '/static/images/defend_status1.png';
					}
					$('#defend_word').html(str_html).data('defend', n_defendStatus);
					$('#defendStatus').attr('title', str_html);
					$('#defend_status').attr('src', str_dImg); // 终端最后一次设防状态
				} else if ( str_who == 'terminalList' ) {
					// 终端列表,进行数据ID回填
					obj_data[0].id = data.ids[0].id;
					fn_callbackData(obj_data);
				}
				dlf.fn_closeDialog(); // 窗口关闭 去除遮罩
				dlf.fn_jNotifyMessage(data.message, 'message', false, 3000);
			} else {
				dlf.fn_jNotifyMessage(data.message, 'message', true);
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
*/
window.dlf.fn_jsonPut = function(url, obj_data, str_who, str_msg) {
	var obj_cWrapper = $('#'+str_who+'Wrapper'), 
		obj_content = $('.'+str_who+'Content');

	dlf.fn_jNotifyMessage(str_msg+'...<img src="/static/images/blue-wait.gif" />', 'message', true);
	dlf.fn_lockContent(obj_content); // 添加内容区域的遮罩
	
	$.put_(url, JSON.stringify(obj_data), function (data) {
		var f_warpperStatus = !obj_cWrapper.is(':hidden');
		if ( f_warpperStatus ) { // 如果查到结束后,用户关闭的窗口,不进行后续操作
			if ( data.status == 0 ) {
				if ( str_who == 'personal') {
					// 用户名称回填
					var str_name = obj_data.name;
					if ( str_name == '' ) {
						str_name = obj_data.uid;
					} 
					$('#uName').html('欢迎您，'+ str_name);
				}
				if ( str_who != 'terminal' ) {
					dlf.fn_closeDialog(); // 窗口关闭 去除遮罩
				} else {
					dlf.fn_initTerminalWR();
				}
				dlf.fn_jNotifyMessage(data.message, 'message', false, 3000);
			} else {
				dlf.fn_jNotifyMessage(data.message, 'message', true);
			}
		}
		dlf.fn_unLockContent(); // 清除内容区域的遮罩
	}, 
	function(XMLHttpRequest, textStatus, errorThrown) {
		dlf.fn_serverError(XMLHttpRequest);
	});
}
/**
*post 操作成功后的id回填
*obj_tempData: 操作完成后台返回的数据
*/
function fn_callbackData(obj_tempData) {
	var obj_data = obj_tempData[0],
		obj_carList = $('#carList'), 
		n_carNum = $('#carList a').length,
		str_html = '';
	
	str_html+= '<li class="carlogout" clogin="0" tlid="'+obj_data.id+'" tid="'+obj_data.tid+'">'+obj_data.mobile+'</li>';
	obj_carList.append(str_html);
	dlf.fn_bindCarListItem(); // 对新增的车辆进行绑定点击事件
	if ( n_carNum <= 0 ) {
		dlf.fn_switchCar($('#carList a').eq(0).attr('tid'), $($('#carList a')[0])); // 登录成功, 车辆列表切换
	}
}
// input string, return a number
window.dlf.fn_getNumber = function(str) {
	return str.replace(/\D/g,'');
}
// 提示用户绑定终端车辆
window.dlf.fn_showTerminalMsgWrp = function() {
	var obj_wrapper = $('#terminalMsgWrapper');
	obj_wrapper.show();
}
/**
****周边查询
*/

// 查询周边信息
window.dlf.fn_searchPoints = function (obj_keywords, n_clon, n_clat) {	
	var str_keywords = '',
		n_bounds = parseInt($('#txtBounds').val()),
		obj_kw = $('#txtKeywords');
	if ( obj_keywords !='' ) {
		str_keywords = obj_keywords.html();
		obj_kw.val(str_keywords); // 填充关键字文本框
	} else {
		str_keywords = obj_kw.val();
		if ( str_keywords == '查找其他关键词' ) {
			$('#keywordsTip').html('请输入关键词'); return;
		} else {
			$('#keywordsTip').html('');
		}
	}
	if ( !obj_localSearch ) { 
		obj_localSearch = new BMap.LocalSearch(mapObj, {
				renderOptions:{map: mapObj} // 查询结果显示在地图容器
		}); 
	}
	obj_localSearch.setSearchCompleteCallback(function(results) { 
		
	});
	obj_localSearch.searchNearby(str_keywords, new BMap.Point(n_clon, n_clat), n_bounds);
	obj_localSearch.disableFirstResultSelection();	// 禁用自动选择第一个检索结果
	obj_localSearch.disableAutoViewport();	// 禁用根据结果自动调整地图层级
}

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
	//关键字点击事件
	$('.siv_list li a').unbind('click').bind('click', function() {
		dlf.fn_searchPoints($(this), n_clon, n_clat);
	});
	// 搜索点击事件 
	$('#btnSearch').click(function() {
		dlf.fn_searchPoints('',n_clon, n_clat);
	});
	//显示窗口
	$('#POISearchWrapper').css({'right': '10px', 'top': '205px'}).show();
}
// 无钥匙挂件:无定位操作
window.dlf.fn_showOrHideLocation = function(str_keys_num) {
	if ( str_keys_num == '0' ) {
		$('#warnEvent').parent().hide();
		$('#defend').parent().hide();
	} else {
		$('#warnEvent').parent().show();
		$('#defend').parent().show();
	}
}
})();

// jquery 异步请求架构
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

// 继承并重写jquery的异步方法
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
// 页面加载完成后进行加载地图
$(function () {
	// jnotify init
	$('#jNotifyMessage').jnotifyInizialize({
		oneAtTime : true,
		appendType : 'append'
	});
})