(function () {
/**
* 设置marker的中心移动
* n_tid: 要设置的终端tid
* str_flag : 是否是第一次加载  2013-07-16 add
*/
dlf.fn_moveMarker = function(n_tid, str_flag) { 
	var str_trackStatus = $('.j_delay').css('display');
	
	if ( str_trackStatus == 'none' ) {	// 如果当前点击的不是轨迹按钮，先关闭轨迹查询	
		/**
		* 查找到当前车辆的信息  更新marker信息
		*/
		var obj_tempMarker = obj_selfmarkers[n_tid],	//obj_currentItem.data('selfmarker'),
			arr_overlays = $('.j_carList .j_terminal');
		
		if ( obj_tempMarker ) {
            var obj_currentCarInfo = $('.j_carList').data('carsData')[n_tid];
			
			for ( var i = 0; i < arr_overlays.length; i++ ) {
				var obj_marker = obj_selfmarkers[$(arr_overlays[i]).attr('tid')];
				
				if ( obj_marker ) {
					obj_marker.setTop(false);
				}
			}
			//注释 hs:2014-6-25
			/*if ( mapObj.getZoom() < 15 ) {
				mapObj.setZoom(15);
			}*/
			obj_tempMarker.setTop(true);
			if ( !str_flag ) {
				setTimeout(function() {
					mapObj.setCenter(obj_tempMarker.getPosition());
				}, 100);
			}
			setTimeout(function() {
				dlf.fn_createMapInfoWindow(obj_currentCarInfo, 'actiontrack');
				obj_tempMarker.openInfoWindow(obj_mapInfoWindow); // 显示吹出框
				
				dlf.fn_updateOpenTrackStatusColor(n_tid);	
			}, 130);
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
dlf.fn_updateInfoData = function(obj_carInfo, str_type) {
	var obj_tempData = [], 
		obj_currentCar = $('.j_carList a[class*=j_currentCar]'),
		str_carTid = obj_currentCar.attr('tid');	// 当前车定位器编号
	
	if ( obj_currentCar.length == 0 ) {
		if ( dlf.fn_userType() ) {
			str_carTid = str_currentTid;
			obj_currentCar = $('.j_terminal[tid='+ str_currentTid +']');
		}
	}
	
	var	str_iconType = obj_currentCar.attr('icon_type'),	// icon_type
		str_tempTid = obj_carInfo.tid,
		str_tid = str_type == 'current' ? str_carTid : str_tempTid,
		str_alias = obj_carInfo.alias,
		n_carTimestamp = obj_carInfo.timestamp,
		n_clon = obj_carInfo.clongitude/NUMLNGLAT,
		n_clat = obj_carInfo.clatitude/NUMLNGLAT,
		n_lon = obj_carInfo.longitude,
		n_lat = obj_carInfo.latitude,
		n_degree = obj_carInfo.degree,
		n_speed = obj_carInfo.speed,
		n_iconType = obj_carInfo.icon_type,	// icon_type
		n_pointType = obj_carInfo.type, 
		str_loginSt = obj_carInfo.login,
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
		str_track = n_track == 1 ? 'yes' : 'no',
		b_regionCreateWpST = $('#regionCreateWrapper').is(':visible'),
		b_corpRegionWpST = $('#bindRegionWrapper').is(':visible'),
		b_bindBatchRegionWpST = $('#bindBatchRegionWrapper').is(':visible'),
		b_corpRegionST = $('#corpRegionWrapper').is(':visible'),	// 电子围栏是否显示
		b_trackSt = $('.j_delay').is(':visible'), 
		b_eventSearchWpST = $('#eventSearchWrapper').is(':visible'),		
		b_operatorWpST = $('#operatorWrapper').is(':visible'),
		b_notifyManageAddWpST = $('#notifyManageAddWrapper').is(':visible'),
		b_mileageWpST = $('#mileageWrapper').is(':visible'),
		b_mileageSetWpST = $('#mileageSetWrapper').is(':visible');
	
	if ( b_trackSt || b_eventSearchWpST || b_operatorWpST || b_notifyManageAddWpST || b_mileageWpST || b_mileageSetWpST ) {
		return;
	}
	
	
	if ( n_lon != 0 && n_lat != 0 ) {
		if ( n_clon != 0 && n_clat != 0 ) {
			
		} else {
			dlf.fn_translateToBMapPoint(n_lon, n_lat, 'actiontrack', obj_carInfo, true);	// 前台偏转 kjj 2013-09-27
			return;
		}
	} else {
		return;
	}
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
			var str_tempOldColor = obj_actionTrack[str_tid].color,
				obj_tempCarsData = $('.j_carList').data('carsData');
			
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
						/*if ( b_isCorpUser ) {
							obj_carsData[str_tid].timestamp = n_trackTimestamp;
						} else {
							$('.j_carList').data('carsData')[str_tid].timestamp = n_trackTimestamp;
						} #todo */
						obj_tempCarsData[str_tid].timestamp = n_trackTimestamp;
					}
				}
			}
			if ( n_pointType == GPS_TYPE ) {
				obj_tempVal.val.push(obj_tempPoint);
				/*if ( b_isCorpUser ) {
					obj_carsData[str_tid].timestamp = n_carTimestamp;
				} else {
					$('.j_carList').data('carsData')[str_tid].timestamp = n_carTimestamp;
				} #todo */
				obj_tempCarsData[str_tid].timestamp = n_carTimestamp;
			}
			if ( str_tempOldColor == '' ) {
				str_tempOldColor = str_randomColor;
				obj_actionTrack[str_tid].color = str_tempOldColor;
			}
			obj_polylineOptions = {'color': str_tempOldColor, 'weight': 4} ;
			if ( str_tid == str_currentTid ) {	// 只移动当前终端到地图中心
				// hs:2014-6-30 注释 
				//dlf.fn_boundContainsPoint(obj_tempPoint);	// 开启追踪是否超出地图
			}
		} else {
			arr_tempTracePoints.push(obj_tempPoint);
			obj_tempVal.val = [];
			obj_tempVal.val = arr_tempTracePoints;
		}
		obj_tempData = obj_tempVal;
		if ( obj_selfPolyline ) {
			dlf.fn_clearMapComponent(obj_selfPolyline); // 删除相应轨迹线
		}
	} else {
		arr_tempTracePoints.push(obj_tempPoint);
		obj_tempData = {'key': str_tid, 'val': arr_tempTracePoints};
		arr_infoPoint.push(obj_tempData);
	}
	if ( obj_tempData.val ) {
		obj_selfPolyline = dlf.fn_createPolyline(obj_tempData.val, obj_polylineOptions); 
		dlf.fn_addOverlay(obj_selfPolyline);	//向地图添加覆盖物 
		
		obj_polylines[str_tid] = obj_selfPolyline;	// 存储开启追踪轨迹
	}
	
	if ( str_actionTrack == 'yes' && n_pointType == CELLID_TYPE ) { // 2013.7.5 开户追踪后,基站点及信息不进行显示
		return;
	}
	if ( obj_selfMarker ) {
		var obj_selfInfoWindow = obj_selfMarker.infoWindow;

		str_alias = dlf.fn_encode(str_alias);
		if ( obj_selfMarker.getLabel() ) {
			obj_selfMarker.getLabel().setContent(str_alias);
		}		
		if ( str_currentTid == str_tid ) {
			if ( obj_selfInfoWindow ) {
				dlf.fn_createMapInfoWindow(obj_carInfo, 'actiontrack');
				obj_selfMarker.openInfoWindow(obj_mapInfoWindow); // 显示吹出框
			}
		}
		
		obj_selfMarker.setPosition(obj_tempPoint);
		// 设置marker的icon
		dlf.fn_setMarkerTraceIcon(n_imgDegree, n_iconType, str_loginSt, obj_selfMarker, n_carTimestamp, n_speed);
		
		/**if ( b_isCorpUser ) {
			
			* KJJ add in 2014.04.28
			* 判断5分钟之内的点，速度大于5的证明终端在移动
			
			var b_flag = false;
			if ( n_nowtime - n_carTimestamp < 300 && n_speed > 5 ) {	// 5分钟之内的点
				b_flag = true;
			}
			str_iconUrl = dlf.fn_setMarkerIconType(n_imgDegree, n_iconType, str_loginSt, true);
		} else {
			str_iconUrl = BASEIMGURL + 'default.png';
		}
		obj_selfMarker.setIcon(new BMap.Icon(str_iconUrl, new BMap.Size(34, 34)));	// 设置方向角图片
		*/
		
		//obj_carA.data('selfmarker', obj_selfMarker);
		obj_selfmarkers[str_tid] = obj_selfMarker;
		var str_actionTrack = dlf.fn_getActionTrackStatus(str_tid);
		
		if ( str_actionTrack == 'yes' ) {
			dlf.fn_updateOpenTrackStatusColor(str_tid);
		}
		if ( str_tempTid == str_currentTid ) {
			dlf.fn_loadBaiduShare();
		}
	} else { 		
		if ( dlf.fn_userType() ) {
			if ( $('#leafNode_'+str_tid).attr('class').search('jstree-checked') != -1 ) {			
				if ( b_corpRegionST || b_bindBatchRegionWpST || b_regionCreateWpST || b_corpRegionWpST ) {	
					dlf.fn_addMarker(obj_carInfo, 'region', str_tid); // 添加标记
				} else {
					dlf.fn_addMarker(obj_carInfo, 'actiontrack', str_tid); // 添加标记
				}
			}
		} else {
			if ( b_corpRegionST || b_bindBatchRegionWpST || b_regionCreateWpST || b_corpRegionWpST ) {	
				dlf.fn_addMarker(obj_carInfo, 'region', str_tid); // 添加标记
			} else {
				dlf.fn_addMarker(obj_carInfo, 'actiontrack', str_tid); // 添加标记
			}
		}
	}
	
	var obj_toWindowInterval = setInterval(function() {
		var obj_tempMarker = obj_selfmarkers[str_tid];	// obj_carA.data('selfmarker');
		
		if ( !dlf.fn_userType() ) {
			str_currentTid = str_currentPersonalTid;
		}
	
		if ( str_currentTid && str_currentTid == str_tid ) {
			if ( str_type == 'current' ) {	// 查找到当前车辆的信息
				if ( obj_tempMarker ) {
					var obj_carDatas = $('.j_carList').data('carsData')[str_tid];
					
					dlf.fn_createMapInfoWindow(obj_carDatas, 'actiontrack');
					obj_tempMarker.openInfoWindow(obj_mapInfoWindow);
				}
			} else if ( str_type == 'first' && !b_isCorpUser ) {	// 如果第一次lastinfo 移到中心点 打开吹出框
				dlf.fn_moveMarker(str_currentTid);				
			}
			clearInterval(obj_toWindowInterval);
		}		
	}, 500);
}

