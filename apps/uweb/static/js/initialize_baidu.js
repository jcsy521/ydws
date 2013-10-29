(function () {
/**
* 设置marker的中心移动
* n_tid: 要设置的终端tid
* str_flag : 是否是第一次加载  2013-07-16 add
*/
window.dlf.fn_moveMarker = function(n_tid, str_flag) { 
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
			// mapObj.setCenter(obj_tempMarker.getPosition());
			for ( var i = 0; i < arr_overlays.length; i++ ) {
				var obj_marker = obj_selfmarkers[$(arr_overlays[i]).attr('tid')];
				
				if ( obj_marker ) {
					obj_marker.setTop(false);
				}
			}
			obj_tempMarker.setTop(true);
			obj_tempMarker.openInfoWindow(obj_infoWindow); // 显示吹出框
			if ( !str_flag ) {
				setTimeout(function() {
					mapObj.setCenter(obj_tempMarker.getPosition());
				}, 100);
			}
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
		obj_currentCar = $('.j_carList a[class*=j_currentCar]'),
		str_currentTid = obj_currentCar.attr('tid'),	// 当前车定位器编号
		str_iconType = obj_currentCar.attr('icon_type'),	// icon_type
		str_tid = str_type == 'current' ? str_currentTid : obj_carInfo.tid,
		str_alias = obj_carInfo.alias,
		n_carTimestamp = obj_carInfo.timestamp,
		n_clon = obj_carInfo.clongitude/NUMLNGLAT,
		n_clat = obj_carInfo.clatitude/NUMLNGLAT,
		n_degree = obj_carInfo.degree,
		n_iconType = obj_carInfo.icon_type,	// icon_type
		n_pointType = obj_carInfo.type, 
		obj_tempVal = dlf.fn_checkCarVal(str_tid, 'tracklq'), // 查询缓存中是否有当前车辆信息
		obj_tempPoint = new BMap.Point(n_clon, n_clat),
		obj_carA = $('.j_carList a[tid='+str_tid+']'),	// 要更新的车辆
		actionPolyline = null, // 轨迹线对象
		str_actionTrack = dlf.fn_getActionTrackStatus(str_tid),
		obj_selfMarker = obj_selfmarkers[str_tid],		// obj_carA.data('selfmarker'), 
		n_imgDegree = dlf.fn_processDegree(n_degree),	// 方向角处理
		obj_selfPolyline = 	obj_polylines[str_tid],		// obj_carA.data('selfpolyline'),
		n_carIndex = obj_carA.parent().index(),	// 个人用户车辆索引
		str_iconUrl = '',
		b_isCorpUser = dlf.fn_userType(),
		obj_polylineOptions = {'color': '#1AF18D', 'style': 'dashed', 'weight': 4},
		arr_tracePoints = obj_carInfo.trace_info,	// 集团用户甩尾的点数据
		arr_trackPoints = obj_carInfo.track_info,	// 集团用户开启追踪的点数据
		arr_tempTrackPoints = [],	// 临时存储开启追踪的点数组
		arr_tempTracePoints = [],	// 临时存储甩尾的点数组
		str_randomColor = dlf.fn_randomColor(),	// 随机生成的颜色值
		n_track = obj_carInfo.track,	// 是否开启追踪 0: 取消追踪 1: 开启追踪
		str_track = n_track == 1 ? 'yes' : 'no';
		
	/*if ( str_type != 'current' ) {
		obj_actionTrack[str_tid].status = str_track;
	}*/
	str_actionTrack = dlf.fn_getActionTrackStatus(str_tid);
	
	if ( !str_alias ) {	// 如果无alias ，从车辆列表获取
		str_alias = obj_carA.next().html() || obj_carA.text();
	}
	obj_carInfo.alias = str_alias;
	
	if ( b_isCorpUser && str_type == 'current' ) {	// 如果是集团用户 && 实时定位
		n_iconType = str_iconType;
	}
	if ( arr_tracePoints ) {
		var n_trackLength = arr_tracePoints.length;
		
		if ( n_trackLength > 0 ) {	// trace_info如果有数据就甩尾，如果没有就显示basic_info的点
			for ( var x = 0; x < n_trackLength; x=x+2 ) {
				arr_tempTracePoints.push(dlf.fn_createMapPoint(arr_tracePoints[x+1], arr_tracePoints[x]));
			}
		}
	}
	/**
	* 存储车辆信息
	*/
	if ( obj_tempVal ) { // 追加
		if ( str_actionTrack == 'yes' ) {
			// obj_tempVal.val = obj_tempVal.val[0];	// 如果是开启追踪的第一次lastinfo
			var str_tempOldColor = obj_actionTrack[str_tid].color;

			/*if ( b_isCorpUser ) {	// 如果是集团开启追踪后  显示track_info的点数据
				var n_firstTrack = obj_selfMarker.track;
				
				if ( n_firstTrack ) {
					obj_tempVal.val = [];
					obj_selfmarkers[str_tid].track = 0;
				}
			}*/			
			if ( arr_trackPoints ) {
				for ( var x = 0; x < arr_trackPoints.length; x ++ ) {
					var obj_tempTrackInfo = arr_trackPoints[x],
						n_lat = obj_tempTrackInfo.clatitude,
						n_lon = obj_tempTrackInfo.clongitude,
						n_trackPointType = obj_tempTrackInfo.type,
						n_trackTimestamp = obj_tempTrackInfo.timestamp,
						obj_tempTrackPoint = dlf.fn_createMapPoint(n_lon, n_lat);
					
					if ( n_pointType == GPS_TYPE ) {
						obj_tempVal.val.push(obj_tempTrackPoint);
						if ( b_isCorpUser ) {
							obj_carsData[str_tid].timestamp = n_trackTimestamp;
						} else {
							$('.j_carList').data('carsData')[str_tid].timestamp = n_trackTimestamp;
						}
					}
				}
			}
			if ( n_pointType == GPS_TYPE ) {
				obj_tempVal.val.push(obj_tempPoint);
				if ( b_isCorpUser ) {
					obj_carsData[str_tid].timestamp = n_carTimestamp;
				} else {
					$('.j_carList').data('carsData')[str_tid].timestamp = n_carTimestamp;
				}
			}
			if ( str_tempOldColor == '' ) {
				str_tempOldColor = str_randomColor;
				obj_actionTrack[str_tid].color = str_tempOldColor;
			}
			obj_polylineOptions = {'color': str_tempOldColor, 'weight': 4} ;
			if ( str_tid == str_currentTid ) {	// 只移动当前终端到地图中心
				dlf.fn_boundContainsPoint(obj_tempPoint);	// 开启追踪是否超出地图
			}
		} else {
			arr_tempTracePoints.push(obj_tempPoint);
			obj_tempVal.val = [];
			obj_tempVal.val = arr_tempTracePoints;
		}
		obj_tempData = obj_tempVal;
		dlf.fn_clearMapComponent(obj_selfPolyline); // 删除相应轨迹线
	} else {
		arr_tempTracePoints.push(obj_tempPoint);
		obj_tempData = {'key': str_tid, 'val': arr_tempTracePoints};
		arr_infoPoint.push(obj_tempData);
	}
	actionPolyline = dlf.fn_createPolyline(obj_tempData.val, obj_polylineOptions); 
	dlf.fn_addOverlay(actionPolyline);	//向地图添加覆盖物 
	obj_polylines[str_tid] = actionPolyline;	// 存储开启追踪轨迹
	
	if ( str_actionTrack == 'yes' && n_pointType == CELLID_TYPE ) { // 2013.7.5 开户追踪后,基站点及信息不进行显示
		return;
	}
	if ( obj_selfMarker ) {
		var obj_selfLabel = obj_selfMarker.selfLable,
			obj_selfInfoWindow = obj_selfMarker.selfInfoWindow,
			b_isOpen = obj_selfInfoWindow.isOpen();
		
		obj_selfLabel.setContent(str_alias);	// label上的alias值
		obj_selfMarker.setLabel(obj_selfLabel);	// 设置label  obj_carA.data('selfLable')
		obj_selfInfoWindow.setContent(dlf.fn_tipContents(obj_carInfo, 'actiontrack'));
		obj_selfMarker.setPosition(obj_tempPoint);
		
		if ( b_isCorpUser ) {
			str_iconUrl = dlf.fn_setMarkerIconType(n_imgDegree, n_iconType);
		} else {
			str_iconUrl = BASEIMGURL + 'default.png';
		}
		obj_selfMarker.setIcon(new BMap.Icon(str_iconUrl, new BMap.Size(34, 34)));	// 设置方向角图片
		//obj_carA.data('selfmarker', obj_selfMarker);
		obj_selfmarkers[str_tid] = obj_selfMarker;
		var str_actionTrack = dlf.fn_getActionTrackStatus(str_tid);
		
		if ( str_actionTrack == 'yes' ) {
			dlf.fn_updateOpenTrackStatusColor(str_tid);
		}
		if ( b_isOpen ) {
			obj_selfMarker.openInfoWindow(obj_selfMarker.selfInfoWindow);
		}
		
		dlf.fn_loadBaiduShare();
	} else { 
		/*if ( b_isCorpUser ) {
			n_carIndex = $('.j_terminal').index(obj_carA);
		}*/
		dlf.fn_addMarker(obj_carInfo, 'actiontrack', str_tid, false); // 添加标记
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
* 设置地图marker的icon图标=
*/
window.dlf.fn_setMarkerIconType = function(n_degree, n_iconType) {
	// 集团用户icon_type icon显示不同图标
		var str_tempImgUrl = '',
			str_dir = CORPIMGURL + 'terminalIcons/';
		
		if ( n_iconType == 0 ) {	// 车
			str_tempImgUrl = n_degree;
			str_dir = BASEIMGURL;
		} else if ( n_iconType == 1 ) {	// 摩托车
			str_tempImgUrl = 'moto';
		} else if ( n_iconType == 2 ) {	// 人
			str_tempImgUrl = 'person';
		} else if ( n_iconType == 3 ) {	// 图标
			str_tempImgUrl = 'default';
		} else {
			str_tempImgUrl = n_degree;
			str_dir = BASEIMGURL;
		}
	
	return str_dir + str_tempImgUrl + '.png';
}

/**
* 设置是否要启动追踪效果
*/
window.dlf.setTrack = function(arr_tempTids, selfItem) {
	var str_type = typeof(arr_tempTids),
		arr_tids = [],
		arr_openTids = [],
		n_isOpen = 0;

	if ( str_type == 'string' ) {	// 单个定位器的开启追踪
		arr_tids.push(arr_tempTids);
	} else {	// 批量开启追踪
		arr_tids = arr_tempTids;
	}
	for ( var i = 0; i < arr_tids.length; i++ ) {
		var str_tid = arr_tids[i],
			str_actionTrack = dlf.fn_getActionTrackStatus(str_tid),	// obj_carLi.attr('actiontrack'),
			obj_selfMarker = obj_selfmarkers[str_tid],	// obj_carLi.data('selfmarker'), 
			obj_selfInfoWindow = '', // obj_selfMarker.selfInfoWindow,  // 获取吹出框
			str_content = '', // obj_selfInfoWindow.getContent(), // 吹出框内容
			str_tempAction = 'yes';
			str_tempOldMsg = '',
			obj_selfItem = $(selfItem),
			n_track = 0,
			str_tempMsg = '取消跟踪';
		
		if ( str_actionTrack == 'yes' ) {
			str_tempAction = 'no';
			str_tempMsg = '开始跟踪';
			str_tempOldMsg = '取消跟踪';
			// 手动取消追踪清空计时器
			dlf.fn_clearRealtimeTrack(str_tid);
			obj_actionTrack[str_tid].color = '';
			// 关闭jNotityMessage,dialog
			dlf.fn_closeJNotifyMsg('#jNotifyMessage'); 
			dlf.fn_closeDialog();
		} else {
			n_isOpen = 1;
			str_tempAction = 'yes';
			str_tempMsg = '取消跟踪';
			str_tempOldMsg = '开始跟踪';
			n_track = 1;
		}
		// 向后台发送开始跟踪请求，前台倒计时5分钟，5分钟后自动取消跟踪 todo
		arr_openTids.push(str_tid);
		if ( obj_selfMarker ) {
			// obj_selfMarker.track = n_track;	// 存储第一次开启追踪、移除存储第一次开启追踪
			obj_selfInfoWindow = obj_selfMarker.selfInfoWindow,  // 获取吹出框
			str_content = obj_selfInfoWindow.getContent(); // 吹出框内容
			
			str_content = str_content.replace(str_tempOldMsg, str_tempMsg);
			obj_selfInfoWindow.setContent(str_content);		// todo
			obj_selfMarker.selfInfoWindow = obj_selfInfoWindow;
			obj_selfmarkers[str_tid] = obj_selfMarker;
		}
		obj_selfItem.html(str_tempMsg);
		obj_actionTrack[str_tid].status = str_tempAction;
		dlf.fn_updateOpenTrackStatusColor(str_tid);
	}
	if ( arr_openTids.length > 0 )  {
		dlf.fn_openTrack(arr_openTids.join(), selfItem, n_isOpen);
	}
}

/**
* kjj 2013-05-27 
* 修改吹出框上开启追踪的颜色
*/
window.dlf.fn_updateOpenTrackStatusColor = function(str_tid, str_order) {
	var str_actionTrack = dlf.fn_getActionTrackStatus(str_tid),
		str_color = '';

	if ( str_tid == $('.j_currentCar').attr('tid') ) {
		if ( str_order == 'after' ) {
			if ( str_actionTrack == 'yes' ) {
				str_color = 'blue';
			} else {
				str_color = '#F0960F';
			}
		} else {
			if ( str_actionTrack == 'yes' ) {
				str_color = '#F0960F';
			} else {
				str_color = 'blue';
			}
		}
		$('.j_openTrack').css('color', str_color);
	}
}

/**  
* 更新定位器别名 terminal get和put的时候  
* 如果别名为空则显示车牌号，如果车牌号为空则显示定位器手机号
*/
window.dlf.fn_updateAlias = function() {
	var	cnum = $('#t_cnum').val(),	// 车牌号
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
			n_beginNum = str_content.indexOf('定位器：')+4,
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
