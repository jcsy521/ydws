/*
*实时定位相关操作方法
* 设防撤防操作
*/
var n_cellstatus;
(function () {
window.dlf.fn_currentQuery = function() {
	$('#currentWrapper').show();
	var obj_pd = {'locate_flag': GPS_TYPE};	// 第一次post发起gps定位
	fn_currentRequest(obj_pd);
	$('#currentBtn').unbind('click').click(function() {
		dlf.fn_closeDialog(); // 窗口关闭
	});
}
// 是否发起基站定位
function fn_startCell(n_locateFlag) {
	var obj_msg = $('#currentMsg'),
		str_img = '<img src="/static/images/blue-wait.gif" class="waitingImg" />',
		str_errorMsg = '无法获取车辆位置，请稍候重试！';
	// 发起基站定位
	if ( n_locateFlag == GPS_TYPE ) {
		if ( n_cellstatus == 1 ) {
			// GPS定位失败, 3S发起基站
			obj_msg.html('GPS信号弱，切换到基站定位 '+str_img);
			setTimeout(function () {
				var obj_pd = {'locate_flag': CELLID_TYPE };
				fn_currentRequest(obj_pd);
			}, 3000);
		} else {
			obj_msg.html(str_errorMsg);
		}										
	} else { // 基站失败 重新开启lastinfo
		fn_openLastinfo(str_errorMsg);
	}
}
// 重新开启lastinfo
function fn_openLastinfo(str_msg, f_clearInterval) {
	var obj_msg = $('#currentMsg');
	if ( f_clearInterval ) {
		clearInterval(CURRENT_TIMMER);
	}
	obj_msg.html(str_msg);
	// 动态更新终端相关数据
	dlf.fn_updateLastInfo();
}
function fn_currentRequest(obj_pd) {
	var obj_cWrapper = $('#currentWrapper'),
		obj_msg = $('#currentMsg'), 
		str_errorMsg = '无法获取车辆位置，请稍候重试！',
		str_flagVal = obj_pd.locate_flag, 
		str_carCurrent = $('.currentCar').siblings('.j_currentCar').html(), // 当前车辆
		str_img = '<img src="/static/images/blue-wait.gif" class="waitingImg" />',
		str_msg = '车辆<b> '+ str_carCurrent +' </b>'
		f_warpperStatus = !obj_cWrapper.is(':hidden');
	// 判断弹出框是否已经关闭，如果关闭:不进行任何操作
	if ( f_warpperStatus ) {
		if ( str_flagVal == CELLID_TYPE) {
			str_msg = str_msg + '基站定位进行中 ' + str_img;
		} else {
			str_msg = str_msg + 'GPS定位进行中 ' + str_img;
		}
		obj_msg.html(str_msg);
		dlf.fn_lockScreen(); // 添加页面遮罩
		dlf.fn_clearInterval(currentLastInfo);  // lastinfo停止计时
		$.post_(REALTIME_URL, JSON.stringify(obj_pd), function (postData) {
			var p_warpperStatus = !obj_cWrapper.is(':hidden');
			// 判断弹出框是否已经关闭，如果关闭:不进行任何操作
			if ( p_warpperStatus ) { 
				n_cellstatus = postData.cellid_status;	// 是否开启基站定位
				var n_status = postData.status;
				if ( n_status == 0  ) {
					if ( postData.location ) {
						fn_displayCurrentMarker(postData.location);
					} else {
							// 每10秒发起一次get请求, 共发6次，如果查到结果则清除计时器
							var n_count = 0, c_countNum = CHECK_PERIOD / CHECK_INTERVAL;
							
							CURRENT_TIMMER = setInterval(function () { // 每10秒钟启动
								if ( n_count++ >= c_countNum ) {
									clearInterval(CURRENT_TIMMER);
									obj_msg.html(str_errorMsg);
									return;
								}
								var t_warpperStatus = !obj_cWrapper.is(':hidden');
								
								if ( t_warpperStatus ) { // 如果查到结束后,用户关闭的窗口,则不进行标记的显示
									$.get_(REALTIME_URL, '', function (getData) {
										var g_warpperStatus = !obj_cWrapper.is(':hidden');
										if ( g_warpperStatus ) { // 如果查到结束后,用户关闭的窗口,则不进行标记的显示
											var n_getStatus = getData.status;
											
											if ( n_getStatus == 0 ) {
												if ( getData.location ) {
													clearInterval(CURRENT_TIMMER);
													fn_displayCurrentMarker(getData.location);
												} else {
													if ( n_count >= c_countNum ) {
														clearInterval(CURRENT_TIMMER);
														fn_startCell(str_flagVal);
													}
												}
											} else if ( n_getStatus == 201 ) {
												dlf.fn_showBusinessTip();
											} else if ( n_getStatus == 301 || n_getStatus == 801 || n_getStatus == 800 ) {
												fn_startCell(str_flagVal);
											} else { // 基站失败 重新开启lastinfo
												fn_openLastinfo(str_errorMsg, true);
											}
										}
									},
									function (XMLHttpRequest, textStatus, errorThrown) {
										dlf.fn_serverError(XMLHttpRequest);
									});
								}
							}, CHECK_INTERVAL);
					}
				} else if ( n_status == 201 ) {
					dlf.fn_showBusinessTip();
				} else if ( n_status == 301 || n_status == 801 || n_status == 800 )  {
					fn_startCell(str_flagVal);
				} else { // 异常  重新开启lastinfo
					fn_openLastinfo(postData.message);
				}
			}
		}, 
		function(XMLHttpRequest, textStatus, errorThrown) {
			dlf.fn_serverError(XMLHttpRequest);
		});
	}
}
/*实时到数据进行显示*/
function fn_displayCurrentMarker(obj_location) {
	dlf.fn_closeDialog();
	// 动态更新终端相关数据
	dlf.fn_updateLastInfo();
    // 标记显示及中心点移动
	mapObj.setCenter(new BMap.Point(obj_location.clongitude/NUMLNGLAT, obj_location.clatitude/NUMLNGLAT));
	dlf.fn_updateInfoData(obj_location, 'current');
	dlf.fn_updateTerminalInfo(obj_location, 'realtime');
	//dlf.fn_getAddressByLngLat(obj_location.clongitude/NUMLNGLAT, obj_location.clatitude/NUMLNGLAT, obj_location.tid);
}
/*设防撤防操作*/
window.dlf.fn_defendQuery = function() {
	var n_defend = 0,
		obj_defend = {};
	$.get_(DEFEND_URL, '', function(data) {
		if ( data.status == 0 ) {
			var str_defendStatus = data.defend_status,  // 设防撤防状态
				obj_dMsg = $('#defendMsg'), 
				obj_wrapper = $('#defendWrapper'),
				str_html = '',
				str_tip = '',
				str_dImg = '',
				obj_defendBtn = $('#defendBtn'); 
			dlf.fn_lockScreen();	//添加页面遮罩
			obj_wrapper.css({'left':'38%','top':'22%'}).show();
			if ( str_defendStatus == DEFEND_ON ) {
				n_defend = 0;
				str_tip = '您的爱车保当前已设防。';
				dlf.fn_setItemMouseStatus(obj_defendBtn, 'pointer', new Array('cf', 'cf2', 'cf'));	
				str_html = '已设防';
				str_dImg= 'url("/static/images/defend_status1.png")';
			} else {
				n_defend = 1;
				str_tip = '您的爱车保当前未设防。';
				dlf.fn_setItemMouseStatus(obj_defendBtn, 'pointer', new Array('sf', 'sf2', 'sf'));
				str_html = '未设防';
				str_dImg=  'url("/static/images/defend_status0.png")';				
			}
			obj_defend['defend_status'] = n_defend;
			obj_dMsg.html(str_tip);
			$('#defendContent').html(str_html).data('defend', str_defendStatus);
			$('#defendStatus').css('background-image', str_dImg).attr('title', str_html);
		} else if ( data.status == 201 ) {
			dlf.fn_showBusinessTip();
		} else {
			dlf.fn_jNotifyMessage(data.message, 'message', false, 3000);
		}
	});
	//设防撤防 业务保存
	$('#defendBtn').unbind('click').click(function() {
		dlf.fn_jsonPost(DEFEND_URL, obj_defend, 'defend', '爱车保状态保存中');
	}); 
}
})();