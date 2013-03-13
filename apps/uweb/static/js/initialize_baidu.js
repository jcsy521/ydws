(function () {
/**
* 设置marker的中心移动
* n_tid: 要设置的终端tid
*/
window.dlf.fn_moveMarker = function(n_tid) {
	var str_trackStatus = $('#trackHeader').css('display');
	
	if ( str_trackStatus == 'none' ) {	// 如果当前点击的不是轨迹按钮，先关闭轨迹查询	
		/**
		* 查找到当前车辆的信息  更新marker信息
		*/
		var obj_tempMarker = obj_selfmarkers[n_tid],	//obj_currentItem.data('selfmarker'),
			obj_infoWindow = '',
			arr_overlays = $('.j_carList .j_terminal');
			
		if ( obj_tempMarker ) {
			obj_infoWindow = obj_tempMarker.selfInfoWindow;
			mapObj.setCenter(obj_tempMarker.getPosition());
			
			for ( var i = 0; i < arr_overlays.length; i++ ) {
				var obj_marker = obj_selfmarkers[$(arr_overlays[i]).attr('tid')];
				
				if ( obj_marker ) {
					obj_marker.setTop(false);
				}
			}
			obj_tempMarker.setTop(true);
			obj_tempMarker.openInfoWindow(obj_infoWindow); // 显示吹出框
		} else {
			// 关闭所有的marker
			mapObj.closeInfoWindow();
		}
	} else {
		dlf.fn_clearTrack('inittrack');	// 初始化清除数据
	}
}

/**
* 对动态数据做更新
* obj_carInfo: 车辆信息
* str_type: 是否是实时定位
*/
window.dlf.fn_updateInfoData = function(obj_carInfo, str_type) {
	var obj_tempData = [], 
		str_currentTid = $('.j_carList a[class*=j_currentCar]').attr('tid'),	// 当前车定位器编号
		str_tid = str_type == 'current' ? str_currentTid : obj_carInfo.tid,
		str_alias = obj_carInfo.alias,
		n_clon = obj_carInfo.clongitude/NUMLNGLAT,
		n_clat = obj_carInfo.clatitude/NUMLNGLAT,
		n_degree = obj_carInfo.degree,
		obj_tempVal = dlf.fn_checkCarVal(str_tid), // 查询缓存中是否有当前车辆信息
		obj_tempPoint = new BMap.Point(n_clon, n_clat),
		obj_carA = $('.j_carList a[tid='+str_tid+']'),	// 要更新的车辆
		actionPolyline = null, // 轨迹线对象
		str_actionTrack = obj_actionTrack[str_tid],		// obj_carA.attr('actiontrack'), 
		obj_selfMarker = obj_selfmarkers[str_tid],		// obj_carA.data('selfmarker'), 
		n_imgDegree = dlf.fn_processDegree(n_degree),	// 方向角处理
		obj_selfPolyline = 	obj_polylines[str_tid],		// obj_carA.data('selfpolyline'),
		n_carIndex = obj_carA.parent().index();	// 个人用户车辆索引

	if ( !str_alias ) {	// 如果无alias ，从车辆列表获取
		str_alias = obj_carA.next().html() || obj_carA.text();
	}
	obj_carInfo.alias = str_alias;
	/**
	* 存储车辆信息
	*/
	if ( obj_tempVal ) { // 追加
		if ( str_actionTrack == 'yes' ) { 
			obj_tempVal.val.push(obj_tempPoint);
		} else { 
			obj_tempVal.val = [];
			obj_tempVal.val[0] = obj_tempPoint;
		}
		obj_tempData = obj_tempVal;
		dlf.fn_clearMapComponent(obj_selfPolyline); // 删除相应轨迹线
	} else { // 新增
		obj_tempData = {'key': str_tid, 'val': [obj_tempPoint]};
		arr_infoPoint.push(obj_tempData);
	}
	
	actionPolyline = dlf.fn_createPolyline(obj_tempData.val); 
	dlf.fn_addOverlay(actionPolyline);	//向地图添加覆盖物 
	obj_polylines[str_tid] = actionPolyline;	// 存储开启追踪轨迹
	//obj_carA.data('selfpolyline', actionPolyline);
	
	if ( obj_selfMarker ) {
		obj_selfMarker.setLabel(obj_selfMarker.getLabel());	// 设置label  obj_carA.data('selfLable')
		obj_selfMarker.getLabel().setContent(str_alias);	// label上的alias值
		obj_selfMarker.selfInfoWindow.setContent(dlf.fn_tipContents(obj_carInfo, 'actiontrack'));
		obj_selfMarker.setPosition(obj_tempPoint);
		obj_selfMarker.setIcon(new BMap.Icon(BASEIMGURL +n_imgDegree+'.png', new BMap.Size(34, 34)));	// 设置方向角图片
		//obj_carA.data('selfmarker', obj_selfMarker);
		obj_selfmarkers[str_tid] = obj_selfMarker;
	} else { 
		if ( dlf.fn_userType() ) {
			n_carIndex = $('.j_terminal').index(obj_carA);
		}
		dlf.fn_addMarker(obj_carInfo, 'actiontrack', n_carIndex, false); // 添加标记
	}
	
	var obj_toWindowInterval = setInterval(function() {
		var obj_tempMarker = obj_selfmarkers[str_tid];	// obj_carA.data('selfmarker');
		
		if (( str_currentTid == str_tid ) ) {
			if ( str_type == 'current' ) {	// 查找到当前车辆的信息
				if ( obj_tempMarker ) {
					obj_tempMarker.openInfoWindow(obj_tempMarker.selfInfoWindow);
				}
			} else if ( str_type == 'first' ) {	// 如果第一次lastinfo 移到中心点 打开吹出框
				dlf.fn_moveMarker(str_currentTid);				
			}
			clearInterval(obj_toWindowInterval);
		}
	}, 500);
}

/**
* 设置是否要启动追踪效果
*/
window.dlf.setTrack = function(str_tid, selfItem) {
	var obj_carLi = $('.j_carList a[tid='+str_tid+']'), 
		str_actionTrack = obj_actionTrack[str_tid],	// obj_carLi.attr('actiontrack'),
		obj_selfMarker = obj_selfmarkers[str_tid],	// obj_carLi.data('selfmarker'), 
		obj_selfInfoWindow = obj_selfMarker.selfInfoWindow,  // 获取吹出框
		str_content = obj_selfInfoWindow.getContent(), // 吹出框内容
		str_tempAction = 'yes';
		str_tempOldMsg = '',
		str_tempMsg = '取消跟踪';
	
	if ( str_actionTrack == 'yes' ) {
		str_tempAction = 'no';
		str_tempMsg = '开始跟踪';
		str_tempOldMsg = '取消跟踪';
		// 手动取消追踪清空计时器
		dlf.fn_clearRealtimeTrack(str_tid);
	} else {
		str_tempAction = 'yes';
		str_tempMsg = '取消跟踪';
		str_tempOldMsg = '开始跟踪';
		// 向后台发送开始跟踪请求，前台倒计时5分钟，5分钟后自动取消跟踪 todo
		dlf.fn_openTrack(str_tid, selfItem);
	}
	
	str_content = str_content.replace(str_tempOldMsg, str_tempMsg);
	obj_selfInfoWindow.setContent(str_content);		// todo
	obj_selfMarker.selfInfoWindow = obj_selfInfoWindow;
	obj_actionTrack[str_tid] = str_tempAction;
	//obj_carLi.data('selfmarker', obj_selfMarker);
	obj_selfmarkers[str_tid] = obj_selfMarker;
	$(selfItem).html(str_tempMsg);
}


/**  
* 更新定位器别名 terminal get和put的时候  
* 如果别名为空则显示车牌号，如果车牌号为空则显示定位器手机号
*/
window.dlf.fn_updateAlias = function() {
	var	cnum = $('#cnum').val(),	// 车牌号
		tmobile = $('#tmobileContent').html(),
		obj_car = $('.j_carList .j_currentCar'),
		obj_selfMarker = obj_selfmarkers[obj_car.attr('tid')],	// obj_car.data('selfmarker'),
		str_alias = '';
		
	if ( cnum != '' ) {
		str_alias = cnum;
	} else {
		str_alias = tmobile;
	}	
	if ( obj_selfMarker ) {	// 修改 marker label 别名
		var str_tid = $('.j_carList .j_currentCar').eq(0).attr('tid'),
			str_content = obj_selfMarker.selfInfoWindow.getContent(),
			n_beginNum = str_content.indexOf('车辆：')+3,
			n_endNum = str_content.indexOf('</h4>'),
			str_oldname = str_content.substring(n_beginNum, n_endNum),
			str_content = str_content.replace(str_oldname, str_alias);
					
		obj_selfMarker.getLabel().setContent(str_alias);	// todo
		//$('.cMsgWindow h4[tid='+str_tid+']').html('车辆：' + str_alias);
		obj_selfMarker.selfInfoWindow.setContent(str_content);	// todo
	}
	obj_car.attr('title', str_alias);	// 
	obj_car.next().html(str_alias).attr('title', str_alias);
}
})();
