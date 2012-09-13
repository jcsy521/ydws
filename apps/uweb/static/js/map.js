/*
*地图相关操作方法
*/
var postAddress = null;
(function () {
/*添加标记
* n_counter : draw 时根据值修改数组中点的位置描述  下次就不用重新获取位置
*/
window.dlf.fn_addMarker = function(obj_location, str_iconType, n_carNum, isOpenWin, str_operation, n_index) {
	var n_degree = dlf.fn_processDegree(obj_location.degree),  // 车辆方向角
		str_imgUrl = '/static/images/' + n_degree + '.png', 
		myIcon = new BMap.Icon(str_imgUrl, new BMap.Size(34, 34)),
		mPoint = new BMap.Point(obj_location.clongitude/NUMLNGLAT, obj_location.clatitude/NUMLNGLAT), 
		infoWindow = new BMap.InfoWindow(dlf.fn_tipContents(obj_location, str_iconType, str_operation, n_index)),  // 创建信息窗口对象;
		marker = null,
		label = new BMap.Label(obj_location.alias, {offset:new BMap.Size(31, 22)}); // todo  tid >>  别名
	label.setStyle({background: '#FFA500', fontSize: '13px', height: '20px', borderColor: '#000', lineHeight: '24px',opacity: '0.7','paddingLeft': '5px','paddingRight': '5px'});
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
		marker.setLabel(label);	// marker标记
		var obj_carItem = $('#carList a').eq(n_carNum);
		obj_carItem.data('selfmarker', marker);
		obj_carItem.data('selfLable', marker.getLabel());
	} else if ( str_iconType == 'start' || str_iconType == 'end' ) {
		marker.setOffset(new BMap.Size(-1, -14));
	}
	
	mapObj.addOverlay(marker);//向地图添加覆盖物 
	if ( isOpenWin ) {
		console.log('open window');
		marker.openInfoWindow(infoWindow);
	}
	marker.addEventListener('click', function(){  
	    // 进行左侧车辆列表的切换
	   if ( str_iconType == 'actiontrack' ) { // 主页车辆点击与左侧车辆列表同步
			var obj_carItem = $('#carList a').eq(n_carNum),
				str_className = obj_carItem.attr('class'), 
				str_tid = obj_carItem.attr('tid');
			// 如果是当前车的话就直接打开infoWindow否则switchcar中打开infoWindow
			if ( str_className.search('currentCar') != -1 ) { // 如果用户点击当前车辆不做操作
				this.openInfoWindow(this.selfInfoWindow); // 显示吹出框
				return;
			}
			dlf.fn_switchCar(str_tid, obj_carItem); // 车辆列表切换
		} else {
			var str_name = arr_dataArr[n_index].name,
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
// 吹出框内容
window.dlf.fn_tipContents = function (obj_location, str_iconType, str_operation, n_index) { 
	var	address = obj_location.name, 
		speed = obj_location.speed,
		date = dlf.fn_changeNumToDateString(obj_location.timestamp),
		n_degree = obj_location.degree, 
		str_degree = dlf.fn_changeData('degree', n_degree), //方向角处理
		str_degreeTip = '方向角：' + Math.round(n_degree),
		str_tid = obj_location.tid,
		str_clon = obj_location.clongitude/NUMLNGLAT,
		str_clat = obj_location.clatitude/NUMLNGLAT,
		//str_mobile = obj_location.mobile, 
		str_type = obj_location.type == GPS_TYPE ? 'GPS定位' : '基站定位',
		str_alias = obj_location.alias,
		str_title = '车辆：',
		str_tempMsg = '开始跟踪',
		str_actionTrack =$('#carList a[tid='+str_tid+']').attr('actiontrack'),
		str_html = '<div id="markerWindowtitle" class="cMsgWindow">';
	if ( str_actionTrack == 'yes' ) {
		str_tempMsg = '取消跟踪';
	}
	if (str_tid == '' || str_tid == 'undefined' || str_tid == null ) { 
		str_tid = $('#carList a[class*=currentCar]').attr('tid');
	}
	if ( address == '' || address == null ) {
		if ( str_operation == 'lastinfo' ) {
			// 判断经纬度是否和上一次经纬度相同   如果相同直接拿上一次获取位置
			var obj_currentLi = $('#carList a[tid='+str_tid+']'),
				obj_oldCarData = obj_currentLi.parent().data('carData'),
				obj_selfmarker = obj_currentLi.data('selfmarker'),
				str_oldClon = obj_oldCarData.clongitude,
				str_oldClat = obj_oldCarData.clatitude,
				str_newClon = obj_location.clongitude,
				str_newClat = obj_location.clatitude;
			// 第一次加载 没有selfmarker 
			if ( obj_selfmarker ) {
				// lastinfo or realtime not the first request, 判断和上次经纬度的差是否在100之内，在的话认为是同一个点
				if ( Math.abs(str_oldClon-str_newClon) < 100 || Math.abs(str_oldClat-str_newClat) < 100 ) {
					var obj_infowindow = obj_selfmarker.selfInfoWindow;
					if ( obj_infowindow && obj_infowindow != null ) {
						var str_content = obj_infowindow.getContent(),
							n_beginNum = str_content.indexOf('位置： ')+30,	// <lable class="lblAddress">
							n_endNum = str_content.indexOf('</label></li><li class="top10">'),
							str_address = str_content.substring(n_beginNum, n_endNum);
						address = str_address;
					}
				} else {
					// 否则重新获取
					address = '正在获取位置描述...<img src="/static/images/blue-wait.gif" />'; 
					dlf.fn_getAddressByLngLat(str_clon, str_clat, str_tid, 'lastinfo');
				}
			} else {
				address = '正在获取位置描述...<img src="/static/images/blue-wait.gif" />'; 
				dlf.fn_getAddressByLngLat(str_clon, str_clat, str_tid, 'lastinfo');
			}
		} else if ( str_operation == 'draw' || str_operation == 'start' || str_operation == 'end' )  {
			address = '<a href="#" title="获取位置" onclick="dlf.fn_getAddressByLngLat('+str_clon+', '+str_clat+',\''+str_tid+'\',\'draw\','+ n_index +');">获取位置</a>'; 
		} else {
			address = '<a href="#" title="获取位置" onclick="dlf.fn_getAddressByLngLat('+str_clon+', '+str_clat+',event,"'+str_tid+'");">获取位置</a>'; 
		}
	}
	if (speed == '' || speed == 'undefined' || speed == null || speed == ' undefined' || typeof speed == 'undefined') { 
		speed = '0'; 
	} else {
		speed = speed;
	}
	if ( str_alias ) { // 如果是轨迹回放 
		str_title += str_alias;
	} else {
		str_title += $('#carList a[tid='+str_tid+']').siblings('span').html();
	}
	
	str_html += '<h4 tid="'+obj_location.tid+'">'+str_title+'</h4><ul>'+ 
				'<li><label>速度： '+ speed+' km/h</label>'+
				'<label class="labelRight" title="'+str_degreeTip+'">方向： '+str_degree+'</label></li>'+
				'<li><label>经度： E '+Math.round(str_clon*CHECK_INTERVAL)/CHECK_INTERVAL+'</label>'+
				'<label class="labelRight">纬度： N '+Math.round(str_clat*CHECK_INTERVAL)/CHECK_INTERVAL+'</label></li>'+
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
// 清除页面上的地图图形数据
window.dlf.fn_clearMapComponent = function() {
	mapObj.clearOverlays();
}

/**
** 根据经纬度向百度获取地理位置描述
*/
window.dlf.fn_updateAddress = function(str_type, tid, str_result, n_index) {
	var str_result = str_result,
		obj_selfmarker = $('#carList a[tid='+tid+']').data('selfmarker'),
		obj_addressLi = $('#markerWindowtitle ul li').eq(4);
	if ( str_type == 'realtime' || str_type == 'lastinfo' ) {
		var str_currentTid = $('#carList a[class*=currentCar]').attr('tid');
		// 左侧 位置描述填充
		$('#address').html(str_result);
		if ( str_currentTid == tid ) {
			obj_addressLi.html('').html('位置：<lable class="lblAddress">' + str_result + '</label>');	// 替换marker上的位置描述
		}
		if ( obj_selfmarker && obj_selfmarker != null ) {
			var str_content = obj_selfmarker.selfInfoWindow.getContent(),
				str_address = '';
			if ( str_content.search('正在获取位置描述...') != -1 ) {
				str_content = str_content.replace('正在获取位置描述...<img src="/static/images/blue-wait.gif" />', str_result);
			} else {
				n_beginNum = str_content.indexOf('位置： ')+30,	// <lable class="lblAddress">
				n_endNum = str_content.indexOf('</label></li><li class="top10">'),
				str_address = str_content.substring(n_beginNum, n_endNum);
				str_content = str_content.replace(str_address, str_result);
			}
			obj_selfmarker.selfInfoWindow.setContent(str_content);
		}
	} else {
		if ( n_index >= 0 ) {
			arr_dataArr[n_index].name = str_result;
		}
		obj_addressLi.html('位置：' + str_result);	// 替换marker上的位置描述
	}
}
window.dlf.fn_getAddressByLngLat = function(n_lon, n_lat, tid, str_type, n_index) {
	var gc = new BMap.Geocoder(),
		str_result = '',
		obj_point = new BMap.Point(n_lon, n_lat);	// n_lon, n_lat
	if ( n_lon == 0 || n_lat == 0 ) {
		$('#address').html('-');
	} else {
		gc.getLocation(obj_point, function(result){
			str_result = result.address;
			if ( str_result == '' ) {
				// 第一次如果未获取位置则重新获取一次,如果还未获得则显示"无法获取"
				if ( postAddress != null ) {
					clearTimeout(postAddress);
					str_result = '无法获取位置';
					dlf.fn_updateAddress(str_type, tid, str_result, n_index);
				} else {
					// 如果未获取到位置描述  5秒后重新获取
					str_result = '正在获取位置描述...<img src="/static/images/blue-wait.gif" />';
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