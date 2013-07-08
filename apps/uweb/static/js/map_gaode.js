/*
* 地图相关操作方法
* postAddress: 逆地址编码获取位置描述
* mapObj: 地图对象
* obj_NavigationControl: 比例尺缩放对象
* obj_MapTypeControl: 地图类型对象
* obj_trafficControl: 路况信息对象
* obj_satellite : 卫星信息对象
* obj_circleInfowindow: 电子围栏画圆吹出框对象
* markers：
*/
var postAddress = null,
	mapObj = null,
	obj_NavigationControl = null,
	obj_MapTypeControl = null,
	obj_overview = null,
	obj_satellite = null,
	arr_opiMarkers=[],
	infos=[],
	obj_circleInfowindow = null,
	obj_selfMarkers = {};
	
(function () {

/**
* 加载高德MAP
*/
window.dlf.fn_loadMap = function(mapContainer) {       
	var opt = { 
		level: 15,	//初始地图视野级别 
		center: new AMap.LngLat(116.39825820922851,39.904600759441024),//设置地图中心点
		doubleClickZoom: true,//双击放大地图 
		scrollwheel: true	//鼠标滚轮缩放地图 
    };
  
    mapObj = new AMap.Map(mapContainer,opt);
	mapObj.plugin(["AMap.ToolBar","AMap.OverView","AMap.Scale", "AMap.MapType"],function() {
		toolbar = new AMap.ToolBar();
		toolbar.autoPosition=false; //加载工具条  
		mapObj.addControl(toolbar);
		
		obj_overview = new AMap.OverView(); //加载鹰眼 
		mapObj.addControl(obj_overview);
		
		obj_NavigationControl = new AMap.Scale(); //加载比例尺 
		mapObj.addControl(obj_NavigationControl);
		
		obj_MapTypeControl= new AMap.MapType; //地图类型切换
		mapObj.addControl(obj_MapTypeControl);
		
	});
}

/**
* 设置地图控件的显示隐藏
*/
window.dlf.fn_hideControl = function() {
	/*隐藏鹰眼、地图类型控件*/
	$('.amap-overviewcontrol, .amap-maptypecontrol').hide();
}
/**
* 设置地图上地图类型,实时路况的位置
* n_NumTop: 相对于地图上侧做的偏移值 
*/
window.dlf.fn_setMapControl = function(n_NumTop) {
	var obj_tempOverviewControl = $('.amap-overviewcontrol'),
		obj_tempMapTypeControl = $('.amap-maptypecontrol'),
		obj_tempToolbar = $('.amap-toolbar'),	
		b_overview = obj_tempOverviewControl.is(':hidden'),
		b_mapType = obj_tempMapTypeControl.is(':hidden');
		
	if ( b_overview && b_mapType ) {
		obj_tempOverviewControl.show();
		obj_tempMapTypeControl.show();
	}
	if ( n_NumTop ) {
		obj_tempToolbar.css('top', n_NumTop);
		obj_tempMapTypeControl.css('top', n_NumTop);
	}
}

/**
* 高德地图生成点
*/
window.dlf.fn_createMapPoint = function(n_lon, n_lat) {
	if ( n_lon == 0 || n_lat == 0 ) { 
		return '-';
	} else {
		return new AMap.LngLat(n_lon/NUMLNGLAT, n_lat/NUMLNGLAT);
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
			map:mapObj,
            path: arr_drawLine,    
            strokeColor: "#0251ED", //线颜色  
            strokeOpacity: 0.45, //线透明度   
            strokeWeight: 4, //线宽     
            strokeStyle: "solid", //线样式   
            strokeDasharray: [10,5] //补充线样式  
		};
		
		if ( obj_options ) {	// 动态轨迹
			polyOption.strokeColor = obj_options.color;
			polyOption.strokeOpacity = 0.8;
		}
		obj_polyLine = new AMap.Polyline(polyOption);
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
			mapObj.setZoomAndCenter(zoom, centers);//同时设置地图的中心点及zoom级别 
			break;
		case 'viewport':	// todo
			bounds = new AMap.Bounds(centers[0],centers[1]); 
			mapObj.setBounds(bounds);
			break;
	}
}
/**
* 高德地图添加图层
* obj_overlay: 要添加的图层对象
*/
window.dlf.fn_addOverlay = function(obj_overlay) {
	// mapObj.addOverlays(obj_overlay);
	obj_overlay.setMap(mapObj);
}

/**
* 清除页面上的地图图形数据
* obj_overlays: 要删除的图层对象,如果没有则清除地图上所有图层
*/
window.dlf.fn_clearMapComponent = function(obj_overlays) {
	if ( obj_overlays ) {
		obj_overlays.setMap(null);
	} else {
		mapObj.clearMap(); //删除所有覆盖物
	}
}

/**
* 周边查询 todo
* obj_keywords: 关键字
* n_clon：经度
* n_clat: 纬度
*/
window.dlf.fn_searchPoints = function (obj_keywords, n_clon, n_clat) {
	// 清空上次查询结果
	for ( var i = 0; i < arr_opiMarkers.length; i++ ) {
		var infowindow = arr_opiMarkers[i].selfInfoWindow;
		
		if ( infowindow.getIsOpen() ) {
			infowindow.close();
		}
		dlf.fn_clearMapComponent(arr_opiMarkers[i]);
		
	}
	var str_keywords = '',
		n_bounds = parseInt($('#txtBounds').val()),
		obj_kw = $('#txtKeywords'),
		obj_poiSearchOption = { 
			srctype: "POI", //数据来源 
			type: "", //数据类别 
			number: 100, //每页数量,默认10 
			batch: 1, //请求页数，默认1 
			range: n_bounds, //查询范围，默认3000米 
			ext:"" //扩展字段 
		};
		
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
		obj_localSearch =  new AMap.PoiSearch(obj_poiSearchOption);	// 初始化POI查询对象
	}
	obj_localSearch.byCenPoi(new AMap.LngLat(n_clon, n_clat), str_keywords, function(data) {
		if( data.status == 'E0' ) {
			var infos = [];

			arr_opiMarkers = [];	// 清空数组			
			for( var i = 0,l = data.list.length; i < l; i++ ) {
				var marker = new AMap.Marker({ 
					icon:"http://code.mapabc.com/images/lan_1.png", position: new AMap.LngLat(data.list[i].x,data.list[i].y), id: 'marker'+i, offset: new AMap.Pixel(-15,-24)
				}),
				obj_infowindow = new AMap.InfoWindow({
					content:'<b>'+data.list[i].name+'</b><hr/>'+TipContents(data.list[i].type,data.list[i].address,data.list[i].tel),autoMove:true 
				});
				marker.selfInfoWindow = obj_infowindow;
				arr_opiMarkers.push(marker); 
				mapObj.addOverlays(arr_opiMarkers[i]);
				
				infos.push(obj_infowindow);
				
				mapObj.bind(arr_opiMarkers[i], 'click', function(){
					var index = this.obj.id.substring(6);
					
					infos[index].open(mapObj, this.obj.getPosition())
				});
			}
		}
	});
}

