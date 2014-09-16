/*
*单程起点查看详情
*/
$(function () {
	var arr_drawLine = [],
		arr_dataArr = [],
		str_actionState = 0,
		actionMarker = null,
		n_singleCounter = 0,
		timerId = 0,
		n_speed = 200,
		obj_drawLine = null;
	/**
	* 初始化速度滑块
	*/
	var arr_slide = [1000, 500, 200, 100], 
		arr_slideTitle = ['慢速', '一般速度', '比较快', '极速'];
	
	$('#singleSlide').slider({
		min: 0,
		max: 3,
		values: 2,
		range: 'min',
		animate: true,
		slide: function (event, ui) {
			var n_val = ui.value;
			
			n_speed = arr_slide[n_val];
			
			$('#singleSlide').attr('title', arr_slideTitle[n_val]);
			if ( timerId ) { clearInterval(timerId) };
			var obj_tplay = $('#singlePlay'),
				str_ishidden = obj_tplay.is(':hidden');
			
			if ( str_ishidden ) {	// 如果播放按钮不可用
				fn_markerAction();
			}
		}
	}).slider('option', 'value', 2);
	
	$('#singlePause').hide();
	
	$('.j_singleBtnhover').click(function(event) {
		var str_id = event.currentTarget.id;
		
		if ( str_id == 'singlePlay' ) { // 播放
			fn_markerAction();
			$(this).hide();
			$('#singlePause').css('display', 'inline-block');
		} else if ( str_id == 'singlePause' ) { // 暂停
			fn_trackQueryPause();
			$(this).hide();
			$('#singlePlay').css('display', 'inline-block');
		} else if ( str_id == 'singlePrev' ) { // 上一个点
			if ( n_singleCounter > 0 ) {
				arr_drawLine.pop();
				arr_drawLine.pop();
				fn_drawMarker('prev');
			}
		} else if ( str_id == 'singleNext' ) { // 下一个点
			fn_drawMarker('next');
		}
	});
// init single
dlf.fn_initSigleDetail = function (n_singleId, n_startTime, n_endTime) {
	var str_tid = $('#selectTerminals2').val(),
		obj_locusDate = {'tid': str_tid, 'start_time': n_startTime,'end_time': n_endTime};
	
	dlf.fn_setMapPosition(true);
	dlf.fn_ShowOrHideMiniMap(true, 'single');
	dlf.fn_clearSingleAction();
	dlf.fn_clearMapComponent();
	dlf.fn_lockScreen();
	// 关闭小地图
	$('.eventMapClose').unbind('click').bind('click', function() {
		dlf.fn_clearMapComponent();
		dlf.fn_clearSingleAction();
		dlf.fn_ShowOrHideMiniMap(false);
		$('#singleControl_panel').hide();
		$('#singlePause').hide();
		dlf.fn_unLockScreen();
	});
	$.ajax({
		type : 'post',
		url : '/track',
		data: JSON.stringify(obj_locusDate),
		dataType : 'json',
		cache: false,
		contentType : 'application/json; charset=utf-8',
		success : function(data) {
			if ( data.status == 0 ) {
				var arr_locations = data.track, 
					locLength = arr_locations.length,
					arr_calboxData = [],
					str_alias = $('.j_carList a[tid='+ str_tid +']').attr('alias');
				
				if ( $('.mapDragTitle').is(':hidden') ) {
					return;
				}
				if ( locLength <= 0) {
					alert('该段时间没有单程轨迹，请尝试其他时间段。');
				} else {
					$('#singleControl_panel').css('display', 'inline-block');
					$('#singlePause').hide();
					for ( var x = 0; x < locLength; x++ ) {
						arr_locations[x].alias = str_alias;
						arr_locations[x].tid = str_tid;
						arr_calboxData.push(dlf.fn_createMapPoint(arr_locations[x].clongitude, arr_locations[x].clatitude));
					}
					arr_dataArr = arr_locations;
					
					mapObj.setViewport(arr_calboxData);
					
					$('#singleControl_panel').data({'points': arr_calboxData, 'trackdata': arr_dataArr});
					fn_startDrawLineStatic(arr_locations);
				}		
			} else {
				alert(data.message);
				window.close();
			}
		},
		error : function(xyResult) {
			alert('error');
			window.close();
			return;
		}
	});
	fn_getSingleDetail(n_singleId);
}
//查询单程信息并显示
function fn_getSingleDetail(n_singleId) {
	$.ajax({
		type : 'get',
		url : '/single?single_id='+n_singleId,
		data: '',
		dataType : 'json',
		cache: false,
		contentType : 'application/json; charset=utf-8',
		success : function(data) {
			if ( data.status == 0 ) {
				$('#corpMileageSetWrapper').data('mileage_set', true);
				dlf.fn_displayMapShape(data.res, false);
				
				$('#mapConTitle').html('单程起点：'+data.res.single_name);
			} else {
				alert(data.message);
				window.close();
			}
		},
		error : function(xyResult) {
			alert('error');
			window.close();
			return;
		}
	});
}

/**
* 添加轨迹线和轨迹点
*/
function fn_startDrawLineStatic(arr_dataArr) {
	$('#singlePlay, #singlePrev, #singleNext').css('display', 'inline-block');
	var obj_firstMarker = {},
		obj_endMarker = {},
		arr_markers = [];
	
	var polyline = dlf.fn_createPolyline($('#singleControl_panel').data('points'), {color: '#150CFF'});	//通过经纬度坐标数组及参数选项构建多折线对象，arr是经纬度存档数组 
	
	obj_firstMarker = dlf.fn_addMarker(arr_dataArr[0], 'singlestart', 0, 0); // 添加标记
	obj_endMarker = dlf.fn_addMarker(arr_dataArr[arr_dataArr.length - 1], 'singleend', 0, 1); //添加标记
	//存储起终端点以便没有位置时进行位置填充
	arr_markers.push(obj_firstMarker);
	arr_markers.push(obj_endMarker);
	$('#singleControl_panel').data('markers', arr_markers);
	
	arr_drawLine.push(dlf.fn_createMapPoint(arr_dataArr[0].clongitude, arr_dataArr[0].clatitude));
	
	fn_createDrawLine();
}
/**
* 动态标记显示
*/
function fn_markerAction() { 
	$('#singlePlay').unbind('mousedown');
	window.setTimeout(fn_drawMarker, 100);	// 先添加第一个点的marker
	timerId = window.setInterval(fn_drawMarker, n_speed);	// 按照设置播放速度播放轨迹点
}

/**
* 轨迹查询暂停播放动画操作
*/
function fn_trackQueryPause() {
	if ( timerId ) { clearInterval(timerId) };
	str_actionState = n_singleCounter;
}

/**
* 绑定播放按钮的事件
*/
function fn_bindPlay() {
	$('#singlePlay').unbind('mousedown').bind('mousedown', fn_markerAction);
}

/**
* 动态标记移动方法
*/
function fn_drawMarker(str_step) {
	var arr_tempDataArr = $('#singleControl_panel').data('trackdata'),
		n_len = arr_tempDataArr.length,
		str_tid = $('#selectTerminals2').val(),
		obj_selfInfoWindow = null;
	
	if ( str_actionState != 0 ) {
		n_singleCounter = str_actionState;
		str_actionState = 0;
	}
	// 对要播放的点进行计步
	if ( str_step ) {	
		if ( str_step ==  'next' ) {
			n_singleCounter++;
		} else {
			n_singleCounter--;
		}
	} else {
		n_singleCounter++;
	}
	
	if ( n_singleCounter <= n_len-1 ) {
		if ( actionMarker ) {
			obj_selfInfoWindow = actionMarker.infoWindow;
			mapObj.removeOverlay(actionMarker);
		}
		arr_tempDataArr[n_singleCounter].tid = str_tid;	// 轨迹播放传递tid
		actionMarker = dlf.fn_addMarker(arr_tempDataArr[n_singleCounter], 'singledraw', 0, n_singleCounter); // 添加标记
		// 将播放过的点放到数组中
		var obj_tempPoint = dlf.fn_createMapPoint(arr_tempDataArr[n_singleCounter].clongitude, arr_tempDataArr[n_singleCounter].clatitude);
		
		arr_drawLine.push(obj_tempPoint);
		obj_drawLine.setPath(arr_drawLine);
		counter = n_singleCounter;
		
		if ( obj_selfInfoWindow ) {
			dlf.fn_createMapInfoWindow(arr_tempDataArr[n_singleCounter], 'singledraw', n_singleCounter);
			actionMarker.openInfoWindow(obj_mapInfoWindow); // 显示吹出框 
		}
		dlf.fn_boundContainsPoint(obj_tempPoint);
	} else {	// 播放完成
		dlf.fn_clearSingleAction();	// 清除数据
		mapObj.removeOverlay(actionMarker);
		actionMarker = null;
		$('#singlePause').hide();
		$('#singlePlay').css('display', 'inline-block');
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
dlf.fn_clearSingleAction = function(clearType) { 
	if ( timerId ) { clearInterval(timerId) };	// 清除计时器
	str_actionState = 0;
	n_singleCounter = -1;
	arr_drawLine = [];
}

});