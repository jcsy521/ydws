Index: map_baidu.js
===================================================================
--- map_baidu.js	(revision 1288)
+++ map_baidu.js	(working copy)
@@ -573,6 +573,43 @@
 	return str_result;
 }
 
+/**
+* kjj 2013-07-10 create
+* GPS点转换成百度点
+* n_lng, n_lat
+* tips:  data format is jsonp
+*/
+window.dlf.fn_translateToBMapPoint = function(n_lng, n_lat, str_type, obj_carInfo) {
+	//GPS坐标
+	var gpsPoint = dlf.fn_createMapPoint(n_lng, n_lat);
+
+	jQuery.ajax({
+		type : 'get',
+		timeout: 14000,
+		url : 'http://api.map.baidu.com/ag/coord/convert?from=0&to=4&y='+ gpsPoint.lat +'&x='+ gpsPoint.lng,
+		dataType : 'jsonp',
+		contentType : 'application/jsonp; charset=utf-8',
+		success : function(successData) {
+			var lng = successData.x,
+				lat = successData.y
+				point = new BMap.Point(lng, lat),
+				str_currentTid = $($('.j_carList a[class*=j_currentCar]')).attr('tid');
+				
+			if ( str_type == 'lastposition' ) {
+				obj_carInfo.clongitude = point.lng*3600000;
+				obj_carInfo.clatitude = point.lat*3600000;
+				dlf.fn_updateInfoData(obj_carInfo); // 工具箱动态数据		
+				if ( str_currentTid == obj_carInfo.tid ) {	// 更新当前车辆信息
+					dlf.fn_updateTerminalInfo(obj_carInfo);
+				}
+			}
+		},
+        error : function(xyResult) {
+			return;
+		}, 
+	});
+}
+
 /*
 * 点击地图添加标记
 */
Index: track.js
===================================================================
--- track.js	(revision 1288)
+++ track.js	(working copy)
@@ -69,6 +69,8 @@
 		obj_selfmarkers = {};
 		
 		LASTINFOCACHE = 0; //轨迹查询后重新获取终端数据
