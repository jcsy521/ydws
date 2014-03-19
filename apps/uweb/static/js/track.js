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
	dlf.fn_initTrackDatepicker(); // 初始化时间控件
	$('#POISearchWrapper').hide();  // 关闭周边查询
	dlf.fn_clearInterval(currentLastInfo); // 清除lastinfo计时器
	dlf.fn_clearTrack('inittrack');	// 初始化清除数据
	$('#ceillid_flag').removeAttr('checked');
	obj_trackHeader.show();	// 轨迹查询条件显示
	dlf.fn_setMapPosition(false);
	// 调整工具条和
	//dlf.fn_setMapControl(35); /*调整相应的地图控件及服务对象*/
	
	var str_tempAlias = $('.j_currentCar').attr('alias'),
		str_currentCarAlias = dlf.fn_encode(dlf.fn_dealAlias(str_tempAlias)),
		obj_trackPos = $('.trackPos');
	
	if ( dlf.fn_userType() ) {
		$('#trackTerminalAliasLabel').html(str_currentCarAlias).attr('title', str_tempAlias);
		obj_trackPos.css('width', 641);
		$('.j_delay').hide();
		$('.j_delayTbody').html('');
	} else {
		obj_trackPos.css('width', 530);
	}
}

window.dlf.fn_initPanel = function () {
	/**
	* 调整页面大小
	*/
	var n_windowWidth = $(window).width(),
		n_windowWidth = $.browser.version == '6.0' ? n_windowWidth <= 1400 ? 1400 : n_windowWidth : n_windowWidth,
		n_delayLeft = n_windowWidth - 550,
		n_delayIconLeft = n_delayLeft - 17,
		n_alarmLeft = n_windowWidth - 400,
		n_alarmIconLeft = n_alarmLeft - 17,
		obj_tree = $('#corpTree');
	
	if ( dlf.fn_userType() ) {	// 集团用户		
		if ( n_windowWidth < 1500 ) {
			n_delayLeft = 870;
			n_delayIconLeft = 853;
			n_alarmLeft = 1000;
			n_alarmIconLeft = 982;
		}
	}
	// 设置停留点列表的位置
	$('.j_delayPanel').css({'left': n_delayLeft});
	$('.j_disPanelCon').css({'left': n_delayIconLeft});
	$('.j_alarmPanel').css({'left': n_alarmLeft});
	$('.j_alarmPanelCon').css({'left': n_alarmIconLeft});
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
			
			//查找选中的终端,进行添加数据
			var obj_carDatas = $('.j_carList').data('carsData');
			
			$('.j_group .jstree-checked').each(function() {
				var obj_this = $(this),
					obj_current = obj_this.children('.j_terminal'),
					str_tid = obj_current.attr('tid'),
					obj_tempCarData = obj_carDatas[str_tid];
				
				if ( obj_tempCarData ) {
					dlf.fn_updateInfoData(obj_carDatas[str_tid]);
				}
			});			
			dlf.fn_corpLastinfoSwitch(true);
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
		str_tid = dlf.fn_getCurrentTid(),
		str_alias = $('.j_carList a[tid='+ str_tid +']').attr('alias'),
		b_userType = dlf.fn_userType();	// 个人用户或者集团用户
	
	if ( str_beginTime >= str_endTime ) {
		dlf.fn_jNotifyMessage('开始时间不能大于结束时间，请重新选择时间段。', 'message', false, 3000);
		return;
	}
	dlf.fn_clearTrack();	// 清除数据
	$('.j_trackBtnhover').hide();	// 播放按钮隐藏
	dlf.fn_clearInterval(currentLastInfo); // 清除lastinfo定时器
	dlf.fn_clearMapComponent(); // 清除页面图形
	dlf.fn_jNotifyMessage('定位器轨迹查询中' + WAITIMG, 'message', true);
	dlf.fn_lockScreen('j_trackbody'); // 添加页面遮罩
	$('.j_trackbody').data('layer', true);
	dlf.fn_lockScreen();
	
	obj_trackHeader.removeData('delayPoints');	// 清除停留点缓存数据
	// 集团用户显示查询结果面板
	obj_delayCon.hide();
	$('#trackSpeed').hide();	// 速度滑块隐藏
	obj_locusDate.tid = str_tid;
	
	b_trackMsgStatus = true;
	actionMarker = null;
	$.post_(TRACK_URL, JSON.stringify(obj_locusDate), function (data) {
		if ( data.status == 0 ) {
			var arr_locations = data.track, 
				locLength = arr_locations.length,
				str_downloadHash = data.hash_,	// 下载停留点的hash参数
				str_msg = ''.
				arr_calboxData = [];
				
			if ( locLength <= 0) {
				if ( obj_locusDate.cellid_flag == 0 ) {	// 如果没有勾选基站定位
					str_msg = '该时间段没有轨迹记录，请尝试选择“显示基站定位”。';
				} else {
					str_msg = '该时间段没有轨迹记录，请选择其它时间段。';
				}
				dlf.fn_jNotifyMessage(str_msg, 'message', false, 3000);
			} else {
				// 集团用户显示查询结果面板
				var arr_idlePoints = data.idle_points;
				
				if ( b_userType ) {
					if ( arr_idlePoints.length > 0 ) {
						obj_delayCon.show();
						dlf.fn_initPanel();
						$('.j_delayPanel').show();
						// 存储停留点信息
						obj_trackHeader.data('delayPoints', arr_idlePoints);
					}
				}
				
				$('#exportDelay').attr('href', TRACKDOWNLOAD_URL + '?hash_=' + str_downloadHash);
				dlf.fn_closeJNotifyMsg('#jNotifyMessage'); // 关闭消息提示
				for ( var x = 0; x < locLength; x++ ) {
					arr_locations[x].alias = str_alias;
					arr_locations[x].tid = str_tid;
					arr_calboxData.push(dlf.fn_createMapPoint(arr_locations.clongitude, arr_locations.clatitude));
				}
				arr_dataArr = arr_locations;
				
				//dlf.fn_caculateBox(arr_locations);
				$('#trackHeader').data('points', arr_calboxData);
				dlf.fn_setOptionsByType('viewport', arr_calboxData);
				fn_startDrawLineStatic(arr_locations);
			}
		} else if ( data.status == 201 ) {	// 业务变更
			dlf.fn_showBusinessTip();
		} else { // 查询状态不正确,错误提示
			dlf.fn_jNotifyMessage(data.message, 'message');
		}
		dlf.fn_unLockScreen(); // 清除页面遮罩
		$('.j_trackbody').removeData('layer');
	}, 
	function (XMLHttpRequest, textStatus, errorThrown) {
		dlf.fn_serverError(XMLHttpRequest);
	});
}

