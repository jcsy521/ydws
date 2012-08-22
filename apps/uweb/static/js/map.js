/*
*地图相关操作方法
*/
(function () {
/*添加标记*/
window.dlf.fn_addMarker = function(obj_location, str_iconType, n_carNum, isOpenWin) { 
	var n_degree = dlf.fn_processDegree(obj_location.degree),  // 车辆方向角
		str_imgUrl = '/static/images/' + n_degree + '.png', 
		myIcon = new BMap.Icon(str_imgUrl, new BMap.Size(34, 34)),
		mPoint = new BMap.Point(obj_location.clongitude/NUMLNGLAT, obj_location.clatitude/NUMLNGLAT), 
		infoWindow = new BMap.InfoWindow(dlf.fn_tipContents(obj_location, str_iconType)),  // 创建信息窗口对象;
		marker = null;
	if ( str_iconType == 'start' ) {
		str_imgUrl = '/static/images/green_MarkerA.png';
	} else if ( str_iconType == 'end' ) {
		str_imgUrl = '/static/images/green_MarkerB.png';
	} else {
		str_imgUrl = '/static/images/'+n_degree+'.png';
	}
	myIcon.imageUrl = str_imgUrl;
	marker= new BMap.Marker(mPoint, {icon: myIcon}); 
	marker.setOffset(new BMap.Size(0, 0));
	marker.selfInfoWindow = infoWindow;
	if ( str_iconType == 'draw' ) {
		actionMarker = marker;
		marker.setIcon(marker.getIcon().setImageUrl ('/static/images/'+n_degree+'.png'));
	} else if ( str_iconType == 'actiontrack' ) {
		var obj_carItem = $('#carList a').eq(n_carNum);
		obj_carItem.data('selfmarker', marker);
	}
	
	mapObj.addOverlay(marker);//向地图添加覆盖物 
	if ( isOpenWin ) {
		marker.openInfoWindow(infoWindow);
	}
	marker.addEventListener('click', function(){   
	   this.openInfoWindow(infoWindow);
	});
}
// 吹出框内容
window.dlf.fn_tipContents = function (obj_location, str_iconType) { 
	var	address = obj_location.name, 
		speed = obj_location.speed,
		date = dlf.fn_changeNumToDateString(obj_location.timestamp),
		n_degree = Math.round(obj_location.degree), 
		str_tid = obj_location.tid,
		str_clon = obj_location.clongitude/NUMLNGLAT,
		str_clat = obj_location.clatitude/NUMLNGLAT,
		//str_mobile = obj_location.mobile, 
		str_alias = obj_location.alias,
		str_title = '车辆：',
		str_tempMsg = '开始跟踪',
		str_actionTrack =$('#carList .currentCar').attr('actiontrack'),
		str_html = '<div id="markerWindowtitle" class="cMsgWindow">';
	if ( str_actionTrack == 'yes' ) {
		str_tempMsg = '取消跟踪';
	}
	if (address == '' || address == 'undefined' || address == null || address == ' undefined' || typeof address == 'undefined') { 
		address = ''; 
	}
	if (str_tid == '' || str_tid == 'undefined' || str_tid == null || str_tid == ' undefined' || typeof str_tid == 'undefined') { 
		str_tid = ''; 
	}
	if (speed == '' || speed == 'undefined' || speed == null || speed == ' undefined' || typeof speed == 'undefined') { 
		speed = '0'; 
	} else {
		speed = Math.round(speed*10)/10;
	}
	if ( str_alias ) { // 如果是轨迹回放 
		str_title += str_alias;
	} else {
		str_tid = $('#carList .currentCar').attr('tid');
		str_title += $('#carList a[tid='+str_tid+']').siblings('span').html();
	}
	
	if ( n_degree == 0 ) {
		n_degree = 10;
	}
	str_html += '<h4>'+str_title+'</h4><ul>'+ 
				'<li><label>速度： '+ speed+' km/h</label>'+
				'<label class="labelRight">方向角： '+n_degree+'</label></li>'+
				'<li><label>经度： '+Math.floor(str_clon*CHECK_INTERVAL)/CHECK_INTERVAL+'</label>'+
				'<label class="labelRight">纬度： '+Math.floor(str_clat*CHECK_INTERVAL)/CHECK_INTERVAL+'</label></li>'+
				'<li>时间： '+ date +'</li>' + 
				'<li>位置： '+ address +'</li>';
	if ( str_iconType == 'actiontrack' ) {
		str_html+='<li class="top10"><a href="#" onclick="dlf.setTrack(\''+str_tid+'\', this);">'+ str_tempMsg +'</a>'+
			'<a href="#" id="trackReplay" onclick="dlf.fn_initTrack();">轨迹查询</a><a href="#" id="poiSearch" onclick="dlf.fn_POISearch('+ str_clon +', '+ str_clat +');" >周边查询</a></li>';
	}
	str_html += '</ul></div>';
	return str_html;
			
} 
// 清除页面上的地图图形数据
window.dlf.fn_clearMapComponent = function() {
	mapObj.clearOverlays();
}
})();