+		dlf.fn_clearOpenTrackData();	// 初始化开启追踪的数据
+		$('.j_body').data('lastposition_time', -1);
 		if ( !dlf.fn_userType() ) {
 			// $('.j_carList').removeData('carsData');
 			dlf.fn_getCarData('first');	// 重新请求lastinfo
Index: initialize_common.js
===================================================================
--- initialize_common.js	(revision 1288)
+++ initialize_common.js	(working copy)
@@ -454,27 +454,41 @@
 * 每隔15秒获取数据
 */
 window.dlf.fn_getCarData = function(str_flag) {
-	var str_currentTid = $($('.j_carList a[class*=j_currentCar]')).attr('tid'),	//当前车tid
+	var obj_tempCarsData = $('.j_carList').data('carsData'),
+		str_currentTid = $($('.j_carList a[class*=j_currentCar]')).attr('tid'),	//当前车tid
 		obj_carListLi = $('.j_carList li'),
 		n_length = obj_carListLi.length, 	//车辆总数
 		n_count = 0, 
 		arr_tids = [], 
-		obj_tids= {'tids': [str_currentTid], 'cache': 0};	//所有车的tid集合、是否是第一次lastinfo
+		obj_param = {'lastposition_time': -1, 'cache': 0, 'track_list': []},
+		arr_tracklist = [],
+		str_lastpositionTime = $('.j_body').data('lastposition_time');
 	
-	for( var i = 0; i < n_length; i++ ) {	//遍历每辆车获取tid
-		var str_tempTid = obj_carListLi.eq(i).children().attr('tid');	
-		if ( str_tempTid ) {
-			arr_tids[n_count++] = str_tempTid;
-		}
+	if ( dlf.fn_isEmptyObj(obj_tempCarsData) ) {	// 判断carsData是否有数据
+		$('.j_terminal').each(function() {
+			var str_tid = $(this).attr('tid'),
+				str_actionTrack = dlf.fn_getActionTrackStatus(str_tid);
+				
+			if ( str_actionTrack == 'yes' ) {
+				arr_tracklist.push({'track_tid': str_tid, 'track_time': obj_tempCarsData[str_tid].timestamp});
+			}
+		});
 	}
-	obj_tids.tids = arr_tids;
-	$.post_(LASTINFO_URL, JSON.stringify(obj_tids), function (data) {	// 向后台发起lastinfo请求
+	if ( str_lastpositionTime ) {
+		obj_param.lastposition_time = str_lastpositionTime;
+	}
+	if ( arr_tracklist.length > 0 ) {
+		obj_param.track_list = arr_tracklist;
+	}
+	
+	$.post_(LASTPOSITION_URL, JSON.stringify(obj_param), function (data) {	// 向后台发起lastinfo请求
 			if ( data.status == 0 ) {
-				var obj_cars = data.cars_info,
+				var obj_cars = data.res,
 					obj_tempData = {},
 					arr_locations = [],
 					n_pointNum = 0;
-					
+
+				$('.j_body').data('lastposition_time', data.lastposition_time);	// 存储post返回的上次更新时间  返给后台
 				// 重新生成终端列表
 				fn_createTerminalList(obj_cars);
 				if ( !dlf.fn_isEmptyObj(obj_cars) ) {
@@ -483,25 +497,31 @@
 				}
 				
 				for ( var param in obj_cars ) {
-					var obj_carInfo = obj_cars[param], 
+					var obj_resData = obj_cars[param],
+						obj_carInfo = obj_resData.car_info, 
+						obj_trackInfo = obj_resData.track_info,	// 开启追踪后丢的点
 						str_tid = param,
 						n_enClon = obj_carInfo.clongitude,
 						n_enClat = obj_carInfo.clatitude,
+						n_lon = obj_carInfo.longitude,
+						n_lat = obj_carInfo.latitude,
 						n_clon = n_enClon/NUMLNGLAT,	
 						n_clat = n_enClat/NUMLNGLAT;
-						
+					
 					obj_carInfo.tid = str_tid;
 					obj_tempData[str_tid] = obj_carInfo;
 					
-					if ( n_clon != 0 && n_clat != 0 ) {
-						n_pointNum ++;
-						arr_locations.push({'clongitude': n_enClon, 'clatitude': n_enClat});
-						if ( obj_carInfo ) {
-							//obj_carA.data('carData', obj_carInfo);
+					if ( n_lon != 0 && n_lat != 0 ) {
+						obj_carInfo.track_info = obj_trackInfo;
+						
+						if ( n_clon != 0 && n_clat != 0 ) {
+							n_pointNum ++;
+							arr_locations.push({'clongitude': n_enClon, 'clatitude': n_enClat});
 							dlf.fn_updateInfoData(obj_carInfo, str_flag); // 工具箱动态数据
+						} else {
+							dlf.fn_translateToBMapPoint(n_lon, n_lat, 'lastposition', obj_carInfo);	// 前台偏转 kjj 2013-07-11
 						}
 					}
-					
 					if ( str_currentTid == str_tid ) {	// 更新当前车辆信息
 						dlf.fn_updateTerminalInfo(obj_carInfo);
 					}
@@ -574,12 +594,14 @@
 * type: 是否是实时定位
 */
 window.dlf.fn_updateTerminalInfo = function (obj_carInfo, type) {
-	var str_tmobile = obj_carInfo.mobile,
+	var str_tid = obj_carInfo.tid,
+		str_tmobile = obj_carInfo.mobile,
 		n_defendStatus = obj_carInfo.mannual_status, 
 		str_dStatus = n_defendStatus == DEFEND_ON ? '已设防' : '未设防', 
 		str_dStatusTitle =  n_defendStatus == DEFEND_ON ? '设防状态：已设防' : '设防状态：未设防',
 		str_dImg= n_defendStatus == DEFEND_ON ? 'defend_status1.png' : 'defend_status0.png',
-		str_type = obj_carInfo.type == GPS_TYPE ? 'GPS定位' : '基站定位',
+		n_pointType = obj_carInfo.type,
+		str_type = n_pointType == GPS_TYPE ? 'GPS定位' : '基站定位',
 		str_speed = obj_carInfo.speed + ' km/h',
 		n_degree = obj_carInfo.degree,
 		str_degree = dlf.fn_changeData('degree', n_degree), //方向角处理
@@ -590,8 +612,13 @@
 		n_clon = obj_carInfo.clongitude/NUMLNGLAT,	
 		str_clon = '',
 		n_clat = obj_carInfo.clatitude/NUMLNGLAT,
-		str_clat = '';	// 经纬度
+		str_clat = '',	// 经纬度
+		str_actionTrack = dlf.fn_getActionTrackStatus(str_tid);
 		
+		
+	if ( !dlf.fn_userType() && str_actionTrack == '1' && n_pointType == CELLID_TYPE ) { // 2013.7.9 个人用户 开户追踪后,基站点及信息不进行显示
+		return;
+	}
 	if ( n_clat == 0 || n_clon == 0 ) {	// 经纬度为0 不显示位置信息
 		str_address = '-';
 		str_degree = '-';
@@ -659,7 +686,8 @@
 		obj_tempSelfMarker = {};
 	
 	for(var param in obj_carDatas) {
-		var obj_carInfo = obj_carDatas[param], 
+		var obj_tempRes = obj_carDatas[param],
+			obj_carInfo = obj_tempRes.car_info, 
 			str_tid = param, // 终端 tid
 			str_loginStatus = obj_carInfo.login, //终端状态
 			str_alias = obj_carInfo.alias, // 终端车牌号
@@ -1329,7 +1357,8 @@
 		str_tempWrapperId = str_wrapperId,
 		n_wrapperWidth = obj_wrapper.width(),
 		n_width = ($(window).width() - n_wrapperWidth)/2,
-		b_trackStatus = $('#trackHeader').is(':visible');	// 轨迹是否打开着
+		b_trackStatus = $('#trackHeader').is(':visible'),	// 轨迹是否打开着
+		b_bindRegionStatus = $('#bindRegionWrapper').is(':visible');	// 围栏绑定是否显示
 
 	$('.j_delay').hide();
 	dlf.fn_closeJNotifyMsg('#jNotifyMessage');
@@ -1364,8 +1393,8 @@
 			dlf.fn_closeTrackWindow(true);
 		}
 	}
-	if ( b_trackStatus ) {	// 如果轨迹打开 要重启lastinfo	
-		if ( str_wrapperId == 'bindLine' || str_wrapperId == 'corpTerminal' || str_wrapperId == 'defend' || str_wrapperId == 'singleMileage' || str_wrapperId == 'cTerminal' || str_wrapperId == 'fileUpload' || str_wrapperId == 'batchDelete' || str_wrapperId == 'batchDefend' || str_wrapperId == 'batchTrack' || str_wrapperId == 'smsOption' || str_wrapperId == 'terminal' || str_wrapperId == 'corpSMSOption' ) {
+	if ( b_trackStatus || b_bindRegionStatus ) {	// 如果轨迹打开 要重启lastinfo	
+		if ( str_wrapperId == 'realtime' || str_wrapperId == 'bindLine' || str_wrapperId == 'corpTerminal' || str_wrapperId == 'defend' || str_wrapperId == 'singleMileage' || str_wrapperId == 'cTerminal' || str_wrapperId == 'fileUpload' || str_wrapperId == 'batchDelete' || str_wrapperId == 'batchDefend' || str_wrapperId == 'batchTrack' || str_wrapperId == 'smsOption' || str_wrapperId == 'terminal' || str_wrapperId == 'corpSMSOption' ) {
 			dlf.fn_closeTrackWindow(true);	// 关闭轨迹查询,不操作lastinfo
 		} else if ( str_wrapperId == 'bindBatchRegion' || str_wrapperId == 'eventSearch' ) {
 			dlf.fn_closeTrackWindow(false);	// 关闭轨迹查询,不操作lastinfo
