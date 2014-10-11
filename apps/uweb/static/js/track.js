/*
*轨迹查询相关操作方法
*/

/**
*开始动态效果
*timerId : 动态时间控制器
*counter : 动态运行次数
*str_actionState : 暂停操作的状态
*n_speed: 默认播放速度
*b_trackMsgStatus: 动态marker的吹出框是否显示
*/
var timerId = null, counter = 0, str_actionState = 0, n_speed = 200, b_trackMsgStatus = true,obj_drawLine = null, arr_drawLine = [];
/**
* 初始化轨迹显示页面
*/
dlf.fn_initTrack = function() {
	var obj_trackHeader =  $('.j_delay');
	
	$("#showMusic").html('');
	$('.j_alarm').hide();
	dlf.fn_clearNavStatus('eventSearch');  // 移除告警导航操作中的样式
	dlf.fn_closeDialog(); // 关闭所有dialog
	dlf.fn_initTrackDatepicker(); // 初始化时间控件
	$('#track').addClass('trackHover');
	$('#POISearchWrapper').hide();  // 关闭周边查询
	dlf.fn_clearInterval(currentLastInfo); // 清除lastinfo计时器
	dlf.fn_clearTrack('inittrack');	// 初始化清除数据
	$('#control_panel').hide();	
	$('#ceillid_flag').removeAttr('checked');
	obj_trackHeader.show();	// 轨迹查询条件显示
	dlf.fn_setMapPosition(false);
	$('#delayTable').css({'margin-top': 60});
	$('#exportDelay, #completeTrack').hide();
	dlf.resetPanelDisplay();
	// 调整工具条和
	//dlf.fn_setMapControl(35); /*调整相应的地图控件及服务对象*/
	
	var str_tempAlias = $('.j_currentCar').attr('alias'),
		str_currentCarAlias = dlf.fn_encode(str_tempAlias),
		obj_trackPos = $('.trackPos');
	
	if ( $('.j_currentCar').length == 0 ) {
		str_tempAlias = $('.j_terminal[tid='+ str_currentTid +']').attr('alias');
		str_currentCarAlias = dlf.fn_encode(str_tempAlias);
	}
	
	$('#trackTerminalAliasLabel').html(str_currentCarAlias).attr('title', str_tempAlias);
	if ( dlf.fn_userType() ) {
		//$('#trackTerminalAliasLabel').html(str_currentCarAlias).attr('title', str_tempAlias);
		//obj_trackPos.css('width', 490);
		//$('.j_delay').hide();
		//$('.j_delayTbody').html('');
	} else {
		//obj_trackPos.css('width', 475);
	}
	if ( $('#trackSearchPanel').is(':hidden') ) {
		$('#trackSearch_topShowIcon').click();
	}
	//题栏切换
	$('#trackSearch_topShowIcon').toggle(
		function () {
			var n_delayTableHeight = $(window).height() - 219,
				n_windowWidth = $(window).width(),
				n_trackTableMiniHeight = 398;
			
			if ( n_windowWidth < 1500 ) {
				n_trackTableMiniHeight = 440;
			}
			
			$('#trackSearchPanel').hide();
			$('#trackSearch_topShowIcon').css('top', '0').addClass('topShowIcon_hover');
			
			if ( $('#exportDelay').is(':visible') || $('#completeTrack').is(':visible') ) {
				//n_delayTableHeight -= 60;
			}
			$('#delayTable').css({'min-height': n_trackTableMiniHeight, 'height': n_delayTableHeight});
		},
		function () {
			var n_delayTableHeight = $(window).height() - 320,
				n_windowWidth = $(window).width(),
				n_trackTopIcon = 100,
				n_trackTableMiniHeight = 340;
			
			
			if ( n_windowWidth < 1500 ) {
				n_trackTopIcon = 170;
				n_trackTableMiniHeight = 270;
				n_delayTableHeight -= 82;
			}
			
			$('#trackSearchPanel').show();
			$('#trackSearch_topShowIcon').css('top', n_trackTopIcon).removeClass('topShowIcon_hover');		
			if ( $('#exportDelay').is(':visible') || $('#completeTrack').is(':visible') ) {
				//n_delayTableHeight -= 60;
			}
			$('#delayTable').css({'min-height': n_trackTableMiniHeight, 'height': n_delayTableHeight});
		}
	);
	if ( $('.j_delayPanel').is(':hidden') ) {
		$('.j_disPanelCon').click();
	}
	$('#delayTable').html('<li class="default_delayItem">请选择开始和结束时间进行查询</li>');
	$('.j_disPanelCon').css('top', $('.delayTable').height()/2+180);
}

dlf.fn_initPanel = function () {
	/**
	* 调整页面大小
	*/
	var n_windowWidth = $(window).width(),
		n_windowWidth = $.browser.version == '6.0' ? n_windowWidth <= 1024 ? 1024 : n_windowWidth : n_windowWidth,
		n_delayLeft = n_windowWidth - 550,
		n_delayIconLeft = n_delayLeft - 18,
		n_alarmLeft = n_windowWidth - 400,
		n_alarmIconLeft = n_alarmLeft - 18,
		obj_tree = $('#corpTree');
	
	if ( dlf.fn_userType() ) {	// 集团用户		
		if ( n_windowWidth < 1024 ) {
			n_delayLeft = 474;
			n_delayIconLeft = 458;
			n_alarmLeft = 625;
			n_alarmIconLeft = 763;
		}
	}
	// 设置停留点列表的位置
	
	//$('.j_delayPanel').css({'left': n_delayLeft});
	//$('.j_disPanelCon').css({'left': n_delayIconLeft}).addClass('disPanelConShow');
	/*$('.j_alarmPanel').css({'left': n_alarmLeft});
	$('.j_alarmPanelCon').css({'left': n_alarmIconLeft});*/
}

