/*
*单程起点查看详情
*/
var mapObj = null,
	BASEIMGURL = '/static/images/',
	arr_drawLine = [],
	arr_dataArr = [],
	str_actionState = 0,
	actionMarker = null,
	counter = 0,
	timerId = 0,
	n_speed = 200,
	obj_drawLine = null,
	NUMLNGLAT = 3600000,
	obj_mapInfoWindow = null,
	CHECK_ROUNDNUM = 0;
	
$(function () {
	$('#single_mapObj').css({'height': $(window).height(), 'width': $(window).width()});
	fn_loadMap();
	/**
	* 初始化速度滑块
	*/
	var arr_slide = [1000, 500, 200, 100], 
		arr_slideTitle = ['慢速', '一般速度', '比较快', '极速'];
	
	$('#singleSlide').slider({
		min: 0,
		max: 3,
		values: 2,
		range: 'min',
		animate: true,
		slide: function (event, ui) {
			var n_val = ui.value;
			
			n_speed = arr_slide[n_val];
			
			$('#singleSlide').attr('title', arr_slideTitle[n_val]);
			if ( timerId ) { clearInterval(timerId) };
			var obj_tplay = $('#tPlay'),
				str_ishidden = obj_tplay.is(':hidden');
			
			if ( str_ishidden ) {	// 如果播放按钮不可用
				fn_markerAction();
			}
		}
	}).slider('option', 'value', 2);
	
	$('#tPause').hide();
	
	$('.j_trackBtnhover').click(function(event) {
		var str_id = event.currentTarget.id;
		
		if ( str_id == 'tPlay' ) { // 播放
			fn_markerAction();
			$(this).hide();
			$('#tPause').css('display', 'inline-block');
		} else if ( str_id == 'tPause' ) { // 暂停
			fn_trackQueryPause();
			$(this).hide();
			$('#tPlay').css('display', 'inline-block');
		} else if ( str_id == 'tPrev' ) { // 上一个点
			if ( counter > 0 ) {
				arr_drawLine.pop();
				arr_drawLine.pop();
				fn_drawMarker('prev');
			}
		} else if ( str_id == 'tNext' ) { // 下一个点
			fn_drawMarker('next');
		}
	});
	var n_startTime = $('#tempSingleStartTime').html(),
		n_endTime = $('#tempSingleEndTime').html(),
		n_tid = $('#tempSingleTid').html(),
		obj_locusDate = {'tid': n_tid, 'start_time': n_startTime,'end_time': n_endTime};
	
	$.ajax({
		type : 'post',
		url : '/track',
		data: JSON.stringify(obj_locusDate),
		dataType : 'json',
		cache: false,
		contentType : 'application/json; charset=utf-8',
		success : function(data) {
			if ( data.status == 0 ) {
				var arr_locations = data.track, 
					locLength = arr_locations.length,
					arr_calboxData = [],
					str_alias = $('#tempTalias').html(),
					str_tid = $('#tempSingleTid').html();
					
				if ( locLength <= 0) {
					alert('该时间段没有轨迹记录，请选择其它时间段。');
				} else {
					for ( var x = 0; x < locLength; x++ ) {
						arr_locations[x].alias = str_alias;
						arr_locations[x].tid = str_tid;
						arr_calboxData.push(fn_createMapPoint(arr_locations[x].clongitude, arr_locations[x].clatitude));
					}
					arr_dataArr = arr_locations;
					
					mapObj.setViewport(arr_calboxData);
					
					$('#control_panel').data('points', arr_calboxData);
					fn_startDrawLineStatic(arr_locations);
				}		
			} else {
				alert(data.message);
				window.close();
			}
		},
		error : function(xyResult) {
			alert('error');
			window.close();
			return;
		}
	});
	
	fn_getSingleDetail();
});

/**
* 当用户窗口改变时,地图做相应调整
*/
window.onresize = function () {
	$('#single_mapObj').css({'height': $(window).height(), 'width': $(window).width()});
}

