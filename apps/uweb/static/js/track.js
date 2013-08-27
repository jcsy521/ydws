/*
*轨迹查询相关操作方法
*/

/**
*开始动态效果
*timerId : 动态时间控制器
*counter : 动态运行次数
*str_actionState : 暂停操作的状态
*n_speed: 默认播放速度
*b_trackMsgStatus: 动态marker的吹出框是否显示
*/
var timerId = null, counter = 0, str_actionState = 0, n_speed = 200, b_trackMsgStatus = true,obj_drawLine = null, arr_drawLine = [];
/**
* 初始化轨迹显示页面
*/
window.dlf.fn_initTrack = function() {
	var obj_trackHeader =  $('#trackHeader');
	
	$('#track').addClass('trackHover');
	dlf.fn_clearNavStatus('eventSearch');  // 移除告警导航操作中的样式
	dlf.fn_closeDialog(); // 关闭所有dialog
	dlf.fn_setMapPosition(false);
	dlf.fn_initTrackDatepicker(); // 初始化时间控件
	$('#POISearchWrapper').hide();  // 关闭周边查询
	dlf.fn_clearInterval(currentLastInfo); // 清除lastinfo计时器
	dlf.fn_clearTrack('inittrack');	// 初始化清除数据
	$('#ceillid_flag').removeAttr('checked');
	obj_trackHeader.show();	// 轨迹查询条件显示
	// 调整工具条和
	dlf.fn_setMapControl(35); /*调整相应的地图控件及服务对象*/
	
	var str_tempAlias = $('.j_currentCar').attr('alias'),
		str_currentCarAlias = dlf.fn_dealAlias(str_tempAlias), 
		obj_trackPos = $('.trackPos');
	
	if ( dlf.fn_userType() ) {
		$('#trackTerminalAliasLabel').html(str_currentCarAlias).attr('title', str_tempAlias);
		obj_trackPos.css('width', 700);
		$('.j_delay').hide();
		$('.j_delayTbody').html('');
	} else {
		obj_trackPos.css('width', 530);
	}
}

/**
* 关闭轨迹显示页面
* b_ifLastInfo: 清除规矩相关的时候是否要发起lastinfo
*/
window.dlf.fn_closeTrackWindow = function(b_ifLastInfo) {
	$('#mapObj').show();
	dlf.fn_clearNavStatus('track'); // 移除导航操作中的样式
	dlf.fn_clearMapComponent(); // 清除页面图形
	dlf.fn_clearTrack();	// 清除数据
	$('#trackHeader').hide();	// 轨迹查询条件隐藏
	$('.j_delay').hide();
	/**
	* 清除地图后要清除车辆列表的marker存储数据
	*/
	var obj_cars = $('.j_carList .j_terminal'),
		obj_selfMarker = null,
		obj_carInfo = null; 
		
	n_currentLastInfoNum = 0;
	if ( b_ifLastInfo ) {
		
		// obj_carsData = {};
		obj_selfmarkers = {};
		
		LASTINFOCACHE = 0; //轨迹查询后重新获取终端数据
		dlf.fn_clearOpenTrackData();	// 初始化开启追踪的数据
		$('.j_body').data('lastposition_time', -1);
		if ( !dlf.fn_userType() ) {
			// $('.j_carList').removeData('carsData');
			dlf.fn_getCarData('first');	// 重新请求lastinfo
		} else {
			arr_infoPoint = [];
			arr_tracePoints = [];
			obj_oldData = {'gids': '', 'tids': '', 'n_gLen': 0};
			dlf.fn_corpGetCarData(true);
		}
		dlf.fn_updateLastInfo();// 动态更新定位器相关数据
	}
	dlf.fn_closeJNotifyMsg('#jNotifyMessage'); // 关闭消息提示
	dlf.fn_setMapControl(10); /*调整相应的地图控件及服务对象*/
}

