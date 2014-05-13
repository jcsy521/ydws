/**
* 主页面方法
*/
(function () {
/**
* 我的资料初始化 
*/
window.dlf.fn_personalData = function() {
	dlf.fn_dialogPosition('personal'); // 我的资料dialog显示
	dlf.fn_lockScreen(); // 添加页面遮罩
	// dlf.fn_onInputBlur();	// input的鼠标样式
	dlf.fn_jNotifyMessage('用户信息查询中' + WAITIMG, 'message', true); 
	dlf.fn_lockContent($('.personalContent')); // 添加内容区域的遮罩
	var str_tid = dlf.fn_getCurrentTid();
	
	$.get_(PERSON_URL + '?tid='+ str_tid, '', function (data) {	// 获取最新的个人资料数据
		if ( data.status == 0 ) {
			var obj_data = data.profile,
				str_name = obj_data.name,
				str_newName = str_name,
				str_cnum = obj_data.cnum,
				str_phone = obj_data.mobile;
				
			$('#name').val(str_name).data('name', str_name);
			if ( str_name == '' ) {
				str_name = str_phone;
			}
			if ( str_name.length > 4 ) {	// 姓名长度大于4显示...
				str_newName = str_name.substr(0,4)+'...';
			}
			$('#spanWelcome').html('欢迎您，' + dlf.fn_encode(str_newName)).attr('title', str_name);	// 更新主页用户名
			$('#phone').html(str_phone).data('phone', str_phone);
			// $('#cnum').val(str_cnum).data('cnum', str_cnum);
			
			// dlf.fn_updateAlias();	// 修改定位器别名
			dlf.fn_closeJNotifyMsg('#jNotifyMessage'); // 关闭消息提示
		} else if ( data.status == 201 ) {	// 业务变更
			dlf.fn_showBusinessTip();
		} else { 
			dlf.fn_jNotifyMessage(data.message, 'message', false, 5000); // 查询状态不正确,错误提示
		}
		dlf.fn_unLockContent(); // 清除内容区域的遮罩	
	}, 
	function (XMLHttpRequest, textStatus, errorThrown) {
		dlf.fn_serverError(XMLHttpRequest);
	});
}

/**
* 个人信息保存 
*/
window.dlf.fn_personalSave = function() { 
	dlf.fn_lockContent($('.personalContent')); // 添加内容区域的遮罩	
	var b_warpperStatus = !$('#personalWrapper').is(':hidden'),
		n_num = 0,
		obj_personalData = {};
		
	$('.j_personal').each(function(index, dom) {
		var obj_input = $(dom),
			str_val = obj_input.val(),
			str_id = obj_input.attr('id'),
			str_data = $('#'+str_id).data(str_id);
			
		if ( str_val != str_data ) {
			obj_personalData[str_id] = str_val;
		}
	});
	
	for(var param in obj_personalData) {	// 我的资料中修改项的个数
		n_num = n_num +1;
	}
	if ( n_num != 0 ) {	// 我的资料中如果有修改内容 ，向后台发送post请求，否则提示未做任何修改
		obj_personalData.tid = dlf.fn_getCurrentTid();
		dlf.fn_jsonPut(PERSON_URL, obj_personalData, 'personal', '个人资料保存中');
	} else {
		dlf.fn_jNotifyMessage('您未做任何修改。', 'message', false, 4000); // 查询状态不正确,错误提示
		dlf.fn_unLockContent(); // 清除内容区域的遮罩
	}
}

/**
* 修改密码初始化
*/
window.dlf.fn_changePwd = function() {
	dlf.fn_dialogPosition('pwd');
	dlf.fn_lockScreen(); // 添加页面遮罩
	$('#pwdWrapper input[type=password]').val('');// 清除文本框数据
}

/**
* 短息通知
*/
window.dlf.fn_initSMSParams = function() {
	dlf.fn_dialogPosition('smsOption');
	dlf.fn_lockScreen(); // 添加页面遮罩
	dlf.fn_lockContent($('.terminalContent')); // 添加内容区域的遮罩
	$.get_(SMS_URL, '', function(data) {
		if ( data.status == 0 ) {
			var obj_data = data.sms_options;
			
			for(var param in obj_data) {	// 获取短信设置项的数据，进行更新
				var n_val = obj_data[param],
					obj_param = $('#' + param);
					
				obj_param.attr('t_checked', n_val);
				if ( n_val == 1 ) {
					obj_param.attr('checked', true)
				} else {
					obj_param.attr('checked', false)
				}
			}
			dlf.fn_closeJNotifyMsg('#jNotifyMessage'); // 关闭消息提示
		} else if ( data.status == 201 ) {	// 业务变更
			dlf.fn_showBusinessTip();
		} else { 
			dlf.fn_jNotifyMessage(data.message, 'message', false, 5000); // 查询状态不正确,错误提示
		}
		dlf.fn_unLockContent(); // 清除内容区域的遮罩	
	}, 
	function (XMLHttpRequest, textStatus, errorThrown) {
		dlf.fn_serverError(XMLHttpRequest);
	});
	$('#smsNoticeSave').unbind('click').bind('click', function() {
		dlf.fn_saveSMSOption();
	});
}

/**
* 短信参数的保存方法
*/
window.dlf.fn_saveSMSOption = function() {
	var obj_checkbox = $('.j_checkbox'),
		n_num = 0,
		obj_smsData = {};
		
	$.each(obj_checkbox, function(index, dom) {
		var obj_this = $(dom),
			str_nowVal = obj_this.attr('checked') == 'checked' ? 1 : 0,
			str_oldVal = parseInt(obj_this.attr('t_checked')),
			str_id = obj_this.attr('id');
			
		if ( str_nowVal != str_oldVal ) {
			obj_smsData[str_id] = str_nowVal;
		}
	});
	/**
	* 只保存有修改的数据
	*/
	for(var param in obj_smsData) {	// 修改项的数目
		n_num = n_num + 1;
	}
	if ( n_num != 0 ) {	// 如果有修改向后台发送数据,否则提示无任何修改
		dlf.fn_jsonPut(SMS_URL, obj_smsData, 'sms', '短信告警参数保存中');
	} else {
		dlf.fn_jNotifyMessage('您未做任何修改。', 'message', false, 4000); // 查询状态不正确,错误提示
		dlf.fn_unLockContent(); // 清除内容区域的遮罩
	}
}

/**
* 用户点击退出按钮 
*/
window.dlf.fn_exit = function() {
	if ( confirm('您确定退出本系统吗？') ) {
		window.location.href='/logout';
	}
}

/**
* 初始化集团资料
*/
window.dlf.fn_initCorpData = function() {
	$('#hidCName').val('');
	dlf.fn_dialogPosition('corp'); // 我的资料dialog显示
	dlf.fn_lockScreen(); // 添加页面遮罩
	dlf.fn_onInputBlur();	// input的鼠标样式
	dlf.fn_jNotifyMessage('集团信息查询中' + WAITIMG, 'message', true); 
	dlf.fn_lockContent($('.corpContent')); // 添加内容区域的遮罩
	$('#c_name').unbind('blur').bind('blur', function() {
		var obj_this = $(this),
			str_old = obj_this.data('c_name'),
			str_new = obj_this.val(),
			n_nameLength = str_new.length;
		
		if ( n_nameLength > 0 ) {
			if ( n_nameLength > 20 ) {
				dlf.fn_jNotifyMessage('集团名称最多可输入20个汉字或字符！', 'message', false, 3000); // 查询状态不正确,错误提示
				return;
			}
			if ( !/^[\u4e00-\u9fa5A-Za-z0-9]+$/.test(str_new) ) {
				dlf.fn_jNotifyMessage('集团名称只能由中文、英文、数字组成！', 'message', false, 3000);
				return;
			}
			if ( str_old != str_new ) {
				dlf.fn_checkCName($(this).val());
			} else {
				$('#hidCName').val('');
			}
		} else {
			dlf.fn_jNotifyMessage('集团名称不能为空。', 'message', false, 3000);
		}
	});
	$.get_(CORPPERSON_URL, '', function (data) {	// 获取最新的集团资料数据
		if ( data.status == 0 ) {
			var obj_data = data.profile,
				str_name = obj_data.c_name, 		// 集团名称
				str_address = obj_data.c_address,	// 集团地址
				str_email = obj_data.c_email,		// 集团email
				str_linkMan = obj_data.c_linkman,	// 集团联系人
				str_newName = str_linkMan,			
				str_mobile = obj_data.c_mobile,		// 集团联系人手机号
				str_alert_mobile = obj_data.c_alert_mobile;	// 离线通知人
				
			if ( str_linkMan.length > 4 ) {	// 姓名长度大于4显示...
				str_newName = str_linkMan.substr(0,4)+'...';
			}
			$('#spanWelcome').html('欢迎您，' + dlf.fn_encode(str_newName)).attr('title', str_linkMan);	// 更新主页用户名
			// todo 集团名称修改的话左侧树根节点也修改
			$('.corpNode').html('<ins class="jstree-checkbox">&nbsp;</ins><ins class="jstree-icon">&nbsp;</ins>' + str_name).children().eq(1).css('background', 'url("/static/images/corpImages/corp.png") 0px no-repeat');
			dlf.fn_setCorpIconDiffBrowser();
			$('#c_name').val(str_name).data('c_name', str_name);
			$('#c_address').val(str_address).data('c_address', str_address);
			$('#c_email').val(str_email).data('c_email', str_email);
			$('#c_mobile').html(str_mobile);
			$('#c_linkman').val(str_linkMan).data('c_linkman', str_linkMan);
			$('#c_alert_mobile').val(str_alert_mobile).data('c_alert_mobile', str_alert_mobile);
			dlf.fn_closeJNotifyMsg('#jNotifyMessage'); // 关闭消息提示
		} else if ( data.status == 201 ) {	// 业务变更
			dlf.fn_showBusinessTip();
		} else {
			dlf.fn_jNotifyMessage(data.message, 'message', false, 5000); // 查询状态不正确,错误提示
		}
		dlf.fn_unLockContent(); // 清除内容区域的遮罩	
	},
	function (XMLHttpRequest, textStatus, errorThrown) {
		dlf.fn_serverError(XMLHttpRequest);
	});
}

/**
* 保存集团资料修改
*/
window.dlf.fn_corpSave = function() {
	dlf.fn_lockContent($('.corpContent')); // 添加内容区域的遮罩	
	var b_warpperStatus = !$('#corpWrapper').is(':hidden'),
		n_num = 0,
		obj_corpData = {};
		
	$('.j_corpData1').each(function(index, dom) {
		var obj_input = $(dom),
			str_val = obj_input.val(),
			str_id = obj_input.attr('id'),
			str_data = $('#'+str_id).data(str_id);
	
		if ( str_val != str_data ) {
			obj_corpData[str_id] = str_val;
		}
	});
	
	for(var param in obj_corpData) {	// 我的资料中修改项的个数
		n_num = n_num +1;
	}
	if ( n_num != 0 ) {	// 我的资料中如果有修改内容 ，向后台发送post请求，否则提示未做任何修改
		dlf.fn_jsonPut(CORPPERSON_URL, obj_corpData, 'corp', '个人资料保存中');
	} else {
		dlf.fn_jNotifyMessage('您未做任何修改。', 'message', false, 4000); // 查询状态不正确,错误提示
		dlf.fn_unLockContent(); // 清除内容区域的遮罩
	}
}

/**
* 初始化操作员个人资料
*/
window.dlf.fn_initOperatorData = function() {
	dlf.fn_lockScreen(); // 添加页面遮罩
	dlf.fn_dialogPosition('operatorData'); // 我的资料dialog显示
	dlf.fn_onInputBlur();	// input的鼠标样式
	dlf.fn_jNotifyMessage('操作员信息查询中' + WAITIMG, 'message', true); 
	dlf.fn_lockContent($('.operatorContent')); // 添加内容区域的遮罩
	$.get_(OPERATORPERSON_URL, '', function (data) {	// 获取最新的集团资料数据
		if ( data.status == 0 ) {
			var obj_data = data.profile,
				str_name = $('.corpNode').text().replace(/(^\s*)/g, ""), 		// 集团名称
				str_address = obj_data.address,	// 操作员地址
				str_email = obj_data.email,		// 操作员email
				str_linkMan = obj_data.name,	// 操作员联系人
				str_newName = str_linkMan,			
				str_mobile = obj_data.mobile;		// 操作员手机号
				
			if ( str_linkMan.length > 4 ) {	// 姓名长度大于4显示...
				str_newName = str_linkMan.substr(0,4)+'...';
			}
			$('#span_operCName').html(str_name);
			$('#span_operName').html(str_linkMan);
			$('#span_operMobile').html(str_mobile);
			$('#txt_operAddress').val(str_address).data('address', str_address);
			$('#txt_operEmail').val(str_email).data('email', str_email);
			dlf.fn_closeJNotifyMsg('#jNotifyMessage'); // 关闭消息提示
		} else if ( data.status == 201 ) {	// 业务变更
			dlf.fn_showBusinessTip();
		} else {
			dlf.fn_jNotifyMessage(data.message, 'message', false, 5000); // 查询状态不正确,错误提示
		}
		dlf.fn_unLockContent(); // 清除内容区域的遮罩	
	},
	function (XMLHttpRequest, textStatus, errorThrown) {
		dlf.fn_serverError(XMLHttpRequest);
	});
}

/**
* 保存操作员个人资料修改
*/
window.dlf.fn_operatorDataSave = function() {
	dlf.fn_lockContent($('.operatorContent')); // 添加内容区域的遮罩	
	var b_warpperStatus = !$('#operatorDataWrapper').is(':hidden'),
		n_num = 0,
		obj_corpData = {},
		obj_address = $('#txt_operAddress'),
		str_newAddress = obj_address.val(),
		str_oldAddress = obj_address.data('address'),
		obj_email = $('#txt_operEmail'),
		str_newEmail = obj_email.val(),
		str_oldEmail = obj_email.data('email');
	
	if ( str_oldAddress != str_newAddress ) {
		obj_corpData['address'] = str_newAddress;
		n_num = n_num + 1;
	}
	if ( str_oldEmail != str_newEmail ) {
		obj_corpData['email'] = str_newEmail;
		n_num = n_num + 1;
	}
	if ( n_num != 0 ) {	// 我的资料中如果有修改内容 ，向后台发送post请求，否则提示未做任何修改
		dlf.fn_jsonPut(OPERATORPERSON_URL, obj_corpData, 'operatorData', '个人资料保存中');
	} else {
		dlf.fn_jNotifyMessage('您未做任何修改。', 'message', false, 4000); // 查询状态不正确,错误提示
		dlf.fn_unLockContent(); // 清除内容区域的遮罩
	}
}

/**
* 初始化告警时间段设置列表
* kjj add in 2013-09-23
*/
window.dlf.fn_initAlertSetting = function(str_who) {
	var obj_alertSettingDialog = $('#addAlertSettingDialog');
		
	$('#' + str_who + 'TableHeader').nextAll().remove();
	// 初始化新增按钮事件
	$('.j_alertSettingCreateBtn').unbind('click').bind('click', function() {
		if ( $('.j_weekList').data('weeks').length < 7 ) {
			fn_initAlertSettingCreate(str_who);
			obj_alertSettingDialog.attr('title', '新增告警时间段').dialog('option', 'title', '新增告警时间段').dialog( "open" );
		} else {
			dlf.fn_jNotifyMessage('该定位器所有星期都已设置告警时间段。', 'message', false, 3000);
			return;
		}
	});
	// 新增初始化dialog
	obj_alertSettingDialog.dialog({
		autoOpen: false,
		width: 430,
		height: 360,
		modal: true,
		resizable: false
	});
}

/**
* 新增告警时间段初始化条件
*/
function fn_initAlertSettingCreate(str_who) {
	dlf.fn_initSlider('Alart');	// 初始化时间滑块
	dlf.fn_closeJNotifyMsg('#jNotifyMessage');
	var arr_checkWeek = $('.j_weekList').data('weeks'),
		n_weekLength = arr_checkWeek.length,
		obj_ckWeeks = $('.j_ckWeek');
	
	obj_ckWeeks.removeAttr('disabled').removeAttr('checked');
	// 已经设置的星期 不可再设置
	if ( n_weekLength > 0 ) {
		for ( var x = 0; x < n_weekLength; x++ ) {
			obj_ckWeeks.eq(arr_checkWeek[x]).attr('checked', true).attr('disabled', true);
		}
	}
	
	$('#alertSettingSave').unbind('click').click(function() {	// 保存按钮事件
		var n_alartHour0 = parseInt($('#txtAlartHour0').val()),
			n_alartHour1 = parseInt($('#txtAlartHour1').val()),
			n_alartMinute0 = parseInt($('#txtAlartMinute0').val()),
			n_alartMinute1 = parseInt($('#txtAlartMinute1').val()),
			n_startTime = (n_alartHour0*60+n_alartMinute0)*60,
			n_endTime = (n_alartHour1*60+n_alartMinute1)*60,
			str_tid = dlf.fn_getCurrentTid(),
			str_week = '',
			obj_data = {'tid': str_tid, 'start_time': n_startTime, 'end_time': n_endTime, 'week': str_week},
			b_isflag = false;
		
		obj_ckWeeks.each(function(index, obj) {
			var b_checked = $(obj).is(':checked'),
				b_disabled = $(obj).is(':disabled');
			
			if ( b_checked && !b_disabled ) {
				str_week += '1';
				b_isflag = true;
			} else {
				str_week += '0';
			}
		});
		if ( !b_isflag ) {	// 如果一个都没选中
			dlf.fn_jNotifyMessage('请选择需要设置告警时间段的星期。', 'message', false, 3000);
			return;
		}
		obj_data.week = str_week;
		// 提交表单
		$.post_(ALEERSETTING_URL, JSON.stringify(obj_data), function(data){
			if ( data.status == 0 ) {
				obj_ckWeeks.each(function(index, obj) {
					var obj_this = $(obj),
						b_checked = obj_this.is(':checked'),
						b_disabled = obj_this.is(':disabled');
					
					if ( b_checked ) {
						obj_this.attr('disabled', true)
					}
				});
				dlf.fn_jNotifyMessage('保存成功，请稍后再试。', 'message', false, 3000);
				dlf.fn_searchData(str_who);	// 重新刷新数据
			} else {
				dlf.fn_jNotifyMessage('保存失败，请稍后再试。', 'message', false, 3000);
			}
        });
	});
}
})();