dlf.fn_setMarkerTraceIcon = function(n_degree, n_iconType, str_loginSt, obj_currentMarker, n_carTimestamp, n_speed) {
	var n_nowtime = new Date().getTime()/1000,
		b_flag = false,
		b_isCorpUser = dlf.fn_userType(),
		obj_iconSize = new BMap.Size(100, 100),
		obj_imageOffset = new BMap.Size(-30, -35),
		str_imgUrl = str_loginSt == 1 ? 'default' : 'default_logout', 
		myIcon = new BMap.Icon(BASEIMGURL + str_imgUrl+'.png', new BMap.Size(34, 34));
	
	if ( b_isCorpUser ) {
		/**
		* KJJ add in 2014.04.28
		* 判断5分钟之内的点，速度大于5的证明终端在移动
		*/
		
		if ( n_nowtime - n_carTimestamp < 300 && n_speed > 5 ) {	// 5分钟之内的点
			b_flag = true;
			
			if ( n_iconType == 1 || n_iconType == 3 || n_iconType == 4|| n_iconType == 5 ) {
				obj_iconSize = new BMap.Size(50, 50);
				if ( n_iconType == 1 || n_iconType == 4 || n_iconType == 5 ) {
					obj_imageOffset = new BMap.Size(0, -10);
				} else {
					obj_imageOffset = new BMap.Size(-5, 0);
				}
			} else if ( n_iconType == 2 ) {
				obj_iconSize = new BMap.Size(34, 34);
				obj_imageOffset = new BMap.Size(0, 0);
			}
			myIcon.setSize(obj_iconSize);
			myIcon.setImageOffset(obj_imageOffset);
		}
		myIcon.imageUrl = dlf.fn_setMarkerIconType(n_degree, n_iconType, str_loginSt, b_flag);
	} else {
		myIcon.setImageOffset(new BMap.Size(0, 0));		
	}
	obj_currentMarker.setIcon(myIcon);	// 设置方向角图片
	return obj_currentMarker;
}