/**
* 轨迹查询操作
*/
function fn_trackQuery() {
	var obj_trackHeader = $('#trackHeader'),
		arr_delayPoints = [],
		obj_delayCon = $('.j_delay'),
		str_beginTime = dlf.fn_changeDateStringToNum($('#trackBeginTime').val()), 
		str_endTime = dlf.fn_changeDateStringToNum($('#trackEndTime').val()),
		n_cellid_flag = $('#ceillid_flag').attr('checked') == 'checked' ? 1 : 0,
		obj_locusDate = {'start_time': str_beginTime, 
						'end_time': str_endTime,
						'cellid_flag': n_cellid_flag},
		b_userType = dlf.fn_userType();	// 个人用户或者集团用户
	
	if ( str_beginTime >= str_endTime ) {
		dlf.fn_jNotifyMessage('开始时间不能大于结束时间，请重新选择时间段。', 'message', false, 3000);
		return;
	}
	dlf.fn_clearTrack();	// 清除数据
	$('.j_trackBtnhover').hide();	// 播放按钮隐藏
	dlf.fn_clearInterval(currentLastInfo); // 清除lastinfo定时器
	dlf.fn_clearMapComponent(); // 清除页面图形
	dlf.fn_jNotifyMessage('车辆轨迹查询中' + WAITIMG, 'message', true);
	dlf.fn_lockScreen('j_trackbody'); // 添加页面遮罩
	$('.j_trackbody').data('layer', true);
	dlf.fn_lockScreen();
	
	obj_trackHeader.removeData('delayPoints');	// 清除停留点缓存数据
	// 集团用户显示查询结果面板
	obj_delayCon.hide();
	obj_locusDate.tid = dlf.fn_getCurrentTid();
	$.post_(TRACK_URL, JSON.stringify(obj_locusDate), function (data) {
		if ( data.status == 0 ) {
			var arr_locations = data.track, 
				locLength = arr_locations.length,
				str_downloadHash = data.hash_,	// 下载停留点的hash参数
				str_msg = '';
				
			if ( locLength <= 0) {
				if ( obj_locusDate.cellid_flag == 0 ) {	// 如果没有勾选基站定位
					str_msg = '该时间段没有轨迹记录，请尝试选择“显示基站定位”。';
				} else {
					str_msg = '该时间段没有轨迹记录，请选择其它时间段。';
				}
				dlf.fn_jNotifyMessage(str_msg, 'message', false, 3000);
				$('#trackSpeed').hide();	// 速度滑块隐藏
			} else {
				// 集团用户显示查询结果面板
				var arr_idlePoints = data.idle_points;
				
				if ( b_userType ) {
					if ( arr_idlePoints.length > 0 ) {
						obj_delayCon.show();
						$('.j_delayPanel').show();
						// 存储停留点信息
						obj_trackHeader.data('delayPoints', arr_idlePoints);
					}
				}
				
				$('#exportDelay').attr('href', TRACKDOWNLOAD_URL + '?hash_=' + str_downloadHash);
				dlf.fn_closeJNotifyMsg('#jNotifyMessage'); // 关闭消息提示
				arr_dataArr = arr_locations;
				
				dlf.fn_caculateBox(arr_locations);
				fn_startDrawLineStatic(arr_locations);
			}
		} else if ( data.status == 201 ) {	// 业务变更
			dlf.fn_showBusinessTip();
		} else { // 查询状态不正确,错误提示
			dlf.fn_jNotifyMessage(data.message, 'message');
		}
		dlf.fn_unLockScreen(); // 清除页面遮罩
		$('.j_trackbody').removeData('layer');
	});
}

/**
* 根据经纬度求两点间距离

function fn_forMarkerDistance(firstPoint, secondPoint) {
	var EarthRadiusKm = 6378137.0; // 取WGS84标准参考椭球中的地球长半径(单位:m)
	var dLat1InRad = firstPoint.lat/NUMLNGLAT * (Math.PI / 180);
	var dLong1InRad = firstPoint.lng/NUMLNGLAT * (Math.PI / 180);
	var dLat2InRad = secondPoint.lat/NUMLNGLAT * (Math.PI / 180);
	var dLong2InRad = secondPoint.lng/NUMLNGLAT * (Math.PI / 180);
	var dLongitude = dLong2InRad - dLong1InRad;
	var dLatitude = dLat2InRad - dLat1InRad;
	var a = Math.pow(Math.sin(dLatitude / 2), 2) + 
		Math.cos(dLat1InRad) * Math.cos(dLat2InRad) * 
		Math.pow(Math.sin(dLongitude / 2), 2);
	var c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
	var n_Distance = EarthRadiusKm * c;
	return n_Distance;
}
*/

