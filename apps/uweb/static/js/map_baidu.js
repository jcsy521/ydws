/*
* 地图相关操作方法
* postAddress: 逆地址编码获取位置描述
* mapObj: 地图对象
* obj_NavigationControl: 比例尺缩放对象
* obj_MapTypeControl: 地图类型对象
* obj_trafficControl: 路况信息对象
*/
var postAddress = null,
	mapObj = null,
	obj_NavigationControl = null,
	obj_MapTypeControl = null,
	obj_trafficControl = null,
	obj_selfMarkers = {};
(function () {

/**
* 加载百度MAP
*/
window.dlf.fn_loadMap = function() {                  	
	mapObj = new BMap.Map('mapObj'); // 创建地图实例
	markerPoint = new BMap.Point(116.39825820922851 ,39.904600759441024); // 创建点坐标
	mapObj.centerAndZoom(markerPoint, 15); // 初始化地图，设置中心点坐标和地图级别 
	mapObj.enableScrollWheelZoom();  // 启用滚轮放大缩小。

	viewControl = new BMap.OverviewMapControl({isOpen: true});
	obj_NavigationControl = new BMap.NavigationControl({anchor: BMAP_ANCHOR_TOP_LEFT});
	
	mapObj.addControl(obj_NavigationControl);	// 比例尺缩放
	mapObj.addControl(viewControl); //添加缩略地图控件
	mapObj.addControl(new BMap.ScaleControl());  // 添加比例尺控件
	dlf.fn_setMapControl(10); /*设置相应的地图控件及服务对象*/
}

/**
* 设置地图上地图类型,实时路况的位置
* n_NumTop: 相对于地图上侧做的偏移值 
*/
window.dlf.fn_setMapControl = function(n_NumTop) {
	/*移除相应的地图控件及服务对象*/
	mapObj.removeControl(obj_MapTypeControl);	// 地图类型 自定义显示 普通地图和卫星地图
	mapObj.removeControl(obj_trafficControl); //添加路况信息控件
	
	/*重新声明相应的地图控件及服务对象*/
	obj_MapTypeControl = new BMap.MapTypeControl({mapTypes: [BMAP_NORMAL_MAP,BMAP_SATELLITE_MAP], offset: new BMap.Size(100, n_NumTop)});
	obj_trafficControl = new BMapLib.TrafficControl(new BMap.Size(10, n_NumTop));

	/*添加相应的地图控件及服务对象*/
	mapObj.addControl(obj_MapTypeControl);	// 地图类型 自定义显示 普通地图和卫星地图
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
		obj_polyLine = new BMap.Polyline(arr_drawLine);
		if ( obj_options ) {
			obj_polyLine.setStrokeColor(obj_options.color);
		}
		dlf.fn_addOverlay(obj_polyLine);
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
			mapObj.zoomOut();
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
* isOpenWin: 是否打开infowindow
* n_index: 轨迹点的索引值，根据其值获取对应的位置
* n_counter : draw 时根据值修改数组中点的位置描述  下次就不用重新获取位置
*/
window.dlf.fn_addMarker = function(obj_location, str_iconType, n_carNum, isOpenWin, n_index) { 
	var n_degree = dlf.fn_processDegree(obj_location.degree),  // 车辆方向角
		str_imgUrl = n_degree, 
		myIcon = new BMap.Icon(BASEIMGURL + str_imgUrl + '.png', new BMap.Size(34, 34)),
		mPoint = new BMap.Point(obj_location.clongitude/NUMLNGLAT, obj_location.clatitude/NUMLNGLAT), 
		infoWindow = new BMap.InfoWindow(dlf.fn_tipContents(obj_location, str_iconType, n_index)),  // 创建信息窗口对象;
		marker = null,
		str_alias = obj_location.alias,
		str_tid = obj_location.tid,
		obj_carA = $('.j_carList a[tid='+ str_tid +']'),
		label = null; 

	if ( !str_alias ) {	// 实时定位无alias，则根据tid获取对应定位器别名
		str_alias = obj_carA.next().html();
	}
	label = new BMap.Label(str_alias, {offset:new BMap.Size(31, 22)});
	label.setStyle({'backgroundColor': '#000000', 'fontSize': '13px', 'height': '20px','borderWidth':'0px','borderColor': '#000',
	'opacity': '0.55','filter': 'alpha(opacity=50)','lineHeight': '20px','borderRadius': '6px','paddingLeft': '5px','paddingRight': '5px', 'color': '#ffffff'});	// 设置label样式
	/**
	* 设置marker图标
	*/
	if ( str_iconType == 'start' ) {	// 轨迹起点图标
		myIcon.imageUrl = BASEIMGURL + 'green_MarkerA.png';
	} else if ( str_iconType == 'end' ) {	// 轨迹终点图标
		myIcon.imageUrl = BASEIMGURL + 'green_MarkerB.png';
	}
	
	marker= new BMap.Marker(mPoint, {icon: myIcon}); 
	marker.setOffset(new BMap.Size(0, 0));
	marker.selfInfoWindow = infoWindow;
	if ( str_iconType == 'draw' ) {	// 轨迹播放点的marker设置
		actionMarker = marker;
		marker.setIcon(marker.getIcon().setImageUrl( BASEIMGURL + n_degree+'.png' ));
	} else if ( str_iconType == 'actiontrack' ) {	// lastinfo or realtime marker点设置
		marker.setLabel(label);
		var obj_carItem = $('.j_carList .j_terminal').eq(n_carNum);
		obj_selfmarkers[str_tid] = marker;
		//obj_carItem.data('selfmarker', marker);
		//obj_carItem.data('selfLable', marker.getLabel());
		dlf.fn_setOptionsByType('center', mPoint);
	} else if ( str_iconType == 'start' || str_iconType == 'end' ) {
		marker.setOffset(new BMap.Size(-1, -14));
	}
	mapObj.addOverlay(marker);	//向地图添加覆盖物 
	if ( isOpenWin ) {
		marker.openInfoWindow(infoWindow);
	}
	
	/**
	* marker click事件
	*/
	marker.addEventListener('click', function(){
	   if ( str_iconType == 'actiontrack' ) { // 主页车辆点击与左侧车辆列表同步
			var obj_carItem = $('.j_carList .j_terminal').eq(n_carNum),
				str_className = obj_carItem.attr('class'), 
				str_tid = obj_carItem.attr('tid');
				
			if ( str_className.search('j_currentCar') != -1 ) { // 如果是当前车的话就直接打开吹出框，否则switchcar中打开infoWindow
				this.openInfoWindow(this.selfInfoWindow); 
				return;
			} else {
				if ( dlf.fn_userType() ) {
					$('.jstree-clicked').removeClass('jstree-clicked');
					$('.j_leafNode a[tid='+ str_tid +']').addClass('jstree-default jstree-clicked');
				}
			}			
			dlf.fn_switchCar(str_tid, obj_carItem); // 车辆列表切换
		} else {
			var str_name = obj_location.name,
				n_beginNum =0,
				n_endNum = 0,
				str_address = '',
				address = '';
				
			if ( str_name != '' ) {
				var str_content = infoWindow.getContent();
				if ( str_content.search('<a') != -1 ) {
					n_beginNum = str_content.indexOf('位置：');
					n_endNum = str_content.indexOf('</a></label>') + 12;
					str_address = str_content.substring(n_beginNum, n_endNum),
					address = '位置： <lable class="lblAddress">'+ str_name +'</label>';
					str_content = str_content.replace(str_address, address);
					marker.selfInfoWindow.setContent(str_content);
				}
			}
			this.openInfoWindow(infoWindow);
		}
	});
}

/**
* 吹出框内容更新
* obj_location: 位置信息
* str_iconType: marker类型
* n_index: 轨迹索引
*/
window.dlf.fn_tipContents = function (obj_location, str_iconType, n_index) { 
	var	address = obj_location.name, 
		speed = obj_location.speed,
		date = dlf.fn_changeNumToDateString(obj_location.timestamp),
		n_degree = obj_location.degree, 
		str_degree = dlf.fn_changeData('degree', n_degree), //方向角处理
		str_degreeTip = '方向角：' + Math.round(n_degree),
		str_tid = obj_location.tid,
		str_clon = obj_location.clongitude/NUMLNGLAT,
		str_clat = obj_location.clatitude/NUMLNGLAT,
		str_type = obj_location.type == GPS_TYPE ? 'GPS定位' : '基站定位',
		str_alias = obj_location.alias,
		str_title = '车辆：',
		str_tempMsg = '开始跟踪',
		str_actionTrack = obj_actionTrack[str_tid],	// $('.j_carList a[tid='+str_tid+']').attr('actiontrack'),
		str_html = '<div id="markerWindowtitle" class="cMsgWindow">';
		
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
					str_newClat = obj_location.clatitude;
				
				if ( $('.j_carList').data('carsData') != undefined ) {
					obj_oldCarData = $('.j_carList').data('carsData')[str_tid];
					str_oldClon = obj_oldCarData.clongitude;
					str_oldClat = obj_oldCarData.clatitude;
				}
				
				if ( obj_selfmarker ) {	// 第一次加载 没有selfmarker 
					if ( Math.abs(str_oldClon-str_newClon) < 100 || Math.abs(str_oldClat-str_newClat) < 100 ) {	// 判断和上次经纬度的差是否在100之内，在的话认为是同一个点
						var obj_infowindow = obj_selfmarker.selfInfoWindow;
						
						if ( obj_infowindow && obj_infowindow != null ) {	// infowindow中位置替换
							var str_content = obj_infowindow.getContent(),
								n_beginNum = str_content.indexOf('位置： ')+30,
								n_endNum = str_content.indexOf('</label></li><li class="top10">'),
								str_address = str_content.substring(n_beginNum, n_endNum);
								
							address = str_address;
						}
					} else {	// 否则重新获取						
						address = '正在获取位置描述' + WAITIMG; 
						dlf.fn_getAddressByLngLat(str_clon, str_clat, str_tid, 'lastinfo');
					}
				} else {
					address = '正在获取位置描述' + WAITIMG; 
					dlf.fn_getAddressByLngLat(str_clon, str_clat, str_tid, 'lastinfo');
				}
			} else if ( str_iconType == 'draw' || str_iconType == 'start' || str_iconType == 'end' )  {
				address = '<a href="#" title="获取位置" onclick="dlf.fn_getAddressByLngLat('+str_clon+', '+str_clat+',\''+str_tid+'\',\'draw\','+ n_index +');">获取位置</a>'; 
			} else {
				address = '<a href="#" title="获取位置" onclick="dlf.fn_getAddressByLngLat('+str_clon+', '+str_clat+',"'+str_tid+',event");">获取位置</a>'; 
			}
		}
	} else {	// 判断是否是当前车辆
		var str_currenttid = $('.j_carList .j_currentCar').attr('tid');
		
		if ( str_tid == str_currenttid && str_iconType == 'actiontrack' ) {
			$('#address').html(address);
		}
	}
	$('.j_carList a[tid='+ str_tid +']').data('address', address);	// 临时存储每辆车的位置描述
	
	if (speed == '' || speed == 'undefined' || speed == null || speed == ' undefined' || typeof speed == 'undefined') { 
		speed = '0'; 
	} else {
		speed = speed;
	}
	if ( str_alias ) { // 如果是轨迹回放 
		str_title += str_alias;
	} else {
		str_title += $('.j_carList a[tid='+str_tid+']').next().html();
	}
	str_html += '<h4 tid="'+obj_location.tid+'">'+str_title+'</h4><ul>'+ 
				'<li><label>速度： '+ speed+' km/h</label>'+
				'<label class="labelRight" title="'+str_degreeTip+'">方向： '+str_degree+'</label></li>'+
				'<li><label>经度： E '+str_clon.toFixed(CHECK_ROUNDNUM)+'</label>'+
				'<label class="labelRight">纬度： N '+str_clat.toFixed(CHECK_ROUNDNUM)+'</label></li>'+
				'<li>类型： '+ str_type +'</li>'+
				'<li>时间： '+ date +'</li>' + 
				'<li>位置： <lable class="lblAddress">'+ address +'</label></li>';

	if ( str_iconType == 'actiontrack' ) {
		str_html+='<li class="top10"><a href="#" onclick="dlf.setTrack(\''+str_tid+'\', this);">'+ str_tempMsg +'</a>'+
			'<a href="#" id="trackReplay" onclick="dlf.fn_initTrack();">轨迹查询</a><a href="#" id="poiSearch" onclick="dlf.fn_POISearch('+ str_clon +', '+ str_clat +');" >周边查询</a></li>';
	}
	str_html += '</ul></div>';
	return str_html;
} 