/**
* 关闭轨迹显示页面
* b_ifLastInfo: 清除规矩相关的时候是否要发起lastinfo
*/
dlf.fn_closeTrackWindow = function(b_ifLastInfo) {
	$('#mapObj').show();
	dlf.fn_clearNavStatus('track'); // 移除导航操作中的样式
	dlf.fn_clearMapComponent(); // 清除页面图形
	dlf.fn_clearTrack();	// 清除数据
	/**
	* 清除地图后要清除车辆列表的marker存储数据
	*/
	var obj_cars = $('.j_carList .j_terminal'),
		obj_selfMarker = null,
		obj_carInfo = null; 
		
	n_currentLastInfoNum = 0;
	if ( b_ifLastInfo ) {
		
		// obj_carsData = {};
		obj_selfmarkers = {};
		
		LASTINFOCACHE = 0; //轨迹查询后重新获取终端数据
		dlf.fn_clearOpenTrackData();	// 初始化开启追踪的数据
		$('.j_body').data('lastposition_time', -1);
		if ( !dlf.fn_userType() ) {
			// $('.j_carList').removeData('carsData');
			dlf.fn_getCarData();	// 重新请求lastinfo
		} else {
			dlf.fn_setMapPosition(false);
			arr_infoPoint = [];
			arr_tracePoints = [];
			obj_oldData = {'gids': '', 'tids': '', 'n_gLen': 0};
			
			//查找选中的终端,进行添加数据
			var obj_carDatas = $('.j_carList').data('carsData'),
				arr_lastLocations = [],
				b_bindRegionWpST = $('#bindRegionWrapper').is(':hidden'),
				b_bindBatchRegionWpST = $('#bindBatchRegionWrapper').is(':hidden');
			
			$('.j_group .jstree-checked').each(function() {
				var obj_this = $(this),
					obj_current = obj_this.children('.j_terminal'),
					str_tid = obj_current.attr('tid'),
					obj_tempCarData = obj_carDatas[str_tid];
				
				if ( obj_tempCarData ) {
					dlf.fn_updateInfoData(obj_carDatas[str_tid]);
					if ( obj_tempCarData.clongitude != 0 ) {
						arr_lastLocations.push(dlf.fn_createMapPoint(obj_tempCarData.clongitude, obj_tempCarData.clatitude));
					}
				}
			});
			if ( arr_lastLocations.length != 0 ) {
				//dlf.fn_setOptionsByType('viewport', arr_lastLocations);
				setTimeout (function () {
					mapObj.setCenter(arr_lastLocations[0]);
				}, 310);
			}
				
			//if ( b_bindBatchRegionWpST && b_bindRegionWpST ) {
			//	dlf.fn_corpLastinfoSwitch(true);
			//}
			dlf.fn_corpGetCarData(true);
		}
		dlf.fn_updateLastInfo();// 动态更新定位器相关数据
	}
	dlf.fn_closeJNotifyMsg('#jNotifyMessage'); // 关闭消息提示
	dlf.fn_setMapControl(10); /*调整相应的地图控件及服务对象*/
}

/**
* 轨迹查询操作
*/
function fn_trackQuery() {
	var obj_trackHeader = $('.j_delay'),
		arr_delayPoints = [],
		obj_delayCon = $('.j_delay'),
		str_tempBeginTime = $('#trackBeginTime').val(),
		str_tempEndTime = $('#trackEndTime').val(),
		str_excelName = '',
		str_beginTime = dlf.fn_changeDateStringToNum(str_tempBeginTime), 
		str_endTime = dlf.fn_changeDateStringToNum(str_tempEndTime),
		n_cellid_flag = $('#ceillid_flag').attr('checked') == 'checked' ? 1 : 0,
		obj_locusDate = {'start_time': str_beginTime, 
						'end_time': str_endTime,
						'cellid_flag': n_cellid_flag},
		str_tid = dlf.fn_getCurrentTid(),
		str_alias = $('.j_carList a[tid='+ str_tid +']').attr('alias'),
		b_userType = dlf.fn_userType(),	// 个人用户或者集团用户
		str_masspointUrl = '/masspoint/basic',
		n_masspointFlag = 3*24*60*60,
		b_masspointFlag = true;
	
	if ( str_beginTime >= str_endTime ) {
		dlf.fn_jNotifyMessage('开始时间不能大于结束时间，请重新选择时间段。', 'message', false, 3000);
		return;
	}
	
	if ( (str_endTime - str_beginTime) > n_masspointFlag ) {
		str_masspointUrl = '/masspoint/day';
		b_masspointFlag = false;
	}
	$('#completeTrack').data('change', false);
	dlf.fn_clearTrack();	// 清除数据
	dlf.fn_clearInterval(currentLastInfo); // 清除lastinfo定时器
	dlf.fn_clearMapComponent(); // 清除页面图形
	dlf.fn_jNotifyMessage('定位器轨迹查询中' + WAITIMG, 'message', true);
	dlf.fn_lockScreen('j_trackbody'); // 添加页面遮罩
	$('.j_trackbody').data('layer', true);
	dlf.fn_lockScreen();
	
	obj_trackHeader.removeData('delayPoints');	// 清除停留点缓存数据
	// 集团用户显示查询结果面板
	obj_locusDate.tid = str_tid;
	
	b_trackMsgStatus = true;
	actionMarker = null;
	if ( $('#exportDelay').is(':visible') ) {
		$('#delayTable').height($('#delayTable').height()+60);
	}
	$('#exportDelay, #completeTrack').hide();
	$('#control_panel').hide();
	$('.j_trackBtnhover').show();
	$('#tPause').hide();
	
	$.post_(str_masspointUrl, JSON.stringify(obj_locusDate), function (data) {
		if ( data.status == 0 ) {			
			$('#delayTable').css('margin-top', 60);
			fn_dealTrackDatas(b_masspointFlag, data, obj_locusDate);
			
			dlf.fn_closeJNotifyMsg('#jNotifyMessage'); // 关闭消息提示
		} else if ( data.status == 201 ) {	// 业务变更
			dlf.fn_showBusinessTip();
		}  else if ( data.status == 1401 ) {	// 对不起，8月1日之前的数据一次查询范围不能超过1周。
			$('#delayTable').html('<li class="default_delayItem3"></li><li class="default_delayItem2Text">对不起，8月1日之前的数据一次查询范围不能超过1周。</li>');	
			dlf.fn_jNotifyMessage(data.message, 'message');			
		} else { // 查询状态不正确,错误提示
			dlf.fn_jNotifyMessage(data.message, 'message');
		}
		dlf.fn_unLockScreen(); // 清除页面遮罩
		$('.j_trackbody').removeData('layer');
	}, 
	function (XMLHttpRequest, textStatus, errorThrown) {
		dlf.fn_serverError(XMLHttpRequest);
	});
}