/**
* 设置地图marker的icon图标=
*/
dlf.fn_setMarkerIconType = function(n_degree, n_iconType, str_loginSt, b_flagTrace) {
	// 集团用户icon_type icon显示不同图标
	var str_tempImgUrl = '',
		b_isCar = false,
		str_dir = CORPIMGURL + 'terminalIcons/',
		str_imgSrc = '';
	
	if ( n_iconType == 0 ) {	// 车
		str_tempImgUrl = 27; // n_degree;
		str_dir = BASEDEGREEIMGURL;
		b_isCar = true;
	} else if ( n_iconType == 1 ) {	// 摩托车
		str_tempImgUrl = 'moto';
		b_isCar = true;
	} else if ( n_iconType == 2 ) {	// 人
		str_tempImgUrl = 'person';
	} else if ( n_iconType == 3 ) {	// 图标
		str_tempImgUrl = 'default';
		b_isCar = true;
	} else if ( n_iconType == 4 ) {	// 警车
		str_tempImgUrl = 'police';
		b_isCar = true;
	} else if ( n_iconType == 5 ) {	// 警摩托车
		str_tempImgUrl = 'policeMoto';
		b_isCar = true;
	} else {
		str_tempImgUrl = 27; // n_degree;
		str_dir = BASEDEGREEIMGURL;
		b_isCar = true;
	}
	if ( str_loginSt == '0' ) {
		str_tempImgUrl += '_logout';
	}
	if ( b_flagTrace && b_isCar ) {	// 甩尾动态图
		str_tempImgUrl += '_trace';
	}
	
	//str_imgSrc = obj_markerPngForBase64[str_tempImgUrl];
	//return str_imgSrc;
	return str_dir + str_tempImgUrl + '.png';
}