//查询单程信息并显示
function fn_getSingleDetail() {
	$.ajax({
		type : 'get',
		url : '/single?single_id='+$('#tempSingleId').html(),
		data: '',
		dataType : 'json',
		cache: false,
		contentType : 'application/json; charset=utf-8',
		success : function(data) {
			if ( data.status == 0 ) {
				fn_displayMapShape(data.res, false);
			} else {
				alert(data.message);
				window.close();
			}
		},
		error : function(xyResult) {
			alert('error');
			window.close();
			return;
		}
	});
}

/**
* 添加轨迹线和轨迹点
*/
function fn_startDrawLineStatic(arr_dataArr) {
	$('#tPlay, #tPrev, #tNext, #trackSpeed').css('display', 'inline-block');
	var obj_firstMarker = {},
		obj_endMarker = {},
		arr_markers = [];
	
	var polyline = fn_createPolyline($('#control_panel').data('points'), {color: '#150CFF'});	//通过经纬度坐标数组及参数选项构建多折线对象，arr是经纬度存档数组 
	
	obj_firstMarker = fn_addMarker(arr_dataArr[0], 'start', 0, 0); // 添加标记
	obj_endMarker = fn_addMarker(arr_dataArr[arr_dataArr.length - 1], 'end', 0, 1); //添加标记
	//存储起终端点以便没有位置时进行位置填充
	arr_markers.push(obj_firstMarker);
	arr_markers.push(obj_endMarker);
	$('#control_panel').data('markers', arr_markers);
	
	arr_drawLine.push(fn_createMapPoint(arr_dataArr[0].clongitude, arr_dataArr[0].clatitude));
	
	fn_createDrawLine();
}
//加载地图
function fn_loadMap() {                  	
	mapObj = new BMap.Map('single_mapObj'); // 创建地图实例
	var markerPoint = new BMap.Point(116.39825820922851 ,39.904600759441024); // 创建点坐标
	mapObj.centerAndZoom(markerPoint, 5); // 初始化地图，设置中心点坐标和地图级别 
	mapObj.enableScrollWheelZoom();  // 启用滚轮放大缩小。

	mapObj.addControl(new BMap.NavigationControl({anchor: BMAP_ANCHOR_TOP_LEFT}));	// 比例尺缩放
	mapObj.addControl(new BMap.ScaleControl());  // 添加比例尺控件
	mapObj.setMinZoom(5);
	/*添加相应的地图控件及服务对象*/
	mapObj.addControl(new BMap.MapTypeControl({mapTypes: [BMAP_NORMAL_MAP,BMAP_SATELLITE_MAP], offset: new BMap.Size(100, 10)}));	// 地图类型 自定义显示 普通地图和卫星地图
	
	mapObj.addControl(new BMap.OverviewMapControl()); //添加缩略地图控件
}

/**
* 百度地图生成点
*/
function fn_createMapPoint(n_lon, n_lat) {
	if ( n_lon == 0 || n_lat == 0 ) { 
		return '-';
	} else {
		return new BMap.Point(n_lon/NUMLNGLAT, n_lat/NUMLNGLAT);
	}
}

//添加标记
function fn_addMarker (obj_location, str_iconType, str_tempTid, n_index) {
	var myIcon = new BMap.Icon(BASEIMGURL + 'default.png', new BMap.Size(34, 34)),
		n_clon = obj_location.clongitude,
		n_clat = obj_location.clatitude,
		n_lon = obj_location.longitude,
		n_lat = obj_location.latitude,
		mPoint = new BMap.Point(n_clon/NUMLNGLAT, n_clat/NUMLNGLAT), 
		marker = null,
		str_alias = obj_location.alias,
		str_tid = obj_location.tid;

	/**
	* 设置marker图标
	*/
	if ( str_iconType == 'start' ) {	// 轨迹起点图标
		myIcon.imageUrl = BASEIMGURL + 'green_MarkerA.png';
	} else if ( str_iconType == 'end' ) {	// 轨迹终点图标
		myIcon.imageUrl = BASEIMGURL + 'green_MarkerB.png';
	} else if ( str_iconType == 'draw' ) {
		myIcon.imageUrl = BASEIMGURL + 'default.png';
	}
	marker= new BMap.Marker(mPoint, {icon: myIcon});
	marker.setOffset(new BMap.Size(0, 0));
	
	if ( str_iconType == 'draw' ) {	// 轨迹播放点的marker设置
		actionMarker = marker;
		
	} else if ( str_iconType == 'start' || str_iconType == 'end' || str_iconType == 'delay' ) {
		marker.setTop(true);
		marker.setOffset(new BMap.Size(-1, -14));
	}   
	mapObj.addOverlay(marker);	//向地图添加覆盖物 
	/**
	* marker click事件
	*/
	marker.addEventListener('click', function() {
		fn_createMapInfoWindow(obj_location, str_iconType, n_index);
		this.openInfoWindow(obj_mapInfoWindow);
	});
	return marker;
}