/**
** 将获取到的name更新到marker或label上
* str_type: 轨迹或 realtime或lastinfo
* str_result: 获取到的位置
* n_index: 如果是轨迹则根据索引获取name
*/
window.dlf.fn_updateAddress = function(str_type, tid, str_result, n_index) {
	var str_result = str_result,
		obj_selfmarker = obj_selfmarkers[tid],	// $('.j_carList a[tid='+tid+']').data('selfmarker'),
		obj_addressLi = $('#markerWindowtitle ul li').eq(4);
		
	if ( str_type == 'realtime' || str_type == 'lastinfo' ) {
		var str_currentTid = $('.j_carList a[class*=j_currentCar]').attr('tid');
		// 左侧 位置描述填充
		if ( str_currentTid == tid ) {
			obj_addressLi.html('').html('位置：<lable class="lblAddress">' + str_result + '</label>');	// 替换marker上的位置描述
			$('#address').html(str_result);
		}
		if ( obj_selfmarker && obj_selfmarker != null ) {
			var str_content = obj_selfmarker.selfInfoWindow.getContent(),
				str_address = '';
				
			if ( str_content.search('正在获取位置描述...') != -1 ) {
				str_content = str_content.replace('正在获取位置描述' + WAITIMG, str_result);
			} else {
				n_beginNum = str_content.indexOf('位置： ')+30,	// <lable class="lblAddress">
				n_endNum = str_content.indexOf('</label></li><li class="top10">'),
				str_address = str_content.substring(n_beginNum, n_endNum);
				str_content = str_content.replace(str_address, str_result);
			}
			obj_selfmarker.selfInfoWindow.setContent(str_content);
		}
	} else if ( str_type == 'event' ) {
		if ( n_lon != 'none' ) {
			var str_tempAddress = str_result.length >= 30 ? str_result.substr(0,30) + '...':str_result;
		
			$('#eventResult tr').eq(tid+1).find('.j_getPosition').parent().html('<label href="#" title="'+ str_result +'">'+str_tempAddress+'</label><a href="#" c_lon="'+n_lon+'" c_lat="'+n_lat+'" class="j_eventItem viewMap" >查看地图</a>');
			arr_eventData[tid].name = str_result;
			dlf.fn_showMarkerOnEvent();
		} else {
			$('#eventResult tr').eq(tid+1).find('a').html(str_result).addClass('j_eventItem');
		}
	} else {
		if ( n_index >= 0 ) {
			arr_dataArr[n_index].name = str_result;
		}
		obj_addressLi.html('位置：' + str_result);	// 替换marker上的位置描述
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
		obj_point = new BMap.Point(n_lon, n_lat);
		
	if ( n_lon == 0 || n_lat == 0 ) {
		$('#address').html('-');
	} else {
		gc.getLocation(obj_point, function(result){
			str_result = result.address;
			if ( str_result == '' ) {
				if ( postAddress != null ) {	// 第一次如果未获取位置则重新获取一次,如果还未获得则显示"无法获取"
					clearTimeout(postAddress);
					str_result = '-';
					dlf.fn_updateAddress(str_type, tid, str_result, n_index);
				} else {	// 如果未获取到位置描述  5秒后重新获取					
					str_result = '正在获取位置描述' + WAITIMG;
					dlf.fn_updateAddress(str_type, tid, str_result, n_index, 'none');
					postAddress = setTimeout(function() {
						dlf.fn_getAddressByLngLat(n_lon, n_lat, tid, str_type, n_index);
					}, 5000);
				}
			} else {
				dlf.fn_updateAddress(str_type, tid, str_result, n_index, n_lon, n_lat);
			}
		});
	}
	return str_result;
}
})();