/**
* 根据经纬度求两点间距离
*/
window.dlf.fn_forMarkerDistance = function (point1, point2) {
	// Based on http://www.ngs.noaa.gov/PUBS_LIB/inverse.pdf
	// using the "Inverse Formula" (section 4)
	var EARTHRADIUS = 6370996.81,  // 取WGS84标准参考椭球中的地球长半径(单位:m)
		lon1 = point1.lng,
		lon2 = point2.lng,
		lat1 = point1.lat,
		lat2 = point2.lat,
		MAXITERS = 20;
		
	// Convert lat/long to radians
	lat1 = lat1 * Math.PI / 180.0;
	lat2 = lat2 * Math.PI / 180.0;
	lon1 = lon1 * Math.PI / 180.0;
	lon2 = lon2 * Math.PI / 180.0;

	var a = 6378137.0, // WGS84 major axis
		b = 6356752.3142, // WGS84 semi-major axis
		f = (a - b) / a,
		aSqMinusBSqOverBSq = (a * a - b * b) / (b * b);

	var L = lon2 - lon1,
		A = 0.0,
		U1 = Math.atan((1.0 - f) * Math.tan(lat1)),
		U2 = Math.atan((1.0 - f) * Math.tan(lat2));

	var cosU1 = Math.cos(U1),
		cosU2 = Math.cos(U2),
		sinU1 = Math.sin(U1),
		sinU2 = Math.sin(U2),
		cosU1cosU2 = cosU1 * cosU2,
		sinU1sinU2 = sinU1 * sinU2;

	var sigma = 0.0,
		deltaSigma = 0.0,
		cosSqAlpha = 0.0,
		cos2SM = 0.0,
		cosSigma = 0.0,
		sinSigma = 0.0,
		cosLambda = 0.0,
		inLambda = 0.0;

	var lambda = L; // initial guess
	
	for (var iter = 0; iter < MAXITERS; iter++) {
		var lambdaOrig = lambda;
		
		cosLambda = Math.cos(lambda);
		sinLambda = Math.sin(lambda);
		var t1 = cosU2 * sinLambda,
			t2 = cosU1 * sinU2 - sinU1 * cosU2 * cosLambda,
			sinSqSigma = t1 * t1 + t2 * t2; // (14)
			
		sinSigma = Math.sqrt(sinSqSigma);
		cosSigma = sinU1sinU2 + cosU1cosU2 * cosLambda; // (15)
		sigma = Math.atan2(sinSigma, cosSigma); // (16)
		
		var sinAlpha = (sinSigma == 0) ? 0.0 : cosU1cosU2 * sinLambda
				/ sinSigma; // (17)
				
		cosSqAlpha = 1.0 - sinAlpha * sinAlpha;
		cos2SM = (cosSqAlpha == 0) ? 0.0 : cosSigma - 2.0 * sinU1sinU2
				/ cosSqAlpha; // (18)

		var uSquared = cosSqAlpha * aSqMinusBSqOverBSq; // defn
		
		A = 1 + (uSquared / 16384.0)
				* // (3)
				(4096.0 + uSquared
						* (-768 + uSquared * (320.0 - 175.0 * uSquared)));
						
		var B = (uSquared / 1024.0) * // (4)
				(256.0 + uSquared
						* (-128.0 + uSquared * (74.0 - 47.0 * uSquared)));
		var C = (f / 16.0) * cosSqAlpha
				* (4.0 + f * (4.0 - 3.0 * cosSqAlpha)); // (10)
		var  cos2SMSq = cos2SM * cos2SM;
		
		deltaSigma = B
				* sinSigma
				* // (6)
				(cos2SM + (B / 4.0)
						* (cosSigma * (-1.0 + 2.0 * cos2SMSq) - (B / 6.0)
								* cos2SM
								* (-3.0 + 4.0 * sinSigma * sinSigma)
								* (-3.0 + 4.0 * cos2SMSq)));

		lambda = L
				+ (1.0 - C)
				* f
				* sinAlpha
				* (sigma + C
						* sinSigma
						* (cos2SM + C * cosSigma
								* (-1.0 + 2.0 * cos2SM * cos2SM))); // (11)

		var delta = (lambda - lambdaOrig) / lambda;
		if (Math.abs(delta) < 1.0e-12) {
			break;
		}
	}
	return (b * A * (sigma - deltaSigma));
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
			obj_second = arr_delayPoints[1],
			str_startName = obj_first.name,
			str_tempStartName = str_startName.length > 20 ? str_startName.substr(0, 20) + '...' : str_startName,
			str_endName = obj_second.name,
			str_tempEndName = str_endName.length > 20 ? str_endName.substr(0, 20) + '...' : str_endName;
		
		arr_markers.push(obj_firstMarker);
		arr_markers.push(obj_endMarker);
		// str_html += '<thead><tr><td>事件</td><td class="delayCenterTd">时间(开始)</td><td class="delayCenterTd">位置</td></tr></thead>';
		
		str_html += '<tr><td><img src="../static/images/green_MarkerA.png" width="25px" />起点</td><td class="delayCenterTd">'+ dlf.fn_changeNumToDateString(obj_first.timestamp)+'</td><td class="delayCenterTd" title="'+ str_startName +'">'+ str_tempStartName +'</td></tr>';
		
		str_html += '<tr><td><img src="../static/images/green_MarkerB.png" width="25px" />终点</td><td class="delayCenterTd">'+ dlf.fn_changeNumToDateString(obj_second.timestamp) +'</td><td class="delayCenterTd" title="'+ str_endName +'">'+ str_tempEndName +'</td></tr>';
		
		for ( var x = 2; x < n_delayLength; x++ ) {
			var obj_point = arr_delayPoints[x],
				obj_tempMarker = {},
				str_name = obj_point.name,
				str_tempEndName = str_name.length > 18 ? str_name.substr(0, 18) + '...' : str_name;
			
			obj_tempMarker = dlf.fn_addMarker(obj_point, 'delay', 0, x);
			
			str_html += '<tr><td width="130px"><img src="../static/images/delay_Marker.png" width="25px" /><label>停留'+ dlf.fn_changeTimestampToString(obj_point.idle_time) +'</label></td><td width="130px" class="delayCenterTd">'+ dlf.fn_changeNumToDateString(obj_point.start_time) +'</td><td width="270px" class="delayCenterTd" title="'+ str_name +'">'+ str_tempEndName +'</td></tr>';
			arr_markers.push(obj_tempMarker);
		}
	}
	obj_table.data('markers', arr_markers);
	$('.j_delayTbody').html(str_html);
	if ( parseInt($.browser.version) <= 7 ) {
		$('.delayTable img').css('position', 'static');
	}

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
			obj_tempMarker = arr_markerList[n_index],
			str_trackType = 'delay',
			str_trackTempIndex = n_index;
		
		for ( var i = 0; i < arr_markerList.length; i++ ) {
			var obj_marker = arr_markerList[i];
			
			if ( obj_marker ) {
				obj_marker.setTop(false);
			}
		}
		obj_tempMarker.setTop(true);
		
		if ( n_index == 0 ) {
			str_trackType = 'start';
			str_trackTempIndex = 0;
		} else if ( n_index == 1 ) {
			str_trackType = 'end';
			str_trackTempIndex = arr_dataArr.length - 1;
		}
		dlf.fn_createMapInfoWindow(arr_delayPoints[n_index], str_trackType, str_trackTempIndex);
		obj_tempMarker.openInfoWindow(obj_mapInfoWindow);
		
		mapObj.setCenter(obj_tempMarker.getPosition());
		
		obj_this.addClass('clickedBg').siblings('tr').removeClass('clickedBg');	// 添加背景色
	});	
}

