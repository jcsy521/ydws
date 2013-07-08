/*
* 线路管理及绑定相关操作方法
*/
// 根据终端tid获得终端绑定的线路
window.dlf.fn_initBindLine = function( str_tid, str_who ) {
	var str_getLineUrl = BINDLINE_URL+'?tid='+str_tid;
	
	$.get_(str_getLineUrl, '', function (data) {  
		if (data.status == 0) {
			var obj_line = data.line,
				obj_bindSelect = $('#bindLine_lineData'),
				obj_routLineName = $('#corp_routeLineName');
			
			if ( obj_line != '' ) {
				var str_lineName = obj_line.line_name, 
					str_lineId = obj_line.line_id;
				
				if ( str_who == 'bindLine' ) {
					obj_bindSelect.val(str_lineId).data('lineid', str_lineId);
				} else {
					obj_routLineName.html(str_lineName).css('color', '#000');
				}
			} else {
				obj_routLineName.html('暂无创建线路。').css('color', 'red');
				obj_bindSelect.removeData('lineid');
			}
			dlf.fn_closeJNotifyMsg('#jNotifyMessage');
		} else if ( data.status == 201 ) {	// 业务变更
			dlf.fn_showBusinessTip();
		} else { // 查询状态不正确,错误提示
			dlf.fn_jNotifyMessage(data.message, 'message', false, 5000);
		}
		dlf.fn_unLockContent(); // 清除内容区域的遮罩
	}, 
	function (XMLHttpRequest, textStatus, errorThrown) {
		dlf.fn_serverError(XMLHttpRequest);
	});
}

// 绑定车辆与线路
window.dlf.fn_routeLineBindEvent = function() {
	//显示窗口
	dlf.fn_dialogPosition('bindLine');	// 设置dialog的位置并显示
	dlf.fn_lockScreen(); // 添加页面遮罩
	
	var obj_currentCar = $($('.j_carList a[class*=j_currentCar]')),
		str_tmoile = obj_currentCar.attr('title'), 
		str_tid = obj_currentCar.attr('tid'), 
		obj_bindSelect = $('#bindLine_lineData');
	
	$('#bindLine_tMobile').html(str_tmoile); // 填充页面终端号码
	//获取所有线路信息并进行填充
	$.get_(GETLINES_URL, '', function (data) {  
		if (data.status == 0) {
			var str_lineSelectHtml = fn_createLineSelect(data.lines);
			
			obj_bindSelect.html(str_lineSelectHtml);
			//获取当前终端线路信息
			dlf.fn_initBindLine(str_tid, 'bindLine');
			
			dlf.fn_closeJNotifyMsg('#jNotifyMessage');
		} else if ( data.status == 201 ) {	// 业务变更
			dlf.fn_showBusinessTip();
		} else { // 查询状态不正确,错误提示
			dlf.fn_jNotifyMessage(data.message, 'message', false, 5000);
		}
		dlf.fn_unLockContent(); // 清除内容区域的遮罩
	}, 
	function (XMLHttpRequest, textStatus, errorThrown) {
		dlf.fn_serverError(XMLHttpRequest);
	});
	
	// 线路保存
	$('#bindLineSave').unbind('click').click(function(event) {
		var str_oldLineId = obj_bindSelect.data('lineid'), 
			str_currentLineId = obj_bindSelect.val(),
			obj_bindLineData = {'tid': str_tid, 'line_id': str_currentLineId};
		
		if ( str_currentLineId == '' ){
			dlf.fn_jNotifyMessage('请选择您要绑定的线路。', 'message', false, 3000);
			return;
		}
		if ( str_oldLineId ) {
			dlf.fn_jsonPut(BINDLINE_URL, obj_bindLineData, 'bindLine', '车辆与线路绑定中');
		} else {
			dlf.fn_jsonPost(BINDLINE_URL, obj_bindLineData, 'bindLine', '车辆与线路绑定中');
		}
	});
}

//=========================================================
// 根据指定的数据生成线的下拉框 
function fn_createLineSelect( arr_lines ) {
	var n_lines = arr_lines.length,
		str_selectHtml = '<option value="0">无</option>';
	
	for ( var i = 0; i< n_lines; i++ ) {
		var obj_tempArr = arr_lines[i];
		
		str_selectHtml += '<option value="' +obj_tempArr.line_id+ '">'+ obj_tempArr.line_name +'</option>';
	}
	return str_selectHtml; 
}

