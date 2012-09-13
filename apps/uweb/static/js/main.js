/*
*主页面方法
*/

(function () {
// 个人信息框 
window.dlf.fn_personalData = function() {
	dlf.fn_lockScreen(); // 添加页面遮罩
	$('#personalWrapper').css({'left': '40%', 'top': '22%'}).show();
	// 获取用户数据
	dlf.fn_jNotifyMessage('用户信息查询中...<img src="/static/images/blue-wait.gif" />', 'message', true); 
	dlf.fn_lockContent($('.personalContent')); // 添加内容区域的遮罩
	$.get_(PERSON_URL, '', function (data) {
		if ( data.status == 0 ) {
			var obj_data = data.details,
				str_name = obj_data.name,
				str_phone = obj_data.mobile,
				str_address = obj_data.address,
				str_email = obj_data.email,
				str_remark = obj_data.remark;
			$('#name').val(str_name).data('name', str_name);
			$('#phone').val(str_phone).data('phone', str_phone);
			$('#address').val(str_address).data('address', str_address);
			$('#email').val(str_email).data('email', str_email);
			$('#remark').val(str_remark).data('remark', str_remark);
			dlf.fn_closeJNotifyMsg('#jNotifyMessage'); // 关闭消息提示
		} else if ( data.status == 201 ) {
			dlf.fn_showBusinessTip();
		} else { 
			dlf.fn_jNotifyMessage(data.message, 'message'); // 查询状态不正确,错误提示
		}
		dlf.fn_unLockContent(); // 清除内容区域的遮罩	
	}, 
	function (XMLHttpRequest, textStatus, errorThrown) {
		dlf.fn_serverError(XMLHttpRequest);
	});
}

// 个人信息保存 
window.dlf.fn_personalSave = function() { 
	dlf.fn_lockContent($('.personalContent')); // 添加内容区域的遮罩	
	var f_warpperStatus = !$('#personalWrapper').is(':hidden');
	var obj_personalData = {};
	$('.j_personal').each(function(index, dom) {
		var obj_input = $(dom),
			str_val = obj_input.val(),
			str_id = obj_input.attr('id'),
			str_data = $('#'+str_id).data(str_id);
		if ( str_val != str_data ) {
			obj_personalData[str_id] = str_val;
		}
	});
	dlf.fn_jsonPut(PERSON_URL, obj_personalData, 'personal', '个人资料保存中');
}

//  修改密码框显示
window.dlf.fn_changePwd = function() {
	dlf.fn_lockScreen(); // 添加页面遮罩
	$('#pwdWrapper').css({'left': '38%', 'top': '22%'}).show();
	$('#pwdWrapper input[type=password]').val('');// 清除文本框数据
}
// 短息通知
window.dlf.fn_initSMSParams = function() {
	dlf.fn_lockScreen(); // 添加页面遮罩
	$('#smsWrapper').css({'left': '38%', 'top': '22%'}).show();
	// get smsoption
	$.get_(SMS_URL, '', function(data) {
		if ( data.status == 0 ) {
			var obj_data = data.sms_options;
			for(var param in obj_data) { 
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
		} else if ( data.status == 201 ) {
			dlf.fn_showBusinessTip();
		} else { 
			dlf.fn_jNotifyMessage(data.message, 'message'); // 查询状态不正确,错误提示
		}
		dlf.fn_unLockContent(); // 清除内容区域的遮罩	
	});
	$('#smsNoticeSave').unbind('click').bind('click', function() {
		dlf.fn_saveSMSOption();
	});
}
window.dlf.fn_saveSMSOption = function() {
	var obj_checkbox = $('.j_checkbox'),
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
	dlf.fn_jsonPut(SMS_URL, obj_smsData, 'sms', '短信告警参数保存中...');
}
window.dlf.fn_bindcheckbox = function(obj_checkbox) {
	obj_checkbox.bind('mouseover', function() {
		$(this).addClass('sp_xjCheckBox_H');
	}).bind('mouseout', function() {
		$(this).removeClass('sp_xjCheckBox_H').removeClass('sp_xjCheckBox_C');
	})
}
// 用户点击退出按钮 
window.dlf.fn_exit = function() {
	if ( confirm('您确定退出本系统吗？') ) {
		window.location.href = '/logout'; 
	}
}
})();

// 当用户窗口改变时,地图做相应调整
window.onresize = function () {
	setTimeout (function () {
		// 调整页面大小
		var n_windowHeight = $(window).height(), 
			n_windowWidth = $(window).width(),
			//str_infoStatus = $('#infoStatus').attr('status'), // 车辆信息框是否显示状态
			n_mapHeight = n_windowHeight - 164,
			n_trackLeft = ( n_windowWidth - 1028 )/2,
			n_banner = n_windowWidth - 247,
			n_mainContent = n_windowHeight - 104;
		if ( $.browser.msie ) { // 根据浏览器不同调整页面部分元素大小 
			n_banner = n_windowWidth - 249;
		}
		$('#banner').css('width', n_banner); // banner width
		$('#top, #main').css('width', n_windowWidth);
		$('#main').css('height', n_windowHeight - 123 );
		$('#left, #right').css('height', n_windowHeight - 128 );	// 左右栏高度
		$('#right, #navi, #mapObj, #trackHeader').css('width', n_windowWidth - 253);	// 右侧宽度
		$('.trackPos').css('padding-left', n_trackLeft); // 轨迹查询条件 位置调整
		$('#mapObj').css('height', n_mapHeight);
		// 动态调整遮罩层
		var f_layer = $('.j_body').data('layer');
		if ( f_layer ) { 
			dlf.fn_lockScreen();
		}
	}, 25);
}
// 页面加载完成后进行加载地图
$(function () {
	$.ajaxSetup({ cache: false }); // 不保存缓存
	// 屏蔽鼠标右键相关功能
    $(document).bind('contextmenu', function (e) {
        return false;
    });
	// 调整页面大小
	var n_windowHeight = $(window).height(),
		n_windowWidth = $(window).width(),
		n_mapHeight = n_windowHeight - 164,
		n_trackLeft = ( n_windowWidth - 1028 )/2,
		n_banner = n_windowWidth - 247,
		obj_track = $('#trackHeader');
	if ( $.browser.msie ) { // 根据浏览器不同调整页面部分元素大小 
		n_banner = n_windowWidth - 249;
	}
	$('#banner').css('width',  n_banner); // banner width
	$('#top, #main').css('width', n_windowWidth);
	$('#main').css('height', n_windowHeight - 123); // 内容域的高度
	$('#left, #right').css('height', n_windowHeight - 128 );	// 左右栏高度
	$('#right, #navi, #mapObj, #trackHeader').css('width', n_windowWidth - 253);	// 右侧宽度
	$('.trackPos').css('padding-left', n_trackLeft); // 轨迹查询条件 位置调整
	$('#mapObj').css('height', n_mapHeight);
	// 加载ABCMAP
	dlf.fn_loadMap();
	
	// 页面的点击事件分流处理
	$('.j_click').click(function(event) {
		var str_id = event.currentTarget.id, 
			n_carNum = $('#carList li').length,
			str_trackStatus = $('#trackHeader').css('display');			
		// 检测当前是否有车辆信息
		if ( n_carNum <= 0 ){
			if ( str_id != 'personalData' && str_id != 'changePwd' && str_id != 'infoStatus') {
				// 没有绑定车辆
				dlf.fn_showTerminalMsgWrp();
				return false;
			}
		}
		if ( str_trackStatus != 'none' && str_id != 'infoStatus' ) {
			if ( str_id == 'track' ) {
				return;
			}
			dlf.fn_closeTrackWindow();	// 关闭轨迹查询
		}
		$('#terminalMsgWrapper').hide();
		switch (str_id) {
			case 'personalData': //  个人资料 
				dlf.fn_personalData();
				break;
			case 'changePwd': // 修改密码
				dlf.fn_changePwd();
				break;
			case 'terminal': // 参数设置
				dlf.fn_initTerminal();
				break;
			case 'realtime': // 实时查询
				dlf.fn_currentQuery();
				break;
			case 'defend': // 设防撤防
				dlf.fn_defendQuery();
				break;
			case 'track': // 轨迹查询
				dlf.fn_initTrack();
				break;
		}
	});
	
	dlf.fn_closeWrapper(); //吹出框关闭事件
	// 弹出窗口
	$('.j_drag').draggable({handle: 'h2', containment: 'body',
		drag: function(event, ui) {
			var f_conStatus = !$('#jContentLock').is(':hidden');
			if ( f_conStatus ) {
				dlf.fn_lockContent($($(this).children().eq(1)));
			}
		},
		stop: function(event, ui) {
			if ( ui.position.top < 0 ) {
				$(this).css('top', 0);
			}
	}});
	// params input css 
	$('#bListR input[type=text]').focus(function() {
		$(this).addClass('bListR_text_mouseFocus');
	}).blur(function() {
		$(this).removeClass('bListR_text_mouseFocus');
	});
	
	dlf.fn_setItemMouseStatus($('.j_save'), 'pointer', new Array('bc', 'bc2', 'bc'));	// 保存按钮鼠标滑过样式
	
	// 个人信息的验证
	$.formValidator.initConfig({
		formID: 'personalForm', //指定from的ID 编号
		debug: true, // 指定调试模式,不提交form
		submitButtonID: 'personalSave', // 指定本form的submit按钮
		onError: function(msg) { 
			dlf.fn_jNotifyMessage(msg, 'message', true); 
		}, 
		onSuccess: function() { 
			dlf.fn_personalSave();
		}
	});
	$('#name').formValidator().inputValidator({max: 11, onError: '车主姓名过长，请重新输入！'}).regexValidator({regExp: 'name', dataType: 'enum', onError: "车主姓名只能是由数字、英文、下划线或中文组成！"});  // 别名;
	$('#txtAddress').formValidator().inputValidator({max: 255, onError: '地址过长，请重新输入！'});
	$('#email').formValidator({empty:true}).inputValidator({max: 255, onError: '你输入的邮箱长度非法,请确认！'}).regexValidator({regExp: 'email', dataType: 'enum', onError: '你输入的邮箱格式不正确！'});
	$('#corporation').formValidator().inputValidator({max: 255, onError: '公司名称过长，请重新输入！'});
	$('#remark').formValidator().inputValidator({max: 255, onError: '备注过长，请重新输入！'});
	// 密码进行验证
	$.formValidator.initConfig({
		formID: 'pwdForm', //指定from的ID 编号
		debug: true, // 指定调试模式,不提交form
		validatorGroup: '2', // 指定本form组编码,默认为1, 多个验证组时使用
		submitButtonID: 'pwdSave', // 指定本form的submit按钮
		onError: function(msg) { 
			dlf.fn_jNotifyMessage(msg, 'message', true); 
		}, 
		onSuccess: function() { 
			var obj_pwd = {'old_password' : $("#oldPwd").val(), 
						   'new_password' : $("#newPwd").val() 
						  }; 
			//提交服务器
			dlf.fn_jsonPut(PWD_URL, obj_pwd, 'pwd', '密码保存中');
		}
	});
	$('#oldPwd').formValidator({validatorGroup: '2'}).inputValidator({min: 1, onError: '密码不能为空，请重新输入！'});
	$('#newPwd').formValidator({validatorGroup: '2'}).inputValidator({min: 1, onError: '密码不能为空，请重新输入！'});
	$('#newPwd2').formValidator({validatorGroup: '2'}).inputValidator({min: 1, onError: '重复密码不能为空，请重新输入！'}).compareValidator({desID: 'newPwd', operateor: '=', datatype: 'number', onError: '两次密码不一致，请重新输入！'});
	// 终端参数的验证
	$.formValidator.initConfig({
		formID: 'terminalForm', //指定from的ID 编号
		debug: true, // 指定调试模式,不提交form
		validatorGroup: '3', // 指定本form组编码,默认为1, 多个验证组时使用
		submitButtonID: 'terminalSave', // 指定本form的submit按钮
		onError: function(msg) {
			dlf.fn_jNotifyMessage(msg, 'message', false, 4000); 
		}, 
		onSuccess: function() { 
			dlf.fn_baseSave();	// put请求
		}
	});
	$('#t_freq').formValidator({empty:true, validatorGroup: '3'}).inputValidator({max: 4, onError: '上报频率最大长度为4位数字！'}).regexValidator({regExp: 'freq', dataType: 'enum', onError: '您设置的上报频率不正确，范围(15-3600秒)！'});
	$('#t_pulse').formValidator({validatorGroup: '3'}).inputValidator({max: 4, onError: '心跳时间最大长度为4位数字！'}).regexValidator({regExp: 'pulse', dataType: 'enum', onError: '您设置的终端的心跳时间不正确，范围(1-1800秒)！'});;
	
	$('#t_white_list_2').formValidator({empty:true, validatorGroup: '3'}).inputValidator({max: 11, onError: '车主手机号最大长度是11位！'}).regexValidator({regExp: 'owner_mobile', dataType: 'enum', onError: '您设置的车主号码不正确，请输入正确的手机号！'}).compareValidator({desID: 't_white_list1', operateor: '!=', datatype: 'string', onError: '白名单2不能和白名单1相同'});;
	$('#t_cnum').formValidator({empty:true, validatorGroup: '3'}).inputValidator().regexValidator({regExp: 'licensenum', dataType: 'enum', onError: '车牌号输入错误，正确格式:汉字+大写字母+数字！', param:'g'}); // 区分大小写
	$('#t_alias').formValidator({empty:false, validatorGroup: '3'}).inputValidator({max: 12, onError: '终端别名最大长度为6位汉字，12位字符！'}).regexValidator({regExp: 'name', dataType: 'enum', onError: "终端别名只能是英文、数字、下划线或中文"});  // 别名
	$('#t_vibchk0').formValidator({validatorGroup: '3'}).inputValidator().regexValidator({regExp: 'vibchk', dataType: 'enum', onError: '配置在 X 秒时间内产生了Y次震动，才产生震动告警，范围(1:1--30:30)！'}); // 区分大小写
	$('#t_vibchk1').formValidator({validatorGroup: '3'}).inputValidator().regexValidator({regExp: 'vibchk', dataType: 'enum', onError: '配置在 X 秒时间内产生了Y次震动，才产生震动告警，范围(1:1--30:30)！'}); // 区分大小写
	// 如果没有车辆信息,提示用户
	var n_carNum = $('#carList li').length;
	if ( n_carNum > 0 ) {
		dlf.fn_switchCar($('#carList a').eq(0).attr('tid'), $($('#carList a')[0])); // 登录成功, 车辆列表切换
		dlf.fn_bindCarListItem();
	} else { // 提示添加终端车辆
		dlf.fn_showTerminalMsgWrp();
	}
})