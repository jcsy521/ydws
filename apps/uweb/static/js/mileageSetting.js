/*
* 单程起点管理及绑定相关操作方法
*/

// 单程起点的初始化查询展示
dlf.fn_initMileageSet = function() {
	var str_mileageSet = 'corpMileageSet', 
		obj_mileageSetWapper = $('#corpMileageSetWrapper'), 
		obj_mileageSetAddWapper = $('#mileageSetCreateWrapper'),
		b_mapType = dlf.fn_isBMap();
	
	$('.j_alarm').hide();
	dlf.fn_dialogPosition(str_mileageSet);	// 设置dialog的位置并显示
	dlf.fn_mapRightClickFun(); //清除地图画围栏事件及状态 
	dlf.fn_clearInterval(currentLastInfo); // 清除lastinfo计时器
	dlf.fn_clearTrack();	// 初始化清除数据
	dlf.fn_clearMapComponent(); // 清除页面图形
	fn_displayCars(); // 显示车辆信息数据
	
	//获取单程起点
	dlf.fn_searchData(str_mileageSet);

	// 新增单程起点事件侦听
	$('#corpMileageSetCreateBtn').unbind('click').click(function(event){
		var n_circleNum = $('#corpMileageSetTable').data('regionnum');
			
		if ( n_circleNum ) {
			if ( n_circleNum >= 10 ) { //最多只能有十个单程起点
				dlf.fn_jNotifyMessage('单程起点最多只能创建10个。', 'message', false, 3000);
				return;
			}
		}
		obj_mileageSetWapper.hide();
		dlf.fn_clearRegionShape(); 
		
		obj_mileageSetAddWapper.css({'left': '305px', 'top': '160px'}).show();
		
		$('.regionCreateBtnPanel a').removeClass('regionCreateBtnCurrent');
		$('#mileageSetCreate_circle').addClass('regionCreateBtnCurrent');
		
		// 初始化画圆事件,并添加画圆事件
		dlf.fn_initCreateRegion();
	
		$('#createRegionName').val('');
		dlf.fn_clearMapComponent(); // 清除页面图形
		fn_displayCars(); // 显示车辆信息数据
		obj_regionShape =  null;
		
		if ( b_mapType ) {
			// 启动画图形事件
			dlf.fn_mapStartDraw();
		}
	});
	//关闭新增单程起点窗口
	$('#mileageSetCreateClose').unbind('click').click(function(event){
		if ( !b_mapType ) {
			dlf.fn_gaodeCloseDrawCircle();
		}
		dlf.fn_initMileageSet(); // 重新显示围栏管理 
	});
	//默认样式初始化
	$('.regionCreateBtnPanel a').removeClass('regionCreateBtnCurrent');
	
	// 给绘制圆形 多边形 绑定事件
	$('#mileageSetCreate_circle, #mileageSetCreate_polygon ').unbind('click').click(function(event){
		dlf.fn_mapRightClickFun();
		dlf.fn_closeJNotifyMsg('#jNotifyMessage');  // 关闭消息提示
		$('.regionCreateBtnPanel a').removeClass('regionCreateBtnCurrent');
		$(this).addClass('regionCreateBtnCurrent');
		
		if ( obj_drawingManager ) {
			//obj_drawingManager.open();
		} else {
			mousetool.close(true);	// 关闭鼠标画圆事件				
		}
		
		dlf.fn_initCreateRegion();
		if ( b_mapType ) {
			// 启动画图形事件
			dlf.fn_mapStartDraw();
		}
	});
	
	// 给拖动地图绑定事件
	$('#mileageSetCreate_dragMap').unbind('click').click(function(event){
		if ( !b_mapType ) {
			dlf.fn_gaodeCloseDrawCircle();
		} else {
			dlf.fn_mapRightClickFun();
		}
		$('.regionCreateBtnPanel a').removeClass('regionCreateBtnCurrent');
		$(this).addClass('regionCreateBtnCurrent');
	});
}

// 操作围栏不清除车辆
function fn_displayCars () {
	// 显示车辆信息数据
	var obj_carDatas = $('.j_carList').data('carsData');
		
	$('.j_group .jstree-checked').each(function() {
		var obj_this = $(this),
			str_tid = obj_this.children('.j_terminal').attr('tid'),
			obj_carInfo = obj_carDatas[str_tid],
			n_clon = obj_carInfo.clongitude,
			n_clat = obj_carInfo.clatitude;
		
		if ( n_clon != 0 && n_clat != 0 ) {
			dlf.fn_addMarker(obj_carInfo, 'region', str_tid); // 添加标记
		}
	});
}

