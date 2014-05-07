/*
* 地图相关操作方法
* postAddress: 逆地址编码获取位置描述
* mapObj: 地图对象
* obj_NavigationControl: 比例尺缩放对象
* obj_MapTypeControl: 地图类型对象
* obj_trafficControl: 路况信息对象
* obj_viewControl: 小地图
*/
var postAddress = null,
	mapObj = null,
	obj_NavigationControl = null,
	obj_MapTypeControl = null,
	obj_trafficControl = null,
	obj_viewControl = null;
	
(function () {

/**
* 加载百度MAP
*/
window.dlf.fn_loadMap = function(mapContainer) {                  	
	mapObj = new BMap.Map(mapContainer); // 创建地图实例
	markerPoint = new BMap.Point(116.39825820922851 ,39.904600759441024); // 创建点坐标
	mapObj.centerAndZoom(markerPoint, 12); // 初始化地图，设置中心点坐标和地图级别 
	mapObj.enableScrollWheelZoom();  // 启用滚轮放大缩小。

	obj_NavigationControl = new BMap.NavigationControl({anchor: BMAP_ANCHOR_TOP_LEFT});
	
	mapObj.addControl(obj_NavigationControl);	// 比例尺缩放
	mapObj.addControl(new BMap.ScaleControl());  // 添加比例尺控件
	
	/*添加相应的地图控件及服务对象*/
	mapObj.addControl(new BMap.MapTypeControl({mapTypes: [BMAP_NORMAL_MAP,BMAP_SATELLITE_MAP], offset: new BMap.Size(100, 10)}));	// 地图类型 自定义显示 普通地图和卫星地图
	
	mapObj.addControl(new BMap.OverviewMapControl()); //添加缩略地图控件
 	if ( mapContainer == 'mapObj' ) {
 		dlf.fn_setMapControl(10); /*设置相应的地图控件及服务对象*/
 	}
}

/**
* 设置地图控件的显示隐藏
* b_menu: true: 显示 false: 隐藏
*/
window.dlf.fn_hideControl = function(b_menu) {
	/*移除相应的地图控件及服务对象*/
	if ( obj_trafficControl != null ) {
		mapObj.removeControl(obj_trafficControl); //移除路况信息控件
		obj_trafficControl = null;
	}
}

/**
* 设置地图上地图类型,实时路况的位置
* n_NumTop: 相对于地图上侧做的偏移值 
*/
window.dlf.fn_setMapControl = function(n_NumTop) {
	/*移除相应的地图控件及服务对象*/
	if ( obj_trafficControl ) {
		mapObj.removeControl(obj_trafficControl); //移除路况信息控件
	}
	/*重新声明相应的地图控件及服务对象*/
	obj_trafficControl = new BMapLib.TrafficControl(new BMap.Size(10, n_NumTop));
	
	/*添加相应的地图控件及服务对象*/
	mapObj.addControl(obj_trafficControl); //添加路况信息控件
}
/**
* 百度地图生成点
*/
window.dlf.fn_createMapPoint = function(n_lon, n_lat) {
	if ( n_lon == 0 || n_lat == 0 ) { 
		return '-';
	} else {
		return new BMap.Point(n_lon/NUMLNGLAT, n_lat/NUMLNGLAT);
	}
}

/**
* 生成线
* arr_drawLine: 轨迹线的点集合
* options: 轨迹线的属性
*/
window.dlf.fn_createPolyline = function(arr_drawLine, obj_options) {
	var obj_polyLine = null;
	if ( arr_drawLine.length > 0 ) {
		obj_polyLine = new BMap.Polyline(arr_drawLine, {'strokeOpacity': 0.5});
		dlf.fn_addOverlay(obj_polyLine);
		if ( obj_options ) {
			var str_color = obj_options.color,
				str_style = obj_options.style,
				n_weight = obj_options.weight;
			
			if ( str_color ) {
				obj_polyLine.setStrokeColor(str_color);
			}
			if ( str_style ) {
				obj_polyLine.setStrokeStyle(str_style);
			}
			if ( n_weight ) {
				obj_polyLine.setStrokeWeight(n_weight);
			}
		}
	}
	return obj_polyLine;
}

/**
* 中心点移动方法、中心点及比例尺设置、viewport设置
* type: center(中心点)、zoom(地图级别)、centerAndZoom(设置中心点和比例尺)、viewport(根据对角点计算比例尺进行显示)
* centers: point对象
* zoom: 地图级别值
*/
window.dlf.fn_setOptionsByType = function(type, centers, zoom) {
	switch (type) {
		case 'center':	// 设置中心点
			mapObj.setCenter(centers);
			break;
		case 'zoom': 
			mapObj.setZoom(zoom);
			break;
		case 'centerAndZoom':
			mapObj.centerAndZoom(centers, zoom);
			break;
		case 'viewport':
			mapObj.setViewport(centers);
			// mapObj.zoomOut();
			break;
	}
}
/**
* 百度地图添加图层
* obj_overlay: 要添加的图层对象
*/
window.dlf.fn_addOverlay = function(obj_overlay) {
	mapObj.addOverlay(obj_overlay);
}

/**
* 清除页面上的地图图形数据
* obj_overlays: 要删除的图层对象,如果没有则清除地图上所有图层
*/
window.dlf.fn_clearMapComponent = function(obj_overlays) {
	if ( obj_overlays ) {
		mapObj.removeOverlay(obj_overlays);
	} else {
		mapObj.clearOverlays();
	}
}

/**
* 周边查询
* obj_keywords: 关键字
* n_clon：经度
* n_clat: 纬度
*/
window.dlf.fn_searchPoints = function (obj_keywords, n_clon, n_clat) {
	var str_keywords = '',
		n_bounds = parseInt($('#txtBounds').val()),
		obj_kw = $('#txtKeywords');
		
	if ( obj_keywords !='' ) {
		str_keywords = obj_keywords.html();
		obj_kw.val(str_keywords); // 填充关键字文本框
	} else {
		str_keywords = obj_kw.val();
		if ( str_keywords == '查找其他关键词' ) {
			$('#keywordsTip').html('请输入关键词'); return;
		} else {
			$('#keywordsTip').html('');
		}
	}
	if ( !obj_localSearch ) { 
		obj_localSearch = new BMap.LocalSearch(mapObj, {
				renderOptions:{map: mapObj} // 查询结果显示在地图容器
		}); 
	}
	obj_localSearch.searchNearby(str_keywords, new BMap.Point(n_clon, n_clat), n_bounds);
	obj_localSearch.disableFirstResultSelection();	// 禁用自动选择第一个检索结果
	obj_localSearch.disableAutoViewport();	// 禁用根据结果自动调整地图层级
}

/**
*添加标记
* obj_location: 位置信息
* str_iconType: marker类型
* n_carNum: 车辆编号
* n_index: 轨迹点的索引值，根据其值获取对应的位置
* n_counter : draw 时根据值修改数组中点的位置描述  下次就不用重新获取位置
*/
window.dlf.fn_addMarker = function(obj_location, str_iconType, str_tempTid, n_index) {
	var n_degree = dlf.fn_processDegree(obj_location.degree),  // 车辆方向角
		str_imgUrl = 'default', 
		myIcon = new BMap.Icon(BASEIMGURL + str_imgUrl + '.png', new BMap.Size(34, 34)),
		n_clon = obj_location.clongitude,
		n_clat = obj_location.clatitude,
		n_lon = obj_location.longitude,
		n_lat = obj_location.latitude,
		mPoint = new BMap.Point(n_clon/NUMLNGLAT, n_clat/NUMLNGLAT), 
		marker = null,
		str_alias = obj_location.alias,
		str_tid = obj_location.tid,
		n_iconType = obj_location.icon_type,	// icon_type 
		str_loginSt =  obj_location.login,
		n_timestamp = obj_location.timestamp,
		obj_carA = $('.j_carList a[tid='+ str_tid +']'),
		label = null,
		b_userType = dlf.fn_userType();

	// kjj add in 2013-09-30 如果是轨迹、告警 经纬度偏转失败，不去处理
	if ( str_iconType == 'start' || str_iconType == 'end' || str_iconType == 'draw' || str_iconType == 'eventSurround' ) {
		if ( n_lon == 0 || n_lat == 0 || n_clon == 0 || n_clat == 0 ) {
			return;
		}
	}
	
	if ( !str_alias ) {	// 实时定位无alias，则根据tid获取对应定位器别名
		str_alias = b_userType == true ? obj_carA.attr('alias') : obj_carA.next().html();
	}
	str_alias = dlf.fn_encode(str_alias);
	label = new BMap.Label(str_alias, {offset:new BMap.Size(31, 22)});
	label.setStyle({'backgroundColor': '#fff', 'fontSize': '13px', 'lineheight': '20px','borderRadius': '6px','padding': '5px','color': '#000'});	// 设置label样式
	/**
	* 设置marker图标
	*/
	if ( b_userType ) {	// 集团用户修改图标
		if ( !n_iconType ) {
			n_iconType = obj_carA.attr('icon_type');
		}
		/**
		* KJJ add in 2014.04.28
		* 判断5分钟之内的点，速度大于5的证明终端在移动
		*/
		var b_flag = false,
			n_nowtime = new Date().getTime()/1000;
		
		if ( n_nowtime - n_timestamp < 300 && n_speed > 5 ) {	// 5分钟之内的点
			b_flag = true;
			myIcon.setSize(new BMap.Size(100, 100));
			myIcon.setImageOffset(new BMap.Size(-30, -35));
		}
		myIcon.imageUrl = dlf.fn_setMarkerIconType(n_degree, n_iconType, str_loginSt, b_flag);	// 集团用户设置marker的图标		
	}
	if ( str_iconType == 'start' ) {	// 轨迹起点图标
		myIcon.imageUrl = BASEIMGURL + 'green_MarkerA.png';
	} else if ( str_iconType == 'end' ) {	// 轨迹终点图标
		myIcon.imageUrl = BASEIMGURL + 'green_MarkerB.png';
	} else if ( str_iconType == 'delay' ) {	// 停留点图标
		myIcon.imageUrl = BASEIMGURL + 'delay_Marker.png';
	} else if ( str_iconType == 'alarmInfo' ) {
		myIcon.imageUrl = BASEIMGURL + 'alarmsign.gif';
	}
	marker= new BMap.Marker(mPoint, {icon: myIcon});
	marker.setOffset(new BMap.Size(0, 0));
	
	if ( str_iconType == 'draw' ) {	// 轨迹播放点的marker设置
		actionMarker = marker;
	} else if ( str_iconType == 'actiontrack' ) {	// lastinfo or realtime marker点设置
		marker.setLabel(label);
		marker.setTitle(str_alias);
		obj_selfmarkers[str_tid] = marker;
		
		// dlf.fn_setOptionsByType('center', mPoint);
	} else if ( str_iconType == 'region' ) {
		obj_selfmarkers[str_tid] = marker;
	} else if ( str_iconType == 'start' || str_iconType == 'end' || str_iconType == 'delay' ) {
		if ( str_iconType != 'delay' ) {
			marker.setTop(true);
		}
		marker.setOffset(new BMap.Size(-1, -14));
	} else if ( str_iconType == 'eventSurround' ) {
		marker.setLabel(label);
		marker.setTitle(str_alias);
	} else if ( str_iconType ==	'alarmInfo' ) {
		marker.getIcon().imageOffset = new BMap.Size(5, 5);
	}  
	//if ( !dlf.fn_userType() ) { // 个人用户向地图添加标记,集团用户使用聚合
		mapObj.addOverlay(marker);	//向地图添加覆盖物 
	//}
	/**
	* marker click事件
	*/
	marker.addEventListener('click', function() {
		if ( str_iconType == 'actiontrack' ) { // 主页车辆点击与左侧车辆列表同步
			var obj_carItem = $('.j_carList .j_terminal[tid='+ str_tempTid +']'),				
				str_className = obj_carItem.attr('class'), 
				str_tid = str_tempTid;
			
			if ( str_className.search('j_currentCar') != -1 ) { // 如果是当前车的话就直接打开吹出框，否则switchcar中打开infoWindow
				var obj_carDatas = $('.j_carList').data('carsData'),
					obj_tempCarData = obj_carDatas[str_tid];
			
				dlf.fn_createMapInfoWindow(obj_tempCarData, str_iconType);
				this.openInfoWindow(obj_mapInfoWindow);
				fn_infoWindowCloseShow();
				dlf.fn_updateOpenTrackStatusColor(str_tid);
				return;
			} else {
				if ( dlf.fn_userType() ) {
					$('.jstree-clicked').removeClass('jstree-clicked');
					$('.j_leafNode a[tid='+ str_tid +']').addClass('jstree-default jstree-clicked');
				}
			}
			fn_infoWindowCloseShow();
			dlf.fn_switchCar(str_tid, obj_carItem); // 车辆列表切换
		} else {
			dlf.fn_createMapInfoWindow(obj_location, str_iconType, n_index);
			this.openInfoWindow(obj_mapInfoWindow);
		}
	});
	return marker;
}

// 百度分享js引用
window.dlf.fn_loadBaiduShare = function() {
	var obj_script = document.createElement('script'),
		obj_share = $('#bdshare_s');
	
	if ( dlf.fn_isEmptyObj(obj_share) ) {
		obj_share.remove();
	}
	obj_script.setAttribute('type', 'text/javascript');
	obj_script.setAttribute('id', 'bdshell_js');
	document.getElementsByTagName('head')[0].appendChild(obj_script);
	setTimeout(function() {
		document.getElementById("bdshell_js").src = "http://bdimg.share.baidu.com/static/js/shell_v2.js?cdnversion=" + Math.ceil(new Date()/3600000);
	}, 1000);
}

/**
* kjj add in 2013-10-11 
* 中英文长度大于Ilength的显示省略号
* str: 要截取的字符串
* n_tempLength: 要截取的长度
*/
function CutStrLength(str, n_tempLength) {
	var n_chineseLength = 0,
		n_charLength = 0, 
		n_totalLength = 0;
	
	for( var i = 0; i < n_tempLength; i++ ) {
		if ( str.charCodeAt(i) > 255) {
			n_chineseLength+=2;
		} else {
			n_charLength+=1;
		}
		n_totalLength+=1;		
		if ( n_chineseLength+n_charLength == n_tempLength ) {
			return (str.substring(0,n_totalLength));
			break;
		}
		if ( n_chineseLength+n_charLength > n_tempLength ) {
			return (str.substring(0,n_totalLength-1) + '...' );
			break;
		}
	}
}

/**
* kjj update in 2013-10-11
* 截取字符串 kjj add 2013-08-21
* str_temp: 要截取的字符串
*/ 
function fn_cutString(str) {
	var theLen = 0;
	
	for( i = 0;i < str.length; i++ ) {
		if(str.charCodeAt(i)>255) {
			theLen=theLen+2;
		} else {
			theLen=theLen+1;
		}
	}
	if( theLen > 30 ) {
		str = CutStrLength(str, 60);
	}
	return str;
}

/**
* 吹出框的关闭按钮显示
*/
function fn_infoWindowCloseShow() {
	$('#markerWindowtitle').parent().parent().next().show();//显示关闭按钮
}

/*
* 创建地图吹出框对象
*/
window.dlf.fn_createMapInfoWindow = function(obj_location, str_type, n_pointIndex) {
	if ( !obj_mapInfoWindow ) {
		obj_mapInfoWindow = new BMap.InfoWindow(dlf.fn_tipContents(obj_location, str_type, n_pointIndex));
		
		obj_mapInfoWindow.addEventListener('close', function(e) {	// 吹出框关闭
			var obj_markerRegion = $('.j_body').data('markerregion');
			
			if ( obj_markerRegion ) {
				dlf.fn_clearMapComponent(obj_markerRegion);
			}
		});
	} else {
		obj_mapInfoWindow.setContent(dlf.fn_tipContents(obj_location, str_type, n_pointIndex));
	}
	mapObj.closeInfoWindow();
	//注销之前的窗口事件
	obj_mapInfoWindow.removeEventListener('open', fn_infoWindowTextUpdate);
	//重新绑定吹出框事件
	obj_mapInfoWindow.addEventListener('open', fn_infoWindowTextUpdate(obj_location));
}

/**
* 吹出框打开方法的函数
*/
function fn_infoWindowTextUpdate(obj_location) { 
	var n_clon = obj_location.clongitude,
		n_clat = obj_location.clatitude;
	
	dlf.fn_loadBaiduShare();
	dlf.fn_updateOpenTrackStatusColor(obj_location.tid);
	// 圆: 经纬度,半径 显示误差圈 //TODO
	var obj_circleData = {'circle': {'longitude': n_clon, 'latitude': n_clat, 'radius': obj_location.locate_error}, 'region_shape': 0};
	
	dlf.fn_displayMapShape(obj_circleData, true, true);
}


/**
* 吹出框内容更新
* obj_location: 位置信息
* str_iconType: marker类型
* n_index: 轨迹索引
*/
window.dlf.fn_tipContents = function (obj_location, str_iconType, n_index) {
	var	address = obj_location.name, 
		str_tempAddress = address,
		speed = obj_location.speed,
		n_timestamp = obj_location.timestamp,
		date = dlf.fn_changeNumToDateString(n_timestamp),
		n_degree = obj_location.degree, 
		str_imgUrl = 'default',  // 车辆方向角
		n_iconType = obj_location.icon_type,
		str_degree = dlf.fn_changeData('degree', n_degree, speed), //方向角处理
		str_degreeTip = '方向角：' + Math.round(n_degree),
		str_tid = obj_location.tid,
		str_currenttid = $('.j_carList .j_currentCar').attr('tid'),
		str_clon = obj_location.clongitude/NUMLNGLAT,
		str_clat = obj_location.clatitude/NUMLNGLAT,
		str_type = obj_location.type == GPS_TYPE ? 'GPS定位' : '基站定位',
		str_alias = obj_location.alias,
		str_delayTime = obj_location.idle_time,
		str_loginSt = obj_location.login,
		str_title = '定位器：',
		str_tempMsg = '开始跟踪',
		str_actionTrack = dlf.fn_getActionTrackStatus(str_tid),	// $('.j_carList a[tid='+str_tid+']').attr('actiontrack'),
		str_html = '<div id="markerWindowtitle" class="cMsgWindow">',
		b_routeLineWpST = $('#routeLineWrapper').is(':visible'), //线路展示窗口是否打开
		b_routeLineCreateWpST = $('#routeLineCreateWrapper').is(':visible'), // 线路新展示窗口是否打开
		b_regionWpST = $('#regionWrapper').is(':visible'),
		b_regionCreateWpST = $('#regionCreateWrapper').is(':visible'),
		b_corpRegionWpST = $('#corpRegionWrapper').is(':visible'),
		b_bindRegionWpST = $('#bindRegionWrapper').is(':visible'),
		b_bindBatchRegionWpST = $('#bindBatchRegionWrapper').is(':visible');
	
	address = fn_cutString(address);
	if ( dlf.fn_userType() ) {	// 集团用户修改图标
		var b_flag = false,
			n_nowtime = new Date().getTime()/1000;
		
		if ( n_nowtime - n_timestamp < 300 && n_speed > 5 ) {	// 5分钟之内的点
			b_flag = true;
		}
		str_imgUrl = dlf.fn_setMarkerIconType(n_degree, n_iconType, str_loginSt, true);	// 集团用户设置marker的图标
	}
	if ( str_actionTrack == 'yes' ) {
		str_tempMsg = '取消跟踪';
	}
	if (str_tid == '' || str_tid == 'undefined' || str_tid == null ) { 
		str_tid = $('.j_carList a[class*=j_currentCar]').attr('tid');
	}
	if ( address == '' || address == null ) {
		if ( str_clon == 0 || str_clat == 0 ) {
			address = '-';
		} else {
			if ( str_iconType == 'actiontrack' ) {
				/** 
				* 判断经纬度是否和上一次经纬度相同   如果相同直接拿上一次获取位置
				*/
				var obj_currentLi = $('.j_carList a[tid='+str_tid+']'),
					obj_oldCarData = null,	
					obj_selfmarker = obj_selfmarkers[str_tid],
					str_oldClon = 0,
					str_oldClat = 0,
					str_newClon = obj_location.clongitude,
					str_newClat = obj_location.clatitude,
					obj_carsData = $('.j_carList').data('carsData');
				
				if ( obj_carsData != undefined ) {
					obj_oldCarData = obj_carsData[str_tid];
					if ( obj_oldCarData ) {
						str_oldClon = obj_oldCarData.clongitude;
						str_oldClat = obj_oldCarData.clatitude;
					}
				}
				address = '正在获取位置描述' + WAITIMG; 
				dlf.fn_getAddressByLngLat(str_clon, str_clat, str_tid, 'actiontrack');
				
			} else {
				address = '<a href="#" title="获取位置" onclick="dlf.fn_getAddressByLngLat('+str_clon+', '+str_clat+',\''+str_tid+'\',\''+ str_iconType +'\','+ n_index +');">获取位置</a>'; 
			}
		}
	} else {	// 判断是否是当前车辆
		if ( str_tid == str_currenttid && str_iconType == 'actiontrack' ) {
			$('#address').html(str_tempAddress);
		}
	}
	if ( str_iconType == 'actiontrack' ) {	// 2013-07-30 update 只有lastinfo或realtime时 存储address
		$('.j_carList a[tid='+ str_tid +']').data('address', address);	// 临时存储每辆车的位置描述
	}
	
	if ( speed == '' || speed == 'undefined' || speed == null || speed == ' undefined' || typeof speed == 'undefined' ) { 
		speed = '0'; 
	} else {
		speed = speed;
	}
	if ( str_alias ) { // 如果是轨迹回放 
		str_alias = str_alias;
	} else {
		if ( dlf.fn_userType() ) {
			str_alias = $('.j_carList a[id=leaf_'+ str_tid +']').text().substr(2); 
		} else {
			str_alias = $('.j_carList a[tid='+str_tid+']').next().html();
		}
	}
	str_title += dlf.fn_encode(str_alias);
	if ( str_iconType == 'delay' ) {	// 如果是轨迹播放的停留点 infowindow显示内容不同
		str_html += '<h4 tid="'+obj_location.tid+'">'+str_title+'</h4><ul>'+ 
					'<li><label>停留：  '+ dlf.fn_changeTimestampToString(str_delayTime) +'</label>'+
					'<li><label>开始：  '+ dlf.fn_changeNumToDateString(obj_location.start_time) +'</label>'+
					'<li><label>结束：  '+ dlf.fn_changeNumToDateString(obj_location.end_time) +'</label></li>' + 
					'<li title="'+ str_tempAddress +'">位置： <lable class="lblAddress">'+ address +'</label></li>';	
	} else {
		str_html += '<h4 tid="'+obj_location.tid+'">'+str_title+'</h4><ul>'+ 
					'<li><label>速度： '+ dlf.fn_NumForRound(speed, 1)+' km/h</label>'+
					'<label class="labelRight" title="'+str_degreeTip+'">方向： '+str_degree+'</label></li>'+
					'<li><label>经度： E '+str_clon.toFixed(CHECK_ROUNDNUM)+'</label>'+
					'<label class="labelRight">纬度： N '+str_clat.toFixed(CHECK_ROUNDNUM)+'</label></li>'+
					'<li><label>类型： '+ str_type +'</label>';
		
		// hs:2014.1.21 轨迹查询的吹出框增加里程显示
		//-==============轨迹的播放点	
		var n_tempDist = 0;
		
		if ( str_iconType == 'draw' ) { 
			// 距离计算
			if ( n_index == 0 ) {
				n_tempDist = 0;
			} else {
				for ( var i = 1; i <= counter ; i++ ) {
					var obj_currentData = arr_dataArr[i],
						obj_prevData = arr_dataArr[i - 1],
						obj_currentPoint = dlf.fn_createMapPoint(obj_currentData.clongitude, obj_currentData.clatitude),
						obj_prevPoint = dlf.fn_createMapPoint(obj_prevData.clongitude, obj_prevData.clatitude),
						n_pointDist = dlf.fn_forMarkerDistance(obj_currentPoint, obj_prevPoint);
					
					n_tempDist = n_tempDist + n_pointDist;
				}
			}
		}
		//==============轨迹的起点
		if ( str_iconType == 'start' ) { 
			n_tempDist = 0;
		}
		//==============轨迹的终点
		if ( str_iconType == 'end' ) {
			var n_dataLen = arr_dataArr.length;
			
			for ( var i = 1 ; i < n_dataLen; i++ ) {
				var obj_currentData = arr_dataArr[i],
					obj_prevData = arr_dataArr[i - 1], 
					obj_currentPoint = dlf.fn_createMapPoint(obj_currentData.clongitude, obj_currentData.clatitude),
					obj_prevPoint = dlf.fn_createMapPoint(obj_prevData.clongitude, obj_prevData.clatitude),
					n_pointDist = dlf.fn_forMarkerDistance(obj_currentPoint, obj_prevPoint);
				
				n_tempDist += n_pointDist;
			}
		}
		if ( str_iconType == 'draw' || str_iconType == 'start' || str_iconType == 'end' ) {
			str_html += '<label class="labelRight">里程： '+ dlf.fn_NumForRound(n_tempDist/1000, 1) +' km</label></li>';
		}
		
		str_html += '<li>时间： '+ date +'</li>' + 
					'<li title="'+ str_tempAddress +'">位置： <lable class="lblAddress">'+ address +'</label></li>';

		if ( str_iconType == 'actiontrack' ) {
			if ( b_regionWpST || b_bindBatchRegionWpST || b_regionCreateWpST || b_routeLineWpST || b_routeLineCreateWpST || b_corpRegionWpST || b_bindRegionWpST ) {	// 如果告警查询,告警统计 ,里程统计,围栏相关 ,轨迹是打开并操作的,不进行数据更新
			
			} else {
				str_html+='<li class="top10"><a href="#" id="infowindow_realtime"  onclick="dlf.fn_currentQuery();">定位</a><a href="#" id="trackReplay" onclick="dlf.fn_initTrack();">轨迹</a>';
				if ( dlf.fn_userType() ) {	// 如果是集团用户的话 定位、轨迹、设防撤防、参数设置放在marker上
					str_html+='<a href="#" id="corpTerminal"  onclick="dlf.fn_initCorpTerminal();">设置</a><a href="#" onclick="dlf.fn_initRegion();">围栏</a>';
				} else {	// 如果是个人用户
					str_html += '<a href="#" id="infowindow_terminal" onclick="dlf.fn_initTerminal();">设置</a>';
				}
				str_html += '<a href="#" id="infowindow_defend"  onclick="dlf.fn_defendQuery();">设防/撤防</a><a href="#"  class ="j_openTrack" onclick="dlf.setTrack(\''+str_tid+'\', this);">'+ str_tempMsg +'</a></li>';
				
				if ( str_tid == str_currenttid || !str_currenttid ) {
					var str_fileUrl = location.href,
						str_fileUrl = str_fileUrl.substr(0, str_fileUrl.length-1),
						str_iconUrl = BASEIMGURL + str_imgUrl + '.png',
						// str_iconUrl = dlf.fn_userType() == true ? dlf.fn_setMarkerIconType(n_degree, n_iconType, str_loginSt) : str_iconUrl,
						str_shareUrl = 'http://api.map.baidu.com/staticimage?&width=600&height=600&markers=' + str_clon + ',' + str_clat + '&markerStyles=-1,' + str_fileUrl + str_iconUrl + ',-1,34,34';

					str_html += '<li><span class="share">分享到：</span><div id="bdshare" class="bdshare_t bds_tools get-codes-bdshare" data="{\'url\': \''+ str_shareUrl +'\', \'text\': \'中国移动推出的“移动卫士”产品太好用了，可以实时通过手机客户端看到车辆或小孩老人的位置和行动轨迹，还有移动或震动短信报警等功能，有了这个神器，从此不怕爱车丢失了，可以登录http://www.ydcws.com/查看详细情况哦!\',\'comment\': \'无需安装：定位器可放置监控目标任何位置隐藏（如抱枕内，后备箱，座位下，储物盒，箱包内，口袋等）。\', \'pic\': \''+ str_shareUrl +'\'}"><a class="bds_tsina"></a><a class="bds_qzone"></a><a class="bds_tqf"></a><a class="bds_renren"></a></div></li>';	// 分享代码
				}
			}
		} else if ( str_iconType == 'alarmInfo' ) {
			str_html += '<li class="top10">告警： <lable class="colorRed">'+ dlf.fn_eventText(obj_location.category) +'告警</label></li>';
		}
	}
	str_html += '</ul></div>';
	return str_html;
}


/**
** 将获取到的name更新到marker或label上
* str_type: 轨迹或 realtime
* str_result: 获取到的位置
* n_index: 如果是轨迹则根据索引获取name
*/
window.dlf.fn_updateAddress = function(str_type, tid, str_result, n_index, n_lon, n_lat) {
	var str_result = str_result,
		str_tempResult = fn_cutString(str_result),	// 位置描述过长显示省略号 kjj add in 2013-08-21
		obj_selfmarker = obj_selfmarkers[tid],	// $('.j_carList a[tid='+tid+']').data('selfmarker'),
		obj_addressLi = $('#markerWindowtitle ul li').eq(4);
		
	if ( str_type == 'realtime' || str_type == 'actiontrack' ) {
		var str_currentTid = $('.j_carList a[class*=j_currentCar]').attr('tid');
		
		if ( obj_selfmarker && obj_selfmarker != null ) {			
			$('.j_carList a[tid='+ tid +']').data('address', str_result);	// 存储最新从百度获取到的位置描述以便更新页面左侧位置信息
			var obj_carDatas = $('.j_carList').data('carsData'),
				obj_tempCarData = obj_carDatas[tid];
			
			obj_tempCarData.name = str_tempResult;
			
			// 左侧 位置描述填充
			if ( str_currentTid == tid ) {
				dlf.fn_createMapInfoWindow(obj_tempCarData, str_type);
				obj_selfmarker.openInfoWindow(obj_mapInfoWindow); // 显示吹出框
				$('#address').attr('html', str_result);
			}
		}
		$('.j_carList').data('carsData', obj_carDatas);
		dlf.fn_updateOpenTrackStatusColor(tid);
	} else if ( str_type == 'event' ) {
		if ( n_lon != 'none' ) {
			var str_tempAddress = str_result.length > 28 ? str_result.substr(0,28) + '...':str_result;
			
			$('.eventSearchTable tr').eq(n_index+1).find('.j_getPosition').parent().html('<label href="#" title="'+ str_result +'">'+str_tempAddress+'</label><a href="#" c_lon="'+n_lon+'" c_lat="'+n_lat+'" class="j_eventItem viewMap" >查看地图</a>');
			arr_dwRecordData[n_index].name = str_tempAddress;
			
			dlf.fn_showMarkerOnEvent();	// 初始化查看地图事件
		}
	} else if ( str_type == 'alarmInfo' ) {
		$('.j_alarmTable').data('markers')[n_index].name = str_result;
		$('.clickedBg').children('td').eq(2).attr('html', str_result);
			//todo update address
		dlf.fn_createMapInfoWindow(obj_tempCarData, str_type, n_index);
		obj_selfmarker.openInfoWindow(obj_mapInfoWindow); // 显示吹出框
	} else if ( str_type == 'delay' || str_type == 'start' || str_type == 'end' || str_type == "draw" ) {
		var obj_trackLocation = '';
		
		$('.j_delayTbody').children('tr').eq(n_index).children('td').eq(2).html(str_result);	// 修改右侧列表位置描述
		if ( n_index >= 0 ) {
			arr_dataArr[n_index].name = str_result;
			obj_trackLocation = arr_dataArr[n_index];
			if ( str_type == 'delay' ) {
				var arr_delayPoints = $('#trackHeader').data('delayPoints');
				
				arr_delayPoints[n_index].name = str_result;
				
				obj_trackLocation = arr_delayPoints[n_index];
				
				$('#trackHeader').data('delayPoints', arr_delayPoints);
			}
		}
		
		if ( str_type == 'delay' && dlf.fn_userType() ) {	// 如果是集团的停留点的话
			obj_trackMarker = $('.delayTable').data('markers')[n_index];
		} else if ( str_type == 'draw' ) {
			obj_trackMarker = actionMarker;
		} else if ( str_type == 'start' ) {
			obj_trackMarker = $('.delayTable').data('markers')[0];
		} else if ( str_type == 'end' ) {
			obj_trackMarker = $('.delayTable').data('markers')[1];
		}
		// 根据不同的marker对象,填充数据
		if ( obj_trackMarker ) {
			dlf.fn_createMapInfoWindow(obj_trackLocation, str_type, n_index);
			obj_trackMarker.openInfoWindow(obj_mapInfoWindow); // 显示吹出框
		}
	} else {
		var obj_carDatas = $('.j_carList').data('carsData'),
				obj_tempCarData = obj_carDatas[tid];
		
		obj_tempCarData.name = str_tempResult;
		
		$('.j_carList').data('carsData', obj_carDatas);
		dlf.fn_createMapInfoWindow(obj_tempCarData, str_type, n_index);
		obj_selfmarker.openInfoWindow(obj_mapInfoWindow); // 显示吹出框
	}
}

/**
* 根据经纬度向百度获取地理位置描述
* n_lon: 经度
* n_lat: 纬度
* tid: 终端编号
* str_type: 类型: realtime lastinfo or draw
* n_index: 如果是轨迹则显示轨迹点的索引
*/
window.dlf.fn_getAddressByLngLat = function(n_lon, n_lat, tid, str_type, n_index) {
	var gc = new BMap.Geocoder(),
		str_result = '',
		str_surroundingPois = '',
		obj_point = new BMap.Point(n_lon, n_lat);
	
	if ( $('.j_currentCar').attr('tid') != tid ) {
		//return; // todo 2013.12.4
	}
	if ( str_type == 'event' ) {
		dlf.fn_ShowOrHideMiniMap(false);	// 如果是告警的获取位置，关闭小地图
	}
	gc.getLocation(obj_point, function(result){
		str_result = result.address;
		var arr_surroundingPois = result.surroundingPois;
		
		if ( arr_surroundingPois.length > 0 ) {
			str_result += '，' + arr_surroundingPois[0].title + '附近';
		}
		
		dlf.fn_updateAddress(str_type, tid, str_result, n_index, n_lon, n_lat);
	});
	return str_result;
}

/**
* kjj 2013-07-10 create
* GPS点转换成百度点
* n_lng, n_lat
* tips:  data format is jsonp
* b_geoCode: 是否进行逆地址请求
*/
window.dlf.fn_translateToBMapPoint = function(n_lng, n_lat, str_type, obj_carInfo, b_geoCode) {
	$('.j_body').data('intervalkey', true);
	//GPS坐标
	var gpsPoint = dlf.fn_createMapPoint(n_lng, n_lat);
	jQuery.ajax({
		type : 'get',
		timeout: 14000,
		url : 'http://api.map.baidu.com/ag/coord/convert?from=0&to=4&y='+ gpsPoint.lat +'&x='+ gpsPoint.lng,
		dataType : 'jsonp',
		contentType : 'application/jsonp; charset=utf-8',
		success : function(successData) {
			var n_error = successData.error,
				lng = successData.x,
				lat = successData.y
				point = new BMap.Point(lng, lat),
				str_currentTid = $($('.j_carList a[class*=j_currentCar]')).attr('tid');
			
			$('.j_body').data('intervalkey', false);
			if ( n_error == 0 ) {
				if ( str_type == 'actiontrack' ) {
					obj_carInfo.clongitude = point.lng*3600000;
					obj_carInfo.clatitude = point.lat*3600000;
					$('.j_carList').data('carsData')[obj_carInfo.tid] = obj_carInfo;
					dlf.fn_updateInfoData(obj_carInfo); // 工具箱动态数据		
					if ( str_currentTid == obj_carInfo.tid ) {	// 更新当前车辆信息
						dlf.fn_updateTerminalInfo(obj_carInfo);
					}
					// 偏转成功后进行逆地址操作 2014.1.15
					if ( b_geoCode ) {
						dlf.fn_getAddressByLngLat(obj_carInfo.clongitude, obj_carInfo.clatitude, obj_carInfo.tid, str_type);
					}
				}
			}
		},
        error : function(xyResult) {
			return;
		}
	});
}

/**
* 点击地图添加标记
*/
window.dlf.fn_clickMapToAddMarker = function() {
	//实例化鼠标绘制工具
	obj_drawingManager = new BMapLib.DrawingManager(mapObj, {
		isOpen: false, //是否开启绘制模式
		enableDrawingTool: false //是否显示工具栏
	});
	obj_drawingManager.setDrawingMode(BMAP_DRAWING_MARKER);
}

/**
* 添加线路的标记
*/
window.dlf.fn_addRouteLineMarker = function(obj_stations){ 
	var str_stationName = obj_stations.name,
		obj_stationPoint = dlf.fn_createMapPoint(obj_stations.longitude, obj_stations.latitude),
		obj_stationMarker = new BMap.Marker(obj_stationPoint); 
	
	mapObj.addOverlay(obj_stationMarker);	//向地图添加覆盖物 

	/**
	* obj_stationMarker click事件
	*/
	obj_stationMarker.addEventListener('click', function(){ 
		var str_infoWindowText = '<label class="clickWindowPolder">站点名称：'+ str_stationName +'</label>',
			obj_clickInfoWindow = new BMap.InfoWindow(str_infoWindowText);  // 创建信息窗口对象
		
		this.openInfoWindow(obj_clickInfoWindow);
		return;
	});
}

/**
* 初始化画圆及事件绑定
*/
window.dlf.fn_initCreateRegion = function() {
	//实例化鼠标绘制工具
	var str_regionType = $('.regionCreateBtnCurrent').attr('regiontype'),
		obj_regionStyleOpts = {//圆的样式
				strokeColor: '#5ca0ff',    //边线颜色。
				fillColor: '#ced7e8',      //填充颜色。当参数为空时，圆形将没有填充效果。
				strokeWeight: 0.5,       //边线的宽度，以像素为单位。
				strokeOpacity: 0.8,	   //边线透明度，取值范围0 - 1。
				fillOpacity: 0.5,      //填充的透明度，取值范围0 - 1。
				strokeStyle: 'solid' //边线的样式，solid或dashed。
			};
	
	obj_drawingManager = new BMapLib.DrawingManager(mapObj, {
		isOpen: false, //是否开启绘制模式
		enableDrawingTool: false, //是否显示工具栏
		circleOptions: obj_regionStyleOpts, //圆的样式
		polygonOptions: obj_regionStyleOpts //多边形的样式
	});
		
	if ( str_regionType == 'circle' ) {
		obj_drawingManager.setDrawingMode(BMAP_DRAWING_CIRCLE);
	} else if ( str_regionType == 'polygon' ) {
		obj_drawingManager.setDrawingMode(BMAP_DRAWING_POLYGON);
		dlf.fn_jNotifyMessage('单击鼠标开始绘制多边形。', 'message', false, 3000);
	} else {
		return;
	}
	//添加鼠标绘制工具监听事件，用于获取绘制结果
	/*obj_drawingManager.addEventListener('overlaycomplete', function(e){
		//obj_circle = e.overlay;
		 var n_radius = obj_circle.getRadius();
		
		if ( n_radius < 500 ) {
			dlf.fn_jNotifyMessage('电子围栏半径最小为500米！', 'message', false, 3000);
		} else {
			dlf.fn_closeJNotifyMsg('#jNotifyMessage');  // 关闭消息提示
		} 
	});*/
	mapObj.addEventListener('rightclick', dlf.fn_mapRightClickFun);
}

/**
* 地图的右击事件
*/
window.dlf.fn_mapRightClickFun = function() {
	if ( obj_regionShape ) { 
		dlf.fn_clearRegionShape(); // 清除页面圆形
		dlf.fn_clearMapComponent(obj_shapeLabel); // 清除地图上的半径提示
		dlf.fn_clearMapComponent(obj_shapeMarker);// 清除地图上的圆心标记
	}
	dlf.fn_mapStopDraw();
	obj_regionShape = null;
}

/**
* 地图的右击事件移除
*/
window.dlf.fn_mapRightClickRemoveFun = function() { 
	mapObj.removeEventListener('rightclick', dlf.fn_mapRightClickFun);
}

/**
* 地图开始画圆或者加点
*/
window.dlf.fn_mapStartDraw = function() { 
	obj_drawingManager.open();
}

/**
* 地图停止画图或者加点
*/
window.dlf.fn_mapStopDraw = function() {
	$('.regionCreateBtnPanel a').removeClass('regionCreateBtnCurrent currentCircle currentDrag');
	$('#regionCreate_dragMap').addClass('regionCreateBtnCurrent');
	if ( obj_drawingManager ) {	
		obj_drawingManager.close();
	}
}

/**
* 获取围栏数据
*/
window.dlf.fn_getShapeData = function() {
	if ( obj_regionShape ) {
		var str_regionType = obj_regionShape._className;
		
		if ( str_regionType == 'Circle' ) {
			obj_circleCenter = obj_regionShape.getCenter();
			
			return {'circle': {'radius': Math.round(obj_regionShape.getRadius()), 'longitude': parseInt(obj_circleCenter.lng*NUMLNGLAT), 'latitude': parseInt(obj_circleCenter.lat*NUMLNGLAT)}, 'region_type': '0'};
		} else {
			return {'points': obj_regionShape.getPath(), 'region_type': '1'};
		}
	}
}

/**
* 显示图形
*/
window.dlf.fn_displayMapShape = function(obj_shpaeData, b_seCenter, b_locateError) {
	var shapeOptions = {//样式
			strokeColor: '#5ca0ff',    //边线颜色。
			fillColor: '#ced7e8',      //填充颜色。当参数为空时，圆形将没有填充效果。
			strokeWeight: 0.5,       //边线的宽度，以像素为单位。
			strokeOpacity: 0.8,	   //边线透明度，取值范围0 - 1。
			fillOpacity: 0.5,      //填充的透明度，取值范围0 - 1。
			strokeStyle: 'solid' //边线的样式，solid或dashed。
		},
		n_region_shape = obj_shpaeData.region_shape,
		arr_calboxData = [],
		obj_tempRegionShape = null;
	
	// hs:2013.12.24 根据不同的围栏类型进行相应操作显示
	if ( n_region_shape == 0 ) { // 围栏类型 0: 圆形 1: 多边形
		var obj_regionData = obj_shpaeData.circle
			centerPoint = dlf.fn_createMapPoint(obj_regionData.longitude, obj_regionData.latitude);
			
		obj_tempRegionShape = new BMap.Circle(centerPoint, obj_regionData.radius, shapeOptions);
	} else {
		var arr_tempPolygonData = [],
			arr_polygonDatas = obj_shpaeData.polygon,
			n_lenPolygon = arr_polygonDatas.length;
		
		for ( var i = 0; i < n_lenPolygon; i++) {
			var obj_temPolygonPts = arr_polygonDatas[i],
				n_lon = obj_temPolygonPts.longitude,
				n_lat = obj_temPolygonPts.latitude;
			
			arr_tempPolygonData.push(dlf.fn_createMapPoint(n_lon, n_lat));
			//arr_calboxData.push({'clongitude': n_lon, 'clatitude': n_lat});
			arr_calboxData.push(dlf.fn_createMapPoint(n_lon, n_lat));
		}
		obj_tempRegionShape = new BMap.Polygon(arr_tempPolygonData, shapeOptions);
		centerPoint = arr_tempPolygonData[0];
	}
	// 是否是误差圈
	if ( b_locateError ) {
		var obj_markerRegion = $('.j_body').data('markerregion');
		
		if ( obj_markerRegion ) {
			dlf.fn_clearMapComponent(obj_markerRegion);
		}
		$('.j_body').data('markerregion', obj_tempRegionShape);
		mapObj.addOverlay(obj_tempRegionShape);
	} else {
		obj_regionShape = obj_tempRegionShape;
		mapObj.addOverlay(obj_regionShape);
	}
	//是否需要移动中心点
	if ( b_seCenter ) {
		mapObj.setCenter(centerPoint);
		if ( n_region_shape == 0 ) {
			// 计算bound显示 
			var obj_circleData = obj_shpaeData.circle,
				n_radius = obj_circleData.radius;
				n_lng = obj_circleData.longitude,
				n_lat = obj_circleData.latitude,
				n_otherLat = Math.abs(n_lat/NUMLNGLAT + n_radius/111000.0)*NUMLNGLAT,
				n_otherLat2 = Math.abs(n_lat/NUMLNGLAT - n_radius/111000.0)*NUMLNGLAT,
				obj_otherPoint = dlf.fn_createMapPoint(n_lng, n_otherLat),
				obj_otherPoint2 = dlf.fn_createMapPoint(n_lng, n_otherLat2);
			
			dlf.fn_setOptionsByType('viewport', [obj_otherPoint2, obj_otherPoint]);
		} else {
			//dlf.fn_caculateBox(arr_calboxData);
			dlf.fn_setOptionsByType('viewport', arr_calboxData);
		}
	}
	return obj_regionShape;
}

/***
* kjj 2013-06-05
* 计算点是否超出地图，如果超出设置地图中心点为当前点
*/
window.dlf.fn_boundContainsPoint = function(obj_tempPoint) {
	// 是否进行中心点移动操作 如果当前播放点在屏幕外则,设置当前点为中心点
	var obj_mapBounds = mapObj.getBounds(), 
		b_isInbound = null;
	
	if ( obj_mapBounds ) {
		b_isInbound = obj_mapBounds.containsPoint(obj_tempPoint);
	}
	if ( !b_isInbound ) {
		dlf.fn_setOptionsByType('center', obj_tempPoint);
	}
}

/**
* 根据操作的参数,增加聚合点
*/
window.dlf.fn_addMarkerClusterer = function(str_markerAction, arr_markers) {
	if ( !obj_mapMarkerClusterer ) {
		obj_mapMarkerClusterer = new BMapLib.MarkerClusterer(mapObj);
	}
	if ( str_markerAction == 'add' ) {
		obj_mapMarkerClusterer.addMarkers(arr_markers);
	} else if ( str_markerAction == 'remove' ) {
		obj_mapMarkerClusterer.removeMarkers(arr_markers);
	} else if ( str_markerAction == 'clear' ) {
		obj_mapMarkerClusterer.clearMarkers();
		
	}
}


})();