function TipContents(type,address,tel){ 
    if (type == "" || type == "undefined" || type == null || type == " undefined" || typeof type == "undefined") { 
        type = "暂无";  
    }  
    if (address == "" || address == "undefined" || address == null || address == " undefined" || typeof address == "undefined") { 
        address = "暂无";  
    }  
    if (tel == "" || tel == "undefined" || tel == null || tel == " undefined" || typeof address == "tel") { 
        tel = "暂无";   
    }
    var str ="地址：" + address + "<br/>电话：" + tel + " <br/>类型："+type; 
    return str; 
} 

/**
* kjj 2013-06-26 create
* 创建marker图标icon
* todo
*/
window.dlf.fn_createAMapIcon = function(str_url, arr_size, arr_offset) {
	var opt = {image: str_url};
	
	if ( arr_size.length > 0 ) {
		opt.size = new AMap.Size(34, 34);
	}
	if ( arr_offset.length > 0 ) {
		opt.imageOffset = new AMap.Pixel(arr_offset[0], arr_offset[1]);
	}
	return new AMap.Icon(opt);
}

window.dlf.fn_createAMapInfoWindow = function(str_content, obj_position, arr_offset ) {
	var opt = {content: str_content};
	
	if ( obj_position ) {
		opt.position = obj_position;
	}
	if ( arr_offset.length > 0 ) {
		opt.offset = new AMap.Pixel(Pixel[0], Pixel[1]);
	}
	return new AMap.InfoWindow(opt);  // 创建信息窗口对象;
}

