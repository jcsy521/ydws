/*
* 围栏管理及绑定相关操作方法
*/

// 围栏管理的初始化查询展示
window.dlf.fn_initRegion = function() {
	var str_alias = dlf.fn_encode($('.j_currentCar').attr('alias')),
		str_region = 'region', 
		obj_regionWapper = $('#regionWrapper'), 
		obj_regionAddWapper = $('#regionCreateWrapper'),
		b_mapType = dlf.fn_isBMap();
	
	dlf.fn_dialogPosition(str_region);	// 设置dialog的位置并显示
	dlf.fn_mapRightClickFun(); //清除地图画围栏事件及状态 
	dlf.fn_clearInterval(currentLastInfo); // 清除lastinfo计时器
	dlf.fn_clearTrack();	// 初始化清除数据
	dlf.fn_clearMapComponent(); // 清除页面图形
	fn_displayCars(); // 显示车辆信息数据
	
	//填充当前终端tid在围栏页面
	$('#regionForTerminal').html('定位器：'+str_alias);
	
	//获取围栏数据 
	dlf.fn_setSearchRecord(str_region);
	dlf.fn_searchData(str_region);

	// 新增围栏事件侦听
	$('#regionCreateBtn').unbind('click').click(function(event){
		var n_circleNum = $('#regionTable').data('regionnum');
			
		if ( n_circleNum ) {
			if ( n_circleNum >= 10 ) { //最多只能有十个电子围栏
				dlf.fn_jNotifyMessage('电子围栏最多只能创建10个。', 'message', false, 3000);
				return;
			}
		}
		obj_regionWapper.hide();
		dlf.fn_clearRegionShape(); // 清除页面图形
		
		obj_regionAddWapper.css({'left': '305px', 'top': '160px'}).show();
		$('.regionCreateBtnPanel a').removeClass('regionCreateBtnCurrent');
		$('#regionCreate_circle').addClass('regionCreateBtnCurrent');
		// 初始化画围栏事件,并添加画围栏事件
		dlf.fn_initCreateRegion();
				
		$('#createRegionName').val('');
		dlf.fn_clearMapComponent(); // 清除页面图形
		fn_displayCars(); // 显示车辆信息数据
		obj_regionShape =  null;
		
		if ( b_mapType ) {
			// 启动画围栏事件
			dlf.fn_mapStartDraw();
		}
	});
	//关闭新增围栏窗口
	$('#regionCreateClose').unbind('click').click(function(event){
		if ( !b_mapType ) {
			dlf.fn_gaodeCloseDrawCircle();
		}
		dlf.fn_initRegion(); // 重新显示围栏管理 
	});
	//默认样式初始化
	$('.regionCreateBtnPanel a').removeClass('regionCreateBtnCurrent');
	
	// 给绘制圆形 多边形 围栏绑定事件
	$('#regionCreate_circle, #regionCreate_polygon ').unbind('click').click(function(event){
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
			// 启动画围栏事件
			dlf.fn_mapStartDraw();
		}
	});
	
	// 给拖动地图绑定事件
	$('#regionCreate_dragMap').unbind('click').click(function(event){
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
	
	for ( var param in obj_carDatas ) {
		var obj_carInfo = obj_carDatas[param],
			str_tid = obj_carInfo.tid,
			/*obj_carA = $('.j_carList a[tid='+str_tid+']'),	// 要更新的车辆
			n_carIndex = $('.j_terminal').index(obj_carA), */
			n_clon = obj_carInfo.clongitude,
			n_clat = obj_carInfo.clatitude;
		
		if ( n_clon != 0 && n_clat != 0 ) {
			dlf.fn_addMarker(obj_carInfo, 'region', str_tid); // 添加标记
		}
	}
}

/*
* 重新绘制围栏
*/
window.dlf.fn_resetRegion = function(str_regionType) {
	dlf.fn_mapRightClickFun();
	if ( obj_drawingManager ) {
		dlf.fn_mapStartDraw();
	} else {
		dlf.fn_initCreateRegion();
	}
	$('.regionCreateBtnPanel a').removeClass('regionCreateBtnCurrent');
	
	var obj_regionCBtn = $('#regionCreate_circle');
	
	if ( str_regionType == 'polygon' ) {
		obj_regionCBtn = $('#regionCreate_polygon');
	} 
	
	obj_regionCBtn.addClass('regionCreateBtnCurrent');
}

/*
* 围栏保存操作
*/
window.dlf.fn_saveReginon = function() {
	dlf.fn_mapStopDraw();
	var str_regionName = $.trim($('#createRegionName').val()), 
		n_radius = 0, 
		obj_regions = $('#regionTable').data('regions'),
		n_circleNum = $('#regionTable').data('regionnum'),
		str_tid = $('.j_currentCar').attr('tid'),
		obj_regionData = {};
		
	if ( n_circleNum ) {
		if ( n_circleNum >= 10 ) { //最多只能有十个电子围栏
			dlf.fn_jNotifyMessage('电子围栏最多只能创建10个。', 'message', false, 3000);
			return;
		}
		// 围栏名称 重复性校验
		for ( var i = 0; i < n_circleNum; i++ ) {
			var obj_tempRegion = obj_regions[i], 
				str_tempRegionName = obj_tempRegion.region_name;
				
			if ( str_regionName == str_tempRegionName ) {
				dlf.fn_jNotifyMessage('围栏名称与第'+ (i+1) +'个重复。', 'message', false, 3000);
				return;
			}		
		}
	}
	if ( !obj_regionShape ) { 
		dlf.fn_jNotifyMessage('您还没有创建电子围栏。', 'message', false, 3000);
		return;
	}
	if ( str_regionName == '' ) {
		dlf.fn_jNotifyMessage('您还没有填写围栏名称。', 'message', false, 3000);
		return;
	} else {
		if ( str_regionName.length > 20 ) {
			dlf.fn_jNotifyMessage('围栏名称长度不能大于20个字符。', 'message', false, 3000);
			return;
		}
		if ( !/^[\u4e00-\u9fa5A-Za-z0-9]+$/.test(str_regionName) ) {
			dlf.fn_jNotifyMessage('围栏名称只能由中文、数字、英文组成。', 'message', false, 3000);
			return;
		}
	}
	var obj_shapeData = dlf.fn_getShapeData(),
		arr_polygonData = [];
	
	obj_regionData.region_name = str_regionName;
	obj_regionData.region_shape = obj_shapeData.region_type;	// 默认先画圆
	obj_regionData.tid = str_tid;
	
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
			dlf.fn_jNotifyMessage('多边形围栏最少需要3个点！', 'message', false, 3000);
			return;
		}
	} else { // 如果是圆
		var n_radius = obj_shapeData.circle.radius;

		if ( n_radius < 500 ) {
			dlf.fn_jNotifyMessage('电子围栏半径最小为500米！', 'message', false, 3000);
			return;
		}
		obj_regionData.circle = obj_shapeData.circle;
	}
	// 发送线请求数据
	dlf.fn_jsonPost(REGION_URL, obj_regionData, 'regionCreate', '电子围栏数据保存中');
	
}

