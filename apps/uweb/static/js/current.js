/*
*实时定位相关操作方法
* 设防撤防操作
*/
(function () {
window.dlf.fn_currentQuery = function() {
	var str_cellid_status = $('.carCurrent').attr('cellid_status'),	// 是否是基站定位
		obj_pd = {
					'timestamp': new Date().getTime(),
					'cellid_status': str_cellid_status
				}, 
		obj_cWrapper = $('#currentWrapper');
	obj_cWrapper.show();
	fn_currentRequest(obj_pd);
	$('#currentBtn').unbind('click').click(function() {
		dlf.fn_closeDialog(); // 窗口关闭
	});
}
function fn_currentRequest(obj_pd) {
	var obj_cWrapper = $('#currentWrapper'),
		obj_msg = $('#currentMsg'), 
		str_carCurrent = $('.carCurrent').html(), // 当前车辆
		str_msg = '车辆<b>'+ str_carCurrent +'</b>定位中...<img src="/static/images/blue-wait.gif" />';
		
	obj_msg.html(str_msg);
	dlf.fn_lockScreen(); // 添加页面遮罩
	dlf.fn_clearInterval(currentLastInfo); //停止计时
	$.post_(REALTIME_URL, JSON.stringify(obj_pd), function (data) {
		var f_warpperStatus = !obj_cWrapper.is(':hidden');
		if ( f_warpperStatus ) { // 如果查到结束后,用户关闭的窗口,则不进行标记的显示
			if ( data.status == 0 ) { 
				// 如果第一次拿到数据就进行显示
				if ( data.location ) {
					fn_displayCurrentMarker(data.location);
				} else {
					obj_msg.html(data.message);
				}
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
	dlf.fn_updateInfoData(obj_location, 'realtime');
	dlf.fn_updateTerminalInfo(obj_location, 'realtime');
}

/*设防撤防操作*/
window.dlf.fn_defendQuery = function() {
	var str_defendStatus = $('#defendStatus').html(),  // 设防撤防状态
		obj_dMsg = $('#defendMsg'), 
		obj_wrapper = $('#defendWrapper'),
		obj_defendBtn = $('#defendBtn'); 
		
	//dlf.fn_clearMapComponent(); //清除地图上的图形
	dlf.fn_lockScreen();	//添加页面遮罩
	obj_wrapper.css({'left':'38%','top':'22%'}).show();
	
	if ( str_defendStatus == '已设防' ) {
		obj_dMsg.html('您的爱车保当前已设防');
		obj_defendBtn.css('background', 'url("/static/images/cf.png")');
	} else {
		obj_dMsg.html('您的爱车保当前未设防');
		obj_defendBtn.css('background', 'url("/static/images/sf.png")');
	}
	//设防撤防 业务保存
	$('#defendBtn').unbind('click').click(function() {
		dlf.fn_jsonPost(DEFEND_URL, '', 'defend', '爱车保状态保存中');
	}); 
}
})();