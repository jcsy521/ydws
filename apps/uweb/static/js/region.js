/*
* 围栏管理及绑定相关操作方法
*/

// 围栏管理的初始化查询展示
window.dlf.fn_initRegion = function() {
	var str_region = 'region', 
		obj_regionWapper = $('#regionWrapper'), 
		obj_regionAddWapper = $('#regionCreateWrapper');
	
	dlf.fn_dialogPosition(str_region);	// 设置dialog的位置并显示
	dlf.fn_clearInterval(currentLastInfo); // 清除lastinfo计时器
	dlf.fn_clearTrack();	// 初始化清除数据
	dlf.fn_clearMapComponent(); // 清除页面图形
	fn_displayCars(); // 显示车辆信息数据
	
	//获取围栏数据 
	dlf.fn_setSearchRecord(str_region);
	dlf.fn_searchData(str_region);
	// 新增围栏事件侦听
	$('#regionCreateBtn').unbind('click').click(function(event){
	
		obj_regionWapper.hide();
		dlf.fn_clearMapComponent(obj_circle); // 清除页面图形
		
		obj_regionAddWapper.css({'left': '305px', 'top': '160px'}).show();
		// 初始化画圆事件,并添加画圆事件
		dlf.fn_initCreateCircle();
		$('#createRegionName').val('');
		fn_displayCars(); // 显示车辆信息数据
		obj_circle =  null;
		
		// 启动画围栏事件
		dlf.fn_mapStartDrawCirlce();
		$('.regionCreateBtnPanel a').removeClass('regionCreateBtnCurrent');
		$('#regionCreate_clickMap').addClass('regionCreateBtnCurrent');
	});
	//关闭新增围栏窗口
	$('#regionCreateClose').unbind('click').click(function(event){
		dlf.fn_initRegion(); // 重新显示围栏管理 
		dlf.fn_mapRightClickRemoveFun();
	});
	//默认样式初始化
	$('.regionCreateBtnPanel a').removeClass('regionCreateBtnCurrent');
	// 给绘制地图绑定事件
	$('#regionCreate_clickMap').unbind('click').click(function(event){
		dlf.fn_mapStartDrawCirlce();
		$('.regionCreateBtnPanel a').removeClass('regionCreateBtnCurrent');
		$(this).addClass('regionCreateBtnCurrent');
	});
	// 给拖动地图绑定事件
	$('#regionCreate_dragMap').unbind('click').click(function(event){
		dlf.fn_mapRightClickFun();
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
			obj_carA = $('.j_carList a[tid='+str_tid+']'),	// 要更新的车辆
			n_carIndex = $('.j_terminal').index(obj_carA), 
			n_clon = obj_carInfo.clongitude,
			n_clat = obj_carInfo.clatitude;
		
		if ( n_clon != 0 && n_clat != 0 ) {
			dlf.fn_addMarker(obj_carInfo, 'actiontrack', n_carIndex, false); // 添加标记
		}
	}
}
/*
* 重新绘制围栏
*/
window.dlf.fn_resetRegion = function() {
	dlf.fn_mapRightClickFun();
	obj_drawingManager.open();
	
	$('.regionCreateBtnPanel a').removeClass('regionCreateBtnCurrent');
	$('#regionCreate_clickMap').addClass('regionCreateBtnCurrent');
}
/*
* 围栏保存操作
*/
window.dlf.fn_saveReginon = function() {
	dlf.fn_mapStopDrawCirlce();
	var str_regionName = $.trim($('#createRegionName').val()), 
		n_radius = 0, 
		obj_regions = $('#regionTable').data('regions'),
		n_circleNum = 0, 
		obj_regionData = {};
		
	if ( obj_regions ) {
		n_circleNum = obj_regions.length;
	
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
	if ( !obj_circle ) { 
		dlf.fn_jNotifyMessage('您还没有创建电子围栏。', 'message', false, 3000);
		return;
	}
	if ( str_regionName == '' ) {
		dlf.fn_jNotifyMessage('您还没有填写围栏名称。', 'message', false, 3000);
		return;
	}
	
	obj_regionData = dlf.fn_getCirlceData();
	obj_regionData.region_name = str_regionName;
	n_radius = obj_regionData.radius;
	
	if ( n_radius < 500 ) {
		dlf.fn_jNotifyMessage('电子围栏半径最小为500米！', 'message', false, 3000);
		return;
	}
	// 发送线请求数据
	dlf.fn_jsonPost(REGION_URL, obj_regionData, 'regionCreate', '电子围栏数据保存中');
}
/*
* 查看围栏的详细信息
*/
window.dlf.fn_detailRegion = function(n_seq) {
	var obj_regionDatas = $('#regionTable').data('regions'), 
		obj_circleData = obj_regionDatas[n_seq], 
		n_radius = obj_circleData.radius;
		n_lng = obj_circleData.longitude,
		n_lat = obj_circleData.latitude,
		n_otherLng = Math.abs(n_lng/NUMLNGLAT + n_radius/111000.0)*NUMLNGLAT,
		obj_centerPoint = dlf.fn_createMapPoint(n_lng, n_lat),
		obj_otherPoint = dlf.fn_createMapPoint(n_otherLng, n_lat),
	
	fn_clearCircleRegion();
	// 调用地图显示圆形
	dlf.fn_displayCircle(obj_circleData);
	// 计算bound显示 
	dlf.fn_setOptionsByType('viewport', [obj_centerPoint, obj_otherPoint]);
	mapObj.zoomOut();
}

/*
* 删除围栏信息
*/
window.dlf.fn_deleteRegion = function(n_id) {
	if ( n_id ) {
		if ( confirm('确定要删除该围栏吗？') ) {
			$.delete_(REGION_URL+'?ids='+n_id, '', function(data) {
				if ( data.status == 0 ) {
					$('#regionTable tr[id='+ n_id +']').remove();
					fn_clearCircleRegion();
				} else {
					dlf.fn_jNotifyMessage(data.message, 'message', false, 3000);
					return;
				}
			});
		}
	}
}
/*
* 清除地图上显示的围栏图形 
*/
function fn_clearCircleRegion () {
	if ( obj_circle ) {
		dlf.fn_clearMapComponent(obj_circle); // 清除页面图形
	}
}
//--------------bind regions----------------
/*
* 绑定围栏初始化
*/
window.dlf.fn_initBindRegion = function() {
	var str_bindRegion = 'bindRegion',
		obj_currentCar = $($('.j_carList a[class*=j_currentCar]')),
		str_tid = obj_currentCar.attr('tid');
	
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
			dlf.fn_jsonPost(BINDREGION_URL, obj_bindRegionData, str_bindRegion, '车辆与电子围栏绑定中');
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
			dlf.fn_jsonPost(BINDREGION_URL, obj_bindRegionData, str_bindBatchRegion, '车辆与电子围栏绑定中');
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