/**
* 根据标记分别处理停留点或者按天显示
*/
function fn_dealTrackDatas (b_masspointFlag, data, obj_locusDate) {
	var str_tid = dlf.fn_getCurrentTid(),
		str_alias = $('.j_carList a[tid='+ str_tid +']').attr('alias');
	
	if ( b_masspointFlag ) { //按停留显示
		var n_flag = data.track_sample,
			arr_trackDatas = data.track,
			n_locLength = arr_trackDatas.length,
			arr_stopDatas = data.stop,
			n_stopLength = arr_stopDatas.length,
			obj_trackStData = data.start,
			obj_trackEndData = data.end,
			arr_calboxData = [],
			arr_trackQueryData = [],
			str_msg = '',
			obj_delayCon = $('.j_delay'),
			obj_trackHeader = $('.j_delay');	
			arr_delayPoints = [],
			str_excelName = '';
		
		if ( dlf.fn_isEmptyObj(obj_trackEndData) ) {
			arr_trackQueryData.push(obj_trackEndData);
		}
		
		if ( arr_stopDatas.length > 0 ) {
			arr_trackQueryData = arr_trackQueryData.concat(arr_stopDatas);
		}
		
		if ( dlf.fn_isEmptyObj(obj_trackStData) ) {
			arr_trackQueryData.push(obj_trackStData);
		}
			
		//判断标记
		if ( n_flag == 0 ) { //直接显示数据	
			if ( n_locLength <= 0) {
				if ( obj_locusDate.cellid_flag == 0 ) {	// 如果没有勾选基站定位
					str_msg = '该段时间无轨迹记录，请尝试选择“基站定位”。';
				} else {
					str_msg = '该段时间无轨迹记录，请选择其它时间段。';
				}
			}
		} else {
			if ( arr_trackQueryData.length <= 0) {
				if ( obj_locusDate.cellid_flag == 0 ) {	// 如果没有勾选基站定位
					str_msg = '该段时间无轨迹记录，请尝试选择“基站定位”。';
				} else {
					str_msg = '该段时间无轨迹记录，请选择其它时间段。';
				}
			}
		}
		
		if ( str_msg != '' ) {			
			$('#delayTable').css('margin-top', 60);
			$('#delayTable').html('<li class="default_delayItem2"></li><li class="default_delayItem2Text">'+str_msg+'</li>');
			dlf.fn_jNotifyMessage(str_msg, 'message', false, 3000);
			dlf.fn_unLockScreen();
			return;
		}
		
		$('#delayTable').html('');
		if ( arr_trackQueryData.length > 0 ) {
			obj_delayCon.show();
			$('.j_disPanelCon').addClass('disPanelConShow');
			$('.j_delayPanel').show();
			// 存储停留点信息
			obj_trackHeader.data('delayPoints', arr_trackQueryData);
			$('#delayTable').css('height', $(window).height()-296);				
			
			// to add for 2014-9-28 hs
			if ( $('#trackSearchPanel').is(':visible') ) {
				$('#trackSearch_topShowIcon').click();
			}
		} else {
			$('#exportDelay, #completeTrack').hide();
			$('#delayTable').html('');
		}
		dlf.resetPanelDisplay();
		if ( n_flag == 0 ) { //直接显示数据				
			for ( var x = 0; x < n_locLength; x++ ) {
				arr_trackDatas[x].alias = str_alias;
				arr_trackDatas[x].tid = str_tid;
				arr_calboxData.push(dlf.fn_createMapPoint(arr_trackDatas[x].clongitude, arr_trackDatas[x].clatitude));
			}
			
			$('#delayTable').height($('#delayTable').height()-60).css({'margin-top': 60});
			if ( arr_trackQueryData.length > 2 ) {
				fn_exportDelayPoints(arr_trackQueryData);
			}
			
			arr_dataArr = arr_trackDatas;
			
			$('.j_delay').data('points', arr_calboxData);
			dlf.fn_setOptionsByType('viewport', arr_calboxData);
			
			fn_startDrawLineStatic(arr_trackDatas, true);
		} else { //以停留形式显示数据
			$('.j_delay').data('delayPoints', arr_trackQueryData);
			fn_startDrawLineStatic([], false);
			$('#trackMileagePanel0').click();
		}			
	} else { //按天显示
		var arr_trackDatas = data.res,
			arr_trackQueryData = data.stop,
			n_currentWeekNum = dlf.fn_calDateWeekNum(new Date()),
			str_html = '',
			arr_noAddressPoint = [],
			str_msg = '';
		
		if ( arr_trackDatas.length <= 0) {
			if ( obj_locusDate.cellid_flag == 0 ) {	// 如果没有勾选基站定位
				str_msg = '该段时间无轨迹记录，请尝试选择“基站定位”。';
			} else {
				str_msg = '该段时间无轨迹记录，请选择其它时间段。';
			}
		}
		
		if ( str_msg != '' ) {
			$('#delayTable').html('<li class="default_delayItem2"></li><li class="default_delayItem2Text">'+str_msg+'</li>');
			dlf.fn_jNotifyMessage(str_msg, 'message', false, 3000);
			dlf.fn_unLockScreen();
			return;
		}
		dlf.resetPanelDisplay();
		$('#delayTable').html('');
		if ( arr_trackDatas.length <= 0 ) {
			$('#exportDelay, #completeTrack').hide();
			$('#delayTable').html('');			
		} else {
			$('#delayTable').css('height', $(window).height()-295);	
			$('.j_delay').data('delayPoints', arr_trackQueryData);
			
			for ( var i = 0; i < arr_trackDatas.length; i++ ) {
				var obj_tempTrackData = arr_trackDatas[i],
					n_lcoateTime = obj_tempTrackData.timestamp,
					n_distance = obj_tempTrackData.distance,
					n_clat = obj_tempTrackData.clatitude,
					n_clon = obj_tempTrackData.clongitude,
					n_lat = obj_tempTrackData.latitude,
					n_lon = obj_tempTrackData.longitude,
					str_ymd = dlf.fn_changeNumToDateString(n_lcoateTime*1000, 'ymd'),
					str_md = dlf.fn_changeNumToDateString(n_lcoateTime, 'md'),
					str_fullYear = new Date(n_lcoateTime*1000).getFullYear(),
					str_trackAddress = obj_tempTrackData.name,
					str_yearLabel = str_fullYear,
					str_dateLabel = str_md,
					n_tempWeekNum = dlf.fn_calDateWeekNum(new Date(str_ymd)),
					trackLsItemSt = '';
				
				if ( n_tempWeekNum == n_currentWeekNum ) {
					str_yearLabel = str_ymd;
					str_dateLabel = dlf.fn_changeTimestampToWeek(n_lcoateTime);
				}
				
				if ( str_trackAddress == '' ) {
					str_trackAddress = '暂无位置信息';
					if ( n_lat != 0 ) {
						arr_noAddressPoint.push({'pd': obj_tempTrackData, 'index':i});
					} else {
						str_trackAddress = '无位置信息';
					}
				}
				if ( i == 0 ) {
					trackLsItemSt = 'trackLsItemSt';
				}
				
				str_html += '<li id="trackLsDayItem'+i+'" class="trackLsItem trackLsItemForDay '+trackLsItemSt+'">';
				str_html += '<div class="trackLsDate trackLsDateForDay">';
				str_html += '<div>'+str_dateLabel+'</div><div class="dayFontStyle">'+str_yearLabel+'</div></div>';
				str_html += '<div class="trackLsIcon"></div>';
				str_html += '<div class="trackLsContent">';
				str_html += '<div id="trackLsAddressPanel'+i+'" class="trackLsAddress">'+str_trackAddress+'</div>';
				if ( n_lat == 0 ) {					
					str_html += '<div id="trackMileagePanelDisabled'+i+'" class="trackLsMileage trackLsMileage_disabled j_trackMileagePanel">';
					str_html += '<span class="trackLsDgIconFd trackLsDgIcon_disabled j_trackLsDgIconFd"></span>';
				} else {
					str_html += '<div id="trackMileagePanel'+i+'" class="trackLsMileage j_trackMileagePanel">';
					str_html += '<span class="trackLsDgIconFd j_trackLsDgIconFd"></span>';
				}
				if ( n_lat == 0 ) {
					str_html += '<span class="textZooIn">今天没有活动轨迹哦。</span>';
				} else {
					str_html += '活动路线：<span class="textZooIn">';
					
					if ( n_distance < 1000 ) {
						str_html +=dlf.fn_NumForRound(n_distance, 0)+'</span>（米）';
					} else {
						str_html +=dlf.fn_NumForRound(n_distance/1000, 1)+'</span>（公里）';
					}
				}
				str_html += '</div></div>';
			}
			$('#delayTable').html(str_html);
			
			$('#trackSearch_topShowIcon').click();
			if ( arr_trackQueryData.length > 0 ) {
				$('#delayTable').css('height', $('#delayTable').height()+60);	
				fn_exportDelayPoints(arr_trackQueryData);
			}
			
			//是否对无地址的进行地址解析操作
			if ( arr_noAddressPoint.length > 0 ) {
				for ( var paramA in arr_noAddressPoint ) {
					var obj_tempParamData = arr_noAddressPoint[paramA],
						n_tempIndex = obj_tempParamData.index,
						obj_pData = obj_tempParamData.pd;
					
					dlf.fn_getAddressByLngLat(obj_pData.clongitude/NUMLNGLAT, obj_pData.clatitude/NUMLNGLAT, dlf.fn_getCurrentTid(), 'stop', n_tempIndex);
				}
			}
			
			$('.j_body').data({'track_daydata': arr_trackDatas, 'track_daysearch': obj_locusDate });
			$('.j_delay').data('delayPoints', arr_trackDatas);
			//添加 mouseover, mouseout,click事件
			$('.j_trackMileagePanel').unbind('mouseover mouseout click').mouseover(function(e){
				$(this).addClass('trackLsMileage_hover');
				$($(this).children('.trackLsDgIconFd')).addClass('trackLsDgIcon_hoverFd');
			}).mouseout(function(e) {
				$(this).removeClass('trackLsMileage_hover');
				$($(this).children('.trackLsDgIconFd')).removeClass('trackLsDgIcon_hoverFd');
			}).click(function(e){
				var str_itemTitleId = $(this).attr('id'),
					str_itemTitleNum = str_itemTitleId.substr(17);
				
				if ( str_itemTitleNum.search('Disabled') != -1 ) {
					return;
				}
				
				$('.j_trackMileagePanel').removeClass('trackLsMileage_click trackLsMileage_clickIcon');
				$(this).addClass('trackLsMileage_click trackLsMileage_clickIcon');
				
				$('.j_trackLsDgIconFd').removeClass('trackLsDgIcon_clickFd');
				$($(this).children('.trackLsDgIconFd')).addClass('trackLsDgIcon_clickFd');
				
				$('#control_panel').hide();
				$('.j_trackBtnhover').show();
				$('#tPause').hide();
				dlf.fn_clearMapComponent(); // 清除页面图形
				actionMarker = null;
				arr_drawLine = [];
				arr_dataArr = [];
				counter = -1;
				str_actionState = 0;
				fn_getTrackDatas(parseInt(str_itemTitleNum), 'trackDelayDay');
			});
			$('#trackMileagePanel0').click();
		}
	}
}