/**
*添加标记
* obj_location: 位置信息
* str_iconType: marker类型
* str_tempTid: 车辆编号
* isOpenWin: 是否打开infowindow
* n_index: 轨迹点的索引值，根据其值获取对应的位置
* n_counter : draw 时根据值修改数组中点的位置描述  下次就不用重新获取位置
*/
window.dlf.fn_addMarker = function(obj_location, str_iconType, str_tempTid, isOpenWin, n_index) { 
	var n_degree = dlf.fn_processDegree(obj_location.degree),  // 车辆方向角
		str_imgUrl = n_degree, 
		str_tid = obj_location.tid,
		myIcon = null,
		str_iconUrl = BASEIMGURL + str_imgUrl + '.png',
		mPoint = dlf.fn_createMapPoint(obj_location.clongitude, obj_location.clatitude),
		infoWindow = new AMap.InfoWindow({content: dlf.fn_tipContents(obj_location, str_iconType, n_index), position: mPoint}),
		str_alias = obj_location.alias,
		n_iconType = obj_location.icon_type,	// icon_type 
		obj_carA = $('.j_carList a[tid='+ str_tid +']'),
		label = null,
		startMarker = null,
		endMarker = null,
		delayMarker = null,
		str_corpIconUrl = dlf.fn_setMarkerIconType(n_degree, n_iconType);
		
	if ( !str_alias ) {	// 实时定位无alias，则根据tid获取对应定位器别名
		str_alias = obj_carA.next().html();
	}
	if ( dlf.fn_userType() ) {	// 集团用户修改图标
		str_iconUrl = str_corpIconUrl;	// 集团用户设置marker的图标
	}
	
	/**
	* 设置marker图标
	*/
	if ( str_iconType == 'start' ) {	// 轨迹起点图标
		str_iconUrl = BASEIMGURL + 'green_MarkerA.png';
	} else if ( str_iconType == 'end' ) {	// 轨迹终点图标
		str_iconUrl = BASEIMGURL + 'green_MarkerB.png';
	} else if ( str_iconType == 'delay' ) {	// 停留点图标
		str_iconUrl = BASEIMGURL + 'delay_Marker.png';
	} else if ( str_iconType == 'alarmInfo' ) {
		str_iconUrl = BASEIMGURL + 'alarmsign.gif';
	} else if ( str_iconType == 'draw' ) {
		str_iconUrl = str_corpIconUrl;
	}
	myIcon = new AMap.Icon({image: str_iconUrl, size: new AMap.Size(34, 34)});
	
	var marker = new AMap.Marker({
		map: mapObj,
		position: mPoint, //基点位置
		icon: myIcon, //marker图标，直接传递地址url
		offset: {x:-20,y:-10} //相对于基点的位置
	});
	marker.selfInfoWindow = infoWindow;
	// marker.isOpenInfoWindow = false;
	if ( str_iconType == 'draw' ) {	// 轨迹播放点的marker设置
		actionMarker = marker;
	} else if ( str_iconType == 'actiontrack' ) {	// lastinfo or realtime marker点设置
		obj_selfmarkers[str_tid] = marker;
		dlf.fn_setOptionsByType('center', mPoint);
	} else if ( str_iconType == 'region' ) {
		obj_selfmarkers[str_tid] = marker;
	} else if ( str_iconType == 'start' || str_iconType == 'end' || str_iconType == 'delay'  ) {
		if ( str_iconType == 'delay' ) {
			delayMarker = marker;
		}
		if ( str_iconType == 'start' ) {
			startMarker = marker;
		} else if ( str_iconType == 'end' ) {
			endMarker = marker;
		}
		marker.offset = new AMap.Pixel(-10, -14);
	} else if ( str_iconType == 'eventSurround' ) {
		obj_selfmarkers['eventSurround'] = marker;
	} else if ( str_iconType ==	'alarmInfo' ) {
		marker.offset = new AMap.Pixel(-10, -14);
	}
	
	var obj_infowindow = marker.selfInfoWindow;

	if ( str_iconType == 'draw'	) {
		obj_infoWindow = actionMarker.selfInfoWindow;
		
		AMap.event.addListener(obj_infoWindow, "open", function(e) {
			b_trackMsgStatus = true;
		});
		AMap.event.addListener(obj_infowindow, "close", function(e) {
			b_trackMsgStatus = false;
		});
	} else {
		AMap.event.addListener(obj_infowindow, "open", function(e) { // 吹出框打开时判断是否开启追踪 然后改变对应的文字颜色
			if ( str_iconType == 'actiontrack' ) {
				dlf.fn_updateOpenTrackStatusColor(str_tid);
			} else if ( str_iconType == 'draw' ) {
				b_trackMsgStatus = true;
			}
			dlf.fn_changeAddressHeight('actiontrack');
		});
	}
	if ( isOpenWin ) {
		if ( str_iconType == 'draw' ) {
			actionMarker.selfInfoWindow.open(mapObj, mPoint);
		} else {
			infoWindow.open(mapObj, mPoint);	
		}
		dlf.fn_changeAddressHeight(str_iconType);
	}
	/**
	* marker click事件
	*/
	AMap.event.addListener(marker, "click", function(e) {
		if ( str_iconType == 'actiontrack' ) { // 主页车辆点击与左侧车辆列表同步
				var obj_carItem = $('.j_carList .j_terminal[tid='+ str_tempTid +']'),				
					str_className = obj_carItem.attr('class'), 
					str_tid = str_tempTid;
				
				if ( str_className.search('j_currentCar') != -1 ) { // 如果是当前车的话就直接打开吹出框，否则switchcar中打开infoWindow
					var obj_tempPosition = obj_selfmarkers[str_tid].getPosition();
					
					obj_selfmarkers[str_tid].selfInfoWindow.open(mapObj, obj_tempPosition);	// 打开吹出框
					dlf.fn_updateOpenTrackStatusColor(str_tid);
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
				var str_content = marker.selfInfoWindow.getContent(),
					obj_infowindowLi = $('#markerWindowtitle ul li').eq(4);
					
				obj_infowindowLi.html('').html('位置：<lable class="lblAddress left60">' + str_name + '</label>');	// 替换marker上的位置描述
			}
			marker.selfInfoWindow.open(mapObj, marker.getPosition());
		}
		dlf.fn_changeAddressHeight(str_iconType);
    });
	return marker;
}