/**
* 当用户窗口改变时,地图做相应调整
*/
window.onresize = function () {
	dlf.resetPanelDisplay();
}

/**
* 页面加载完成后进行加载地图
*/
$(function () {
	if ( $('#errormsg').length > 0 ) {
		dlf.fn_showBusinessTip();
		return;
	}
	
	$.ajaxSetup({ cache: false }); // 不保存缓存
    
	$(document).bind('contextmenu', function (e) { 	// 屏蔽鼠标右键相关功能
		return false; 
});
	/**
	* 调整页面大小
	*/
	var n_windowHeight = $(window).height(),
		n_windowHeight = $.browser.version == '6.0' ? n_windowHeight <= 624 ? 624 : n_windowHeight : n_windowHeight,
		n_windowWidth = $(window).width(),
		n_windowWidth = $.browser.version == '6.0' ? n_windowWidth <= 1024 ? 1024 : n_windowWidth : n_windowWidth,
		n_tilelayerLeft = n_windowWidth <= 1024 ? 1024 - 188 : n_windowWidth - 188,
		n_mapHeight = n_windowHeight - 161,
		n_right = n_windowWidth - 249,
		n_trackLeft = 0,
		obj_track = $('#trackHeader'),
		n_mainHeight = n_windowHeight - 123,
		n_corpTreeContainerHeight = n_mainHeight-270,
		n_treeHeight = n_corpTreeContainerHeight - 55,
		n_delayLeft = n_windowWidth - 550,
		n_delayIconLeft = n_delayLeft - 17,
		n_alarmLeft = n_windowWidth - 400,
		n_alarmIconLeft = n_alarmLeft - 17,
		n_topPanelLeft = '50%',
		n_leftPanelTop = '50%',	// 左侧收缩按钮距离上面的高度
		obj_tree = $('#corpTree');
		
	if ( $.browser.msie ) { // 根据浏览器不同调整页面部分元素大小 
		n_right = n_windowWidth - 259;
		n_mapHeight = n_mapHeight - 10;
	}
	$('.mainBody').height(n_windowHeight);
	$('.j_corpCarInfo').css('height', n_corpTreeContainerHeight);	// 集团用户左侧树的高度
	
	if ( n_treeHeight < 255 ) {
		n_treeHeight = 255;
	}
	obj_tree.css('min-height', n_treeHeight).height(n_treeHeight);
	
	if ( dlf.fn_userType() ) {	// 集团用户
		n_trackLeft = ( obj_track.width() ) / 8;
		
		if ( n_windowWidth < 1024 ) {
			n_windowWidth = 1024;
			n_trackLeft = 40;
			n_delayLeft = 474;
			n_delayIconLeft = 458;
			n_alarmLeft = 623;
			n_alarmIconLeft = 609;
			n_topPanelLeft = 1024/2;
			n_right = 775;
		}
		if ( n_mainHeight < 600 ) {
			n_leftPanelTop = 300 + 123;
		}
	} else {
		n_trackLeft = ( obj_track.width() ) / 6;
		if ( n_windowWidth < 1024 ) {
			n_trackLeft = 90;
		}
	}
	$('#right, #corpRight, #navi, #mapObj, #trackHeader, .j_wrapperContent, .eventSearchContent, .mileageContent, .operatorContent, .onlineStaticsContent').css('width', n_right);	// 右侧宽度
	
	$('#top, #main, #corpMain').css('width', n_windowWidth);
	$('#main, #corpMain, #left, #corpLeft, #right, #corpRight').css('height', n_mainHeight);	// 内容域的高度 左右栏高度
	$('#topShowIcon').css('left', n_topPanelLeft);
	$('#leftPanelShowIcon').css('top', n_leftPanelTop);
	if ( n_windowWidth > 1510 ) {
		$('.trackPos').css('padding-left', n_trackLeft); // 轨迹查询条件 位置调整
	} else {
		$('.trackPos').css('padding-left', 0);
	}
	$('#mapObj, .j_wrapperContent, .eventSearchContent, .mileageContent, .operatorContent, .onlineStaticsContent').css('height', n_mapHeight);
	
	if ( !dlf.fn_isBMap() ) {	// 高德地图初始化tilelayer的位置
		$('#mapTileLayer').css('left', n_tilelayerLeft);
	}
	// 设置停留点列表的位置
	$('.j_delayPanel').css({'left': n_delayLeft});
	$('.j_disPanelCon').css({'left': n_delayIconLeft});
	/*
	$('.j_alarmPanelCon').css({'left': n_alarmIconLeft});
	*/
	$('.j_alarmPanel').hide();
	$('.j_alarmPanel').css({'left': n_alarmLeft});
	$('.j_alarmPanelCon').css({'left': (n_windowWidth-18)});
	$('.j_alarmArrowClick').css('backgroundPosition', '-29px -29px');

	dlf.fn_loadMap('mapObj');	// 加载百度map
	
	$('#home').css('color', '#0E6CA5');
	
	/**
	* 页面的点击事件分流处理
	*/
	var str_userType = $('.j_body').attr('userType');
	$('.j_click').click(function(e) { 
		var str_id = e.currentTarget.id, 
			b_mapType = dlf.fn_isBMap(),
			n_carNum = $('#carList li').length,
			b_trackStatus = $('#trackHeader').is(':visible'), 
			b_eventSearchStatus = $('#eventSearchWrapper').is(':visible'),	// 告警查询是否显示
			b_routeLineWpST = $('#routeLineWrapper').is(':visible'), //线路展示窗口是否打开
			b_operatorStatus = $('#operateorWrapper').is(':visible'),	// 操作员是否显示
			b_mileageStatus = $('#mileageWrapper').is(':visible'),	// 里程统计是否显示
			b_addLineRoute = $('#routeLineCreateWrapper').is(':visible');	// 添加站点是否显示
			b_regionStatus = $('#regionWrapper').is(':visible'),	// 围栏显示是否显示
			b_corpRegionStatus = $('#corpRegionWrapper').is(':visible'),	// 集团的围栏管理
			b_bindRegionStatus = $('#bindRegionWrapper').is(':visible'),	// 围栏绑定是否显示
			b_bindBatchRegionStatus = $('#bindBatchRegionWrapper').is(':visible'),	// 围栏批量绑定是否显示
			b_regionCreateStatus = $('#regionCreateWrapper').is(':visible'),	// 新增围栏是否显示
			obj_navItemUl = $('.j_countNavItem'),
			obj_alarm = $('.j_alarm'),
			obj_delay = $('.j_delay');

		if ( b_trackStatus ) {	// 如果当前点击的不是轨迹按钮，先关闭轨迹查询
			if ( str_id == 'track' ) {
				return;
			} else {
				obj_delay.hide();
			}
		}
		// 除了对多个定位器操作外
		if ( str_id != 'home' && str_id != 'personalData' && str_id != 'corpData' && str_id != 'changePwd' && str_id != 'statics' && str_id != 'mileage' && str_id != 'operator' && str_id != 'passenger' && str_id != 'infoPush' && str_id != 'routeLine' && str_id != 'eventSearch' && str_id != 'corpRegion' && str_id != 'region' && str_id != 'operatorData' && str_id != 'logout' && str_id != 'help' ) {
			if ( $('.j_terminal').length <= 0 ) {
				dlf.fn_jNotifyMessage('当前用户没有可用终端，不能操作', 'message', false, 5000); // 查询状态不正确,错误提示
				return;
			} else {
				var obj_currentNode = $('.jstree-clicked'),
					b_class = obj_currentNode.hasClass('groupNode'), 
					n_currentGroupUlLen = $($('.jstree-clicked').next('ul')).length;
				
				if ( b_class && n_currentGroupUlLen == 0 ) {
					dlf.fn_jNotifyMessage('当前组下没有可用终端，请选择其他组下的终端。', 'message', false, 5000); // 查询状态不正确,错误提示
					return;
				}
			}
		}
		// 是否清除地图及lastinfo
		if ( str_id == 'eventSearch' || str_id == 'routeLine' ) {
			obj_alarm.hide();
			dlf.fn_closeTrackWindow(false);	// 关闭轨迹查询,不操作lastinfo
		}
		if ( !b_mapType ) {
			dlf.fn_gaodeCloseDrawCircle();	// 关闭高德地图的画圆事件
			dlf.fn_mapStopDraw(true);	// 关闭高德地图的 添加站点事件
		}
		if ( str_userType !=  USER_PERSON ) {
			dlf.fn_secondNavValid();
		} else {	// 个人用户如果告警查询后显示小地图  再操作其他有关地图的功能要还原地图
			if ( b_eventSearchStatus ) {
				dlf.fn_setMapPosition(false);	// 还原地图
			}
		}
		
		// kjj add in 2014.05.07
		if ( str_id == 'operatorData' || str_id == 'track' || str_id == 'eventSearch' || str_id == 'operator' || str_id == 'mileage' || str_id == 'passenger' || str_id == 'infoPush' || str_id == 'routeLine' || str_id == 'corpRegion' || str_id == 'region' ||  str_id == 'notifyManage_add' || str_id == 'notifyManage_search' ) {
			$("#showMusic").html('');
		}
		switch (str_id) {
			case 'home': // 主页
				$('.wrapper').hide();
				$('#mapObj').show();
				
				if ( b_eventSearchStatus || b_routeLineWpST || b_addLineRoute ) {	// 如果打开的是告警、线路、添加站点则还原地图开启lastinfo  同时移除地图的click事件
					dlf.fn_setMapPosition(false);	// 还原地图
					$('#eventSearch').removeClass('eventSearchHover');
				}
				dlf.fn_clearAllMenu();
				$('#home').addClass('menuHover').css('color', '#0E6CA5');	// homeHover
				// 如果上次操作的是 轨迹、告警查询、线路管理、添加线路、围栏管理、绑定围栏、批量绑定围栏、创建围栏 操作的话 点击“车辆位置” 清除所有数据重新发起lastinfo请求
				
				if ( b_trackStatus || b_eventSearchStatus || b_routeLineWpST || b_addLineRoute || b_regionStatus || b_corpRegionStatus || b_bindRegionStatus || b_bindBatchRegionStatus || b_regionCreateStatus ) {
					dlf.fn_closeTrackWindow(true);	// 关闭轨迹查询 清除lastinfo
				} else { 
					var obj_current = obj_selfmarkers[$('.j_carList .j_currentCar').attr('tid')];
					
					if ( obj_current ) {
						setTimeout(function() {
							mapObj.setCenter(obj_current.getPosition());
						}, 300);
					}
				}
				//显示标题及左侧收缩按钮 
				$('#topShowIcon, #leftPanelShowIcon').show();
				break;
			case 'personalData': //  个人资料 
				dlf.fn_personalData();
				break;
			case 'corpData':	// 集团资料
				dlf.fn_initCorpData();	
				break;
			case 'operatorData':	// 操作员资料
				dlf.fn_initOperatorData();	
				break;
			case 'changePwd': // 修改密码
				dlf.fn_changePwd();
				break;
			case 'terminal': // 参数设置
				dlf.fn_initTerminal();
				break;
			case 'corpTerminal': // 集团参数设置
				dlf.fn_initCorpTerminal();
				break;
			case 'realtime': // 实时查询
				dlf.fn_currentQuery();
				break;
			case 'defend': // 设防撤防
				dlf.fn_defendQuery();
				break;
			case 'track': // 轨迹查询
				// dlf.fn_clearOpenTrackData();	// 初始化开启追踪
				obj_alarm.hide();
				dlf.fn_initTrack();
				break;
			case 'smsOption': // 短信设置
				dlf.fn_initSMSParams();
				break;
			case 'eventSearch': // 告警查询
				dlf.fn_initRecordSearch('eventSearch');
				break;
			case 'operator': // 操作员查询
				dlf.fn_initRecordSearch('operator');
				break;
			case 'statics': // 告警统计
				dlf.fn_initRecordSearch('statics');
				obj_navItemUl.hide();
				break;
			case 'mileage': // 里程统计
				dlf.fn_initRecordSearch('mileage');
				// obj_navItemUl.hide();
				break;
			case 'passenger': // 乘客查询
				dlf.fn_initRecordSearch('passenger');
				break;
			case 'infoPush': // 信息推送
				dlf.fn_initInfoPush();
				break;
			case 'routeLine': // 线路管理
				// dlf.fn_clearOpenTrackData();	// 初始化开启追踪
				if ( b_eventSearchStatus ) {
					dlf.fn_setMapPosition(false);	// 还原地图
				}
				dlf.fn_initRouteLine();
				break;
			case 'corpRegion': 	// 集团围栏管理
			case 'region': // 个人围栏管理
				obj_alarm.hide();
				dlf.fn_closeTrackWindow(false);	// 关闭轨迹查询,不操作lastinfo
				if ( b_eventSearchStatus ) {
					dlf.fn_setMapPosition(false);	// 还原地图
				}
				dlf.fn_initRegion();
				break;
			case 'onlineStatics': // 在线统计
				dlf.fn_initRecordSearch('onlineStatics');
				break;
			case 'corpSMSOption': 
				dlf.fn_initSMSOption();
				break;
			case 'notifyManage_add': //通知发布
				dlf.fn_notifyManage_addInit();
				break;
			case 'notifyManage_search': // 通知查询
				dlf.fn_initRecordSearch('notifyManageSearch');
				break;
			case 'help':
				dlf.fn_secondNavValid();
				break;
			case 'logout':
				dlf.fn_secondNavValid();
				dlf.fn_exit();
				break;
		}
	});
	/*鼠标滑动显示统计二级菜单*/
	$('.j_countRecord, .j_notifyManage, .j_userProfileManage, .j_welcome').unbind('mouseover mousedown').bind('mouseover mousedown', function(event) {
		dlf.fn_fillNavItem(event.target.id);
	}).unbind('mouseout').bind('mouseout', function() {
		dlf.fn_secondNavValid();
	});
	dlf.fn_closeWrapper(); //吹出框关闭事件
	
	/**
	* dialogs 的拖动效果
	*/
	$('.j_drag').draggable({handle: '.wrapperTitle', containment: 'body', cursor:'move',
		drag: function(event, ui) {
			var b_conStatus = !$('#jContentLock').is(':hidden'),
				str_currentId = event.target.id,
				obj_whitePop = $('#whitelistPopWrapper'),
				b_warpperStatus = !obj_whitePop.is(':hidden'),
				n_left = ui.position.left + 380,
				n_top = ui.position.top + 60;
				
			if ( b_conStatus ) {
				dlf.fn_lockContent($($(this).children().eq(1)));
			}
			if ( str_currentId == 'terminalWrapper' && b_warpperStatus ) {	// 定位器设置dialog拖动时，白名单未填提示框跟着拖动
				obj_whitePop.css({left: n_left, top: n_top});
			}
			if ( str_currentId == 'corpSMSOptionWrapper' ) {
				$('#smsOwerMobile').autocomplete('close');
			}
		},
		stop: function(event, ui) {
			if ( ui.position.top < 0 ) {
				$(this).css('top', 0);
			}
	}});
	
	/**
	* 定位器设置、个人资料、修改 input的焦点事件
	*/
	$('#bListR input[type=text], .personalList input, .pwdList input, #remark').focus(function() {
		$(this).addClass('bListR_text_mouseFocus');
	}).blur(function() {
		$(this).removeClass('bListR_text_mouseFocus');
	});
	
	dlf.fn_setItemMouseStatus($('.j_save'), 'pointer', new Array('bc', 'bc2'));	// 保存按钮鼠标滑过样式
	
	/**
	* 个人信息的验证
	*/
	$.formValidator.initConfig({
		formID: 'personalForm', //指定from的ID 编号
		debug: true, // 指定调试模式,不提交form
		wideWord: false,	// 一个汉字当一个字节
		validatorGroup: '1', // 指定本form组编码,默认为1, 多个验证组时使用
		submitButtonID: 'personalSave', // 指定本form的submit按钮
		onError: function(msg) { 
			dlf.fn_jNotifyMessage(msg, 'message', false, 5000); 
		}, 
		onSuccess: function() {
			var str_name = $('#name').val();
			
			if ( str_name.length > 0 && $.trim(str_name).length == 0 ) {
				dlf.fn_jNotifyMessage('用户姓名不能为空，请重新输入。', 'message', false, 3000);
				return;
			}
			dlf.fn_personalSave();
		}
	});
	$('#name').formValidator({validatorGroup: '1'}).inputValidator({min: 1, onErrorMin: '用户姓名不能为空，请重新输入。', max: 20, onErrorMax: '用户姓名最多可输入20个字符！'});  // 别名.regexValidator({regExp: 'name', dataType: 'enum', onError: "用户姓名只能由数字、英文、中文、空格组成！"}); 

	/**
	* 密码进行验证
	*/
	$.formValidator.initConfig({
		formID: 'pwdForm', //指定from的ID 编号
		debug: true, // 指定调试模式,不提交form
		validatorGroup: '2', // 指定本form组编码,默认为1, 多个验证组时使用
		submitButtonID: 'pwdSave', // 指定本form的submit按钮
		onError: function(msg) { 
			dlf.fn_jNotifyMessage(msg, 'message', false, 5000); 
		}, 
		onSuccess: function() { 
			var obj_pwd = {'old_password' : $("#oldPwd").val(), 
						   'new_password' : $("#newPwd").val() 
						  },
				str_url = PWD_URL,
				str_userType = $('.j_body').attr('userType');
			//提交服务器
			if ( str_userType == USER_CORP ) {
				str_url = CORPPWD_URL;
			} else if ( str_userType == USER_OPERATOR ) {
				str_url = OPERATORPWD_URL;
			}
			dlf.fn_jsonPut(str_url, obj_pwd, 'pwd', '密码保存中');
		}
	});
	
	$('#oldPwd').formValidator({validatorGroup: '2'}).inputValidator({min: 6, onError: '密码最小长度不能小于6位！'}).regexValidator({regExp: 'password', dataType: 'enum', onError: '密码为不少于6位的字母或数字组成！'});
	$('#newPwd').formValidator({validatorGroup: '2'}).inputValidator({min: 6, onError: '密码最小长度不能小于6位！'}).regexValidator({regExp: 'password', dataType: 'enum', onError: '密码为不少于6位的字母或数字组成！'});
	$('#newPwd2').formValidator({validatorGroup: '2'}).compareValidator({desID: 'newPwd', operateor: '=', datatype: 'number', onError: '两次密码不一致，请重新输入！'});
	
	/** 
	* 定位器参数的验证
	*/
	$.formValidator.initConfig({
		formID: 'terminalForm', //指定from的ID 编号
		debug: true, // 指定调试模式,不提交form
		validatorGroup: '3', // 指定本form组编码,默认为1, 多个验证组时使用
		wideWord: false, // 一个汉字当一个字节
		submitButtonID: 'terminalSave', // 指定本form的submit按钮
		onError: function(msg) {
			dlf.fn_jNotifyMessage(msg, 'message', false, 4000); 
		}, 
		onSuccess: function() {
			var str_alert_freq = $('#t_alert_freq').val(),				
				str_mode = $('#alert_freq_mode').val(),
				str_val = $('#t_cnum').val(),
				str_oldVal = $('#corp_cnum').attr('t_val');
			
			if ( str_mode == '1' ) {
				if ( str_alert_freq <= 0 ) {
					dlf.fn_jNotifyMessage('告警工作模式只能是大于0的整数！', 'message', false, 3000);
					return;
				} else if ( str_alert_freq > 1440 ) {
					dlf.fn_jNotifyMessage('告警工作模式最大不能超过24小时！', 'message', false, 3000);
					return;
				} else {
					if ( !/^[0-9]*[1-9][0-9]*$/.test(str_alert_freq) ) {
						dlf.fn_jNotifyMessage('告警工作模式只能是正整数！', 'message', false, 3000);
						return;
					}
				}
			}
			
			if ( str_val.length > 0 && $.trim(str_val).length == 0 ) {
				dlf.fn_jNotifyMessage('定位器名称不能为空，请重新输入。', 'message', false, 3000);
				return;
			} else { 
				// 如果旧的值是0 新的值也是0
				if ( str_oldVal.length == 0 && str_val.length == 0 ) {
					
				} else if ( str_oldVal.length > 0 && str_val.length == 0 ) {
					dlf.fn_jNotifyMessage('定位器名称不能为空，请重新输入。', 'message', false, 3000);
					return;
				}
			}
			dlf.fn_baseSave();	// put请求
		}
	});
	$('#t_cnum').formValidator({validatorGroup: '3', empty: true}).inputValidator({min: 1, onErrorMin: '定位器名称不能为空，请重新输入。', max: 20, onErrorMax: '定位器名称最多可输入20个字符！'}); // 区分大小写.regexValidator({regExp: 'licensenum', dataType: 'enum', onError: '定位器名称只能由汉字、数字、大写字母、空格组成！'})
	
	/**
	* 集团信息的验证
	*/
	$.formValidator.initConfig({
		formID: 'corpForm', //指定from的ID 编号
		validatorGroup: '4', // 指定本form组编码,默认为1, 多个验证组时使用
		debug: true, // 指定调试模式,不提交form
		wideWord: false,	// 一个汉字当一个字节
		submitButtonID: 'corpSave', // 指定本form的submit按钮
		onError: function(msg) { 
			dlf.fn_jNotifyMessage(msg, 'message', false, 5000);
			return;
		}, 
		onSuccess: function() {
			if ( $('#hidCName').val() != '' ) {
				dlf.fn_jNotifyMessage('集团名称已存在。', 'message', false, 5000);
				return;
			} else {
				dlf.fn_corpSave();
			}
		}
	});
	$('#c_name').formValidator({validatorGroup: '4'}).inputValidator({min: 1, onErrorMin: '集团名称不能为空。', max: 20, onErrorMax: '集团名称最多可输入20个汉字或字符！'}).regexValidator({regExp: 'c_name', dataType: 'enum', onError: "集团名称只能由中文、英文、数字组成！"});  //集团名
	$('#c_linkman').formValidator({validatorGroup: '4'}).inputValidator({max: 20, onError: '联系人最多可输入20个字符！'});  // 联系人姓名regexValidator({regExp: 'c_name', dataType: 'enum', onError: "联系人姓名只能由中文、英文、数字组成！"});
	$('#c_alert_mobile').formValidator({empty: true, validatorGroup: '4'}).regexValidator({regExp: 'owner_mobile', dataType: 'enum', onError: "离线通知号码输入不合法，请重新输入！"}); // 离线联系人手机号
	$('#c_email').formValidator({empty:true, validatorGroup: '4'}).inputValidator({max: 50, onError: '联系人邮箱最多可输入50个字符！'}).regexValidator({regExp: 'email', dataType: 'enum', onError: "联系人邮箱输入不合法，请重新输入！"});  // 联系人email
	$('#c_address').formValidator({empty:true, validatorGroup: '4'}).inputValidator({max: 100, onError: '联系人地址最多可输入100个汉字或字符！'}).regexValidator({regExp: 'address', dataType: 'enum', onError: "联系人地址输入不合法，请重新输入！"});  // 联系人email; // 地址
	
	/**
	* 操作员个人信息的验证
	*/
	$.formValidator.initConfig({
		formID: 'operatorForm', //指定from的ID 编号
		validatorGroup: '9', // 指定本form组编码,默认为1, 多个验证组时使用
		debug: true, // 指定调试模式,不提交form
		wideWord: false,	// 一个汉字当一个字节
		submitButtonID: 'operatorDataSave', // 指定本form的submit按钮
		onError: function(msg) { 
			dlf.fn_jNotifyMessage(msg, 'message', false, 5000); 
		}, 
		onSuccess: function() { 
			dlf.fn_operatorDataSave();
		}
	});
	$('#txt_operAddress').formValidator({empty:true, validatorGroup: '9'}).inputValidator({max: 100, onError: '地址最大长度是100个汉字或字符！'});  // 联系人email
	$('#txt_operEmail').formValidator({empty:true, validatorGroup: '9'}).regexValidator({regExp: 'email', dataType: 'enum', onError: "邮箱输入不合法，请重新输入！"});  // 联系人email
	
	/**
	* 新建定位器验证
	*/
	$.formValidator.initConfig({
		formID: 'cTerminalForm', //指定from的ID 编号
		validatorGroup: '5', // 指定本form组编码,默认为1, 多个验证组时使用
		debug: true, // 指定调试模式,不提交form
		wideWord: false,	// 一个汉字当一个字节
		submitButtonID: 'cTerminalSave', // 指定本form的submit按钮
		onError: function(msg) {
			dlf.fn_jNotifyMessage(msg, 'message', false, 5000);
			return;
		}, 
		onSuccess: function() {
			var str_val = $('#c_cnum').val(),
				str_cmobile = $('#c_tmobile').val();
			
			$.get_(CHECKMOBILE_URL + '/' + str_cmobile, '', function(data){
				if ( data.status != 0 ) {
					dlf.fn_jNotifyMessage(data.message, 'message', false, 5000);
					return;
				} else {
					if ( str_val.length > 0 && $.trim(str_val).length == 0 ) {
						dlf.fn_jNotifyMessage('定位器名称不能为空。', 'message', false, 3000);
						return;
					} else {
						dlf.fn_cTerminalSave();
					}
				}
			}, 
			function (XMLHttpRequest, textStatus, errorThrown) {
				dlf.fn_serverError(XMLHttpRequest);
			});
		}
	});
	$('#c_tmobile').formValidator({validatorGroup: '5'}).regexValidator({regExp: 'owner_mobile', dataType: 'enum', onError: "定位器手机号输入不合法，请重新输入！"});  // 别名;
	$('#c_umobile').formValidator({empty:true, validatorGroup: '5'}).regexValidator({regExp: 'owner_mobile', dataType: 'enum', onError: "短信接收号码输入不合法，请重新输入！"});  // 别名;
	$('#c_cnum').formValidator({empty:true, validatorGroup: '5'}).inputValidator({max: 20, onError: '定位器名称最多可输入20个汉字或字符！'});  // 别名;.regexValidator({regExp: 'licensenum', dataType: 'enum', onError: '定位器名称只能由汉字、数字、大写字母、空格组成！'})
	$('#c_color').formValidator({empty:true, validatorGroup: '5'}).inputValidator({max: 20, onError: '车辆颜色最多可输入20个汉字或字符！'});
	$('#c_brand').formValidator({empty:true, validatorGroup: '5'}).inputValidator({max: 20, onError: '车辆品牌最多可输入20个汉字或字符！'});
	
	/**
	* 编辑定位器验证
	*/
	$.formValidator.initConfig({
		formID: 'cTerminalEditForm', //指定from的ID 编号
		validatorGroup: '6', // 指定本form组编码,默认为1, 多个验证组时使用
		debug: true, // 指定调试模式,不提交form
		wideWord: false,	// 一个汉字当一个字节
		submitButtonID: 'cTerminalEditSave', // 指定本form的submit按钮
		onError: function(msg) { 
			dlf.fn_jNotifyMessage(msg, 'message', false, 5000);
			return;
		}, 
		onSuccess: function() {
			dlf.fn_cEditTerminalSave();
		}
	});
	$('#c_editcnum').formValidator({empty:true,validatorGroup: '5'}).inputValidator({max: 20, onError: '定位器名称最大长度为20个汉字或字符！'});  // 别名;
	$('#c_editccolor').formValidator({empty:true,validatorGroup: '5'}).inputValidator({max: 20, onError: '车辆颜色最大长度为20个汉字或字符！'});
	$('#c_editcbrand').formValidator({empty:true,validatorGroup: '5'}).inputValidator({max: 20, onError: '车辆品牌最大长度是20个汉字或字符！'});
	
	
	/**
	* 操作员进行验证
	*/
	$.formValidator.initConfig({
		formID: 'addOperatorForm', //指定from的ID 编号
		debug: true, // 指定调试模式,不提交form
		wideWord: false,	// 一个汉字当一个字节
		validatorGroup: '8', // 指定本form组编码,默认为1, 多个验证组时使用
		submitButtonID: 'operatorSave', // 指定本form的submit按钮
		onError: function(msg) {
			dlf.fn_jNotifyMessage(msg, 'message', false, 5000, 'dw');
			return;
		}, 
		onSuccess: function() { 
			var str_msg = $('#hidOperatorMobile').val(),
				str_address = $.trim($('#txt_operatorAddress').val()),
				n_checkGroupLng = $('#operatorGroups input:checked').length;
			
			if ( str_msg != '' ) {
				dlf.fn_jNotifyMessage(str_msg, 'message', false, 3000);
				return;
			} else if ( n_checkGroupLng == 0 ) {
				dlf.fn_jNotifyMessage('请至少选择一个分组！', 'message', false, 3000);
				return;
			} else {
				if ( str_address.length > 0 ) {
					if ( !/^[a-zA-Z0-9\u4e00-\u9fa5]+$/.test(str_address) ) {
						dlf.fn_jNotifyMessage('操作员地址只能由汉字、数字、英文组成！', 'message', false, 3000);
						return;
					}
				}
				dlf.fn_saveOperator();
			}
		}
	});
	$('#txt_operatorMobile').formValidator({validatorGroup: '8'}).regexValidator({regExp: 'owner_mobile', dataType: 'enum', onError: '操作员手机号输入不合法，请重新输入！'});
	$('#txt_operatorName').formValidator({validatorGroup: '8'}).inputValidator({max: 20, onError: '操作员姓名最多可输入20个汉字或字符！'}).regexValidator({regExp: 'c_name', dataType: 'enum', onError: '操作员姓名只能由汉字、数字、英文组成！'});
	
	$('#txt_operatorEmail').formValidator({empty:true, validatorGroup: '8'}).inputValidator({max: 50, onError: '操作员邮箱最多可输入50个字符！'}).regexValidator({regExp: 'email', dataType: 'enum', onError: "操作员邮箱输入不合法，请重新输入！"});  // 联系人email
	
	/**
	* 乘客进行验证
	*/
	$.formValidator.initConfig({
		formID: 'addPassengerForm', //指定from的ID 编号
		debug: true, // 指定调试模式,不提交form
		validatorGroup: '10', // 指定本form组编码,默认为1, 多个验证组时使用
		submitButtonID: 'passengerSave', // 指定本form的submit按钮
		onError: function(msg) {
			dlf.fn_jNotifyMessage(msg, 'message', false, 5000, 'dw');
			return;
		}, 
		onSuccess: function() { 
			if ( $('#hidPassengerMobile').val() != '' ) {
				dlf.fn_jNotifyMessage('乘客手机号已存在。', 'message', false, 5000);
				return;
			} else {
				dlf.fn_savePassenger();
			}
		}
	});
	$('#txt_passengerName').formValidator({validatorGroup: '10'}).regexValidator({regExp: 'name', dataType: 'enum', onError: '乘客姓名不正确！'});
	$('#txt_passengerMobile').formValidator({validatorGroup: '10'}).regexValidator({regExp: 'owner_mobile', dataType: 'enum', onError: '乘客手机号不正确！'});
	
	/**
	* 消息推送进行验证
	*/
	$.formValidator.initConfig({
		formID: 'infoPushForm', //指定from的ID 编号
		debug: true, // 指定调试模式,不提交form
		validatorGroup: '11', // 指定本form组编码,默认为1, 多个验证组时使用
		submitButtonID: 'infoPushSave', // 指定本form的submit按钮
		onError: function(msg) {
			dlf.fn_jNotifyMessage(msg, 'message', false, 5000, 'dw');
			return;
		}, 
		onSuccess: function() { 
			dlf.fn_saveInfoPush();
		}
	});
	$('#text_infoPush').formValidator({validatorGroup: '11'}).inputValidator({min: 1, max: 256, onError: '消息内容最大长度是128个汉字！'});
	/**
	* 通知发布进行验证
	*/
	$.formValidator.initConfig({
		formID: 'notifyManageAddForm', //指定from的ID 编号
		debug: true, // 指定调试模式,不提交form
		validatorGroup: '13', // 指定本form组编码,默认为1, 多个验证组时使用
		submitButtonID: 'notifyManageSave', // 指定本form的submit按钮
		onError: function(msg) {
			dlf.fn_jNotifyMessage(msg, 'message', false, 5000, 'dw');
			return;
		}, 
		onSuccess: function() { 
			dlf.fn_notifyManageMsg();
		}
	});
	/**
	* 加载完成后，第一次发送switchcar请求
	*/
	if ( !dlf.fn_userType() ) {
		dlf.fn_getCarData('first');
	} else {
		$('.j_corpLeft').css('background-color', '#fff')
		// 点击查询按钮触发自动搜索功能	
		$('#autoSearch').unbind('click').click(function() {
			$('#txtautoComplete').autocomplete('search');
		});
		
		$('#txtautoComplete').unbind('blur').bind('blur', function() {
			var obj_this = $('#txtautoComplete'),
				str_val = obj_this.val();
				
			if ( str_val == '' ) {
				obj_this.val('请输入定位器名称或号码').addClass('gray');
			}
		}).unbind('focus').bind('focus', function() {	// 获得焦点 隐藏tip
			var obj_this = $('#txtautoComplete'),
				str_val = obj_this.val();
				
			if ( str_val == '请输入定位器名称或号码' ) {
				obj_this.val('').removeClass('gray');
			}
		});
		
		$('#carCount').parent().addClass('currentTNum');
		dlf.fn_corpGetCarData();
		$('#corpTree').data('ftree', true);
	}
	
	$('#txtautoComplete').val('');	// 清空autocomplete搜索框
	/*=====================================*/
	var obj_addOperator = $('#addOperator');
	// 新增操作员 单击事件
	obj_addOperator.unbind('click').bind('click', function() {
		$('.operatorfieldset input, textarea').val('');
		$('#txt_operatorMobile').removeData('oldmobile');
		$('#hidOperatorId').val('');
		fn_getGroupData('add');	// 初始化分组
		dlf.fn_onInputBlur();	// 操作员手机号事件侦听
		$('#addOperatorDialog').dialog('option', 'title', '新增操作员').dialog( "open" );
	});
	// 新增初始化dialog
	$('#addOperatorDialog').dialog({
		autoOpen: false,
		width: 430,
		modal: true,
		resizable: false,
		close: function( event, ui ) {
			dlf.fn_closeJNotifyMsg('#jNotifyMessage');
		}
	});
	/*================================*/
	var obj_addPassenger = $('#addPassenger');
	// 新增乘客 单击事件
	obj_addPassenger.unbind('click').bind('click', function() {
		dlf.fn_closeJNotifyMsg('#jNotifyMessage');
		$('.passengerfieldset input, textarea').val('');
		$('#txt_passengerMobile').removeData('oldmobile');
		$('#hidPassengerId').val('');
		dlf.fn_onInputBlur();	// 乘客手机号事件侦听
		$('#addPassengerDialog').attr('title', '新增乘客').dialog('option', 'title', '新增乘客').dialog( "open" );
	});
	// 新增初始化dialog
	$('#addPassengerDialog').dialog({
		autoOpen: false,
		height: 300,
		width: 400,
		modal: true,
		resizable: false
	});
	//窗口最大最小化事件声明
    $('.j_hosBtn').unbind('click').click(function (event) {
        var obj_elem = $(this), 
			obj_content = $(this).parent().next(),
			obj_wrapper = $(this).parent().parent(),
			n_bodyHeight = $('.j_body').height(),
			n_wrapperTop = obj_wrapper.offset().top;
		
        if ( obj_elem.hasClass('min') ) {
            obj_elem.removeClass('min').addClass('max').attr('title', 'Expand');
            obj_content.hide();
			obj_wrapper.css('height', 34);
        } else if ( obj_elem.hasClass('max') ) {
            obj_elem.removeClass('max').addClass('min').attr('title', 'Retract');
            obj_content.show();
			obj_wrapper.css('height', 493);
			
			if ( n_wrapperTop + 493 > n_bodyHeight ) {
				obj_wrapper.css('top', n_bodyHeight - 500);
			}
        }
    });
	// 轨迹查询停留点图标事件、告警提示列表图标事件
	$('.j_alarmPanelCon').unbind('mouseover mouseout click').bind('mouseover', function() {
		var b_panel = $('.j_alarmPanel').is(':visible'),
			obj_arrowIcon = $('.j_alarmArrowClick');
		
		if ( b_panel ) {
			obj_arrowIcon.css('backgroundPosition', '-45px -29px').attr('title', '隐藏');
		} else {	// 关闭面板 鼠标移上去效果
			obj_arrowIcon.css('backgroundPosition', '-38px -29px').attr('title', '显示');
		}
	}).bind('mouseout', function() {
		var b_panel = $('.j_alarmPanel').is(':visible'),
			obj_arrowIcon = $('.j_alarmArrowClick');
		
		if ( b_panel ) {
			obj_arrowIcon.css('backgroundPosition', '-20px -29px');
		} else {
			obj_arrowIcon.css('backgroundPosition', '-29px -29px');
		}
	}).bind('click', function() {
		var obj_panel = $('.j_alarmPanel'),
			obj_arrowCon = $('.j_alarmPanelCon'),
			obj_arrowIcon = $('.j_alarmArrowClick'),
			b_panel = obj_panel.is(':visible'),
			n_windowWidth = $(window).width(),
			n_alarmIconLeft = n_windowWidth - 417;
		
		if ( n_windowWidth < 1024 ) {
			n_windowWidth = 1024;
			n_alarmIconLeft = 609;
		}
		if ( b_panel ) {
			obj_panel.hide();
			n_alarmIconLeft = n_windowWidth - 18;
			obj_arrowIcon.css('backgroundPosition', '-6px -29px');
		} else {
			obj_panel.show();
			obj_arrowIcon.css('backgroundPosition', '-20px -29px');
		}
		obj_arrowCon.css({'left': n_alarmIconLeft});
	});
	// 告警信息提示的关闭按钮
	$('.j_closeAlarm').unbind('click').bind('click', function() {
		dlf.fn_closeAlarmPanel();
	});
	
	//题栏切换
	$('#topShowIcon').toggle(
		function () {
			$('#top').hide();
			dlf.resetPanelDisplay();
			$('#topShowIcon').css('top', '36px').addClass('topShowIcon_hover');
		},
		function () {
			dlf.resetPanelDisplay(1);
			$('#topShowIcon').css('top', '158px').removeClass('topShowIcon_hover');		
		}
	);
	//终端列表切换
	$('#leftPanelShowIcon').toggle(
		function () {
			$('#left, #corpLeft').hide();
			dlf.resetPanelDisplay();
			$('#leftPanelShowIcon').css('left', '0px').addClass('leftPanelShowIcon_hover');
		},
		function () {
			dlf.resetPanelDisplay(0);
			$('#leftPanelShowIcon').css('left', '247px').removeClass('leftPanelShowIcon_hover');
		}
	);
});