/**
* 导出停留点
*/
function fn_exportDelayPoints(arr_trackQueryData) {	
	var obj_currentDate = new Date(),
		str_tempYear = obj_currentDate.getFullYear(),
		str_tempMonth = obj_currentDate.getMonth() + 1,
		str_tempDay = obj_currentDate.getDate();
	
	str_tempMonth = str_tempMonth < 10 ? '0' + str_tempMonth : str_tempMonth;
	str_tempDay = str_tempDay < 10 ? '0' + str_tempDay : str_tempDay;
	
	str_excelName = '停留点列表-' + ( str_tempYear + '' + str_tempMonth + '' + str_tempDay);
	$('#delayTable').css({'margin-top': 0});
	$('#exportDelay').show().attr('download', str_excelName).click(function() {
		var obj_table = $('#tempDelayTable'),
			str_tableHtml = '',
			b_isNullName = false,
			arr_delayPoints = $('.j_delay').data('delayPoints'),
			str_html ='<tr><td>事件</td><td>时间（开始）</td><td>位置</td></tr>';
		
		for ( var i = 1; i < arr_delayPoints.length-1; i++ ) {
			var obj_tempTrackData = arr_delayPoints[i];
			
			str_html +='<tr><td>停留'+ dlf.fn_changeTimestampToString(obj_tempTrackData.end_time-obj_tempTrackData.start_time) +'</label></td><td>'+ dlf.fn_changeNumToDateString(obj_tempTrackData.start_time) +'</td><td>'+ obj_tempTrackData.name +'</td></tr>';
		}
		obj_table.html(str_html);
		if ( b_isNullName ) {
			dlf.fn_jNotifyMessage('正在获取数据，请稍等。', 'message', false, 3000);
			return;
		} else {
			fn_exportExcel(str_excelName);
		}
	});
	
}

