/*
*实时定位相关操作方法
* 设防撤防操作
*/
(function () {
window.dlf.fn_currentQuery = function() {
	$('#currentWrapper').show();
	fn_currentRequest();
	$('#currentBtn').unbind('click').click(function() {
		dlf.fn_closeDialog(); // 窗口关闭
	});
}
function fn_currentRequest() {
	var obj_cWrapper = $('#currentWrapper'),
		obj_msg = $('#currentMsg'), 
		str_carCurrent = $('.currentCar').siblings('span').html(), // 当前车辆
		str_msg = '车辆<b>'+ str_carCurrent +'</b>定位中...<img src="/static/images/blue-wait.gif" />';
		
	obj_msg.html(str_msg);
	dlf.fn_lockScreen(); // 添加页面遮罩
	dlf.fn_clearInterval(currentLastInfo); //停止计时
	$.get_(REALTIME_URL, '', function (data) {
		var f_warpperStatus = !obj_cWrapper.is(':hidden');
		if ( f_warpperStatus ) { // 如果查到结束后,用户关闭的窗口,则不进行标记的显示
			if ( data.status == 0 ) { 
				// 如果第一次拿到数据就进行显示
				if ( data.location ) {
					fn_displayCurrentMarker(data.location);
				} else {
					obj_msg.html(data.message);
				}
			} else if ( data.status == 201 ) {
				dlf.fn_showBusinessTip();
			} else {
				obj_msg.html(data.message);
			}
		}
		// 动态更新终端相关数据
		dlf.fn_updateLastInfo();
	}, 
	function(XMLHttpRequest, textStatus, errorThrown) {
		dlf.fn_serverError(XMLHttpRequest);
	});
}
/*实时到数据进行显示*/
function fn_displayCurrentMarker(obj_location) {
	dlf.fn_closeDialog();
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
				str_dImg = '',
				obj_defendBtn = $('#defendBtn'); 
			dlf.fn_lockScreen();	//添加页面遮罩
			obj_wrapper.css({'left':'38%','top':'22%'}).show();
			if ( str_defendStatus == DEFEND_ON ) {
				n_defend = 0;
				obj_dMsg.html('您的爱车保当前已设防。');
				dlf.fn_setItemMouseStatus(obj_defendBtn, 'pointer', new Array('cf', 'cf2', 'cf'));	
				str_html = '设防状态：  已设防';
				str_dImg= '/static/images/defend_status1.png';
			} else {
				n_defend = 1;
				obj_dMsg.html('您的爱车保当前未设防。');
				dlf.fn_setItemMouseStatus(obj_defendBtn, 'pointer', new Array('sf', 'sf2', 'sf'));
				str_html = '设防状态：  未设防';
				str_dImg=  '/static/images/defend_status0.png';				
			}
			obj_defend['defend_status'] = n_defend;
			$('#defend_word').html(str_html).data('defend', str_defendStatus);
			$('#defendStatus').attr('title', str_html);
			$('#defend_status').attr('src', str_dImg); // 终端最后一次设防状态
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