/**
* 重新绘制图形
*/
dlf.fn_resetMileageSet = function(str_regionType) {
	dlf.fn_mapRightClickFun();
	if ( obj_drawingManager ) {
		dlf.fn_mapStartDraw();
	} else {
		dlf.fn_initCreateRegion();
	}
	$('.regionCreateBtnPanel a').removeClass('regionCreateBtnCurrent');
	
	var obj_regionCBtn = $('#mileageSetCreate_circle');
	
	if ( str_regionType == 'polygon' ) {
		obj_regionCBtn = $('#mileageSetCreate_polygon');
	} 
	
	obj_regionCBtn.addClass('regionCreateBtnCurrent');
}

/**
* 保存操作
*/
dlf.fn_saveMileageSet = function() {
	dlf.fn_mapStopDraw();
	var str_regionName = $.trim($('#createRegionName').val()), 
		n_radius = 0, 
		obj_regions = $('#corpMileageSetTable').data('regions'),
		n_circleNum = $('#corpMileageSetTable').data('regionnum'),
		str_tid = $('.j_currentCar').attr('tid'),
		obj_regionData = {};
		
	if ( n_circleNum ) {
		if ( n_circleNum >= 10 ) { //最多只能有十个电子单程起点
			dlf.fn_jNotifyMessage('单程起点最多只能创建10个。', 'message', false, 3000);
			return;
		}
		// 单程起点名称 重复性校验
		for ( var i = 0; i < n_circleNum; i++ ) {
			var obj_tempRegion = obj_regions[i], 
				str_tempRegionName = obj_tempRegion.single_name;
				
			if ( str_regionName == str_tempRegionName ) {
				dlf.fn_jNotifyMessage('起点名称已存在，请重新输入。', 'message', false, 3000);
				$('#createRegionName').addClass('borderRed');
				//dlf.fn_jNotifyMessage('单程起点名称与第'+ (i+1) +'个重复。', 'message', false, 3000);
				return;
			}
		}
	}
	if ( !obj_regionShape ) { 
		dlf.fn_jNotifyMessage('您还没有创建单程起点。', 'message', false, 3000);
		return;
	}
	if ( str_regionName == '' ) {
		dlf.fn_jNotifyMessage('您还没有填写单程起点名称。', 'message', false, 3000);
		$('#createRegionName').addClass('borderRed');
		return;
	} else {
		if ( str_regionName.length > 20 ) {
			dlf.fn_jNotifyMessage('单程起点名称长度不能大于20个字符。', 'message', false, 3000);
			$('#createRegionName').addClass('borderRed');
			return;
		}
		if ( !/^[\u4e00-\u9fa5A-Za-z0-9]+$/.test(str_regionName) ) {
			dlf.fn_jNotifyMessage('单程起点名称只能由中文、数字、英文组成。', 'message', false, 3000);
			$('#createRegionName').addClass('borderRed');
			return;
		}
	}
	$('#createRegionName').removeClass('borderRed');
	var obj_shapeData = dlf.fn_getShapeData(),
		arr_polygonData = [];
	
	obj_regionData.single_name = str_regionName;
	obj_regionData.single_shape = obj_shapeData.region_type;	
	if ( obj_shapeData.region_type == 1 ) { // 如果是多边形,对数据进行转换
		var arr_polygonTempPoints = obj_shapeData.points,
			n_lenPolygon = arr_polygonTempPoints.length;
		
		if ( n_lenPolygon <= 0 ) {
			dlf.fn_jNotifyMessage('请添加多边形区域！', 'message', false, 3000);
			return;
		}
		for ( var i = 0; i < n_lenPolygon; i++) {
			var obj_temPolygonPts = arr_polygonTempPoints[i];
			
			arr_polygonData.push({'latitude': parseInt(obj_temPolygonPts.lat*NUMLNGLAT), 'longitude': parseInt(obj_temPolygonPts.lng*NUMLNGLAT)});	
		}
		obj_regionData.polygon = arr_polygonData;
		
		if ( arr_polygonData.length < 3 ) {
			dlf.fn_jNotifyMessage('多边形单程起点最少需要3个点！', 'message', false, 3000);
			return;
		}
	} else { // 如果是圆
		var n_radius = obj_shapeData.circle.radius;

		if ( n_radius < 500 ) {
			dlf.fn_jNotifyMessage('圆形单程起点半径最小为500米！', 'message', false, 3000);
			return;
		}
		obj_regionData.circle = obj_shapeData.circle;
	}
	
	// 发送线请求数据
	dlf.fn_jsonPost(MILEAGE_SET_URL, obj_regionData, 'mileageSetCreate', '单程起点数据保存中');
	
}