/**
* 根据经纬度求两点间距离
*/
dlf.fn_forMarkerDistance = function (point1, point2) {
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

/**
 * 将度转化为弧度
 * @param {degree} Number 度     
 * @returns {Number} 弧度
 */
dlf.degreeToRad =  function(degree){
	return Math.PI * degree/180;    
}
/**
 * 将弧度转化为度
 * @param {radian} Number 弧度     
 * @returns {Number} 度
 */
dlf.radToDegree = function(rad){
	return (180 * rad) / Math.PI;       
}
/**
 * 将v值限定在a,b之间，纬度使用
 */
function fn_getRange(v, a, b){
	if(a != null){
	  v = Math.max(v, a);
	}
	if(b != null){
	  v = Math.min(v, b);
	}
	return v;
}

/**
 * 将v值限定在a,b之间，经度使用
 */
function fn_getLoop(v, a, b){
	while( v > b){
	  v -= b - a
	}
	while(v < a){
	  v += b - a
	}
	return v;
}

/**
* 显示停留点数据信息
*/
function fn_printDelayDatas(arr_delayPoints, str_operation) {
	var n_delayLength = arr_delayPoints.length,
		obj_table = $('.delayTable'),
		arr_markers = [];
		str_html = ''
		arr_noAddressPoint = [],
		arr_cacheDelayPoints = [];
	
	obj_table.data('operation', str_operation);
	
	for ( var i = 0; i < arr_delayPoints.length; i++ ) {
		var obj_tempTrackData = arr_delayPoints[i],
			n_lcoateTime = obj_tempTrackData.start_time,
			n_distance = obj_tempTrackData.distance,
			n_clat = obj_tempTrackData.latitude,
			n_clon = obj_tempTrackData.longitude,
			str_ymd = dlf.fn_changeNumToDateString(n_lcoateTime*1000, 'ymd').substr(2),
			str_sf = dlf.fn_changeNumToDateString(n_lcoateTime*1000, 'sfm'),
			str_trackAddress = obj_tempTrackData.name,
			str_lsIconClass = '',
			str_fClass = '';
		
		arr_cacheDelayPoints.push(obj_tempTrackData);
		if ( str_trackAddress == '' ) {
			arr_noAddressPoint.push({'pd': obj_tempTrackData, 'index':i});
		}
		
		if ( arr_delayPoints.length == (i +1) ) {
			str_lsIconClass = 'trackLsIcon_start';
			str_trackAddress += '（起点）';
			str_fClass =  'trackLsItemEnd';
		} else if ( i == 0 ) {
			str_lsIconClass = 'trackLsIcon_end';
			str_trackAddress += '（终点）';
			str_fClass = 'trackLsItemSt';
		} else {
			str_trackAddress ='（停留'+ dlf.fn_changeTimestampToString(obj_tempTrackData.idle_time)+'）'+str_trackAddress;
		}		
		
		str_html += '<li id="trackLsItem'+i+'" class="trackLsItem '+str_fClass+'">';
		str_html += '<div class="trackLsDate">';
		str_html += '<div>'+str_ymd+'</div><div>'+str_sf+'</div></div>';
		str_html += '<div class="trackLsIcon '+str_lsIconClass+'"></div>';
		str_html += '<div class="trackLsContent">';
		str_html += '<div id="trackLsAddressPanel'+i+'" class="trackLsAddress">'+str_trackAddress+'</div>';
		if ( arr_delayPoints.length != (i +1) ) {
			str_html += '<div id="trackMileagePanel'+i+'" class="trackLsMileage j_trackMileagePanel">';
			str_html += '<span class="trackLsDgIcon j_trackLsDgIcon"></span>';
			str_html += '活动路线：<span class="textZooIn">';
			
			if ( n_distance < 1000 ) {
				str_html +=dlf.fn_NumForRound(n_distance, 0)+'</span>（米）';
			} else {
				str_html +=dlf.fn_NumForRound(n_distance/1000, 1)+'</span>（公里）';
			}
		}
		str_html += '</div></div>';
		if ( str_operation == 'delay' ) { //显示停留点
			obj_tempMarker = dlf.fn_addMarker(obj_tempTrackData, 'delay', 0, i);
			arr_markers.push(obj_tempMarker);
		}		
	}
	$('.j_delay').data('delayPoints', arr_cacheDelayPoints);
	$('#delayTable').html(str_html);
	$('.delayTable').data('markers', arr_markers);
	if ( arr_delayPoints.length == 1 ) {
		$('#delayTable li').css('background-image', 'none');
	}
	
	//是否对无地址的进行地址解析操作
	if ( arr_noAddressPoint.length > 0 ) {
		for ( var paramA in arr_noAddressPoint ) {
			var obj_tempParamData = arr_noAddressPoint[paramA],
				n_tempIndex = obj_tempParamData.index,
				obj_pData = obj_tempParamData.pd;
			
			dlf.fn_getAddressByLngLat(obj_pData.clongitude/NUMLNGLAT, obj_pData.clatitude/NUMLNGLAT, dlf.fn_getCurrentTid(), 'stop', n_tempIndex);
		}
	}
	
	//添加 mouseover, mouseout,click事件
	$('.j_trackMileagePanel').unbind('mouseover mouseout click').mouseover(function(e){
		$(this).addClass('trackLsMileage_hover');
		$($(this).children('.trackLsDgIcon')).addClass('trackLsDgIcon_hover');
	}).mouseout(function(e) {
		$(this).removeClass('trackLsMileage_hover');
		$($(this).children('.trackLsDgIcon')).removeClass('trackLsDgIcon_hover');
	}).click(function(e){
		$('.j_trackMileagePanel').removeClass('trackLsMileage_click trackLsMileage_clickIcon');	
		$(this).addClass('trackLsMileage_click trackLsMileage_clickIcon');
			
		$('.j_trackLsDgIcon').removeClass('trackLsDgIcon_click');
		$($(this).children('.trackLsDgIcon')).addClass('trackLsDgIcon_click');
		
		//请求数据 or 显示停留点
		var str_tempClickOperation = $('.delayTable').data('operation'),
			str_itemTitleId = $(this).attr('id'),
			n_itemTitleNum = parseInt(str_itemTitleId.substr(17));
		
		if ( str_tempClickOperation == 'delay' ) { //显示停留点
			//fn_getTrackDatas(n_itemTitleNum, 'delay');
			
			if ( $('#delayTable').css('margin-top') == '60px' ) {
				$('#delayTable').css('margin-top', 0);
			}
			$('#completeTrack').show().unbind('click').click(function(e) {
				if ( $('#completeTrack').data('change') ){
					dlf.fn_jNotifyMessage('查询时间条件已改变，请重新查询。', 'message');						
				} else {
					fn_trackQuery();
				}
			});
		}
		//请求路线数据并显示
		$('#control_panel').hide();
		$('.j_trackBtnhover').show();
		$('#tPause').hide();
		dlf.fn_clearMapComponent(); // 清除页面图形
		actionMarker = null;
		arr_drawLine = [];
		arr_dataArr = [];
		counter = -1;
		str_actionState = 0;
		fn_getTrackDatas(n_itemTitleNum);
	});
}

function fn_getTrackDatas(n_stopNum, str_operator) {
	var arr_trackQueryData = $('.j_delay').data('delayPoints'),
		str_cTid = dlf.fn_getCurrentTid(),
		n_endTime = 0,
		n_startTime = 0,
		obj_trackQuery = '',
		n_lon = arr_trackQueryData[n_stopNum].longitude;
	
	if ( n_lon == 0 ) {
		return;
	}
	
	//if ( (n_stopNum+1) >= arr_trackQueryData.length ) {
	//	return;
	//}	
	if ( str_operator == 'trackDelayDay' ) {
		var arr_trackDatas = $('.j_body').data('track_daydata'),
			obj_locusDate = $('.j_body').data('track_daysearch'),
			n_stDateYmd = dlf.fn_changeNumToDateString(obj_locusDate.start_time*1000, 'ymd'),
			n_endDateYmd = dlf.fn_changeNumToDateString(obj_locusDate.end_time*1000, 'ymd'),
			n_dayTimestamp = arr_trackDatas[n_stopNum].timestamp,
			str_dayYmd = dlf.fn_changeNumToDateString(n_dayTimestamp*1000, 'ymd');
		
		if ( n_stDateYmd ==  str_dayYmd ) { //和开始时间所在同一天
			n_startTime = obj_locusDate.start_time;
			n_endTime = new Date(str_dayYmd+' 23:59:59').getTime()/1000;
		} else if ( n_endDateYmd ==  str_dayYmd ) { //和结束时间所在同一天
			n_startTime = new Date(str_dayYmd+' 0:0:0').getTime()/1000;
			n_endTime = obj_locusDate.end_time;
		} else {
			n_startTime = new Date(str_dayYmd+' 0:0:0').getTime()/1000;
			n_endTime = new Date(str_dayYmd+' 23:59:59').getTime()/1000;
		}
		
	} else {
		n_startTime = arr_trackQueryData[n_stopNum+1].start_time;
		n_endTime = arr_trackQueryData[(n_stopNum)].start_time;
	}
	
	obj_trackQuery = {'tid': str_cTid, 'start_time': n_startTime, 'end_time': n_endTime};
	$.ajax({
		type : 'post',
		url : '/masspoint/basic',
		data: JSON.stringify(obj_trackQuery),
		dataType : 'json',
		cache: false,
		contentType : 'application/json; charset=utf-8',
		success : function(data) {
			if ( data.status == 0) {
				var arr_trackQueryLineData = data.track,
					arr_trackLine = [],
					n_trackItemIndex = 0,
					obj_trackEndData = '',
					str_tid = dlf.fn_getCurrentTid(),
					str_alias = $('.j_carList a[tid='+ str_tid +']').attr('alias');
				
				if ( arr_trackQueryLineData.length > 0 ) {
					for ( var i = 0; i < arr_trackQueryLineData.length; i++) {
						var obj_tempTrackData = arr_trackQueryLineData[i], 
							n_clon = obj_tempTrackData.clongitude, 
							n_clat = obj_tempTrackData.clatitude,
							obj_tempTrackPoint = null;
						
						arr_trackQueryLineData[i].alias = str_alias;
						arr_trackQueryLineData[i].tid = str_tid;
						if ( obj_tempTrackData.longitude != 0 ) {
							obj_tempTrackPoint = dlf.fn_createMapPoint(n_clon, n_clat);
							
							// 保存轨迹线数据
							arr_trackLine.push(obj_tempTrackPoint);
						}
					}
					if ( str_operator == 'delay' ) {
						dlf.fn_createPolyline(arr_trackLine, {color: '#ff0000'});	
					} else {						
						dlf.fn_addMarker(arr_trackQueryLineData[0], 'start', 0, 0); // 添加标记
						dlf.fn_addMarker(arr_trackQueryLineData[arr_trackQueryLineData.length - 1], 'end', 0, 1); //添加标记
					
						dlf.fn_createPolyline(arr_trackLine, {color: '#150CFF'});
						
						arr_dataArr = arr_trackQueryLineData;
						
						//设置比例尺
						mapObj.setViewport(arr_trackLine);
						arr_drawLine.push(dlf.fn_createMapPoint(arr_trackQueryLineData[0].clongitude, arr_trackQueryLineData[0].clatitude));

						fn_createDrawLine();
						$('#control_panel').show();
					}				
				}
				if ( str_operator == 'trackDelayDay' ) { // 按天查显示停留点
					var arr_trackQueryData = data.stop,
						arr_tempDelay = [],
						arr_delayFdMarkers = [];
					
					if ( arr_trackQueryData.length > 0 ) { // 如果有停留点,进行显示
						for ( var x = 0; x < arr_trackQueryData.length; x++ ) {
							var obj_currentCar = $('.j_currentCar'),
								obj_tempDelayFdMarker = null;
							
							if ( $('.j_currentCar').length == 0 ) {
								obj_currentCar = $('.j_terminal[tid='+ str_currentTid +']');
							}
							arr_trackQueryData[x].alias = obj_currentCar.attr('alias');
							arr_tempDelay.push(arr_trackQueryData[x]);
							obj_tempDelayFdMarker = dlf.fn_addMarker(arr_trackQueryData[x], 'delayFd', 0, x);
							arr_delayFdMarkers.push(obj_tempDelayFdMarker);
						}
						$('.j_body').data({'delayfd': arr_tempDelay, 'fdmarkers': arr_delayFdMarkers});
					}
				}
			} else if ( data.status == 403 || data.status == 24 ) {
				window.location.replace('/');
			} else {
				dlf.fn_jNotifyMessage(data.message, 'message', false, 3000);
			}
		},
		error : function(XMLHttpRequest) {
			dlf.fn_serverError(XMLHttpRequest);
			return;
		}
	});
}

/**
* 添加轨迹线和轨迹点
*/
function fn_startDrawLineStatic(arr_dataArr, flag) {
	var arr = new Array(), //经纬度坐标数组 
		obj_firstMarker = {},
		obj_endMarker = {},
		arr_markers = [];
	
	if ( flag ) { //直接显示轨迹线及停留点
		var polyline = dlf.fn_createPolyline($('.j_delay').data('points'), {color: '#150CFF'});	//通过经纬度坐标数组及参数选项构建多折线对象，arr是经纬度存档数组 
		
		obj_firstMarker = dlf.fn_addMarker(arr_dataArr[0], 'start', 0, 0); // 添加标记
		obj_endMarker = dlf.fn_addMarker(arr_dataArr[arr_dataArr.length - 1], 'end', 0, 1); //添加标记
		//存储起终端点以便没有位置时进行位置填充
		$('.delayTable').data('markers', arr_markers);
		
		// 添加停留点marker
		var arr_delayPoints = $('.j_delay').data('delayPoints'),
			arr_tempDelay = [];
		
		if ( arr_delayPoints ) { // 如果有停留点,进行显示
			for ( var x = 0; x < arr_delayPoints.length; x++ ) {
				var obj_currentCar = $('.j_currentCar');
				
				if ( $('.j_currentCar').length == 0 ) {
					obj_currentCar = $('.j_terminal[tid='+ str_currentTid +']');
				}
				arr_delayPoints[x].alias = obj_currentCar.attr('alias');
				arr_tempDelay.push(arr_delayPoints[x]);
			}
			fn_printDelayDatas(arr_tempDelay, 'delay');	// 显示停留数据
		}
		$('#control_panel').show();
		arr_drawLine.push(dlf.fn_createMapPoint(arr_dataArr[0].clongitude, arr_dataArr[0].clatitude));

		fn_createDrawLine();
	} else { // 只显示停留点
		var arr_delayPoints = $('.j_delay').data('delayPoints');
		
		fn_printDelayDatas(arr_delayPoints, 'stop');	// 显示停留数据
	}
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
	if ( timerId ) { dlf.fn_clearInterval(timerId) };
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
		str_tid = $('.j_currentCar').attr('tid'),
		obj_selfInfoWindow = null;
	
	if ( $('.j_currentCar').length == 0 ) {
		str_tid = str_currentTid;
	}
	
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
			dlf.fn_clearMapComponent(actionMarker);
		}
		arr_dataArr[counter].tid = str_tid;	// 轨迹播放传递tid
		dlf.fn_addMarker(arr_dataArr[counter], 'draw', 0, counter); // 添加标记
		// 将播放过的点放到数组中
		var obj_tempPoint = dlf.fn_createMapPoint(arr_dataArr[counter].clongitude, arr_dataArr[counter].clatitude);
		
		arr_drawLine.push(obj_tempPoint);
		if ( !obj_drawLine ) {
			fn_createDrawLine();
		} else {
			obj_drawLine.setPath(arr_drawLine);
		}
			
		if ( obj_selfInfoWindow ) {
			dlf.fn_createMapInfoWindow(arr_dataArr[counter], 'draw', counter);
			actionMarker.openInfoWindow(obj_mapInfoWindow); // 显示吹出框 
		}
		dlf.fn_boundContainsPoint(obj_tempPoint);
	} else {	// 播放完成后
		dlf.fn_jNotifyMessage('轨迹播放完毕。', 'message', false, 3000);
		b_trackMsgStatus = true;
		dlf.fn_clearTrack();	// 清除数据
		dlf.fn_clearMapComponent(actionMarker);
		dlf.fn_clearMapComponent(obj_drawLine);
		obj_drawLine = null;
		actionMarker = null;
		$('#tPause').hide();
		$('#tPlay').css('display', 'inline-block');
	}
}