/**
* 根据经纬度求两点间距离
*/
window.dlf.fn_forMarkerDistance = function (point1, point2) {
	var EARTHRADIUS = 6370996.81; // 取WGS84标准参考椭球中的地球长半径(单位:m)
	//判断类型
	/*if(!(point1 instanceof BMap.Point) ||
		!(point2 instanceof BMap.Point)){
		return 0;
	}*/
	
	/*point1.lng = fn_getLoop(point1.lng, -180, 180);
	point1.lat = fn_getRange(point1.lat, -74, 74);
	point2.lng = fn_getLoop(point2.lng, -180, 180);
	point2.lat = fn_getRange(point2.lat, -74, 74);
	*/
	
	var x1, x2, y1, y2;
	x1 = dlf.degreeToRad(point1.lng);
	y1 = dlf.degreeToRad(point1.lat);
	x2 = dlf.degreeToRad(point2.lng);
	y2 = dlf.degreeToRad(point2.lat);

	return EARTHRADIUS * Math.acos((Math.sin(y1) * Math.sin(y2) + Math.cos(y1) * Math.cos(y2) * Math.cos(x2 - x1)));    
}

/**
 * 将度转化为弧度
 * @param {degree} Number 度     
 * @returns {Number} 弧度
 */
window.dlf.degreeToRad =  function(degree){
	return Math.PI * degree/180;    
}
/**
 * 将弧度转化为度
 * @param {radian} Number 弧度     
 * @returns {Number} 度
 */
window.dlf.radToDegree = function(rad){
	return (180 * rad) / Math.PI;       
}
/**
 * 将v值限定在a,b之间，纬度使用
 */
function fn_getRange(v, a, b){
	if(a != null){
	  v = Math.max(v, a);
	}
	if(b != null){
	  v = Math.min(v, b);
	}
	return v;
}

/**
 * 将v值限定在a,b之间，经度使用
 */
function fn_getLoop(v, a, b){
	while( v > b){
	  v -= b - a
	}
	while(v < a){
	  v += b - a
	}
	return v;
}

/**
* 显示停留点数据信息
*/
function fn_printDelayDatas(arr_delayPoints, obj_firstMarker, obj_endMarker) {
	var n_delayLength = arr_delayPoints.length,
		obj_table = $('.delayTable'),
		arr_markers = [];
		str_html = '';
	
	if ( n_delayLength > 0 ) {
		var obj_first = arr_delayPoints[0],
			obj_second = arr_delayPoints[1];
		
		arr_markers.push(obj_firstMarker);
		arr_markers.push(obj_endMarker);
		// str_html += '<thead><tr><td>事件</td><td class="delayCenterTd">时间(开始)</td><td class="delayCenterTd">位置</td></tr></thead>';
		
		str_html += '<tr><td><img src="../static/images/green_MarkerA.png" width="25px" />起点</td><td class="delayCenterTd">'+ dlf.fn_changeNumToDateString(obj_first.timestamp)+'</td><td class="delayCenterTd">'+ obj_first.name +'</td></tr>';
		
		str_html += '<tr><td><img src="../static/images/green_MarkerB.png" width="25px" />终点</td><td class="delayCenterTd">'+ dlf.fn_changeNumToDateString(obj_second.timestamp) +'</td><td class="delayCenterTd">'+ obj_second.name +'</td></tr>';
		
		for ( var x = 2; x < n_delayLength; x++ ) {
			var obj_point = arr_delayPoints[x],
				obj_tempMarker = {};
			
			obj_tempMarker = dlf.fn_addMarker(obj_point, 'delay', 0, false, 0);
			
			str_html += '<tr><td width="130px"><img src="../static/images/delay_Marker.png" width="25px" /><label>停留'+ dlf.fn_changeTimestampToString(obj_point.idle_time) +'</label></td><td width="130px" class="delayCenterTd">'+ dlf.fn_changeNumToDateString(obj_point.start_time) +'</td><td width="270px" class="delayCenterTd">'+ obj_point.name +'</td></tr>';
			arr_markers.push(obj_tempMarker);
			
		}
	}
	obj_table.data('markers', arr_markers);
	$('.j_delayTbody').html(str_html);

	/** 
	* 初始化奇偶行
	*/
	$('.delayTable tbody tr').mouseover(function() {
		$(this).css({'background-color': '#FFFACD', 'cursor': 'pointer'});
	}).mouseout(function() {
		$(this).css('background-color', '');
	}).click(function() {
		var arr_markerList = $('.delayTable').data('markers'),
			obj_this = $(this),
			n_index = obj_this.index(),
			obj_tempMarker = arr_markerList[n_index];
		
		for ( var i = 0; i < arr_markerList.length; i++ ) {
			var obj_marker = arr_markerList[i];
			
			if ( obj_marker ) {
				obj_marker.setTop(false);
			}
		}
		obj_tempMarker.setTop(true);
		obj_tempMarker.openInfoWindow(obj_tempMarker.selfInfoWindow);
		mapObj.setCenter(obj_tempMarker.getPosition());
		
		obj_this.addClass('clickedBg').siblings('tr').removeClass('clickedBg');	// 添加背景色
	});	
}