// 线路管理的初始化查询展示
window.dlf.fn_initRouteLine = function() {
	var str_routeLine = 'routeLine', 
		obj_routeLineWapper = $('#routeLineWrapper'), 
		obj_reouteLineAddWapper = $('#routeLineCreateWrapper'),
		b_mapType = dlf.fn_isBMap();
	
	dlf.fn_dialogPosition(str_routeLine);	// 设置dialog的位置并显示
	$('#routeLineContent').show();
	$('#routeLine_hos').removeClass('max').addClass('min').attr('title', '收起');
	dlf.fn_clearInterval(currentLastInfo); // 清除lastinfo计时器
	dlf.fn_clearTrack();	// 初始化清除数据
	dlf.fn_clearMapComponent(); // 清除页面图形
	//获取线路数据 
	dlf.fn_setSearchRecord(str_routeLine);
	dlf.fn_searchData(str_routeLine);
	//初始化事件
	dlf.fn_clickMapToAddMarker();
	dlf.fn_mapStopDraw();
	$('#routeLineCreate_clickMap').removeClass('routeLineBtnCurrent');
	// 新增线路事件侦听
	$('#routeLineCreateBtn').unbind('click').click(function(event){
		$('#createRouteLineName').val('');
		$('#routeLineCreate_clickMap').html('添加站点');
		obj_routeLineWapper.hide();
		dlf.fn_clearMapComponent(); // 清除页面图形
		obj_reouteLineAddWapper.css({'left': '250px', 'top': '160px'}).show();
		obj_routeLineMarker = {};
		if ( !b_mapType ) {	// 高德地图清除infowindow
			dlf.fn_clickMapToAddMarker();
		}
	});
	//关闭新增窗口
	$('#routeLineCreateClose').unbind('click').click(function(event){
		dlf.fn_initRouteLine(); // 重新显示线路
	});
	// 给保存线路,点击地图绑定事件
	$('#routeLineCreateBtnPanel a').unbind('click').click(function(event){
		var str_id = event.currentTarget.id;
		
		if ( str_id == 'routeLineCreate_save' ) { // 保存线路
			fn_saveRouteLineMarkers();
		} else if ( str_id == 'routeLineCreate_clickMap' ) { // 点击地图
			var str_addPointHtmlText = $(this).html();
			
			
			if ( str_addPointHtmlText == '添加站点' ) {
				$(this).html('取消添加');
				dlf.fn_mapStartDraw(true);
				$(this).addClass('routeLineBtnCurrent');
			} else {
				$(this).html('添加站点');
				//mapObj.removeEventListener('click', dlf.fn_mapClickFunction);
				dlf.fn_mapStopDraw(true);
				$(this).removeClass('routeLineBtnCurrent');
			}
		}
	});
}

/*
* 保存站点名称
*/
window.dlf.fn_saveClickWindowText = function(obj_guid, obj_clickSaveBtn) {
	var obj_markerPanel = obj_routeLineMarker[obj_guid], 
		str_stationName = $('#clickMarkerWindowText').val(),
		b_mapType = dlf.fn_isBMap();
	
	if ( obj_markerPanel ) { 
		var temp_marker = obj_markerPanel.marker;
		//todo 没有填写站点名称
		
		if ( str_stationName == '' ) {
			dlf.fn_jNotifyMessage('您还没有填写站点名称。', 'message', false, 3000);
			return;
		}
		obj_markerPanel.stationname = str_stationName;
		if ( b_mapType  ) {
			temp_marker.closeInfoWindow();
		} else {
			mapObj.clearInfoWindow();
		}
	}
}

/*
* 删除站点
*/
window.dlf.fn_delClickWindowText = function(obj_guid, obj_clickSaveBtn) {
	var obj_markerPanel = obj_routeLineMarker[obj_guid],
		b_mapType = dlf.fn_isBMap();
		
	if ( obj_markerPanel ) {
		var temp_marker = obj_markerPanel.marker;
		
		dlf.fn_clearMapComponent(temp_marker);
		if ( obj_markerPanel.infowindow && !b_mapType ) {	// 高德地图清除infowindow
			mapObj.clearInfoWindow();
		}
		delete obj_routeLineMarker[obj_guid];
	}
}