/**
* 初始化播放过的线对象
*/
function fn_createDrawLine () {
	obj_drawLine = dlf.fn_createPolyline(arr_drawLine, {'color': 'red'});
}

/**
* 关闭轨迹清除数据
*/
dlf.fn_clearTrack = function(clearType) { 
	if ( timerId ) { dlf.fn_clearInterval(timerId) };	// 清除计时器
	str_actionState = 0;
	counter = -1;
	arr_drawLine = [];
	if ( clearType == 'inittrack' ) {
		dlf.fn_clearMapComponent(); // 清除页面图形
	}
}

/**
* 初始化时间控件
*/
dlf.fn_initTrackDatepicker = function() {	
	/**
	* 初始化轨迹查询选择时间
	*/
	var str_nowDate = dlf.fn_changeNumToDateString(new Date().getTime(), 'ymd'), 
		obj_stTime = $('#trackBeginTime'), 
		obj_endTime = $('#trackEndTime'),
		str_tempBeginTime = str_nowDate+' 00:00:00';
		
	obj_stTime.click(function() {	// 初始化起始时间，并做事件关联   maxDate: '#F{$dp.$D(\'trackEndTime\')}',   minDate:'#F{$dp.$D(\'trackBeginTime\')}', // delete in 2013.04.10
		WdatePicker({el: 'trackBeginTime', dateFmt: 'yyyy-MM-dd HH:mm:ss', readOnly: true, isShowClear: false, qsEnabled: false, autoPickDate: false, onpicked: function() {
				$('#completeTrack').data('change', true);
		}});
	}).val(str_tempBeginTime);
	
	obj_endTime.click(function() {	// 初始化结束时间，并做事件关联
		WdatePicker({el: 'trackEndTime', dateFmt: 'yyyy-MM-dd HH:mm:ss', readOnly: true, isShowClear: false, qsEnabled: false, autoPickDate: false, onpicked: function() {
			$('#completeTrack').data('change', true);
		}});
	}).val(dlf.fn_changeNumToDateString(new Date()/1000));
}