/**
* 添加轨迹线和轨迹点
*/
function fn_startDrawLineStatic(arr_dataArr) {
	$('#tPlay, #trackSpeed').css('display', 'inline-block');
	var arr = new Array(), //经纬度坐标数组 
		obj_firstMarker = {},
		obj_endMarker = {};
	
	var polyline = dlf.fn_createPolyline($('#trackHeader').data('points'), {color: '#150CFF'});	//通过经纬度坐标数组及参数选项构建多折线对象，arr是经纬度存档数组 
	
	obj_firstMarker = dlf.fn_addMarker(arr_dataArr[0], 'start', 0, false, 0); // 添加标记
	obj_endMarker = dlf.fn_addMarker(arr_dataArr[arr_dataArr.length - 1], 'end', 0, false, arr_dataArr.length - 1); // 添加标记
	
	// 如果是集团用户的轨迹查询 显示停留点数据信息
	if ( dlf.fn_userType() ) {
		// 添加停留点marker
		var arr_delayPoints = $('#trackHeader').data('delayPoints'),
			arr_tempDelay = [];
		
		if ( arr_delayPoints ) { // 如果有停留点,进行显示
			arr_tempDelay.push(arr_dataArr[0]);
			arr_tempDelay.push(arr_dataArr[arr_dataArr.length - 1]);
			for ( var x = 0; x < arr_delayPoints.length; x++ ) {
				arr_tempDelay.push(arr_delayPoints[x]);
			}
			fn_printDelayDatas(arr_tempDelay, obj_firstMarker, obj_endMarker);	// 显示停留数据
		}
	}
	arr_drawLine.push(dlf.fn_createMapPoint(arr_dataArr[0].clongitude, arr_dataArr[0].clatitude));

	fn_createDrawLine();
}

/**
* 动态标记显示
*/
function fn_markerAction() { 
	$('#tPlay').unbind('mousedown');
	window.setTimeout(fn_drawMarker, 100);	// 先添加第一个点的marker
	timerId = window.setInterval(fn_drawMarker, n_speed);	// 按照设置播放速度播放轨迹点
}

/**
* 轨迹查询暂停播放动画操作
*/
function fn_trackQueryPause() {
	if ( timerId ) { dlf.fn_clearInterval(timerId) };
	str_actionState = counter;
}

/**
* 绑定播放按钮的事件
*/
function fn_bindPlay() {
	$('#tPlay').unbind('mousedown').bind('mousedown', fn_markerAction);
}

/**
* 动态标记移动方法
*/
function fn_drawMarker() {
	var n_len = arr_dataArr.length;
		
	if ( str_actionState != 0 ) {
		counter = str_actionState;
		str_actionState = 0;
	}
	if ( counter <= n_len-1 ) {
		if ( actionMarker ) {
			b_trackMsgStatus = actionMarker.selfInfoWindow.isOpen();	// 百度获取infowindow的状态
			dlf.fn_clearMapComponent(actionMarker);
		}
		dlf.fn_addMarker(arr_dataArr[counter], 'draw', 0, b_trackMsgStatus, counter); // 添加标记
		// 将播放过的点放到数组中
		var obj_tempPoint = dlf.fn_createMapPoint(arr_dataArr[counter].clongitude, arr_dataArr[counter].clatitude);
		
		arr_drawLine.push(obj_tempPoint);
		obj_drawLine.setPath(arr_drawLine);
		
		if ( b_trackMsgStatus ) {
			actionMarker.openInfoWindow(actionMarker.selfInfoWindow); // 显示吹出框 
		}
		dlf.fn_boundContainsPoint(obj_tempPoint);
		counter ++;
	} else {	// 播放完成后
		b_trackMsgStatus = true;
		dlf.fn_clearTrack();	// 清除数据
		dlf.fn_clearMapComponent(actionMarker);
		actionMarker = null;
		$('#tPause').hide();
		$('#tPlay').css('display', 'inline-block');
	}
}