//添加行踪线
function fn_createPolyline (arr_drawLine, obj_options) {
	var obj_polyLine = null;
	
	if ( arr_drawLine.length > 0 ) {
		obj_polyLine = new BMap.Polyline(arr_drawLine, {'strokeOpacity': 0.5});
		mapObj.addOverlay(obj_polyLine);	//向地图添加覆盖物 
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

//生成吹出框

/*
* 创建地图吹出框对象
*/
function fn_createMapInfoWindow (obj_location, str_type, n_pointIndex) {
	if ( !obj_mapInfoWindow ) {
		obj_mapInfoWindow = new BMap.InfoWindow(fn_tipContents(obj_location, str_type, n_pointIndex));
		
		obj_mapInfoWindow.addEventListener('close', function(e) {	// 吹出框关闭
			var obj_markerRegion = $('.j_body').data('markerregion');
			
			if ( obj_markerRegion ) {
				mapObj.removeOverlay(obj_markerRegion);
			}
		});
	} else {
		obj_mapInfoWindow.setContent(fn_tipContents(obj_location, str_type, n_pointIndex));
	}
	mapObj.closeInfoWindow();
	//注销之前的窗口事件
	obj_mapInfoWindow.removeEventListener('open', fn_infoWindowTextUpdate);
	//重新绑定吹出框事件
	obj_mapInfoWindow.addEventListener('open', fn_infoWindowTextUpdate(obj_location, str_type));
}

/**
* 吹出框打开方法的函数
*/
function fn_infoWindowTextUpdate(obj_location, str_type) { 
	var n_clon = obj_location.clongitude,
		n_clat = obj_location.clatitude;
	
	// 圆: 经纬度,半径 显示误差圈 
	var obj_circleData = {'circle': {'longitude': n_clon, 'latitude': n_clat, 'radius': obj_location.locate_error}, 'single_shape': 0};
	
	fn_displayMapShape(obj_circleData, false, true);
}


/**
* 吹出框内容更新
* obj_location: 位置信息
* str_iconType: marker类型
* n_index: 轨迹索引
* b_isGencoder: 是否进行逆地址编码
*/
function fn_tipContents(obj_location, str_iconType, n_index, b_isGencoder) {
	var	address = obj_location.name, 
		str_tempAddress = address,
		speed = obj_location.speed,
		n_timestamp = obj_location.timestamp,
		date = fn_changeNumToDateString(n_timestamp),
		n_degree = obj_location.degree, 
		str_degree = fn_changeData(n_degree, speed), //方向角处理
		str_degreeTip = '方向角：' + Math.round(n_degree),
		str_tid = obj_location.tid,
		str_clon = obj_location.clongitude/NUMLNGLAT,
		str_clat = obj_location.clatitude/NUMLNGLAT,
		str_type = obj_location.type == 0 ? 'GPS定位' : '基站定位',
		str_alias = obj_location.alias,
		str_title = '',
		str_html = '<div id="markerWindowtitle" class="cMsgWindow">';
	
	if ( address == '' || address == null ) {
		if ( str_clon == 0 || str_clat == 0 ) {
			address = '-';
		} else {
			address = '<a href="#" title="获取位置" onclick="fn_getAddressByLngLat('+str_clon+', '+str_clat+',\''+str_tid+'\',\''+ str_iconType +'\','+ n_index +');">获取位置</a>'; 
		}
	}
	
	if ( speed == '' || speed == 'undefined' || speed == null || speed == ' undefined' || typeof speed == 'undefined' ) { 
		speed = '0'; 
	} else {
		speed = speed;
	}
	str_title += fn_encode(str_alias);
	
	str_html += '<h4 tid="'+obj_location.tid+'">'+str_title+'</h4><ul>'+ 
				'<li><label>速度： '+ fn_NumForRound(speed, 1)+' km/h</label>'+
				'<label class="labelRight" title="'+str_degreeTip+'">方向： '+str_degree+'</label></li>'+
				'<li><label>经度： E '+str_clon.toFixed(CHECK_ROUNDNUM)+'</label>'+
				'<label class="labelRight">纬度： N '+str_clat.toFixed(CHECK_ROUNDNUM)+'</label></li>'+
				'<li><label>类型： '+ str_type +'</label>';
	
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
					obj_currentPoint = fn_createMapPoint(obj_currentData.clongitude, obj_currentData.clatitude),
					obj_prevPoint = fn_createMapPoint(obj_prevData.clongitude, obj_prevData.clatitude),
					n_pointDist = fn_forMarkerDistance(obj_currentPoint, obj_prevPoint);
				
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
				obj_currentPoint = fn_createMapPoint(obj_currentData.clongitude, obj_currentData.clatitude),
				obj_prevPoint = fn_createMapPoint(obj_prevData.clongitude, obj_prevData.clatitude),
				n_pointDist = fn_forMarkerDistance(obj_currentPoint, obj_prevPoint);
			
			n_tempDist += n_pointDist;
		}
	}
	if ( str_iconType == 'draw' || str_iconType == 'start' || str_iconType == 'end' ) {
		str_html += '<label class="labelRight">里程： '+ fn_NumForRound(n_tempDist/1000, 1) +' km</label></li>';
	}
	
	str_html += '<li>时间： '+ date +'</li>' + 
				'<li class="msgBox_addressLi" title="'+ str_tempAddress +'"><label class="msgBox_addressTip">位置：</label> <lable class="lblAddress">'+ address +'</label></li>';
	 

	str_html += '</ul></div>';
	return str_html;
}


