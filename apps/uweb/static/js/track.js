/*
*轨迹查询相关操作方法
*/

/**
*开始动态效果
*timerId : 动态时间控制器
*counter : 动态运行次数
*str_actionState : 暂停操作的状态
*n_speed: 默认播放速度
*f_trackMsgStatus: 动态marker的吹出框是否显示
*/
var timerId = null, counter = 0, str_actionState = 0, n_speed = 200, f_trackMsgStatus = false,obj_drawLine = null, arr_drawLine = [];
/**
* 初始化轨迹显示页面
*/
window.dlf.fn_initTrack = function() {
	dlf.fn_initTrackDatepicker(); // 初始化时间控件
	$('#POISearchWrapper').hide();  // 关闭周边查询
	dlf.fn_clearInterval(currentLastInfo); // 清除lastinfo计时器
	dlf.fn_clearTrack('inittrack');	// 初始化清除数据
	$('#ceillid_flag').removeAttr('checked');
	$('#trackHeader').show();	// 轨迹查询条件显示
	dlf.fn_setMapControl(35); /*调整相应的地图控件及服务对象*/
}

/**
* 关闭轨迹显示页面
*/
window.dlf.fn_closeTrackWindow = function() {
	dlf.fn_clearMapComponent(); // 清除页面图形
	dlf.fn_clearTrack();	// 清除数据
	$('#trackHeader').hide();	// 轨迹查询条件隐藏
	/**
	* 清除地图后要清除车辆列表的marker存储数据
	*/
	var obj_cars = $('.j_carList .j_terminal'),
		obj_selfMarker = null,
		obj_carInfo = null; 
	
	$('.j_carList').removeData('carsData');
	obj_carsData = {};
	obj_selfmarkers = {};
	
	if ( !dlf.fn_userType() ) {
		dlf.fn_getCarData();	// 重新请求lastinfo
	} else {
		obj_oldData = {'gids': '', 'tids': '', 'n_gLen': 0};
		dlf.fn_corpGetCarData();
	}
	dlf.fn_updateLastInfo();// 动态更新定位器相关数据
	dlf.fn_closeJNotifyMsg('#jNotifyMessage'); // 关闭消息提示
	dlf.fn_setMapControl(10); /*调整相应的地图控件及服务对象*/
}