/*
* 查看围栏的详细信息
*/
window.dlf.fn_detailRegion = function(n_seq) {
	var obj_regionDatas = $('#regionTable').data('regions'),
		obj_regionData = obj_regionDatas[n_seq], 
		n_region_shape = obj_regionData.region_shape;	// 围栏类型 0: 圆形 1: 多边形
		
	dlf.fn_clearRegionShape();
	// 调用地图显示圆形
	dlf.fn_displayMapShape(obj_regionData, true);
	if ( dlf.fn_isBMap() ) {
		mapObj.closeInfoWindow();// 关闭吹出框 已显示圆
	} else {
		mapObj.clearInfoWindow();	// 高德infowindow不是图层需要单独关闭所有infowindow
	}
}

/*
* 删除围栏信息
*/
window.dlf.fn_deleteRegion = function(n_id) {
	if ( n_id ) {
		if ( confirm('确定要删除该围栏吗？') ) {
			dlf.fn_lockScreen(); // 添加页面遮罩
			dlf.fn_jNotifyMessage('电子围栏数据删除中' + WAITIMG, 'message', true);
			$.delete_(REGION_URL+'?ids='+n_id, '', function(data) {
				if ( data.status == 0 ) {
					var obj_regionTable = $('#regionTable'),
						n_regionNums = obj_regionTable.data('regionnum'),
						obj_currentRegionTr = $('#regionTable tr[id='+ n_id +']');
			
					obj_currentRegionTr.remove();
					obj_regionTable.data('regionnum', n_regionNums - 1);
					dlf.fn_clearRegionShape();
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
* 清除地图上显示的围栏图形 
*/
window.dlf.fn_clearRegionShape = function() {
	if ( obj_regionShape ) {
		dlf.fn_clearMapComponent(obj_regionShape); // 清除页面图形
	}
}
//--------------bind regions----------------
/*
* 绑定围栏初始化
*/
window.dlf.fn_initBindRegion = function() {
	var str_bindRegion = 'bindRegion',
		obj_currentCar = $($('.j_carList a[class*=j_currentCar]')),
		str_tid = obj_currentCar.attr('tid'),
		b_trackStatus = $('#trackHeader').is(':visible');	// 轨迹是否打开着
		
	if ( b_trackStatus ) {
		dlf.fn_closeTrackWindow(false);	// 关闭轨迹查询,不操作lastinfo
	}
	dlf.fn_dialogPosition(str_bindRegion);	// 设置dialog的位置并显示
	dlf.fn_clearInterval(currentLastInfo); // 清除lastinfo计时器
	dlf.fn_clearTrack();	// 初始化清除数据
	dlf.fn_clearMapComponent(); // 清除页面图形
	fn_displayCars(); // 显示车辆信息数据
	//获取围栏数据 
	dlf.fn_searchData(str_bindRegion);
	// 绑定围栏保存
	$('#bindRegionSave').unbind('click').click(function(event) {
		var obj_bindRegionData = {
								'tids': [str_tid], 
								'region_ids': fn_getRegionDatas(str_bindRegion)},
			obj_regionDatas = $('#regionTable').data('regions');
		
		if ( obj_regionDatas ) {
			var n_regionLen = obj_regionDatas.length;
			// 当前没有创建电子围栏
			if ( n_regionLen == 0 ) {
				dlf.fn_jNotifyMessage('当前您还没有电子围栏，请新增电子围栏！', 'message', false, 5000);
				return;
			}
			dlf.fn_jsonPost(BINDREGION_URL, obj_bindRegionData, str_bindRegion, '围栏绑定中');
		} else {
			dlf.fn_jNotifyMessage('当前您还没有电子围栏，请新增电子围栏！', 'message', false, 5000);
		}
	});
}
//=========================批量电子围栏操作============================
/*
* 初始化批量电子围栏方法
*/
window.dlf.fn_initBatchRegions = function(obj_group){
	var str_bindBatchRegion = 'bindBatchRegion', 
		arr_terminalIds = [];
	
	dlf.fn_dialogPosition(str_bindBatchRegion);	// 设置dialog的位置并显示
	dlf.fn_clearInterval(currentLastInfo); // 清除lastinfo计时器
	dlf.fn_clearTrack();	// 初始化清除数据
	dlf.fn_clearMapComponent(); // 清除页面图形
	fn_displayCars(); // 显示车辆信息数据
	//获取围栏数据 
	dlf.fn_searchData(str_bindBatchRegion);
	// 获取组下的所有终端TID
	var str_groupNodeId = $(obj_group).attr('id'), 
		obj_leafUl = $(obj_group).children('ul'),
		n_leafUlLen = obj_leafUl.length;
	
	if ( n_leafUlLen != 0 ) { // 如果当前组下有终端
		var obj_leafLi = obj_leafUl.children();
		
		obj_leafUl.children().each(function() {
			var obj_leatA = $(this).children('a');
			
			arr_terminalIds.push(obj_leatA.attr('tid'));
		});
	}
	// 绑定围栏保存
	$('#bindBatchRegionSave').unbind('click').click(function(event) {
		var obj_bindRegionData = {
								'tids': arr_terminalIds, 
								'region_ids': fn_getRegionDatas(str_bindBatchRegion)},
			obj_regionDatas = $('#regionTable').data('regions'),
			n_tids = arr_terminalIds.length;
		
		if ( obj_regionDatas ) {
			var n_regionLen = obj_regionDatas.length;
			// 当前没有创建电子围栏
			if ( n_regionLen == 0 ) {
				dlf.fn_jNotifyMessage('当前您还没有电子围栏，请新增电子围栏！', 'message', false, 5000);
				return;
			}
			// 当前组下没有终端 
			if ( n_tids == 0 ) {
				dlf.fn_jNotifyMessage('当前组下没有定位器！', 'message', false, 5000);
				return;
			}
			dlf.fn_jsonPost(BINDREGION_URL, obj_bindRegionData, str_bindBatchRegion, '围栏绑定中');
		} else {
			dlf.fn_jNotifyMessage('当前您还没有电子围栏，请新增电子围栏！', 'message', false, 5000);
		}
	});
}
//=========================获取及绑定围栏操作方法========================
/*
* 获取当前终端的围栏信息
*/
window.dlf.fn_getCurrentRegions = function () {
	var obj_currentCar = $($('.j_carList a[class*=j_currentCar]')),
		str_tid = obj_currentCar.attr('tid');
	
	$.get_(BINDREGION_URL +'?tid='+ str_tid, '', function (data) {  
		if ( data.status == 0 ) {
			var obj_oneselfData = data.bind_region,
				n_selfRegion = obj_oneselfData.length;
			
			for( var i = 0; i < n_selfRegion; i++ ) {
				var obj_tempData = obj_oneselfData[i],
					str_regionId = obj_tempData.region_id;
					
				$('#bindRegionCk_'+ str_regionId).attr('checked', 'checked');
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
*获取用户选择的围栏信息
*/
function fn_getRegionDatas(str_who) {
	var arr_regionIds = [],
		obj_checks = $('#'+ str_who +'Table :checkbox[name="'+ str_who +'_check"]');
	
	obj_checks.each(function() {
		var str_isCheck = $(this).attr('checked'), 
			str_regionId = $(this).val();
			
		if ( str_isCheck ) {
			arr_regionIds.push(str_regionId);
		}
	});
	return arr_regionIds;
}