/**
** 将获取到的name更新到marker或label上
* str_type: 轨迹或 realtime
* str_result: 获取到的位置
* n_index: 如果是轨迹则根据索引获取name
*/
function fn_updateAddress (str_type, tid, str_result, n_index, n_lon, n_lat) {
	var str_result = str_result,
		str_tempResult = str_result,
		obj_trackMarker = null,
		obj_trackLocation = '',
		str_tempResult = str_result.length > 20 ? str_result.substr(0, 20) + '...' : str_result;
		
	arr_dataArr[n_index].name = str_result;
	obj_trackLocation = arr_dataArr[n_index];
	
	if ( str_type == 'draw' ) {
		obj_trackMarker = actionMarker;
	} else if ( str_type == 'start' ) {
		obj_trackMarker = $('#control_panel').data('markers')[0];
	} else if ( str_type == 'end' ) {
		arr_dataArr[arr_dataArr.length - 1].name = str_result;
		obj_trackLocation = arr_dataArr[arr_dataArr.length - 1];
	}
	/* 根据不同的marker对象,填充数据*/
	if ( obj_trackMarker && obj_trackMarker.infoWindow ) {
		fn_createMapInfoWindow(obj_trackLocation, str_type, n_index);
		obj_trackMarker.openInfoWindow(obj_mapInfoWindow); // 显示吹出框
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
function fn_getAddressByLngLat(n_lon, n_lat, tid, str_type, n_index) {
	var gc = new BMap.Geocoder(),
		str_result = '',
		str_surroundingPois = '',
		obj_point = fn_createMapPoint(n_lon*3600000, n_lat*3600000);
	
	if ( str_type == 'draw' ) {
		//正在播放时,进行获取地址操作,停止播放动作
		$('#tPause').click();
	}
	var gc = new BMap.Geocoder();
		
	gc.getLocation(obj_point, function(result){
		str_result = result.address;
		
		if ( str_result != '' ) {
			fn_updateAddress(str_type, tid, str_result, n_index, n_lon, n_lat);
		}
	});
}

// timestamp->Date
function fn_changeNumToDateString (myEpoch, str_isYear) {
	var n_myEpoch = '';
	
	if ( str_isYear == 'sfm' ||   str_isYear == 'date' || str_isYear == 'ymd'  ) {
		n_myEpoch = myEpoch;
	} else {
		n_myEpoch = myEpoch*1000;
	}
	var	myDate = new Date(n_myEpoch),
        year = myDate.getFullYear(), 
        month = myDate.getMonth()+1,
	    day = myDate.getDate(), 
        hours = myDate.getHours(), 
        min = myDate.getMinutes(),
	    seconds = myDate.getSeconds();
	
    month = month < 10 ? '0'+month : month;
	day = day < 10 ? '0'+day : day;
	hours = hours < 10 ? '0'+hours : hours;
	min = min < 10 ? '0'+min : min;
	seconds = seconds < 10 ? '0'+seconds : seconds;
	
	if ( str_isYear == 'sfm' ) {
		return hours +':'+ min +':'+ seconds;
	} else if ( str_isYear == 'date' ) {
		return new Date(year, month - 1, day);
	} else if ( str_isYear == 'ymd' ) {
		return year +'-'+ month +'-'+ day;
	} else {
		return year +'-'+ month +'-'+ day +' '+ hours +':'+ min +':'+ seconds;
	}
}

//方向角处理
function fn_changeData (str_val, str_val2) {
	var arr_degree = [355,5,40,50,85,95,130,140,175,185,220,230,265,275,310,320,355],
		arr_desc  = ['正北','北偏东','东北','东偏北','正东','东偏南','东南','南偏东','正南','南偏西','西南','西偏南','正西','西偏北','西北','北偏西','正北'];
	
	if ( str_val2 == 0 ) {
		return '静止';
	}
	for ( var i = 0; i < arr_degree.length; i++ ) {
		if ( str_val >= 355 || str_val < 5 ) {
			str_return = '正北';
			break;
		} else if ( str_val >= arr_degree[i] && str_val < arr_degree[i+1] ) {
			str_return = arr_desc[i];
			break;
		}	
	}
	return str_return;
}

/*
* 对给定的数值进行小数位截取
* n_num: 要操作的数字
* n_round: 小数后保留的位数
*/
function fn_NumForRound (n_num, n_round) {
	var n_roundNum = 1;
	
	if ( n_round != 0 ) {
		for ( var i = 1; i <= n_round; i++ ) {
			n_roundNum = n_roundNum * 10
		}
	}
	return Math.round(n_num * n_roundNum) / n_roundNum;
}

/**
* html标签 编码
*/
function fn_encode (str) {
	return str.replace(/\&/g, '&amp;').replace(/\>/g, '&gt;').replace(/\</g, '&lt;');
}

//计算两点间距离

function fn_forMarkerDistance(point1, point2) {
	// Based on http://www.ngs.noaa.gov/PUBS_LIB/inverse.pdf
	// using the "Inverse Formula" (section 4)
	var EARTHRADIUS = 6370996.81,  // 取WGS84标准参考椭球中的地球长半径(单位:m)
		lon1 = point1.lng,
		lon2 = point2.lng,
		lat1 = point1.lat,
		lat2 = point2.lat,
		MAXITERS = 20;
		
	// Convert lat/long to radians
	lat1 = lat1 * Math.PI / 180.0;
	lat2 = lat2 * Math.PI / 180.0;
	lon1 = lon1 * Math.PI / 180.0;
	lon2 = lon2 * Math.PI / 180.0;

	var a = 6378137.0, // WGS84 major axis
		b = 6356752.3142, // WGS84 semi-major axis
		f = (a - b) / a,
		aSqMinusBSqOverBSq = (a * a - b * b) / (b * b);

	var L = lon2 - lon1,
		A = 0.0,
		U1 = Math.atan((1.0 - f) * Math.tan(lat1)),
		U2 = Math.atan((1.0 - f) * Math.tan(lat2));

	var cosU1 = Math.cos(U1),
		cosU2 = Math.cos(U2),
		sinU1 = Math.sin(U1),
		sinU2 = Math.sin(U2),
		cosU1cosU2 = cosU1 * cosU2,
		sinU1sinU2 = sinU1 * sinU2;

	var sigma = 0.0,
		deltaSigma = 0.0,
		cosSqAlpha = 0.0,
		cos2SM = 0.0,
		cosSigma = 0.0,
		sinSigma = 0.0,
		cosLambda = 0.0,
		inLambda = 0.0;

	var lambda = L; // initial guess
	
	for (var iter = 0; iter < MAXITERS; iter++) {
		var lambdaOrig = lambda;
		
		cosLambda = Math.cos(lambda);
		sinLambda = Math.sin(lambda);
		var t1 = cosU2 * sinLambda,
			t2 = cosU1 * sinU2 - sinU1 * cosU2 * cosLambda,
			sinSqSigma = t1 * t1 + t2 * t2; // (14)
			
		sinSigma = Math.sqrt(sinSqSigma);
		cosSigma = sinU1sinU2 + cosU1cosU2 * cosLambda; // (15)
		sigma = Math.atan2(sinSigma, cosSigma); // (16)
		
		var sinAlpha = (sinSigma == 0) ? 0.0 : cosU1cosU2 * sinLambda
				/ sinSigma; // (17)
				
		cosSqAlpha = 1.0 - sinAlpha * sinAlpha;
		cos2SM = (cosSqAlpha == 0) ? 0.0 : cosSigma - 2.0 * sinU1sinU2
				/ cosSqAlpha; // (18)

		var uSquared = cosSqAlpha * aSqMinusBSqOverBSq; // defn
		
		A = 1 + (uSquared / 16384.0)
				* // (3)
				(4096.0 + uSquared
						* (-768 + uSquared * (320.0 - 175.0 * uSquared)));
						
		var B = (uSquared / 1024.0) * // (4)
				(256.0 + uSquared
						* (-128.0 + uSquared * (74.0 - 47.0 * uSquared)));
		var C = (f / 16.0) * cosSqAlpha
				* (4.0 + f * (4.0 - 3.0 * cosSqAlpha)); // (10)
		var  cos2SMSq = cos2SM * cos2SM;
		
		deltaSigma = B
				* sinSigma
				* // (6)
				(cos2SM + (B / 4.0)
						* (cosSigma * (-1.0 + 2.0 * cos2SMSq) - (B / 6.0)
								* cos2SM
								* (-3.0 + 4.0 * sinSigma * sinSigma)
								* (-3.0 + 4.0 * cos2SMSq)));

		lambda = L
				+ (1.0 - C)
				* f
				* sinAlpha
				* (sigma + C
						* sinSigma
						* (cos2SM + C * cosSigma
								* (-1.0 + 2.0 * cos2SM * cos2SM))); // (11)

		var delta = (lambda - lambdaOrig) / lambda;
		if (Math.abs(delta) < 1.0e-12) {
			break;
		}
	}
	return (b * A * (sigma - deltaSigma));
}

//动态播放事件


//添加图形
function fn_displayMapShape (obj_shapeData, b_seCenter, b_locateError, obj_centerPointer) {
	var shapeOptions = {//样式
			strokeColor: '#5ca0ff',    //边线颜色。
			fillColor: '#ced7e8',      //填充颜色。当参数为空时，圆形将没有填充效果。
			strokeWeight: 0.5,       //边线的宽度，以像素为单位。
			strokeOpacity: 0.8,	   //边线透明度，取值范围0 - 1。
			fillOpacity: 0.5,      //填充的透明度，取值范围0 - 1。
			strokeStyle: 'solid' //边线的样式，solid或dashed。
		},
		n_region_shape = obj_shapeData.single_shape,
		obj_tempRegionShape = null;
	
	if ( n_region_shape == 0 ) { // 围栏类型 0: 圆形 1: 多边形
		var obj_regionData = obj_shapeData.circle
			centerPoint = fn_createMapPoint(obj_regionData.longitude, obj_regionData.latitude);
			
		obj_tempRegionShape = new BMap.Circle(centerPoint, obj_regionData.radius, shapeOptions);
	} else {
		var arr_tempPolygonData = [],
			arr_polygonDatas = obj_shapeData.polygon,
			n_lenPolygon = arr_polygonDatas.length;
		
		for ( var i = 0; i < n_lenPolygon; i++) {
			var obj_temPolygonPts = arr_polygonDatas[i],
				n_lon = obj_temPolygonPts.longitude,
				n_lat = obj_temPolygonPts.latitude;
			
			arr_tempPolygonData.push(fn_createMapPoint(n_lon, n_lat));
		}
		obj_tempRegionShape = new BMap.Polygon(arr_tempPolygonData, shapeOptions);
	}
	// 是否是误差圈
	mapObj.addOverlay(obj_tempRegionShape);
}

/**
* 动态标记显示
*/
function fn_markerAction() { 
	$('#tPlay').unbind('mousedown');
	window.setTimeout(fn_drawMarker, 100);	// 先添加第一个点的marker
	timerId = window.setInterval(fn_drawMarker, n_speed);	// 按照设置播放速度播放轨迹点
}

/**
* 轨迹查询暂停播放动画操作
*/
function fn_trackQueryPause() {
	if ( timerId ) { clearInterval(timerId) };
	str_actionState = counter;
}

/**
* 绑定播放按钮的事件
*/
function fn_bindPlay() {
	$('#tPlay').unbind('mousedown').bind('mousedown', fn_markerAction);
}

/**
* 动态标记移动方法
*/
function fn_drawMarker(str_step) {
	var n_len = arr_dataArr.length,
		str_tid = $('#tempSingleId').html(),
		obj_selfInfoWindow = null;
	
	if ( str_actionState != 0 ) {
		counter = str_actionState;
		str_actionState = 0;
	}
	// 对要播放的点进行计步
	if ( str_step ) {	
		if ( str_step ==  'next' ) {
			counter++;
		} else {
			counter--;
		}
	} else {
		counter++;
	}
	
	if ( counter <= n_len-1 ) {
		if ( actionMarker ) {
			obj_selfInfoWindow = actionMarker.infoWindow;
			mapObj.removeOverlay(actionMarker);
		}
		arr_dataArr[counter].tid = str_tid;	// 轨迹播放传递tid
		fn_addMarker(arr_dataArr[counter], 'draw', 0, counter); // 添加标记
		// 将播放过的点放到数组中
		var obj_tempPoint = fn_createMapPoint(arr_dataArr[counter].clongitude, arr_dataArr[counter].clatitude);
		
		arr_drawLine.push(obj_tempPoint);
		obj_drawLine.setPath(arr_drawLine);
			
		if ( obj_selfInfoWindow ) {
			fn_createMapInfoWindow(arr_dataArr[counter], 'draw', counter);
			actionMarker.openInfoWindow(obj_mapInfoWindow); // 显示吹出框 
		}
		fn_boundContainsPoint(obj_tempPoint);
	} else {	// 播放完成
		fn_clearTrack();	// 清除数据
		mapObj.removeOverlay(actionMarker);
		actionMarker = null;
		$('#tPause').hide();
		$('#tPlay').css('display', 'inline-block');
	}
}

/***
* 计算点是否超出地图，如果超出设置地图中心点为当前点
*/
function fn_boundContainsPoint (obj_tempPoint) {
	// 是否进行中心点移动操作 如果当前播放点在屏幕外则,设置当前点为中心点
	var obj_mapBounds = mapObj.getBounds(), 
		b_isInbound = null;
	
	if ( obj_mapBounds ) {
		b_isInbound = obj_mapBounds.containsPoint(obj_tempPoint);
	}
	if ( !b_isInbound ) {
		mapObj.setCenter(obj_tempPoint);
	}
}

/**
* 初始化播放过的线对象
*/
function fn_createDrawLine () {
	obj_drawLine = fn_createPolyline(arr_drawLine, {'color': 'red'});
}

/**
* 关闭轨迹清除数据
*/
function fn_clearTrack (clearType) { 
	if ( timerId ) { clearInterval(timerId) };	// 清除计时器
	str_actionState = 0;
	counter = -1;
	arr_drawLine = [];
}