function fn_modiyListPanelPosition() {
	var obj_delayPanel = $('.j_delayPanel'),
		b_delayPanel = obj_delayPanel.is(':visible'),
		obj_alarmPanel = $('.j_alarmPanel'),
		b_alarmPanel = obj_alarmPanel.is(':visible'),
		n_tempWindowWidth = $(window).width(),
		n_delayLeft = n_tempWindowWidth - 550,
		n_delayIconLeft = n_delayLeft - 17,
		n_alarmLeft = n_tempWindowWidth - 400,
		n_alarmIconLeft = n_alarmLeft - 17;
	
	
	if ( n_tempWindowWidth < 1024 ) {
		n_trackLeft = 40;
		n_delayLeft = 474;
		n_delayIconLeft = 458;
		n_alarmLeft = 623;
		n_alarmIconLeft = 609;
		n_tempWindowWidth = 896;
	}
	if ( !b_delayPanel ) {
		n_delayIconLeft = n_tempWindowWidth - 17;
	}
	if ( !b_alarmPanel ) {
		n_alarmIconLeft = n_tempWindowWidth - 17;
	}
	obj_delayPanel.css({'left': n_delayLeft});
	$('.j_disPanelCon').css({'left': n_delayIconLeft});
	obj_alarmPanel.css({'left': n_alarmLeft});
	$('.j_alarmPanelCon').css({'left': n_alarmIconLeft});
}