/**
* 设置是否要启动追踪效果
*/
dlf.setTrack = function(arr_tempTids, selfItem) {
	var str_type = typeof(arr_tempTids),
		arr_tids = [],
		arr_openTids = [],
		n_isOpen = 0;

	if ( str_type == 'string' ) {	// 单个定位器的开启追踪
		arr_tids.push(arr_tempTids);
		var n_cLogin = $('.j_currentCar').attr('clogin');
		
		if ( dlf.fn_getActionTrackStatus(arr_tempTids) != 'yes' ) {
			if ( n_cLogin == 0 ) {
				//dlf.fn_jNotifyMessage('定位器不在线！', 'message', false, 4000);
				//return;
			}
		}
		
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
		
		obj_selfItem.html(str_tempMsg);
		obj_actionTrack[str_tid].status = str_tempAction;
		if ( obj_selfMarker ) {
			// obj_selfMarker.track = n_track;	// 存储第一次开启追踪、移除存储第一次开启追踪
			/*obj_selfInfoWindow = obj_selfMarker.selfInfoWindow,  // 获取吹出框
			str_content = obj_selfInfoWindow.getContent(); // 吹出框内容
			
			str_content = str_content.replace(str_tempOldMsg, str_tempMsg);
			obj_selfInfoWindow.setContent(str_content);		// todo
			obj_selfMarker.selfInfoWindow = obj_selfInfoWindow;*/
			
			// todo infowindow 追踪
			var obj_carDatas = $('.j_carList').data('carsData'),
				obj_tempCarData = obj_carDatas[str_tid],
				obj_selfInfoWindow = obj_selfMarker.infoWindow,
				str_carTid = $('.j_carList a[class*=j_currentCar]').attr('tid');
			
			if ( $('.j_carList a[class*=j_currentCar]').length == 0 ) {
				str_carTid = str_currentTid;
			}			
			
			if ( str_carTid == str_tid ) {
				if ( obj_selfInfoWindow ) {
					dlf.fn_createMapInfoWindow(obj_tempCarData, 'actiontrack')
					obj_selfMarker.openInfoWindow(obj_mapInfoWindow); // 显示吹出框
				}
			}
		}
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
dlf.fn_updateOpenTrackStatusColor = function(str_tid, str_order) {
	var str_actionTrack = dlf.fn_getActionTrackStatus(str_tid),
		str_color = '',
		str_carcTid = $('.j_currentCar').attr('tid');
	
	if ( $('.j_currentCar').length == 0 ) {
		str_carcTid = str_currentTid;
	}
	
	if ( str_tid == str_carcTid ) {
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
dlf.fn_updateAlias = function() {
	var	cnum = dlf.fn_encode($('#t_cnum').val()),	// 车牌号
		tmobile = $('#tmobileContent').html(),
		obj_car = $('.j_carList .j_currentCar'),
		obj_selfMarker = obj_selfmarkers[obj_car.attr('tid')],	// obj_car.data('selfmarker'),
		str_alias = '',
		obj_terminal = obj_car.next();
		
	if ( cnum != '' ) {
		str_alias = cnum;
	} else {
		str_alias = tmobile;
	}
	if ( obj_selfMarker ) {	// 修改 marker label 别名
		var str_tid = $('.j_carList .j_currentCar').attr('tid');
		
		obj_selfMarker.getLabel().setContent(str_alias);
		
		var obj_carDatas = $('.j_carList').data('carsData')[str_tid];
			
		obj_carDatas.alias = str_alias;
		
		if ( obj_selfMarker && obj_selfMarker.infoWindow ) {
			dlf.fn_createMapInfoWindow(obj_carDatas, 'actiontrack');
			obj_selfMarker.openInfoWindow(obj_mapInfoWindow); // 显示吹出框
		}
	}
	obj_terminal.html(str_alias);
	str_alias = dlf.fn_decode(str_alias);
	obj_terminal.attr('title', str_alias);
	obj_car.attr('alias', str_alias);
}
})();
