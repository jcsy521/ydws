/*
* 地图相关操作方法
* postAddress: 逆地址编码获取位置描述
* mapObj: 地图对象
* obj_NavigationControl: 比例尺缩放对象
* obj_MapTypeControl: 地图类型对象
* obj_trafficControl: 路况信息对象
* obj_satellite : 卫星信息对象
*/
var postAddress = null,
	mapObj = null,
	obj_NavigationControl = null,
	obj_MapTypeControl = null,
	obj_overview = null,
	obj_trafficControl = null,
	obj_satellite = null,
	obj_selfMarkers = {};
(function () {

/**
* 加载百度MAP
*/
window.dlf.fn_loadMap = function() {       
	var opt = { 
		level: 15,	//初始地图视野级别 
		center: new MMap.LngLat(116.39825820922851,39.904600759441024),//设置地图中心点
		doubleClickZoom: true,//双击放大地图 
		scrollwheel: true	//鼠标滚轮缩放地图 
    };
  
    mapObj = new MMap.Map("mapObj",opt);
	mapObj.plugin(["MMap.ToolBar","MMap.OverView","MMap.Scale"],function() {
		toolbar = new MMap.ToolBar();
		toolbar.autoPosition=false; //加载工具条  
		mapObj.addControl(toolbar); 
		obj_overview = new MMap.OverView(); //加载鹰眼 
		mapObj.addControl(obj_overview);     
		scale = new MMap.Scale(); //加载比例尺 
		mapObj.addControl(scale); 
	});
	
	$('#mapTileLayer ul li').click(function(event) {
		var obj_tilelayer = $(this).data('tilelayer'), 
			str_id = $(this).attr('id'), 
			str_layerType = '', 
			str_background = '#cdcdcd';
			
		if ( obj_tilelayer && obj_tilelayer != undefined ) {
			dlf.fn_removeTileLayer(obj_tilelayer);
			$(this).removeData('tilelayer');
			str_background = 'white';
		} else {
			if ( str_id == 'layerForTraffic' )  {
				str_layerType = 'traffic';
			} else {
				str_layerType = 'satellite';
			}
			dlf.fn_addControl(str_layerType);
		}
		$(this).css('background-color', str_background);
	});
}

window.dlf.fn_addControl = function(str_type) {
	var opt = {}, 
		obj_tilelayer;
	
	if ( str_type == 'traffic' ) {
		opt.id = 'traffic';
		opt.zIndex = 10;
		opt.tileUrl = 'http://tm.mapabc.com/trafficengine/mapabc/traffictile?v=1.0&t=1&x=[x]&y=[y]&zoom=[z]';
		opt.getTileUrl= function(x,y,z) { 
		//取图地址 
			return "http://tm.mapabc.com/trafficengine/mapabc/traffictile?v=1.0&t=1&x="+x+"&y="+y+"&zoom="+(17-z);
		} 
		obj_tilelayer = new MMap.TileLayer(opt); 
		$('#layerForTraffic').data('tilelayer', obj_tilelayer);
	} else {
		opt.id = 'satellite';
		opt.zIndex = 5;
		opt.tileUrl = 'http://tm.mapabc.com/trafficengine/mapabc/traffictile?v=1.0&t=1&x=[x]&y=[y]&zoom=[z]';
		opt.getTileUrl= function(x,y,z) { 
		//取图地址 
			return "http://webst01.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=6&x="+x+"&y="+y+"&z="+z+"";

		} 
		obj_tilelayer = new MMap.TileLayer(opt); 
		$('#layerForSatellite').data('tilelayer', obj_tilelayer);
	}
	
	mapObj.addLayer(obj_tilelayer);
}
window.dlf.fn_removeTileLayer = function(tilelayer) {
	if ( tilelayer )  {
		mapObj.removeLayer(tilelayer);
	}
}


/**
* 设置地图上地图类型,实时路况的位置
* n_NumTop: 相对于地图上侧做的偏移值 
*/
window.dlf.fn_setMapControl = function(n_NumTop) {
	var track_display = $('#trackHeader').is(':hidden'),	
		obj_toolBar = $('.tool_mapabc').parent(),
		obj_tileLayers = $('#mapTileLayer'),
		n_tileLayerTop = obj_tileLayers.offset().top;
	
	if ( track_display ) {
		obj_toolBar.css('top', n_NumTop);
		$('.tool_mapabc').siblings('div').css('top', 28);
		obj_tileLayers.css('top', n_tileLayerTop - 30);
	} else {
		obj_toolBar.css('top', n_NumTop);
		$('.tool_mapabc').siblings('div').css('top', 28);
		obj_tileLayers.css('top', n_tileLayerTop + 30);
	}
}

/**
* 高德地图生成点
*/
window.dlf.fn_createMapPoint = function(n_lon, n_lat) {
	if ( n_lon == 0 || n_lat == 0 ) { 
		return '-';
	} else {
		return new MMap.LngLat(n_lon/NUMLNGLAT, n_lat/NUMLNGLAT);
	}
}

/**
* 生成线
* arr_drawLine: 轨迹线的点集合
* options: 轨迹线的属性
*/
window.dlf.fn_createPolyline = function(arr_drawLine, obj_options, str_tid) {
	var obj_polyLine = null;
	if ( arr_drawLine.length > 0 ) {
		var polyOption = { 
			id: 'polyline',
            path: arr_drawLine,    
            strokeColor: "blue", //线颜色  
            strokeOpacity: 0.4, //线透明度   
            strokeWeight: 3, //线宽     
            strokeStyle: "solid", //线样式   
            strokeDasharray: [10,5] //补充线样式  
		};
		
		if ( obj_options ) {
			if ( str_tid ) {	// 追踪轨迹线
				polyOption.id = 'polyline' + str_tid;
			} else {	// 动态轨迹
				polyOption.strokeColor = obj_options.color;
				polyOption.id = 'polyline_draw';
			}
		}
		obj_polyLine = new MMap.Polyline(polyOption);
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
			mapObj.setZoomAndCenter(zoom, centers);
			break;
		case 'viewport':	// todo
			var southwest = new MMap.LngLat(centers[0].lng, centers[0].lat),
				northeast = new MMap.LngLat(centers[1].lng, centers[1].lat);
				bounds = new MMap.Bounds(southwest,northeast); 
			
			mapObj.setBounds(bounds);
			mapObj.zoomOut();
			break;
	}
}
/**
* 高德地图添加图层
* obj_overlay: 要添加的图层对象
*/
window.dlf.fn_addOverlay = function(obj_overlay) {
	mapObj.addOverlays(obj_overlay);
}

/**
* 清除页面上的地图图形数据
* obj_overlays: 要删除的图层对象,如果没有则清除地图上所有图层
*/
window.dlf.fn_clearMapComponent = function(obj_overlays) {
	if ( obj_overlays ) {
		mapObj.removeOverlays(obj_overlays.id);
	} else {
		mapObj.clearOverlays();
	}
	mapObj.clearInfoWindow();	// 关闭所有infowindow
}

/**
* 周边查询 todo
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
	obj_localSearch.searchNearby(str_keywords, new MMap.LngLat(n_clon, n_clat), n_bounds);
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
		myIcon = new MMap.Icon({image: BASEIMGURL + str_imgUrl + '.png', size: new MMap.Size(34, 34)}),
		mPoint = dlf.fn_createMapPoint(obj_location.clongitude, obj_location.clatitude),
		infoWindow = new MMap.InfoWindow({content: dlf.fn_tipContents(obj_location, str_iconType, n_index)}),  // 创建信息窗口对象;
		marker = null,
		str_alias = obj_location.alias,
		str_tid = obj_location.tid,
		obj_carA = $('.j_carList a[tid='+ str_tid +']'),
		label = null,
		str_markerId = 'marker' + str_tid;
		
	if ( !str_alias ) {	// 实时定位无alias，则根据tid获取对应定位器别名
		str_alias = obj_carA.next().html();
	}
	/*label = new BMap.Label(str_alias, {offset:new BMap.Size(31, 22)});
	label.setStyle({'backgroundColor': '#000000', 'fontSize': '13px', 'height': '20px','borderWidth':'0px','borderColor': '#000',
	'opacity': '0.55','filter': 'alpha(opacity=50)','lineHeight': '20px','borderRadius': '6px','paddingLeft': '5px','paddingRight': '5px', 'color': '#ffffff'});*/	// 设置label样式
	/**
	* 设置marker图标
	*/
	if ( str_iconType == 'start' ) {	// 轨迹起点图标
		myIcon.image = BASEIMGURL + 'green_MarkerA.png';
		str_markerId = 'marker_start';
	} else if ( str_iconType == 'end' ) {	// 轨迹终点图标
		myIcon.image = BASEIMGURL + 'green_MarkerB.png';
		str_markerId = 'marker_end';
	}
	marker = new MMap.Marker({position: mPoint, icon: myIcon, id: str_markerId});
	marker.offset = new MMap.Pixel(-15, -10);
	marker.selfInfoWindow = infoWindow;
	if ( str_iconType == 'draw' ) {	// 轨迹播放点的marker设置
		marker.id = 'marker_draw';
		actionMarker = marker;
	} else if ( str_iconType == 'actiontrack' ) {	// lastinfo or realtime marker点设置
		//marker.setLabel(label);
		var obj_carItem = $('.j_carList .j_terminal').eq(n_carNum);
		obj_selfmarkers[str_tid] = marker;
		dlf.fn_setOptionsByType('center', mPoint);
	} else if ( str_iconType == 'start' || str_iconType == 'end' ) {
		marker.offset = new MMap.Pixel(-15, -10);
	}
	mapObj.addOverlays(marker);	//向地图添加覆盖物 
	
	if ( isOpenWin ) {
		infoWindow.open(mapObj, mPoint);
	}
	/**
	* marker click事件
	*/
	mapObj.bind(marker, "click", function(e){
		if ( str_iconType == 'actiontrack' ) { // 主页车辆点击与左侧车辆列表同步
				var obj_carItem = $('.j_carList .j_terminal').eq(n_carNum),
					str_className = obj_carItem.attr('class'), 
					str_tid = obj_carItem.attr('tid');
					
				if ( str_className.search('j_currentCar') != -1 ) { // 如果是当前车的话就直接打开吹出框，否则switchcar中打开infoWindow
					marker.selfInfoWindow.open(mapObj, marker.getPosition());   
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
				marker.selfInfoWindow.open(mapObj, marker.getPosition());
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
		$('#eventResult tr').eq(tid+1).find('a').html(str_result).addClass('j_eventItem');
		arr_eventData[tid].name = str_result;
		dlf.fn_showMarkerOnEvent();
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
	var str_result = '',
		obj_point = new MMap.LngLat(n_lon, n_lat),
		GeocoderOption = { 
            range: 100, //范围 
            crossnum: 1, //道路交叉口数 
            roadnum : 1, //路线记录数 
            poinum: 1 //POI点数 
        },
		geo = new MMap.Geocoder(GeocoderOption); 
	
	if ( n_lon == 0 || n_lat == 0 ) {
		$('#address').html('-');
	} else {
		geo.regeocode(obj_point, function(data){
			var str_result = '';
			if( data.status == "E0" ) {
				for( var i = 0;i < data.list.length; i++ ) { 
					str_result += data.list[i].province.name+data.list[i].city.name+data.list[i].district.name;	// 省市区
					
					for(var j = 0; j < data.list[i].roadlist.length; j++){
						str_result +=data.list[i].roadlist[j].name;	// 道路
					}
					for (var j=0; j< data.list[i].poilist.length; j++) { 	  
						str_result += data.list[i].poilist[j].address + data.list[i].poilist[j].name;	  
					}		  
				}
			}
			if ( str_result == '' ) {
				if ( postAddress != null ) {	// 第一次如果未获取位置则重新获取一次,如果还未获得则显示"无法获取"
					clearTimeout(postAddress);
					str_result = '无法获取位置';
					dlf.fn_updateAddress(str_type, tid, str_result, n_index);
				} else {	// 如果未获取到位置描述  5秒后重新获取					
					str_result = '正在获取位置描述' + WAITIMG;
					dlf.fn_updateAddress(str_type, tid, str_result, n_index);
					postAddress = setTimeout(function() {
						dlf.fn_getAddressByLngLat(n_lon, n_lat, tid, str_type, n_index);
					}, 5000);
				}
			} else {
				dlf.fn_updateAddress(str_type, tid, str_result, n_index);
			}
		});
	}
	return str_result;
}
})();