/**
* 添加轨迹线和轨迹点
*/
function fn_startDrawLineStatic(arr_dataArr) {
	$('#tPlay, #tPrev, #tNext, #trackSpeed').css('display', 'inline-block');
	var arr = new Array(), //经纬度坐标数组 
		obj_firstMarker = {},
		obj_endMarker = {},
		arr_markers = [];
	
	var polyline = dlf.fn_createPolyline($('#trackHeader').data('points'), {color: '#150CFF'});	//通过经纬度坐标数组及参数选项构建多折线对象，arr是经纬度存档数组 
	
	obj_firstMarker = dlf.fn_addMarker(arr_dataArr[0], 'start', 0, 0); // 添加标记
	obj_endMarker = dlf.fn_addMarker(arr_dataArr[arr_dataArr.length - 1], 'end', 0, arr_dataArr.length - 1); //添加标记
	//存储起终端点以便没有位置时进行位置填充
	arr_markers.push(obj_firstMarker);
	arr_markers.push(obj_endMarker);
	$('.delayTable').data('markers', arr_markers);
	
	// 如果是集团用户的轨迹查询 显示停留点数据信息
	if ( dlf.fn_userType() ) {
		// 添加停留点marker
		var arr_delayPoints = $('#trackHeader').data('delayPoints'),
			arr_tempDelay = [];
		
		if ( arr_delayPoints ) { // 如果有停留点,进行显示
			arr_tempDelay.push(arr_dataArr[0]);
			arr_tempDelay.push(arr_dataArr[arr_dataArr.length - 1]);
			
			$('#trackHeader').data('delayPoints', arr_tempDelay);
			
			for ( var x = 0; x < arr_delayPoints.length; x++ ) {
				arr_delayPoints[x].alias = $('.j_currentCar').attr('alias');
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
function fn_drawMarker(str_step) {
	var n_len = arr_dataArr.length,
		str_tid = $('.j_currentCar').attr('tid'),
		obj_selfInfoWindow = null;
	
	if ( str_actionState != 0 ) {
		counter = str_actionState;
		str_actionState = 0;
	}
	// 对要播放的点进行计步
	if ( str_step ) {	
		if ( str_step ==  'next' ) {
			counter++;
		} else {
			counter--;
		}
	} else {
		counter++;
	}
	
	if ( counter <= n_len-1 ) {
		if ( actionMarker ) {
			obj_selfInfoWindow = actionMarker.infoWindow;
			dlf.fn_clearMapComponent(actionMarker);
		}
		arr_dataArr[counter].tid = str_tid;	// 轨迹播放传递tid
		dlf.fn_addMarker(arr_dataArr[counter], 'draw', 0, counter); // 添加标记
		// 将播放过的点放到数组中
		var obj_tempPoint = dlf.fn_createMapPoint(arr_dataArr[counter].clongitude, arr_dataArr[counter].clatitude);
		
		arr_drawLine.push(obj_tempPoint);
		obj_drawLine.setPath(arr_drawLine);
			
		if ( obj_selfInfoWindow ) {
			dlf.fn_createMapInfoWindow(arr_dataArr[counter], 'draw', counter);
			actionMarker.openInfoWindow(obj_mapInfoWindow); // 显示吹出框 
		}
		dlf.fn_boundContainsPoint(obj_tempPoint);
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
	counter = -1;
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
		obj_endTime = $('#trackEndTime'),
		str_tempBeginTime = str_nowDate+' 00:00:00';
		
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
	}).val(str_tempBeginTime);
	
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
			n_delayIconLeft = n_windowWidth - 567;
		
		
		if ( n_windowWidth < 1500 ) {
			n_windowWidth = 1400;
			n_delayIconLeft = 853;
		}
		if ( b_panel ) {
			obj_panel.hide();
			n_delayIconLeft = n_windowWidth - 17;
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
		/*var str_id = event.currentTarget.id, 
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
		$(this).css('background-image', 'url("'+ BASEIMGURL + str_imgUrl+'")');*/
	}).mouseout(function(event){
		/*var str_id = event.currentTarget.id, 
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
		$(this).css('background-image', 'url("'+ BASEIMGURL + str_imgUrl+'")');*/
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
		} else if ( str_id == 'tPrev' ) { // 上一个点
			if ( counter > 0 ) {
				arr_drawLine.pop();
				arr_drawLine.pop();
				fn_drawMarker('prev');
			}
		} else if ( str_id == 'tNext' ) { // 下一个点
			fn_drawMarker('next');
		} else {
			dlf.fn_closeTrackWindow(true);
			dlf.fn_setMapPosition(false);
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