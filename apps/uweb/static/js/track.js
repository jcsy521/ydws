/*
*轨迹查询相关操作方法
*/
/**
*开始动态效果
*timerId : 动态时间控制器
*counter : 动态运行次数
*str_actionState : 暂停操作的状态
*/
var timerId = null, counter = 0, str_actionState = 0,n_speed = 1000, f_trackMsgStatus = false;
// 初始化轨迹显示页面
window.dlf.fn_initTrack = function() {
	$('#POISearchWrapper').hide();  // 关闭周边查询
	dlf.fn_clearInterval(currentLastInfo); // lastinfo关闭
	dlf.fn_clearInterval(timerId);//计时器关闭
	dlf.fn_clearMapComponent(); // 清除页面图形
	$('#carList a[class*=currentCar]').removeData('selfmarker');	// 清除marker
	$('#carList .currentCar').removeAttr('actiontrack');	// 移除 开始追踪
	// 查询条件初始化
	$('.j_tBtnhover, .trackSpeed').hide();	
	$('#trackHeader').show();	// 轨迹查询条件显示
}
// 关闭轨迹显示页面
window.dlf.fn_closeTrackWindow = function() {
	dlf.fn_clearInterval(timerId);
	dlf.fn_clearMapComponent(); // 清除页面图形
	$('#trackHeader').hide();
	dlf.fn_updateLastInfo($($('#carList li[class*=currentCar]')).attr('tid'));// 动态更新终端相关数据
	dlf.fn_closeJNotifyMsg('#jNotifyMessage'); // 关闭消息提示
}
// 轨迹查询操作
function trackQuery() {
	$('.j_tBtnhover').hide();
	dlf.fn_clearInterval(currentLastInfo); // 清除定时器
	dlf.fn_clearMapComponent(); // 清除页面图形
	str_actionState = 0;
	var str_beginTime = $('#trackBeginTime').val(), 
		str_endTime = $('#trackEndTime').val(), 
	    obj_locusDate = {'start_time': dlf.fn_changeDateStringToNum(str_beginTime)/1000, 
						'end_time': dlf.fn_changeDateStringToNum(str_endTime)/1000, 
						'tid': $($('#carList a[class*=currentCar]')).attr('tid')}; //$('#trackHeader').attr('tid')};
	
	dlf.fn_jNotifyMessage('行踪查询中...<img src="/static/images/blue-wait.gif" />', 'message', true);
	dlf.fn_lockScreen('j_trackbody'); // 添加页面遮罩
	$('.j_trackbody').data('layer', true);
	dlf.fn_lockScreen();
	
	$.post_(TRACK_URL, JSON.stringify(obj_locusDate), function (data) {
		if ( data.status != 0 ) { // 查询状态不正确,错误提示
			dlf.fn_jNotifyMessage(data.message, 'message');
		} else {
			/**
			   * 获取最大和最小的差值
			   * n_tempMax 暂时存储与第一点的最大距离
			   * obj_tempMaxPoint 存储与每一点最大距离的数据
			*/
			var arr_locations = data.track;// data.track, 
				locLength = arr_locations.length;
			if ( locLength <= 0) {
				dlf.fn_jNotifyMessage('该时间段没有行踪数据，请选择其它时间段！', 'message', false, 3000);
				$('#trackSpeed').hide();	// 速度滑块隐藏
			} else {
				dlf.fn_closeJNotifyMsg('#jNotifyMessage'); // 关闭消息提示
				arr_dataArr = [], 
				n_tempMax = 0, 
				obj_tempMaxPoint = arr_locations[0];
				var obj_firstPoint = new BMap.Point(arr_locations[0].clongitude/NUMLNGLAT, arr_locations[0].clatitude/NUMLNGLAT);
				for (var i = 0; i < locLength; i++) {
					var obj_itemLoc = arr_locations[i], 
						obj_tempPoint = new BMap.Point(obj_itemLoc.clongitude/NUMLNGLAT, obj_itemLoc.clatitude/NUMLNGLAT);
					fn_tempDist(obj_firstPoint, obj_tempPoint); // 计算与第一个点距离
					arr_dataArr[i] = obj_itemLoc;
				}
				mapObj.setViewport([obj_firstPoint, obj_tempMaxPoint]);
				fn_startDrawLineStatic(arr_dataArr);
			}
		}
		dlf.fn_unLockScreen(); // 清除页面遮罩
		$('.j_trackbody').removeData('layer');
	});
}

//  两点距离计算
function fn_tempDist(startXY, endXY) {
	var n_pointDist = fn_forMarkerDistance(startXY, endXY);
	if ( n_pointDist > n_tempMax ) {
		n_tempMax = n_pointDist;
		obj_tempMaxPoint = endXY;
	}
}

// 根据经纬度求两点间距离
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

// 添加轨迹线和轨迹点
function fn_startDrawLineStatic(arr_dataArr) { 
	$('#tPlay, #trackSpeed').css('display', 'inline-block');
	var arr = new Array(); //经纬度坐标数组 
	for (var i = 0; i < arr_dataArr.length; i++) {
		arr.push(new BMap.Point(arr_dataArr[i].clongitude/NUMLNGLAT, arr_dataArr[i].clatitude/NUMLNGLAT));
		// dlf.fn_addMarker(arr_dataArr[i]); // 添加标记
	}
	var polyline = new BMap.Polyline(arr);//通过经纬度坐标数组及参数选项构建多折线对象，arr是经纬度存档数组 
	mapObj.addOverlay(polyline);//向地图添加覆盖物 
	
	// 添加开始和结束点标记
	dlf.fn_addMarker(arr_dataArr[0], 'start'); // 添加标记
	dlf.fn_addMarker(arr_dataArr[arr_dataArr.length - 1], 'end'); // 添加标记
	
}

