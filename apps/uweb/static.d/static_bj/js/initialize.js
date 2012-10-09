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
	obj_currentPoint = {},
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
        'left': '40%'
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
	var obj_carLi = $('#carList a[tid='+n_tid+']').parent(),
		n_keys_num = obj_carLi.attr('keys_num');
	/* todo 终端挂件
	if ( n_keys_num ) {
		fn_showOrHideLocation(n_keys_num);
	}
	*/
	// 向后台发送切换请求
	$.get_(SWITCHCAR_URL + '/' + n_tid, '', function (data) {
		if ( data.status == 0 ) {
			dlf.fn_clearMapComponent(); // 清除页面图形
			// 车辆样式
			$('#carList a').removeClass('currentCar');
			obj_currentItem.addClass('currentCar');
			// 更新当前车辆的详细信息显示
			var	obj_carDatas = obj_carLi.data('carData'),
				obj_selfMarkers = $('#carList a'),
				n_len = obj_selfMarkers.length;
			if ( obj_carDatas ) {
				dlf.fn_updateTerminalInfo(obj_carDatas); 	
			} else {
				dlf.fn_getCarData(); // 启动动态获取数据
			}
			// 查找所有的selfmarker 如果存在的话添加marker到地图
			$.each(obj_selfMarkers, function(index, dom) {
				var obj_selfMarker = $(dom).data('selfmarker'),
					obj_label = $(dom).data('selfLable');
				if ( obj_selfMarker ) {
					obj_selfMarker.setLabel(obj_label);
					mapObj.addOverlay(obj_selfMarker);//向地图添加覆盖物 
				}
			});
			// 查找到当前车辆的信息  更新marker信息
			var obj_toCentInterval = setInterval(function() {
				var obj_tempMarker = obj_currentItem.data('selfmarker'),
					obj_infoWindow = '';
				if ( obj_tempMarker ) {
					obj_infoWindow = obj_tempMarker.selfInfoWindow
					mapObj.panTo(obj_tempMarker.getPosition());
					// 查找当前车辆marker 设置位置位于最上面
					var arr_overlays = $('#carList li a');
					for ( var i = 0; i < arr_overlays.length; i++ ) {
						var obj_marker = $(arr_overlays[i]).data('selfmarker');
						if ( obj_marker ) {
							obj_marker.setTop(false);
						}
					}
					obj_tempMarker.setTop(true);
					obj_tempMarker.openInfoWindow(obj_infoWindow); // 显示吹出框
					clearInterval(obj_toCentInterval);
				}
			}, 500);
			dlf.fn_closeJNotifyMsg('#jNotifyMessage');  // 关闭消息提示
			dlf.fn_updateLastInfo(); // 动态更新终端相关数据
		} else if ( data.status == 201 ) {
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
*动态更新终端相关数据
*/
window.dlf.fn_updateLastInfo = function() {
	dlf.fn_clearInterval(currentLastInfo); // 清除定时器
	currentLastInfo = setInterval(function () { // 每15秒启动
		dlf.fn_getCarData();
	}, INFOTIME); 
}
// 每隔15秒获取数据
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
				for(var param in obj_cars) {
					var obj_carInfo = obj_cars[param], 
						str_tid = param,
						str_alias = obj_carInfo.alias,
						str_loginst = obj_carInfo.login,
						str_loginClass = '',
						obj_carA = $('#carList a[tid='+str_tid+']'),
						obj_img = obj_carA.children().eq(0),	// 在线离线图
						obj_carLi = obj_carA.parent(),
						obj_child2 = obj_carLi.children().eq(2), 
						obj_child1 = obj_carLi.children().eq(1),
						n_clon = obj_carInfo.clongitude/NUMLNGLAT,	
						n_clat = obj_carInfo.clatitude/NUMLNGLAT;
					obj_carInfo.tid = str_tid; 
					// 经纬度数据不正确不做处理
					if ( n_clon != 0 && n_clat != 0 ) {
						// 存储当前经纬度
						obj_currentPoint['clongitude'] = n_clon;
						obj_currentPoint['clatitude'] = n_clat;						
						if ( obj_carInfo ) {
							obj_carLi.data('carData', obj_carInfo);
							dlf.fn_updateInfoData(obj_carInfo); // 工具箱动态数据
						}
					}
					// 修改别名
					obj_child1.html(str_alias).attr('title', str_alias);
					// 动态修改车辆当前连接状态
					if ( str_loginst == LOGINST) {
						obj_carA.removeClass('carlogout').addClass('carlogin');
						obj_img.attr('src', 'static/images/car1.png');
						obj_child1.removeClass('gray').addClass('green');
						obj_child2.removeClass('gray').addClass('green').html('(在线)');
					} else {
						obj_carA.removeClass('carlogin').addClass('carlogout');
						obj_img.attr('src', 'static/images/carout1.png');
						obj_child1.removeClass('green').addClass('gray');
						obj_child2.removeClass('green').addClass('gray').html('(离线)');
					}
					obj_carA.attr('clogin', str_loginst);
					// 更新当前车辆信息
					if ( str_currentTid == str_tid ) {
						dlf.fn_updateTerminalInfo(obj_carInfo);
					}
				}
			} else if ( data.status == 201 ) {
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
* 对终端的最新数据进行页面填充
* car_info: 车辆的信息
*/
window.dlf.fn_updateTerminalInfo = function (obj_carInfo, type) {
	var str_tmobile = obj_carInfo.mobile,
		str_titleMobile =  '终端号码：' + str_tmobile,
		n_defendStatus = obj_carInfo.defend_status, 
		str_dStatus = n_defendStatus == DEFEND_ON ? '已设防' : '未设防', 
		str_dStatusTitle =  n_defendStatus == DEFEND_ON ? '设防状态：已设防' : '设防状态：未设防',
		str_dImg= n_defendStatus == DEFEND_ON ? 'url("/static/images/defend_status1.png")' : 'url("/static/images/defend_status0.png")',
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
	// 经纬度为0 不显示位置信息
	if ( n_clat == 0 || n_clon == 0 ) {
		str_address = '-';
		str_degree = '-';
		str_type = '-';
		str_clon += '-';
		str_clat += '-';
		str_speed = '-';
	} else {
		str_address = $('#carList a[tid='+ obj_carInfo.tid +']').data('address');
		str_clon += 'E ' + Math.round(obj_carInfo.clongitude/NUMLNGLAT*CHECK_INTERVAL)/CHECK_INTERVAL;
		str_clat += 'N ' + Math.round(obj_carInfo.clatitude/NUMLNGLAT*CHECK_INTERVAL)/CHECK_INTERVAL;
	}
	// lastinfo 更新车辆信息和终端信息  realtime: 只更新位置信息
	if ( !type ) {
		var n_power = parseInt(obj_carInfo.pbat),
			str_power =  n_power + '%',	// 电池电量 0-100
			str_pImg = dlf.fn_changeData('power', n_power), // 电量图标
			n_gsm = obj_carInfo.gsm,	// gsm 值
			str_gsm = dlf.fn_changeData('gsm', n_gsm),	// gsm信号
			n_gps = obj_carInfo.gps,	// gps 值
			str_gps = dlf.fn_changeData('gps', n_gps);	// gps信号
		// 终端状态
		$('#powerContent').html(str_power);// 电池电量填充
		$('#gsmContent').html(str_gsm);
		$('#gpsContent').html(str_gps);
		$('#defendContent').html(str_dStatus).data('defend', n_defendStatus);
		$('#defendStatus').css('background-image', str_dImg).attr('title', str_dStatusTitle);
		$('#tmobile').attr('title', str_titleMobile);
		$('#tmobileContent').html(str_tmobile)
	}
	// 车辆信息/位置信息
	$('.updateTime').html('更新时间： ' + str_time); // 最后一次定位时间
	$('#address').html(str_address); // 最后一次定们地址
	$('#degree').html(str_degree).attr('title', str_degreeTip);
	$('#type').html(str_type); // 车辆定位类型
	$('#lng').html(str_clon); // 车辆经度
	$('#lat').html(str_clat);	// 车辆纬度
	$('#speed').html(str_speed); // 终端最后一次定位速度
}
/*对动态数据做更新*/
window.dlf.fn_updateInfoData = function(obj_carInfo, str_type) {
	var obj_tempData = [], 
		str_currentTid = $('#carList a[class*=currentCar]').attr('tid'),
		str_tid = obj_carInfo.tid,
		str_alias = obj_carInfo.alias,
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
	// 如果存在marker 更新marker内容
	
	if ( obj_selfMarker ) {
		// 修改别名
		if ( !str_alias ) {
			str_alias = obj_carA.siblings('.j_currentCar').html()
		}
		obj_selfMarker.setLabel(obj_carA.data('selfLable'));
		obj_selfMarker.getLabel().setContent(str_alias);
		obj_selfMarker.selfInfoWindow.setContent(dlf.fn_tipContents(obj_carInfo, 'actiontrack', 'lastinfo'));
		obj_selfMarker.setPosition(obj_tempPoint);
		obj_carA.data('selfmarker', obj_selfMarker);
		//方向角
		obj_selfMarker.setIcon(new BMap.Icon('/static/images/'+n_imgDegree+'.png', new BMap.Size(34, 34)));
		//f_infoWindowStatus = obj_selfMarker.selfInfoWindow.isOpen();	
	} else {
		dlf.fn_addMarker(obj_carInfo, 'actiontrack', obj_carA.parent().index(), false, 'lastinfo'); // 添加标记
	}
	// 查找到当前车辆的信息
	if ( str_type == 'current' ) {
		var obj_toWindowInterval = setInterval(function() {
			var obj_tempMarker = obj_carA.data('selfmarker');
			if (( str_currentTid == str_tid ) ) {  //&& f_infoWindowStatus 
				if ( obj_tempMarker ) {
					obj_tempMarker.openInfoWindow(obj_tempMarker.selfInfoWindow);
					clearInterval(obj_toWindowInterval);
				}
			}
		}, 500);
	}
}
/** 转换GPS,GSM,power,degree 为相应的值**/
window.dlf.fn_changeData = function(str_key, str_val) {
	var str_return = '';
	if ( str_key == 'gsm' ) { // gsm 
		var str_gsmImg = '',
			obj_gsm = $('#gsm');
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
			obj_gsm.css('background-image', str_gsmImg).attr('title', 'GSM 信号强度：' + str_val);;
		}
	} else if ( str_key == 'gps' ) {	// gps 
		var str_gpsImg = '',
			obj_gps = $('#gps');
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
		str_gpsImg = 'url("/static/images/'+ str_gpsImg +'")';
		if ( obj_gps ) {
			obj_gps.css('background-image', str_gpsImg).attr('title', 'GPS信号：' + str_val);
		}
	} else if ( str_key == 'power' ) {
		/*$('#power').attr('title', '剩余电量' + str_val );
		$('#pwoerSign').progressbar({value: str_val}); // 通过进度条实现电池电量效果*/
		var arr_powers = [0,10,20,30,40,50,60,70,80,90,100],
			arr_img = ['power0.png','power1.png','power2.png','power3.png','power4.png','power5.png','power6.png','power7.png','power8.png','power9.png','power10.png'];
		for ( var i = 0; i < arr_powers.length; i++ ) {
			if ( str_val >= 0 && str_val <= 10 ) {
				str_return = 'url("/static/images/power0.png")';
				break;
			} else if ( str_val == 100 ) {
				str_return = 'url("/static/images/power10.png")';
				break;
			} else if ( str_val > arr_powers[i] && str_val <= arr_powers[i+1] ) {
				str_return = 'url("/static/images/'+arr_img[i]+'")';
				break;
			}
		}
		$('#power').css('background-image', str_return).attr('title', '剩余电量：' + str_val );
	} else if ( str_key == 'degree' ) {
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
	/*else if ( str_key == 'vibl' ) {	// 参数设置中的震动灵敏度
		if ( str_val >= 0 && str_val <= 2 ) {
			str_return = '很灵敏';
		} else if ( str_val >= 3 && str_val <= 5 ) {
			str_return = '灵敏';
		} else if ( str_val >= 6 && str_val <= 9 ) {
			str_return = '一般灵敏';
		}
	}*/
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
	var n_roundDegree = Math.round(n_degree/10);
	return n_roundDegree != 0 ? n_roundDegree : 36;
}
/**根据相应的报警状态码显示相应的报警提示*/
window.dlf.fn_eventText = function(n_eventNum) {
	var str_text = '无法获取';
	switch (n_eventNum) {
		case 2:
			str_text = '低电';
			break;
		case 3:
			str_text = '关机';
			break;
		case 4:
			str_text = '非法移动';
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
* 业务变更提示 
*/
window.dlf.fn_showBusinessTip = function(str_type) {
	dlf.fn_clearInterval(currentLastInfo); // 清除lastinfo定时器
	dlf.fn_closeJNotifyMsg('#jNotifyMessage'); // 关闭消息提示
	if ( !str_type ) {
		dlf.fn_closeDialog(); // 窗口关闭 去除遮罩
	}
	// 遮罩
	dlf.fn_lockScreen(); 
	$('#businessWrapper').css({'left': '38%', 'top': '22%'}).show();
	$('#businessBtn').click(function() {
		window.location.replace('/logout');
	});
}
/**
* input blur event
*/
window.dlf.fn_onInputBlur = function() {
	$('.j_onInputBlur').unbind('blur').bind('blur', function() {
		$(this).removeClass('bListR_text_mouseFocus');
		var $this = $(this),
			str_val = $this.val(),
			str_msg = $this.attr('msg'),
			n_maxLength = $this.attr('max'),
			str_who = $this.attr('who'),
			n_valLength = $.trim(str_val).replace(/[^\x00-\xff]/g, '^^').length;	// 一个汉字转换成2个字符
		switch (str_who) {
			case  'validateLength':
				// 验证长度
				if ( n_valLength > n_maxLength ) {
					dlf.fn_jNotifyMessage(str_msg, 'message', false, 4000);
				} else {
					dlf.fn_closeJNotifyMsg('#jNotifyMessage');
				}
				break;
			case 'mobile':
				// 验证手机号
				var reg =  /^(\+86){0,1}1(3[0-9]|5[012356789]|8[02356789]|47)\d{8}$/,
					str_msg = '';
				// 验证长度
				if ( n_valLength == 0 ) {
					str_msg = '';
				} else if ( n_valLength > 14 || n_valLength < 11 ) {
					str_msg = '您设置的车主号码不正确，请输入正确的手机号！'
				} else {
					if ( !reg.test(str_val) ) {
						str_msg = '您设置的车主号码不正确，请输入正确的手机号！';
					}
				}
				if ( str_msg != '' ) {
					dlf.fn_jNotifyMessage(str_msg, 'message', false, 4000);
				} else {
					dlf.fn_closeJNotifyMsg('#jNotifyMessage');
				}
				break;
			case 'email': 
				// 验证email
				var reg =  /^\w+((-\w+)|(\.\w+))*\@[A-Za-z0-9]+((\.|-)[A-Za-z0-9]+)*\.[A-Za-z0-9]+$/,
					str_msg = '';
				// 验证长度
				if ( n_valLength > n_maxLength ) {
					str_msg = '邮箱的最大长度是255个字符！'
				} else {
					if ( !reg.test(str_val) ) {
						str_msg = '您输入的邮箱格式不正确！';
					}
				}
				if ( str_msg != '' ) {
					dlf.fn_jNotifyMessage(str_msg, 'message', false, 4000);
				} else {
					dlf.fn_closeJNotifyMsg('#jNotifyMessage');
				}
				break;
			case 'name':
				// 验证车主姓名
				var reg =  /^[a-zA-Z0-9_\u4e00-\u9fa5 ]+$/,
					str_msg = '';
				// 验证长度
				if ( n_valLength > n_maxLength ) {
					str_msg = '车主姓名的最大长度是20个字符！'
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
		}
 	});
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
					// 修改左侧栏设防状态
					var str_defendStatus = $('#defendContent').data('defend'),
						str_html = '',
						str_dImg = '',
						n_defendStatus = 0;
					if ( str_defendStatus == DEFEND_OFF ) { 
						n_defendStatus = 1;
						str_html = '已设防';
						str_dImg= 'url("/static/images/defend_status1.png")';						
					} else {
					// 修改成功 状态改为：撤防
						n_defendStatus = 0;
						str_html = '未设防';
						str_dImg=  'url("/static/images/defend_status0.png")';
					}
					$('#defendContent').html(str_html).data('defend', n_defendStatus);
					$('#defendStatus').css('background-image', str_dImg).attr('title', str_html);
				}
				dlf.fn_closeDialog(); // 窗口关闭 去除遮罩
				dlf.fn_jNotifyMessage(data.message, 'message', false, 3000);
			} else if ( data.status == 201 ) {
				dlf.fn_showBusinessTip();
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
	if ( str_who != 'whitelistPop' ) {
		dlf.fn_jNotifyMessage(str_msg+'...<img src="/static/images/blue-wait.gif" />', 'message', true);
		dlf.fn_lockContent(obj_content); // 添加内容区域的遮罩
	}	
	$.put_(url, JSON.stringify(obj_data), function (data) {
		var f_warpperStatus = !obj_cWrapper.is(':hidden');
		if ( f_warpperStatus ) { // 如果查到结束后,用户关闭的窗口,不进行后续操作
			if ( data.status == 0 ) {
				if ( str_who == 'personal') {
					// 用户名称回填
					var str_name = obj_data.name,
						str_newName = str_name;
					if ( str_name ) {
						if ( str_name.length > 4 ) {
							str_newName = str_name.substr(0,4)+'...';
						}
						$('#spanWelcome').html('欢迎您，'+ str_newName).attr('title', str_name);
					}
					dlf.fn_jNotifyMessage(data.message, 'message', false, 3000);
				} else if ( str_who == 'terminal' ) {
					dlf.fn_updateAlias();
					dlf.fn_jNotifyMessage(data.message, 'message', false, 3000);
					dlf.fn_initTerminalWR();
				} else if ( str_who == 'whitelistPop' ) {
					$('#whitelistPopWrapper').hide();
				} else if ( str_who == 'sms' ) {
					for ( var param in obj_data ) {
						var str_val = obj_data[param];
						$('#' + param).attr('t_checked', str_val).attr('t_val', str_val);
					}
					dlf.fn_jNotifyMessage(data.message, 'message', false, 3000);
				} else {
					dlf.fn_jNotifyMessage(data.message, 'message', false, 3000);
					dlf.fn_closeDialog(); // 窗口关闭 去除遮罩
				}
			} else if ( data.status == 201 ) {
				dlf.fn_showBusinessTip();
			} else {
				dlf.fn_jNotifyMessage(data.message, 'message', true);
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
/**  更新终端别名 terminal get和put的时候  */
window.dlf.fn_updateAlias = function() {
	// 别名回填
	var alias = $('#t_alias').val(),		// 终端别名
		cnum = $('#t_cnum').val(),	// 车牌号
		tmobile = $('#t_mobile').html(),
		obj_car = $('#carList .currentCar'),
		obj_selfMarker = obj_car.data('selfmarker'),
		str_alias = '';
	if ( alias != '' ) {
		str_alias = alias;
	} else if ( cnum != '' ) {
		str_alias = cnum;
	} else {
		str_alias = tmobile;
	}
	if ( obj_selfMarker ) {
		// 修改 marker label 别名
		obj_selfMarker.getLabel().setContent(str_alias);
		var str_tid = $('#carList .currentCar').eq(0).attr('tid'),
			str_content = obj_selfMarker.selfInfoWindow.getContent(),
			n_beginNum = str_content.indexOf('车辆：')+3,
			n_endNum = str_content.indexOf('</h4>'),
			str_oldname = str_content.substring(n_beginNum, n_endNum),
			str_content = str_content.replace(str_oldname, str_alias);
		$('.cMsgWindow h4[tid='+str_tid+']').html('车辆：' + str_alias);
		obj_selfMarker.selfInfoWindow.setContent(str_content);
	}
	obj_car.attr('title', str_alias);	// 
	obj_car.siblings('.j_currentCar').html(str_alias).attr('title', str_alias);
}
// 提示用户绑定终端车辆
window.dlf.fn_showTerminalMsgWrp = function() {
	var obj_wrapper = $('#terminalMsgWrapper');
	obj_wrapper.show();
}
/**
****周边查询
*/
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
window.dlf.fn_showOrHideLocation = function(n_keys_num) {
	if ( n_keys_num == 0 ) {
		$('#defend').parent().hide();
	} else {
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