/**
* 手动在吹出框添加了关闭按钮  关闭按钮的事件above
* 要关闭的吹出框tid
*/
window.dlf.fn_closeWindow = function (str_tid, b_isTrack) {
	mapObj.clearInfoWindow();
	if ( b_isTrack && actionMarker ) {
		actionMarker.isOpenInfoWindow = false;
	} else {
		obj_selfmarkers[str_tid].isOpenInfoWindow = false;
	}
}

/**
* 吹出框打开时修改 开启追踪文字的颜色
*/
window.dlf.fn_updateInfowWindowStatus = function(str_tid, b_isTrack) {
	if ( b_isTrack && actionMarker ) {
		actionMarker.isOpenInfoWindow = true;
		return;
	}
	for ( var str_tempTid in obj_selfmarkers ) {
		var b_status = false;
		if ( str_tid ) {
			if ( str_tempTid == str_tid ) {
				b_status = true;
			}
		}
		obj_selfmarkers[str_tempTid].isOpenInfoWindow = b_status;
	}
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
		str_delayTime = obj_location.idle_time,
		str_title = '车辆：',
		str_tempMsg = '开始跟踪',
		str_actionTrack = dlf.fn_getActionTrackStatus(str_tid),	// $('.j_carList a[tid='+str_tid+']').attr('actiontrack'),
		str_html = str_iconType == 'actiontrack' ? '<div id="markerWindowtitle" class="cMsgWindow">' : '<div id="markerWindowtitle" class="cMsgWindow">',
		n_track = obj_location.track,	// 是否开启追踪1：开启 0：关闭
		str_styleTrack = ' style="color:blue" ';
	
	if ( str_iconType == 'delay' ) {
		str_html = '<div id="markerWindowtitle" class="cMsgWindow">'
	}
	if ( str_actionTrack == 'yes' ) {
		str_styleTrack = ' style="color:#F0960F" ';
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
				
				if ( obj_selfmarker ) {	// 第一次加载 没有selfmarker 
					if ( Math.abs(str_oldClon-str_newClon) < 100 || Math.abs(str_oldClat-str_newClat) < 100 ) {	// 判断和上次经纬度的差是否在100之内，在的话认为是同一个点
						var obj_infowindow = obj_selfmarker.selfInfoWindow;
						
						if ( obj_infowindow && obj_infowindow != null ) {	// infowindow中位置替换
							var str_content = obj_infowindow.getContent(),
								n_beginNum = str_content.indexOf('位置： ')+37,
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
			} else ( str_iconType == 'draw' || str_iconType == 'start' || str_iconType == 'end' )  {
				address = '<a href="#" title="获取位置" onclick="dlf.fn_getAddressByLngLat('+str_clon+', '+str_clat+',\''+str_tid+'\',\''+ str_iconType +'\','+ n_index +');">获取位置</a>'; 
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
		if ( dlf.fn_userType() ) {
			str_title += $('.j_carList a[id=leaf_'+ str_tid +']').text().substr(2); 
		} else {
			str_title += $('.j_carList a[tid='+str_tid+']').next().html();
		}
	}
	
	if ( str_iconType == 'delay' ) {	// 如果是轨迹播放的停留点 infowindow显示内容不同
		str_html += '<h4 tid="'+obj_location.tid+'">'+str_title+'</h4><ul>'+ 
					'<li><label>停留：  '+ dlf.fn_changeTimestampToString(str_delayTime) +'</label>'+
					'<li><label>开始：  '+ dlf.fn_changeNumToDateString(obj_location.start_time) +'</label>'+
					'<li><label>结束：  '+ dlf.fn_changeNumToDateString(obj_location.end_time) +'</label></li>' + 
					'<li>位置： <lable class="lblAddress left60">'+ address +'</label></li>';	
	} else {
		str_html += '<h4 tid="'+obj_location.tid+'">'+str_title+'</h4><ul>'+ 
					'<li><label>速度： '+ speed+' km/h</label>'+
					'<label class="labelRight" title="'+str_degreeTip+'">方向： '+str_degree+'</label></li>'+
					'<li><label>经度： E '+str_clon.toFixed(CHECK_ROUNDNUM)+'</label>'+
					'<label class="labelRight">纬度： N '+str_clat.toFixed(CHECK_ROUNDNUM)+'</label></li>'+
					'<li>类型： '+ str_type +'</li>'+
					'<li>时间： '+ date +'</li>' + 
					'<li>位置： <lable class="lblAddress left60">'+ address +'</label></li>';

		if ( str_iconType == 'actiontrack' ) {
			str_html+='<li class="top10"><a href="#" id="realtime"  onclick="dlf.fn_currentQuery();">定位</a><a href="#" id="trackReplay" onclick="dlf.fn_initTrack();">轨迹</a>';
			if ( dlf.fn_userType() ) {	// 如果是集团用户的话 定位、轨迹、设防撤防、参数设置放在marker上
				str_html+='<a href="#" id="corpTerminal"  onclick="dlf.fn_initCorpTerminal();">设置</a>';
			} else {	// 如果是个人用户
				str_html += '<a href="#" id="terminal" onclick="dlf.fn_initTerminal();">设置</a>';
			}
			str_html += '<a href="#" id="defend"  onclick="dlf.fn_defendQuery();">设防/撤防</a><a href="#"  class ="j_openTrack" onclick="dlf.setTrack(\''+str_tid+'\', this);" >'+ str_tempMsg +'</a></li>';
		} else if ( str_iconType == 'alarmInfo' ) {
			str_html += '<li>告警： <lable class="colorRed">'+ dlf.fn_eventText(obj_location.category) +'告警</label></li>';
		}
	}
	str_html += '</ul></div>';
	return str_html;
} 

/**
* kjj 2013-07-02 create
* 根据位置描述的高度调整功能栏的top值
*/
window.dlf.fn_changeAddressHeight = function(str_iconType) {
	var obj_address = $('.lblAddress'),
		n_addressHeight = 0,
		n_top = 10,
		n_num = 0,
		obj_markerWindow = $('#markerWindowtitle');
	
	if ( obj_address.is(':visible') ) {
		n_addressHeight = obj_address.height();
		n_num = Math.floor(n_addressHeight/15);
		$('.top10').css('padding-top', n_top*n_num);
		
		var n_windowHeight = obj_markerWindow.height();
		
		if ( str_iconType == 'actiontrack' ) {
			
		} else if ( str_iconType == 'alarmInfo' ) {
			obj_address.parent().css('height', n_addressHeight);
			n_windowHeight = n_windowHeight + n_addressHeight;
		} else {
			n_windowHeight = n_windowHeight + n_addressHeight-15;
		}
		obj_markerWindow.height(n_windowHeight);
	}
}

/**
** 将获取到的name更新到marker或label上
* str_type: 轨迹或 realtime或lastinfo
* str_result: 获取到的位置
* n_index: 如果是轨迹则根据索引获取name
*/
window.dlf.fn_updateAddress = function(str_type, tid, str_result, n_index, n_lon, n_lat) {
	var str_result = str_result,
		str_tempResult = str_result.length >= 28 ? str_result.substr(0,28) + '...':str_result,
		obj_selfmarker = obj_selfmarkers[tid],	// $('.j_carList a[tid='+tid+']').data('selfmarker'),
		obj_addressLi = $('#markerWindowtitle ul li').eq(4);

	if ( str_type == 'realtime' || str_type == 'lastinfo' ) {
		var str_currentTid = $('.j_carList a[class*=j_currentCar]').attr('tid');
		// 左侧 位置描述填充
		if ( str_currentTid == tid ) {
			obj_addressLi.html('').html('位置：<lable class="lblAddress left60">' + str_tempResult + '</label>');	// 替换marker上的位置描述
			$('#address').html(str_result);
		}
		if ( obj_selfmarker && obj_selfmarker != null ) {
			var str_content = obj_selfmarker.selfInfoWindow.getContent(),
				str_address = '';
				
			if ( str_content.search('正在获取位置描述...') != -1 ) {
				str_content = str_content.replace('正在获取位置描述' + WAITIMG, str_result);
			} else {
				n_beginNum = str_content.indexOf('位置： ')+37,	// <lable class="lblAddress left60">
				n_endNum = str_content.indexOf('</label></li><li class="top10">'),
				str_address = str_content.substring(n_beginNum, n_endNum);
				str_content = str_content.replace(str_address, str_tempResult);
			}
			$('.j_carList a[tid='+ tid +']').data('address', str_result);
			obj_selfmarker.selfInfoWindow.setContent(str_content);
		}
	} else if ( str_type == 'event' ) {
		if ( n_lon != 'none' ) {
			var str_tempAddress = str_result.length >= 30 ? str_result.substr(0,30) + '...':str_result;
			
			$('.eventSearchTable tr').eq(n_index+1).find('.j_getPosition').parent().html('<label href="#" title="'+ str_result +'">'+str_tempAddress+'</label><a href="#" c_lon="'+n_lon+'" c_lat="'+n_lat+'" class="j_eventItem viewMap" >查看地图</a>');
			arr_dwRecordData[n_index].name = str_tempAddress;
			$('#markerWindowtitle ul li').eq(4).html('位置： ' + str_result);	// 替换marker上的位置描述
			
			dlf.fn_showMarkerOnEvent();	// 初始化查看地图事件
		}
	} else if ( str_type == 'alarmInfo' ) {
		$('.j_alarmTable').data('markers')[n_index].name = str_result;
		// $('.clickedBg').children('td').eq(2).html(str_result);
	} else if ( str_type == 'delay' || str_type == 'start' || str_type == 'end' ) {
		// $('.clickedBg').children('td').eq(2).html(str_result);	// 修改右侧列表位置描述
		$('.lblAddress').html(str_result);	// 修改吹出框位置描述
		if ( str_type == 'delay' && dlf.fn_userType() ) {	// 如果是集团的停留点的话
			var obj_tempMarker = $('.delayTable').data('markers')[$('.clickedBg').index()];
			
			if ( obj_tempMarker ) {
				var str_content = obj_tempMarker.selfInfoWindow.getContent();
					n_beginNum = str_content.indexOf('位置： ')+37,	// <lable class="lblAddress">
					n_endNum = str_content.indexOf('</a></label></li>') + 4;
					str_address = str_content.substring(n_beginNum, n_endNum);
					str_content = str_content.replace(str_address, str_result);
				
				obj_tempMarker.selfInfoWindow.setContent(str_content);
				obj_tempMarker.selfInfoWindow.open(mapObj, obj_tempMarker.getPosition());
			}				
		}		
	} else {
		if ( n_index >= 0 ) {
			arr_dataArr[n_index].name = str_result;
		}
		obj_addressLi.html('位置：' + str_result);	// 替换marker上的位置描述
	}
	dlf.fn_changeAddressHeight(str_type);
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
		obj_point = new AMap.LngLat(n_lon, n_lat),
		GeocoderOption = { 
            range: 100, //范围 
            crossnum: 1, //道路交叉口数 
            roadnum : 1, //路线记录数 
            poinum: 1 //POI点数 
        },
		geo = new AMap.Geocoder(GeocoderOption); 
	
	if ( str_type == 'event' ) {
		dlf.fn_ShowOrHideMiniMap(false);	// 如果是告警的获取位置，关闭小地图
	}
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



// todo记得要修改的:)2013.4.15
/*
* 点击地图添加标记
*/
var obj_mousetoolMarker = null;

window.dlf.fn_clickMapToAddMarker = function() {
	if ( obj_mousetoolMarker ) {
		obj_mousetoolMarker.close(true);
		obj_mousetoolMarker = null;
	}
	mapObj.clearInfoWindow();
}

window.dlf.fn_setCursor = function(b_isUnbind) {
	if ( b_isUnbind ) {
		$('#mapObj').css('cursor', 'default');
		$('#mapObj').unbind('mouseover mouseout').mouseover(function() {
			$(this).css('cursor', 'default');
		});
	} else {
		$('#mapObj').unbind('mouseover mouseout').mouseover(function() {
			$(this).css('cursor', 'crosshair');
		}).mouseout(function() {
			$(this).css('cursor', 'default');
		});
	}
}

window.dlf.fn_mapClickFunction = function(event) {
	//添加鼠标工具插件，并进入鼠标画点模式
	dlf.fn_setCursor();
	mapObj.plugin(["AMap.MouseTool"],function(){ 
		obj_mousetoolMarker = new AMap.MouseTool(mapObj);
		obj_mousetoolMarker.marker(); 
		
		mapObj.bind(obj_mousetoolMarker, "draw", function(e) {
			fn_createRouteLinePoint(e.obj);	// 添加站点
        });
	});
}

/**
* kjj 2013-06-24 create
* 添加站点
*/
function fn_createRouteLinePoint(marker) {
	var obj_clickPoint = marker.getPosition(),
		str_markerGuid = marker.H,
		obj_clickMarker = marker // new AMap.Marker({position: obj_clickPoint});
		
	obj_clickMarker.offset = new AMap.Pixel(-10, -23);
	// mapObj.addOverlays(obj_clickMarker);	//向地图添加覆盖物 
	var n_cnt = 1;
	for ( var obj in obj_routeLineMarker ) {
		n_cnt ++;
	}
	// 吹出框显示
	var str_infoWindowText = '<div class="gaodeClickWindowPanel"><label 				     class="clickWindowPolder">请输入站点名称</label><input type="text" id="clickMarkerWindowText" value="站点'+ n_cnt +'" /><a href="#" onclick="dlf.fn_delClickWindowText(\''+ str_markerGuid +'\');" >删除</a></div>',
		obj_clickInfoWindow = new AMap.InfoWindow({content: str_infoWindowText, offset: new AMap.Pixel(0,-15)});  // 创建信息窗口对象
	
	obj_clickInfoWindow.open(mapObj, obj_clickPoint);	// 打开吹出框
	
	obj_routeLineMarker[str_markerGuid] = {'marker': obj_clickMarker, 'stationname': '', 'infowindow': obj_clickInfoWindow};
	dlf.fn_mapStopDraw(true);
	$('#routeLineCreate_clickMap').removeClass('routeLineBtnCurrent');
	$('#routeLineCreate_clickMap').html('添加站点');
	
	$('#clickMarkerWindowText').focus().blur(function() {
		dlf.fn_saveClickWindowText(str_markerGuid);
	});
	
	/**
	* obj_clickMarker click事件
	*/
	AMap.event.addListener(obj_clickMarker, "click", function(e) {
		var str_tempgid = str_markerGuid, 
			obj_markerPanel = obj_routeLineMarker[str_tempgid],
			str_stationName = obj_markerPanel.stationname,
			str_infoWindowText = '<div class="gaodeClickWindowPanel"><label class="clickWindowPolder">请输入站点名称</label><input type="text" id="clickMarkerWindowText" /><a href="#" onclick="dlf.fn_delClickWindowText(\''+ str_tempgid +'\');" >删除</a></div>',
			obj_clickInfoWindow = new AMap.InfoWindow({content: str_infoWindowText, offset:new AMap.Pixel(0,-15)}),  // 创建信息窗口对象
			n_tempCnt = 1;
		
		for ( var hid in obj_routeLineMarker ) {
			if ( hid == str_tempgid ) {
				break;
			}
			n_tempCnt ++;
		}
		obj_mousetoolMarker.close(false);
		obj_clickInfoWindow.open(mapObj, obj_clickPoint);	// 打开吹出框
		
		$('#clickMarkerWindowText').val(str_stationName || '站点' + n_tempCnt).focus();
		setTimeout( function() {
			//dlf.fn_mapClickFunction();
		}, 100);
	});
}
/*
* 添加线路的标记
*/
window.dlf.fn_addRouteLineMarker = function(obj_stations){ 
	var str_stationName = obj_stations.name,
		obj_stationPoint = dlf.fn_createMapPoint(obj_stations.longitude, obj_stations.latitude),
		obj_stationMarker = new AMap.Marker({position: obj_stationPoint, offset: new AMap.Pixel(-10, -23), icon: 'http://webapi.amap.com/images/marker_sprite.png'}); 
	
	mapObj.addOverlays(obj_stationMarker);	//向地图添加覆盖物 

	/**
	* obj_stationMarker click事件
	*/
	AMap.event.addListener(obj_stationMarker, "click", function(e) {
		var str_infoWindowText = '<label class="clickWindowPolder">站点名称：'+ str_stationName +'</label>',
			obj_clickInfoWindow = new AMap.InfoWindow({content: str_infoWindowText, offset:new AMap.Pixel(0,-5)});  // 创建信息窗口对象
		
		obj_clickInfoWindow.open(mapObj, obj_stationPoint);	// 打开吹出框		
	});
}

/*
* 初始化画圆及事件绑定
*/
window.dlf.fn_initCreateCircle = function() {
	var str_circleId = '';
	dlf.fn_setCursor();	// 鼠标状态
	//添加鼠标工具插件，并进入鼠标画圆模式 	
	mapObj.plugin(["AMap.MouseTool"],function(){ 
		mousetool = new AMap.MouseTool(mapObj); 
		
		mousetool.circle({
			strokeColor: '#5ca0ff',    //边线颜色。
			fillColor: '#ced7e8',      //填充颜色。当参数为空时，圆形将没有填充效果。
			strokeWeight: 0.5,       //边线的宽度，以像素为单位。
			strokeOpacity: 0.8,	   //边线透明度，取值范围0 - 1。
			fillOpacity: 0.5,      //填充的透明度，取值范围0 - 1。
			strokeStyle: 'solid' //边线的样式，solid或dashed。
		});
		AMap.event.addListener(mousetool,"draw",function(e){
		    var obj_event = e.obj,
				n_radius = obj_event.getRadius(),
				obj_centerPoint = obj_event.getCenter();
			
			fn_createCircleCenterPoint(n_radius, obj_centerPoint);
			obj_circle = obj_event;
			mousetool.close();	// 关闭鼠标画圆事件
        });
	});
}

/**
* kjj 2013-06-21 create
* 电子围栏画圆中心点
*/
function fn_createCircleCenterPoint(n_radius, centerPoint) {
	var str_infoWindowText = '<div class="gaodeWindowPanel height38"><label class="clickWindowPolder">围栏名称：</label><input type="text" id="createRegionName" /><a href="#" onclick="dlf.fn_saveReginon();">保存</a><a href="#" onclick="dlf.fn_resetRegion();">重画</a></div>',
		obj_infoWindow = new AMap.InfoWindow({content: str_infoWindowText, offset:new AMap.Pixel(0,-5)});
		marker = null;
		
	if ( n_radius < 500 ) { 
		str_infoWindowText = '<div class="gaodeWindowPanel height38"><span class="errorCircle errorTop10"></span><label class="clickWindowPolder">电子围栏半径最小为500米！</label><a href="#" onclick="dlf.fn_resetRegion();">重画</a></div>';
		
		obj_infoWindow.setContent(str_infoWindowText);
		// obj_infoWindow.setOffset(new AMap.Pixel(-105,-45));
	}
	dlf.fn_mapStopDraw();
	marker = new AMap.Marker({position: centerPoint, offset: new AMap.Pixel(-10, -10)});
	// marker.setIcon({imageOffset: new AMap.Pixel(0,200)});
	mapObj.addOverlays(marker);	//向地图添加覆盖物 
	obj_circleMarker = marker;
	obj_circleInfowindow = obj_infoWindow;
	obj_infoWindow.open(mapObj, centerPoint);
	obj_circlMarker = marker;
	AMap.event.addListener(obj_circlMarker, "click",function(e){
		obj_infoWindow.open(mapObj, centerPoint);
	});
	dlf.fn_setCursor(true);	// 鼠标状态
}

/*
* 地图的右击事件
*/
window.dlf.fn_mapRightClickFun = function() {
	if ( obj_circle ) { 
		dlf.fn_clearMapComponent(obj_circle); // 清除页面圆形
		dlf.fn_clearMapComponent(obj_circleMarker);// 清除地图上的圆心标记
	}
	if ( obj_circleInfowindow ) {
		mapObj.clearInfoWindow();
	}
	dlf.fn_mapStopDraw();
	obj_circle = null;
	obj_circleMarker = null;
}

/*
* 地图的右击事件移除
*/
window.dlf.fn_mapRightClickRemoveFun = function() { 
	mapObj.removeEventListener('rightclick', dlf.fn_mapRightClickFun);
}

/*
* 地图开始画圆或者加点
* b_isCreateRouteLine: 是否是新建站点
*/
window.dlf.fn_mapStartDraw = function(b_isCreateRouteLine) { 
	if ( b_isCreateRouteLine ) {
		dlf.fn_mapClickFunction();
	} else {
		dlf.fn_initCreateCircle();
	}
}

/*
* 地图停止画图或者加点
*/
window.dlf.fn_mapStopDraw = function(b_isCreateRouteLine) {
	$('.regionCreateBtnPanel a').removeClass('regionCreateBtnCurrent currentCircle currentDrag');
	$('#regionCreate_dragMap').addClass('regionCreateBtnCurrent');
	
	if ( b_isCreateRouteLine ) {
		if ( obj_mousetoolMarker ) {
			obj_mousetoolMarker.close();
			dlf.fn_setCursor(true);	// 取消地图的mouseover 事件 让鼠标变成default状态
		}
	}
}

/*
* 获取圆数据
*/
window.dlf.fn_getCirlceData = function() {
	if ( obj_circle ) {
		var obj_circleCenter = obj_circle.getCenter();
		
		return {'radius': obj_circle.getRadius(), 'longitude': obj_circleCenter.lng*NUMLNGLAT, 'latitude': obj_circleCenter.lat*NUMLNGLAT};
	}
}

/*
* 显示圆
*/
window.dlf.fn_displayCircle = function(obj_circleData) { 
	var centerPoint = dlf.fn_createMapPoint(obj_circleData.longitude, obj_circleData.latitude),
		circleOptions = {//圆的样式
			id: 'circle',
			center: centerPoint,
			radius: obj_circleData.radius,	
			strokeColor: '#5ca0ff',    //边线颜色。
			fillColor: '#ced7e8',      //填充颜色。当参数为空时，圆形将没有填充效果。
			strokeWeight: 0.5,       //边线的宽度，以像素为单位。
			strokeOpacity: 0.8,	   //边线透明度，取值范围0 - 1。
			fillOpacity: 0.5,      //填充的透明度，取值范围0 - 1。
			strokeStyle: 'solid' //边线的样式，solid或dashed。
		};
		
	obj_circle = new AMap.Circle(circleOptions);
	mapObj.setCenter(centerPoint);
	mapObj.addOverlays(obj_circle);
	return obj_circle;
}

/***
* kjj 2013-06-20
* 计算点是否超出地图，如果超出设置地图中心点为当前点
*/
window.dlf.fn_boundContainsPoint = function(obj_tempPoint) {
	// 是否进行中心点移动操作 如果当前播放点在屏幕外则,设置当前点为中心点
	var obj_mapBounds = mapObj.getBounds(), 
		b_isInbound = null;
	
	if ( obj_mapBounds ) {
		var obj_southwest = obj_mapBounds.southwest,
			n_swLng = obj_southwest.lng,
			n_swLat = obj_southwest.lat,
			obj_northeast = obj_mapBounds.northeast,
			n_neLng = obj_northeast.lng,
			n_neLat = obj_northeast.lat,
			n_tempLng = obj_tempPoint.lng,
			n_tempLat = obj_tempPoint.lat;

		if ( n_tempLng >= n_swLng && n_tempLng <= n_neLng && n_tempLat >= n_swLat && n_tempLat <= n_neLat ) {
			
		} else {
			dlf.fn_setOptionsByType('center', obj_tempPoint);
		}
	}
}
})();