/**
* 初始化播放过的线对象
*/
function fn_createDrawLine () {
	obj_drawLine = dlf.fn_createPolyline(arr_drawLine, {'color': 'red'});
}

/**
* 关闭轨迹清除数据
*/
window.dlf.fn_clearTrack = function(clearType) { 
	if ( timerId ) { dlf.fn_clearInterval(timerId) };	// 清除计时器
	str_actionState = 0;
	counter = 0;
	arr_drawLine = [];
	if ( clearType == 'inittrack' ) {
		$('.j_trackBtnhover, .trackSpeed').hide();	// 播放速度、播放按钮隐藏
		dlf.fn_clearMapComponent(); // 清除页面图形
	}
}

/**
* 初始化时间控件
*/
window.dlf.fn_initTrackDatepicker = function() {	
	/**
	* 初始化轨迹查询选择时间
	*/
	var str_nowDate = dlf.fn_changeNumToDateString(new Date().getTime(), 'ymd'), 
		obj_stTime = $('#trackBeginTime'), 
		obj_endTime = $('#trackEndTime');
		
	obj_stTime.click(function() {	// 初始化起始时间，并做事件关联   maxDate: '#F{$dp.$D(\'trackEndTime\')}',   minDate:'#F{$dp.$D(\'trackBeginTime\')}', // delete in 2013.04.10
		WdatePicker({el: 'trackBeginTime', dateFmt: 'yyyy-MM-dd HH:mm:ss', readOnly: true, isShowClear: false, qsEnabled: false, 
			onpicked: function() {
				var obj_endDate = $dp.$D('trackEndTime'), 
					str_endString = obj_endDate.y+'-'+obj_endDate.M+'-'+obj_endDate.d+' '+obj_endDate.H+':'+obj_endDate.m+':'+obj_endDate.s,
					str_endTime = dlf.fn_changeDateStringToNum(str_endString), 
					str_beginTime = dlf.fn_changeDateStringToNum($dp.cal.getDateStr());
				if ( str_endTime - str_beginTime > WEEKMILISECONDS) {
					obj_endTime.val(dlf.fn_changeNumToDateString(str_beginTime + WEEKMILISECONDS));
				}
			}
		});
	}).val(dlf.fn_changeNumToDateString((new Date()-7200000)/1000));
	
	obj_endTime.click(function() {	// 初始化结束时间，并做事件关联
		WdatePicker({el: 'trackEndTime', dateFmt: 'yyyy-MM-dd HH:mm:ss', readOnly: true, isShowClear: false, qsEnabled: false, 
			onpicked: function() {
				var obj_beginDate = $dp.$D('trackBeginTime'), 
					str_beginString = obj_beginDate.y+'-'+obj_beginDate.M+'-'+obj_beginDate.d+' '+obj_beginDate.H+':'+obj_beginDate.m+':'+obj_beginDate.s,
					str_beginTime = dlf.fn_changeDateStringToNum(str_beginString), 
					str_endTime = dlf.fn_changeDateStringToNum($dp.cal.getDateStr());
				if ( str_endTime - str_beginTime > WEEKMILISECONDS) {
					obj_stTime.val(dlf.fn_changeNumToDateString(str_endTime - WEEKMILISECONDS));
				}
			}
		});
	}).val(dlf.fn_changeNumToDateString(new Date()/1000));
}