/**
* 查看详细信息
*/
dlf.fn_detailMileageSet = function(n_seq) {
	var obj_regionDatas = $('#corpMileageSetTable').data('regions'),
		obj_regionData = obj_regionDatas[n_seq],	// 围栏类型 0: 圆形 1: 多边形
		n_id = obj_regionData.single_id,
		obj_currentSingleTr = $('#corpMileageSetTable tr[id='+ n_id +']');
	
	$('.j_mileateSetSearchtd, .j_bindMileateSetSearchtd').removeClass('bg4876ff').addClass('bgfff');
	$('#mileageSetDetailTdPanel'+n_id).removeClass('bgfff').addClass('bg4876ff');
	$('#bindMileageSetDetailTdPanel'+n_id).removeClass('bgfff').addClass('bg4876ff');
	
	$('.j_mileageSetSearchA, .j_bindMileageSetSearchA').css({'color': '#4876ff'});
	$('#mileageSetDetailPanel'+n_id).css({'color': '#000'});
	$('#bindMileageSetDetailPanel'+n_id).css({'color': '#000'});
	
	dlf.fn_changeTableBackgroundColor();
	
	$('#corpMileageSetWrapper').data('mileage_set', true);
	dlf.fn_clearRegionShape();
	dlf.fn_displayMapShape(obj_regionData, true);
	if ( dlf.fn_isBMap() ) {
		mapObj.closeInfoWindow();// 关闭吹出框 已显示圆
	} else {
		mapObj.clearInfoWindow();	// 高德infowindow不是图层需要单独关闭所有infowindow
	}
}