/*
* 保存站点及线数据
*/
function fn_saveRouteLineMarkers () {
	var str_lineName = $.trim($('#createRouteLineName').val()), 
		arr_stations = [],
		n_stationsNum = 0;
		obj_routeLineData = {'line_name': str_lineName, 'stations': arr_stations};
	
	if ( str_lineName == '' ) {
		dlf.fn_jNotifyMessage('您还没有填写线路名称。', 'message', false, 3000);
		return;
	}
	
	for ( var obj_mPanel in obj_routeLineMarker ) {
		var obj_markerPanel = obj_routeLineMarker[obj_mPanel];
		
		if ( obj_markerPanel ) {
			var temp_marker = obj_markerPanel.marker, 
				obj_mPoint = temp_marker.getPosition();
				str_stationName = obj_markerPanel.stationname, 
				obj_tempStation = {'name': str_stationName, 'seq': n_stationsNum, 'latitude': obj_mPoint.lat*NUMLNGLAT, 'longitude': obj_mPoint.lng*NUMLNGLAT };
			
			//todo 没有填写站点名称
			if ( str_stationName == '' ) {
				dlf.fn_jNotifyMessage('您还没有填写第'+ (n_stationsNum+1) +'个站点的名称。', 'message', false, 3000);
				return;
			}
			arr_stations[n_stationsNum++] = obj_tempStation;
		}
	}
	obj_routeLineData.stations = arr_stations;
	// 发送线请求数据
	dlf.fn_jsonPost(ROUTELINE_URL, obj_routeLineData, 'routeLineCreate', '线路数据保存中');
}

/*
* 查看线路的详细信息
*/
window.dlf.fn_detailRouteLine = function(n_id) {
	dlf.fn_clearMapComponent();
	var obj_lines = obj_routeLines[n_id], 
		obj_stations = obj_lines.stations;
	
	if ( obj_stations == '' ) {
		dlf.fn_jNotifyMessage('当前线路没有站点信息。', 'message', false, 3000);
		return;
	}
	$('#routeLine_hos').click();
	//添加线
	var n_stations = obj_stations.length, 
		arr_stationPoints = [];
	
	for ( var i = 0; i < n_stations; i++ ) {
		var obj_tempStation = obj_stations[i],
			obj_stationPoint = dlf.fn_createMapPoint(obj_tempStation.longitude, obj_tempStation.latitude);
		
		// 重构经纬度数据
		obj_tempStation.clongitude = obj_tempStation.longitude;
		obj_tempStation.clatitude = obj_tempStation.latitude;
		obj_stations[i] = obj_tempStation;
		
		dlf.fn_addRouteLineMarker(obj_tempStation);
		arr_stationPoints.push(obj_stationPoint);
	}
	// 重构数据并显示计算盒子数据
	dlf.fn_caculateBox(obj_stations);
	dlf.fn_createPolyline(arr_stationPoints);
	//添加线上的标记
}

/*
* 删除线路信息
*/
window.dlf.fn_deleteRouteLine = function(n_id) {
	if ( n_id ) {
		if ( confirm('确定要删除该线路吗？') ) {
			$.delete_(ROUTELINE_URL+'?ids='+n_id, '', function(data) {
				if ( data.status == 0 ) {
					$('#routeLineTable tr[id='+ n_id +']').remove();
					var n_trLength = $('#routeLineTable tr').length;

					if ( n_trLength <= 1 ) {
						$('#routeLinePage').hide();
						$('#routeLineTableHeader').after('<tr><td colspan="5" class="colorRed">没有查询到线路，请先创建。</td></tr>');
					}
					dlf.fn_clearMapComponent(); // 清除页面图形
					if ( !dlf.fn_isBMap() ) {	// 高德地图清除infowindow
						mapObj.clearInfoWindow();
					}
				} else {
					dlf.fn_jNotifyMessage(data.message, 'message', false, 3000);
					return;
				}
			});
		}
	}
}