/**
* 页面加载完成后进行加载地图
*/
$(function () {	
	
	dlf.fn_initTrackDatepicker();	// 初始化时间控件
	$('.j_disPanelCon').unbind('mouseover mouseout click').bind('mouseover', function() {
		var b_panel = $('.j_delayPanel').is(':visible'),
			obj_arrowIcon = $('.j_arrowClick'),
			obj_this = $(this);
		
		if ( b_panel ) {
			obj_arrowIcon.css('backgroundPosition', '-45px -29px');
		} else {	// 关闭面板 鼠标移上去效果
			obj_arrowIcon.css('backgroundPosition', '-38px -29px');
		}
		obj_this.attr('title', '');
	}).bind('mouseout', function() {
		var b_panel = $('.j_delayPanel').is(':visible'),
			obj_arrowIcon = $('.j_arrowClick');
		
		if ( b_panel ) {
			obj_arrowIcon.css('backgroundPosition', '-20px -29px');
		} else {
			obj_arrowIcon.css('backgroundPosition', '-29px -29px');
		}
	}).bind('click', function() {
		var obj_panel = $('.j_delayPanel'),
			obj_arrowCon = $('.j_disPanelCon'),
			obj_arrowIcon = $('.j_arrowClick'),
			b_panel = obj_panel.is(':visible'),
			n_windowWidth = $(window).width(),
			n_delayIconLeft = n_windowWidth - 547;
		
		
		if ( n_windowWidth < 1500 ) {
			n_windowWidth = 1400;
			n_delayIconLeft = 853;
		}
		if ( b_panel ) {
			obj_panel.hide();
			n_delayIconLeft = n_windowWidth - 16;
			//obj_arrowCon.css({'right': '0px'});
			obj_arrowIcon.css('backgroundPosition', '-6px -29px');
		} else {
			obj_panel.show();
			//obj_arrowCon.css({'right': '529px'});
			obj_arrowIcon.css('backgroundPosition', '-20px -29px');
		}
		obj_arrowCon.css({'left': n_delayIconLeft});
	});
	/**
	* 按钮变色
	*/
	$('.j_trackBtnhover, #trackSearch, #trackClose').mouseover(function(event) {
		var str_id = event.currentTarget.id, 
			str_imgUrl = '';
		if ( str_id == 'trackSearch' ) {
			str_imgUrl = 'trackcx2.png';
		} else if ( str_id == 'tPlay' ) {
			str_imgUrl = 'bf2.png';
		} else if ( str_id == 'tPause' ) {
			str_imgUrl = 'zt2.png';
		} else if ( str_id == 'tStop' ) {
			str_imgUrl = 'tz2.png';
		} else {
			str_imgUrl = 'close_default.png';
		}
		$(this).css('background-image', 'url("'+ BASEIMGURL + str_imgUrl+'")');
	}).mouseout(function(event){
		var str_id = event.currentTarget.id, 
			str_imgUrl = '';
		if ( str_id == 'trackSearch' ) {
			str_imgUrl = 'trackcx1.png';
		} else if ( str_id == 'tPlay' ) {
			str_imgUrl = 'bf1.png';
		} else if ( str_id == 'tPause' ) {
			str_imgUrl = 'zt1.png';
		} else if ( str_id == 'tStop' ) {
			str_imgUrl = 'tz1.png';
		} else {
			str_imgUrl = 'close_default.png';
		}
		$(this).css('background-image', 'url("'+ BASEIMGURL + str_imgUrl+'")');
	}).click(function(event) {
		var str_id = event.currentTarget.id, 
			str_imgUrl = '';
		if ( str_id == 'trackSearch' ) { // 轨迹查询
			fn_trackQuery();
		} else if ( str_id == 'tPlay' ) { // 播放
			fn_markerAction();
			$(this).hide();
			$('#tPause').css('display', 'inline-block');
		} else if ( str_id == 'tPause' ) { // 暂停
			fn_trackQueryPause();
			$(this).hide();
			$('#tPlay').css('display', 'inline-block');
		} else {
			dlf.fn_closeTrackWindow(true);
		}
	});
	
	/**
	* 初始化速度滑块
	*/
	var arr_slide = [1000, 500, 200, 100], 
		arr_slideTitle = ['慢速', '一般速度', '比较快', '极速'];
	
	$('#trackSlide').slider({
		min: 0,
		max: 3,
		values: 2,
		range: false,
		slide: function (event, ui) {
			var n_val = ui.value;
			n_speed = arr_slide[n_val];
			$('#trackSlide').attr('title', arr_slideTitle[n_val]);
			if ( timerId ) { dlf.fn_clearInterval(timerId) };
			var obj_tplay = $('#tPlay'),
				str_ishidden = obj_tplay.is(':hidden');
			if ( str_ishidden ) {	// 如果播放按钮不可用
				fn_markerAction();
			}
		}
	}).slider('option', 'value', 2);
})