// 动态标记显示
function fn_markerAction() { 
	$('#tPlay').unbind('mousedown');
	fn_stopDraw();
	window.setTimeout(fn_drawMarker, 100);
	timerId = window.setInterval(fn_drawMarker, n_speed);
}

// 轨迹查询暂停播放动画操作
function trackQueryPause() {
	if ( timerId ) { dlf.fn_clearInterval(timerId) };
	str_actionState = counter;
}

// 绑定播放按钮的事件
function fn_bindPlay() {
	$('#tPlay').unbind('mousedown').bind('mousedown', fn_markerAction);
}

// 停止动态效果
function fn_stopDraw() {
	if ( timerId ) { dlf.fn_clearInterval(timerId) };
	counter = 0;
	mapObj.removeOverlay(actionMarker);
}

// 动态标记移动方法
function fn_drawMarker() {
	var n_len = arr_dataArr.length;
	if ( str_actionState != 0 ) {
		counter = str_actionState;
		str_actionState = 0;
	}
	if ( counter <= n_len-1 ) {
		if ( actionMarker ) {
			f_trackMsgStatus = actionMarker.selfInfoWindow.isOpen();
			mapObj.removeOverlay(actionMarker);
		}
		dlf.fn_addMarker(arr_dataArr[counter], 'draw'); // 添加标记
		if ( f_trackMsgStatus ) {
			actionMarker.openInfoWindow(actionMarker.selfInfoWindow); // 显示吹出框
		}
		counter ++;
	} else {
		str_actionState = 0;
		fn_stopDraw();
		mapObj.removeOverlay(actionMarker);
		$('#tPause').hide();
		$('#tPlay').css('display', 'inline-block');
	}
}
// 页面加载完成后进行加载地图
$(function () {	
	// 初始化时间
	var str_nowDate = dlf.fn_changeNumToDateString(new Date().getTime(), 'ymd');
	$('#trackBeginTime').unbind('click').click(function() {
		WdatePicker({el:'trackBeginTime', dateFmt: 'yyyy-MM-dd HH:mm:ss', readOnly: true, isShowClear: false, maxDate: '#F{$dp.$D(\'trackEndTime\')}'});
	}).val(str_nowDate+' 00:00:00');
	$('#trackEndTime').unbind('click').click(function() {
		WdatePicker({el:'trackEndTime', dateFmt: 'yyyy-MM-dd HH:mm:ss', readOnly: true, isShowClear: false, minDate:'#F{$dp.$D(\'trackBeginTime\')}'});
	}).val(str_nowDate+' '+dlf.fn_changeNumToDateString(new Date(), 'sfm'));
	
	// 按钮变色
	$('.j_tBtnhover, #trackSearch, #trackClose').mouseover(function(event) {
		var str_id = event.currentTarget.id, 
			str_imgUrl = '';
		if ( str_id == 'trackSearch' ) {
			str_imgUrl = 'cx2.png';
		} else if ( str_id == 'tPlay' ) {
			str_imgUrl = 'bf2.png';
		} else if ( str_id == 'tPause' ) {
			str_imgUrl = 'zt2.png';
		} else if ( str_id == 'tStop' ) {
			str_imgUrl = 'tz2.png';
		} else {
			str_imgUrl = 'gb2.png';
		}
		$(this).css('background-image', 'url("/static/images/'+str_imgUrl+'")');
	}).mouseout(function(event){
		var str_id = event.currentTarget.id, 
			str_imgUrl = '';
		if ( str_id == 'trackSearch' ) {
			str_imgUrl = 'cx.png';
		} else if ( str_id == 'tPlay' ) {
			str_imgUrl = 'bf1.png';
		} else if ( str_id == 'tPause' ) {
			str_imgUrl = 'zt1.png';
		} else if ( str_id == 'tStop' ) {
			str_imgUrl = 'tz1.png';
		} else {
			str_imgUrl = 'gb1.png';
		}
		$(this).css('background-image', 'url("/static/images/'+str_imgUrl+'")');
	}).click(function(event) {
		var str_id = event.currentTarget.id, 
			str_imgUrl = '';
		if ( str_id == 'trackSearch' ) { // 轨迹查询
			trackQuery();
			fn_stopDraw();
			//fn_bindPlay();
		} else if ( str_id == 'tPlay' ) { // 播放
			fn_stopDraw();
			fn_markerAction();
			$(this).hide();
			$('#tPause').css('display', 'inline-block');
		} else if ( str_id == 'tPause' ) { // 暂停
			trackQueryPause();
			//fn_bindPlay();
			$(this).hide();
			$('#tPlay').css('display', 'inline-block');
		} else {
			dlf.fn_closeTrackWindow();
		}
		/*else if ( str_id == 'tStop' ) { // 停止
			str_actionState = 0;
			fn_stopDraw();
			fn_bindPlay();
			$('#tPause').hide();
			$('#tPlay').css('display', 'inline-block');
		}*/
	});
	// 初始化速度滑块
	var arr_slide = [1000, 500, 200, 100], 
		arr_slideTitle = ['慢速', '一般速度', '比较快', '极速'];
	
	$('#trackSlide').slider({
		min: 0,
		max: 3,
		values: 1,
		range: false,
		slide: function (event, ui) {
			var n_val = ui.value;
			n_speed = arr_slide[n_val];
			$('#trackSlide').attr('title', arr_slideTitle[n_val]);
			if ( timerId ) { dlf.fn_clearInterval(timerId) };
			$('#tPlay').hide();
			$('#tPause').css('display', 'inline-block');
			fn_markerAction();
		}
	}).slider('option', 'value', 2);
	
})