/**
* 轨迹查询操作
*/
function fn_trackQuery() {
	var str_beginTime = $('#trackBeginTime').val(), 
		str_endTime = $('#trackEndTime').val(),
		n_cellid_flag = $('#ceillid_flag').attr('checked') == 'checked' ? 1 : 0,
		obj_locusDate = {'start_time': dlf.fn_changeDateStringToNum(str_beginTime), 
						'end_time': dlf.fn_changeDateStringToNum(str_endTime),
						'cellid_flag': n_cellid_flag};
	
	dlf.fn_clearTrack();	// 清除数据
	$('.j_tBtnhover').hide();	// 播放按钮隐藏
	dlf.fn_clearInterval(currentLastInfo); // 清除lastinfo定时器
	dlf.fn_clearMapComponent(); // 清除页面图形
	dlf.fn_jNotifyMessage('车辆轨迹查询中' + WAITIMG, 'message', true);
	dlf.fn_lockScreen('j_trackbody'); // 添加页面遮罩
	$('.j_trackbody').data('layer', true);
	dlf.fn_lockScreen();
	
	$.post_(TRACK_URL, JSON.stringify(obj_locusDate), function (data) {
		if ( data.status == 0 ) {
			/**
			   * 获取最大和最小的差值
			   * n_tempMax 暂时存储与第一点的最大距离
			   * obj_tempMaxPoint 存储与每一点最大距离的数据
			   * obj_tempFirstPoint 存储与每最远点的数据
			*/
			var arr_locations =	data.track, 
				locLength = arr_locations.length,
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
				dlf.fn_closeJNotifyMsg('#jNotifyMessage'); // 关闭消息提示
				arr_dataArr = arr_locations, 
				n_tempMax = 0, 
				obj_tempMaxPoint = arr_locations[0];
				obj_tempFirstPoint = arr_locations[0];
				
				for (var i = 0; i < locLength; i++) {
					var obj_currentLoc = arr_locations[i], 
						obj_firstPoint = dlf.fn_createMapPoint(obj_currentLoc.clongitude, obj_currentLoc.clatitude);
						
					for ( var j = i + 1; j < locLength; j++ ) {
						var obj_itemLoc = arr_locations[j], 
							obj_tempPoint = dlf.fn_createMapPoint(obj_itemLoc.clongitude, obj_itemLoc.clatitude);
							
						fn_tempDist(obj_firstPoint, obj_tempPoint); // 计算与第一个点距离
					}
					arr_dataArr[i].alias = dlf.fn_userType() ? $('.j_currentCar').text() : $('.j_currentCar').next().html();
				}
				if ( n_tempMax <= 0 ) {
					dlf.fn_setOptionsByType('centerAndZoom', dlf.fn_createMapPoint(obj_tempFirstPoint.clongitude, obj_tempFirstPoint.clatitude), 18);
				} else {
					dlf.fn_setOptionsByType('viewport', [obj_tempFirstPoint, obj_tempMaxPoint]);
				}
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
*  两点距离比较
*/
function fn_tempDist(startXY, endXY) {
	var n_pointDist = dlf.fn_forMarkerDistance(startXY, endXY);
	if ( n_pointDist > n_tempMax ) {
		n_tempMax = n_pointDist;
		obj_tempFirstPoint = startXY;
		obj_tempMaxPoint = endXY;
	}
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
	if(!(point1 instanceof BMap.Point) ||
		!(point2 instanceof BMap.Point)){
		return 0;
	}

	point1.lng = fn_getLoop(point1.lng, -180, 180);
	point1.lat = fn_getRange(point1.lat, -74, 74);
	point2.lng = fn_getLoop(point2.lng, -180, 180);
	point2.lat = fn_getRange(point2.lat, -74, 74);
	
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
* 添加轨迹线和轨迹点
*/
function fn_startDrawLineStatic(arr_dataArr) {
	$('#tPlay, #trackSpeed').css('display', 'inline-block');
	var arr = new Array(); //经纬度坐标数组 
	
	for (var i = 0; i < arr_dataArr.length; i++) {
		arr.push(dlf.fn_createMapPoint(arr_dataArr[i].clongitude, arr_dataArr[i].clatitude));
	}
	var polyline = dlf.fn_createPolyline(arr);	//通过经纬度坐标数组及参数选项构建多折线对象，arr是经纬度存档数组 
	
	dlf.fn_addMarker(arr_dataArr[0], 'start', 0, false, 0); // 添加标记
	dlf.fn_addMarker(arr_dataArr[arr_dataArr.length - 1], 'end', 0, false, arr_dataArr.length - 1); // 添加标记
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
			f_trackMsgStatus = actionMarker.selfInfoWindow.isOpen();
			dlf.fn_clearMapComponent(actionMarker);
		}
		dlf.fn_addMarker(arr_dataArr[counter], 'draw', 0, false, counter); // 添加标记
		// 将播放过的点放到数组中
		arr_drawLine.push(dlf.fn_createMapPoint(arr_dataArr[counter].clongitude, arr_dataArr[counter].clatitude));
		obj_drawLine.setPath(arr_drawLine);
		
		if ( f_trackMsgStatus ) {
			actionMarker.openInfoWindow(actionMarker.selfInfoWindow); // 显示吹出框
		}
		counter ++;
	} else {	// 播放完成后
		dlf.fn_clearTrack();	// 清除数据
		dlf.fn_clearMapComponent(actionMarker);
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
		$('.j_tBtnhover, .trackSpeed').hide();	// 播放速度、播放按钮隐藏
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
		
	obj_stTime.click(function() {	// 初始化起始时间，并做事件关联
		WdatePicker({el: 'trackBeginTime', dateFmt: 'yyyy-MM-dd HH:mm:ss', readOnly: true, isShowClear: false, maxDate: '#F{$dp.$D(\'trackEndTime\')}', qsEnabled: false, 
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
		WdatePicker({el: 'trackEndTime', dateFmt: 'yyyy-MM-dd HH:mm:ss', readOnly: true, isShowClear: false, minDate:'#F{$dp.$D(\'trackBeginTime\')}', qsEnabled: false, 
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
	/**
	* 按钮变色
	*/
	$('.j_tBtnhover, #trackSearch, #trackClose').mouseover(function(event) {
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
			dlf.fn_closeTrackWindow();
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