/**
* 页面加载完成后进行加载地图
*/
$(function () {	
	dlf.fn_initTrackDatepicker();	// 初始化时间控件
	$('.j_disPanelCon').bind('click', function() {
		var obj_panel = $('.j_delayPanel'),
			obj_arrowCon = $('.j_disPanelCon'),
			obj_arrowIcon = $('.j_arrowClick'),
			b_panel = obj_panel.is(':visible'),
			n_windowWidth = $(window).width(),
			n_delayIconLeft = n_windowWidth - 568,
			n_delayIconRight = 0,
			n_delayTablewidth = $('.j_delayPanel').width(),
			n_chromeIndex = navigator.userAgent.search('Chrome');
		
		
		if ( n_windowWidth < 1024 ) {
			n_windowWidth = 1024;
			n_delayIconLeft = 458;
		}
		if ( b_panel ) {
			obj_panel.hide();
			n_delayIconLeft = n_windowWidth - 17;
			obj_arrowCon.removeClass('disPanelConShow');
		} else {
			obj_arrowCon.addClass('disPanelConShow');
			obj_panel.show();
		}
		
		if ( n_chromeIndex != -1 ) {
			var n_chromeVersion = parseFloat(navigator.userAgent.substring(n_chromeIndex+7));
			
			if ( n_chromeVersion < 35 ) {
				if ( (document.documentElement.clientHeight < document.documentElement.scrollHeight) && (document.documentElement.clientWidth < document.documentElement.scrollWidth)) {
					n_delayIconRight += 17;
				}
			}
		}
		if ( $(window).width() < 1024 ) {
			var n_trackPostNum = 1024-$(window).width();
			
			if ( !b_panel ) {
				$('.j_disPanelCon').css('right', n_delayTablewidth-n_trackPostNum);
				$('.j_delayPanel').css('right', -n_trackPostNum);
			} else {
				$('.j_disPanelCon').css('right', -n_trackPostNum);
			}
		} else {
			if ( !b_panel ) {
				$('.j_disPanelCon').css('right', n_delayTablewidth-n_delayIconRight);
				$('.j_delayPanel').css('right', -n_delayIconRight);
			} else {
				$('.j_disPanelCon').css('right', -n_delayIconRight);
				$('.j_delayPanel').css('right', n_delayTablewidth-n_delayIconRight);
			}
			
		}
	});
	/**
	* 按钮变色
	*/
	$('.j_trackBtnhover, #trackSearch, #trackClose').mouseover(function(event) {
		/*var str_id = event.currentTarget.id, 
			str_imgUrl = '';
		if ( str_id == 'trackSearch' ) {
			str_imgUrl = 'trackcx2.png';
		} else if ( str_id == 'tPlay' ) {
			str_imgUrl = 'bf2.png';
		} else if ( str_id == 'tPause' ) {
			str_imgUrl = 'zt2.png';
		} else if ( str_id == 'tStop' ) {
			str_imgUrl = 'tz2.png';
		} else {
			str_imgUrl = 'close_default.png';
		}
		$(this).css('background-image', 'url("'+ BASEIMGURL + str_imgUrl+'")');*/
	}).mouseout(function(event){
		/*var str_id = event.currentTarget.id, 
			str_imgUrl = '';
		if ( str_id == 'trackSearch' ) {
			str_imgUrl = 'trackcx1.png';
		} else if ( str_id == 'tPlay' ) {
			str_imgUrl = 'bf1.png';
		} else if ( str_id == 'tPause' ) {
			str_imgUrl = 'zt1.png';
		} else if ( str_id == 'tStop' ) {
			str_imgUrl = 'tz1.png';
		} else {
			str_imgUrl = 'close_default.png';
		}
		$(this).css('background-image', 'url("'+ BASEIMGURL + str_imgUrl+'")');*/
	}).click(function(event) {
		var str_id = event.currentTarget.id, 
			str_imgUrl = '';
		if ( str_id == 'trackSearch' ) { // 轨迹查询
			fn_trackQuery();
		} else if ( str_id == 'tPlay' ) { // 播放
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
		} else {
			dlf.fn_closeTrackWindow(true);
			dlf.fn_setMapPosition(false);
		}
	});
	
	/**
	* 初始化速度滑块
	*/
	var arr_slide = [1000, 500, 200, 100], 
		arr_slideTitle = ['慢速', '一般速度', '比较快', '极速'];
	
	$('#trackSlide').slider({
		min: 0,
		max: 3,
		values: 2,
		range: 'min',
		animate: true,
		slide: function (event, ui) {
			var n_val = ui.value;
			n_speed = arr_slide[n_val];
			$('#trackSlide').attr('title', arr_slideTitle[n_val]);
			if ( timerId ) { dlf.fn_clearInterval(timerId) };
			var obj_tplay = $('#tPlay'),
				str_ishidden = obj_tplay.is(':hidden');
			if ( str_ishidden ) {	// 如果播放按钮不可用
				fn_markerAction();
			}
		}
	}).slider('option', 'value', 2);
})