/**
* 删除
*/
dlf.fn_deleteMileageSet = function(n_id) {
	if ( n_id ) {
		if ( confirm('您确定要删除该起点吗？') ) {
			
			dlf.fn_lockScreen(); // 添加页面遮罩
			dlf.fn_jNotifyMessage('单程起点数据删除中' + WAITIMG, 'message', true);
			$.delete_(MILEAGE_SET_URL+'?single_ids='+n_id, '', function(data) {
				if ( data.status == 0 ) {
					var obj_regionTable = $('#corpMileageSetTable'),
						n_regionNums = obj_regionTable.data('regionnum'),
						obj_currentRegionTr = $('#corpMileageSetTable tr[id='+ n_id +']');
			
					obj_currentRegionTr.remove();
					obj_regionTable.data('regionnum', n_regionNums - 1);
					dlf.fn_clearRegionShape();
					dlf.fn_initMileageSet();
				}
				dlf.fn_jNotifyMessage(data.message, 'message', false, 3000);
				dlf.fn_unLockScreen(); // 去除页面遮罩
			}, 
			function (XMLHttpRequest, textStatus, errorThrown) {
				dlf.fn_serverError(XMLHttpRequest);
			});
		}
	}
}
/*
* 清除地图上显示的图形 
*/
dlf.fn_clearRegionShape = function() {
	if ( obj_regionShape ) {
		dlf.fn_clearMapComponent(obj_regionShape); // 清除页面图形
	}
}
//--------------bind mileageset----------------
/*
* 绑定初始化
*/
dlf.fn_initBindMileageSet = function() {
	var str_bindRegion = 'bindMileageSet',
		obj_currentCar = $($('.j_carList a[class*=j_currentCar]')),
		str_tid = obj_currentCar.attr('tid'),
		str_alias = obj_currentCar.attr('alias'),
		str_msg = '当前您还没有单程起点，请新增单程起点！',
		b_trackStatus = $('#trackHeader').is(':visible');	// 轨迹是否打开着
		
	if ( b_trackStatus ) {
		dlf.fn_closeTrackWindow(false);	// 关闭轨迹查询,不操作lastinfo
	}
	
	//填充当前终端tid
	$('#corpMileageSetForTerminal').html('定位器：'+dlf.fn_encode(str_alias));

	dlf.fn_clearInterval(currentLastInfo); // 清除lastinfo计时器
	dlf.fn_clearTrack();	// 初始化清除数据
	dlf.fn_clearMapComponent(); // 清除页面图形
	fn_displayCars(); // 显示车辆信息数据
	//获取单程起点数据 
	dlf.fn_searchData(str_bindRegion);

	// 绑定单程起点保存
	$('#bindMileageSetSave').unbind('click').click(function(event) {
		var obj_bindRegionData = {
								'tids': [str_tid], 
								'single_ids': fn_getMileageSetDatas(str_bindRegion)},
			obj_regionDatas = $('#corpMileageSetTable').data('regions');
		
		if ( obj_bindRegionData.single_ids.length <= 0 ) {
			dlf.fn_jNotifyMessage('请选择要绑定的单程起点！', 'message', false, 3000);
			return;
		}
		
		if ( obj_regionDatas ) {
			var n_regionLen = obj_regionDatas.length;
			// 当前没有创建单程起点
			if ( n_regionLen == 0 ) {
				dlf.fn_jNotifyMessage(str_msg, 'message', false, 5000);
				return;
			}
			dlf.fn_clearRegionShape();
			dlf.fn_jsonPost(BIND_MILEAGE_SET_URL, obj_bindRegionData, str_bindRegion, '单程起点绑定中');
		} else {
			dlf.fn_jNotifyMessage(str_msg, 'message', false, 5000);
		}
	});
}
//=========================批量单程起点操作============================
/*
* 初始化批量单程起点方法
*/
dlf.fn_initBatchMileageSet = function(obj_group){
	var str_bindBatchRegion = 'bindBatchMileageSet', 
		arr_terminalIds = dlf.fn_searchCheckTerminal(true, true, obj_group);//obj_group.children('ul').children('li:visible');
	
	if ( obj_group.children('ul').children('li').length <= 0 ) {	// 没有定位器，不能批量删除
		dlf.fn_jNotifyMessage('该组下没有定位器。', 'message', false, 3000); // 执行操作失败，提示错误消息
		return;
	} else if ( obj_group.hasClass('jstree-unchecked') ) {	// 要删除定位器的组没有被选中
		dlf.fn_jNotifyMessage('没有选中要批量绑定单程起点的定位器。', 'message', false, 3000); // 执行操作失败，提示错误消息
		return;
	}
	
	dlf.fn_clearInterval(currentLastInfo); // 清除lastinfo计时器
	dlf.fn_clearTrack();	// 初始化清除数据
	dlf.fn_clearMapComponent(); // 清除页面图形
	fn_displayCars(); // 显示车辆信息数据
	//获取数据 
	dlf.fn_searchData(str_bindBatchRegion);
	
	// 绑定保存
	$('#bindBatchMileageSetSave').unbind('click').click(function(event) {
		var obj_bindRegionData = {
								'tids': arr_terminalIds, 
								'single_ids': fn_getMileageSetDatas(str_bindBatchRegion)},
			obj_regionDatas = $('#corpMileageSetTable').data('regions'),
			n_tids = arr_terminalIds.length;
		
		if ( obj_bindRegionData.single_ids.length <= 0 ) {
			dlf.fn_jNotifyMessage('请选择要绑定的单程起点！', 'message', false, 3000);
			return;
		}
		
		if ( obj_regionDatas ) {
			var n_regionLen = obj_regionDatas.length;
			// 当前没有创建单程起点
			if ( n_regionLen == 0 ) {
				dlf.fn_jNotifyMessage('当前您还没有单程起点，请新增单程起点！', 'message', false, 5000);
				return;
			}
			// 当前组下没有终端 
			if ( n_tids == 0 ) {
				dlf.fn_jNotifyMessage('当前组下没有定位器！', 'message', false, 5000);
				return;
			}
			dlf.fn_clearRegionShape();
			dlf.fn_jsonPost(BIND_MILEAGE_SET_URL, obj_bindRegionData, str_bindBatchRegion, '单程起点绑定中');
		} else {
			dlf.fn_jNotifyMessage('当前您还没有单程起点，请新增单程起点！', 'message', false, 5000);
		}
	});
}
//=========================获取及绑定单程起点操作方法========================
/*
* 获取当前终端的单程起点信息
*/
dlf.fn_getCurrentMileageSet = function () {
	var obj_currentCar = $($('.j_carList a[class*=j_currentCar]')),
		str_tid = obj_currentCar.attr('tid');
	
	$.get_(BIND_MILEAGE_SET_URL +'?tid='+ str_tid, '', function (data) {  
		if ( data.status == 0 ) {
			var obj_oneselfData = data.res,
				n_selfRegion = obj_oneselfData.length;
			
			for( var i = 0; i < n_selfRegion; i++ ) {
				var obj_tempData = obj_oneselfData[i],
					str_regionId = obj_tempData.single_id;
				
				$('#bindMileageSetRadio_'+ str_regionId).attr('checked', 'checked');
			}
			
		} else if ( data.status == 201 ) {	// 业务变更
			dlf.fn_showBusinessTip();
		} else { // 查询状态不正确,错误提示
			dlf.fn_jNotifyMessage(data.message, 'message', false, 5000);
		}
	}, 
	function (XMLHttpRequest, textStatus, errorThrown) {
		dlf.fn_serverError(XMLHttpRequest);
	});
}
/*
*获取用户选择的单程起点信息
*/
function fn_getMileageSetDatas(str_who) {
	var arr_regionIds = [],
		obj_checks = $('#'+ str_who +'Table :radio[name="'+ str_who +'_radio"]');
	
	obj_checks.each(function() {
		var str_isCheck = $(this).attr('checked'), 
			str_regionId = $(this).val();
			
		if ( str_isCheck ) {
			arr_regionIds.push(str_regionId);
		}
	});
	return arr_regionIds;
}