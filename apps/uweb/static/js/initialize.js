/*
*辅助处理相关操作方法
*/

// 全局变量存放处 :)
var mapObj = null, // 地图对象
	actionMarker = null, // 轨迹的动态marker 
	viewControl = null, // 鹰眼对象
	currentLastInfo = null,  //动态更新的定时器对象
	arr_infoPoint = [];  //通过动态更新获取到的车辆数据进行轨迹显示
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
	mapObj.addControl(new BMap.NavigationControl({anchor: BMAP_ANCHOR_TOP_LEFT})); 
	mapObj.addControl(new BMap.MapTypeControl({anchor: BMAP_ANCHOR_TOP_RIGHT}));
}	
// 窗口关闭事件
window.dlf.fn_closeWrapper = function() {
	// 弹出框的关闭按钮事件 
	var obj_close = $('.j_close');
	dlf.fn_setItemMouseStatus(obj_close, 'pointer', new Array('close_default', 'close_hover', 'close_default'));
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
		alert('操作失败，请重新登录！');
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
	return new Date(year,month,day,hour,min,seconds).getTime(); // Your timezone!
}

// 将日期整数转化为字符串
window.dlf.fn_changeNumToDateString = function(myEpoch, str_isYear) {
	var myDate = new Date(myEpoch),
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
	$('#carList li a').unbind('mousedown').mousedown(function(event) {
		var n_tid = $(this).attr('tid'), 
			obj_currentCar = $(this), 
			obj_curentListItem = obj_currentCar.parent(), 
			str_className = obj_curentListItem[0].className, 
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
			if ( str_className.search('carCurrent') != -1 ) { // 如果用户点击当前车辆不做操作
				return;
			}
			dlf.fn_switchCar(n_tid, obj_curentListItem); // 车辆列表切换
		}
	});
}
// 车辆列表的切换方法
window.dlf.fn_switchCar = function(n_tid, obj_currentItem) {
	$('#carList li[class*=carCurrent]').removeData('selfmarker');
	// 向后台发送切换请求
	$.get_(SWITCHCAR_URL + '/' + n_tid, '', function (data) {
		if ( data.status == 0 ) {
			$('#carList li').removeClass('carCurrent');
			obj_currentItem.addClass('carCurrent');
			dlf.fn_closeJNotifyMsg('#jNotifyMessage'); // 关闭消息提示
			// 动态更新终端相关数据
			dlf.fn_updateLastInfo();
			fn_getCarData(); // lastinfo
		} else { // 查询状态不正确,错误提示
			dlf.fn_jNotifyMessage(data.message, 'error');
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
		fn_getCarData();
	}, INFOTIME); //INFOTIME
}
	
function fn_getCarData() {
	var n_tid = $($('#carList li[class*=carCurrent] a')).attr('tid');
	$.get_(LASTINFO_URL + '/' + n_tid, '', function (data) {
			if ( data.status == 0 ) {
				// 车辆详细信息更新
				var obj_carInfo = data.car_info, 
					polyline = null, 
					str_loginst = obj_carInfo.login,
					str_tid = obj_carInfo.tid,
					n_clon = obj_carInfo.clongitude/NUMLNGLAT,
					n_clat = obj_carInfo.clatitude/NUMLNGLAT,
					obj_car = $($('#carList li a[tid='+str_tid+']')), 
					obj_carLi = obj_car.parent(),
					obj_tempPoint = new BMap.Point(n_clon, n_clat), 
					obj_tempLocation = {'name': obj_carInfo.address, 'timestamp': obj_carInfo.timestamp, 'speed': obj_carInfo.speed, 
									'clongitude': obj_carInfo.clongitude, 'clatitude': obj_carInfo.clatitude, 'type': obj_carInfo.type,'tid': obj_carInfo.tid};
				// 经纬度数据不正确不做处理
				if ( n_clon != 0 && n_clat != 0 ) {	
					mapObj.setCenter(obj_tempPoint);
					dlf.fn_updateInfoData(obj_carInfo); // 工具箱动态数据
				} else {
					dlf.fn_clearMapComponent();
				}
				dlf.fn_updateTerminalInfo(data.car_info); // 填充车辆信息
				
				// 动态修改车辆当前连接状态
				if ( str_loginst == LOGINST) {
					obj_carLi.removeClass('carlogout').addClass('carlogin');
				} else {
					obj_carLi.removeClass('carlogin').addClass('carlogout');
				}
			}
		}, 
		function (XMLHttpRequest, textStatus, errorThrown) {
			dlf.fn_serverError(XMLHttpRequest);
		});
}
/*对动态数据做更新*/
window.dlf.fn_updateInfoData = function(obj_carInfo, str_actionType) {
	var obj_tempData = [], 
		obj_carLi = $('#carList li[class*=carCurrent]'),
		str_tid = obj_carLi.attr('tid'), 
		n_clon = obj_carInfo.clongitude/NUMLNGLAT,
		n_clat = obj_carInfo.clatitude/NUMLNGLAT,
		obj_tempVal = dlf.fn_checkCarVal(str_tid), // 查询缓存中是否有当前车辆信息
		obj_tempPoint = new BMap.Point(n_clon, n_clat),
		actionPolyline = null, // 轨迹线对象
		str_actionTrack = obj_carLi.attr('actiontrack'), 
		obj_selfMarker = obj_carLi.data('selfmarker'), 
		obj_selfPolyline = obj_carLi.data('selfpolyline');
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
	
	obj_carLi.data('selfpolyline', actionPolyline);
	if ( obj_selfMarker ) { 
		var infoWindow = new BMap.InfoWindow(dlf.fn_tipContents(obj_carInfo, 'actiontrack'));
		obj_selfMarker.selfInfoWindow = infoWindow;
		obj_selfMarker.setPosition(obj_tempPoint);
		obj_carLi.data('selfmarker', obj_selfMarker);
		obj_selfMarker.openInfoWindow(infoWindow);
	} else { 
		dlf.fn_addMarker(obj_carInfo, 'actiontrack', obj_carLi.index()); // 添加标记
	}
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
/**
* 对终端的最新数据进行页面填充
* car_info: 车辆的信息
*/
window.dlf.fn_updateTerminalInfo = function (obj_carInfo, type) {
	var str_dStatus = obj_carInfo.defend_status == DEFEND_ON ? '已设防' : '未设防', 
		str_type = obj_carInfo.type == GPS_TYPE ? 'GPS定位' : '基站定位',
		n_degree = obj_carInfo.degree,
		str_eStatus = dlf.fn_eventText(obj_carInfo.event_status),  // 报警状态
		str_address = obj_carInfo.name,
		n_time = obj_carInfo.timestamp != null ? obj_carInfo.timestamp : new Date().getTime(),
		str_lngLat = 'E '+Math.floor(obj_carInfo.clongitude/NUMLNGLAT*CHECK_INTERVAL)/CHECK_INTERVAL+'，N '+
				Math.floor(obj_carInfo.clatitude/NUMLNGLAT*CHECK_INTERVAL)/CHECK_INTERVAL; // 经纬度
	if ( n_degree == 0 ) {
		n_degree = 36;
	}
	if ( str_address == '' || str_address == null ) {
		str_address = '暂无';
	}
	$('#timesTamp').html(dlf.fn_changeNumToDateString(n_time)); // 最后一次定位时间
	$('#carAddress').html(str_address); // 最后一次定们地址
	$('#terminalId').html(obj_carInfo.tid); // 终端卡号
	$('#carDegree').html(n_degree*10); // 车辆当前方向角
	$('#carLocType').html(str_type); // 车辆定位类型
	$('#carLngLat').html(str_lngLat); // 车辆经纬度
	$('#carSpeed').html(obj_carInfo.speed); // 终端最后一次定位速度
	
	if ( !type ) {
		$('#defendStatus').html(str_dStatus); // 终端最后一次设防状态
		$('#eventStatus').html(str_eStatus); // 终端最后一次报警状态
		$('#lockStatus').val(obj_carInfo.lock_status); // 开锁解锁状态 ( 1:车被锁定； 0： 车未被锁定)
	}
}
/**根据相应的报警状态码显示相应的报警提示*/
window.dlf.fn_eventText = function(n_eventNum) {
	var str_text = '无法获取';
	switch (n_eventNum) {
		case 0:
			str_text = '未知类型';
			break;
		case 1:
			str_text = '无报警';
			break;
		case 2:
			str_text = '低电';
			break;
		case 3:
			str_text = '断电';
			break;
		case 4:
			str_text = '越界';
			break;
		case 5:
			str_text = '超速';
			break;
		case 6:
			str_text = '非法移动';
			break;
		case 7:
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
	var obj_carLi = $('#carList li a[tid='+str_tid+']').parent(), 
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
					var str_rStatus = $('#defendStatus').html() == '已设防' ? '未设防' : '已设防';
					$('#defendStatus').html(str_rStatus);	// 设置车辆信息的设防状态
				} else if ( str_who == 'lock' ) {
						//远程解锁车操作成功,根据当前车状态修改页面数据
						var str_lStatus = $('#lockStatus').val() == LOCK_ON ? LOCK_OFF : LOCK_ON;
						$('#lockStatus').val(str_lStatus);
				} else if ( str_who == 'terminalList' ) {
					// 终端列表,进行数据ID回填
					obj_data[0].id = data.ids[0].id;
					fn_callbackData(obj_data);
				}
				dlf.fn_closeDialog(); // 窗口关闭 去除遮罩
				dlf.fn_jNotifyMessage(data.message, 'message', false, 3000);
			} else {
				dlf.fn_jNotifyMessage(data.message, 'error', true);
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
					dlf.fn_initTerminalWR('w');
				}
				dlf.fn_jNotifyMessage(data.message, 'message', false, 3000);
			} else {
				dlf.fn_jNotifyMessage(data.message, 'error', true);
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
		n_carNum = $('#carList li').length,
		str_html = '';
	
	str_html+= '<li class="carlogout"><a clogin="0" tlid="'+obj_data.id+'" tid="'+obj_data.tid+'" href="#">'+obj_data.mobile+'</a></li>';
	obj_carList.append(str_html);
	dlf.fn_bindCarListItem(); // 对新增的车辆进行绑定点击事件
	if ( n_carNum <= 0 ) {
		dlf.fn_switchCar($($('#carList li a')[0]).attr('tid'), $($('#carList li')[0])); // 登录成功, 车辆列表切换
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