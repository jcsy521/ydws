/**
* 主页面方法
*/
(function () {
/**
* 我的资料初始化 
*/
window.dlf.fn_personalData = function() {
	dlf.fn_lockScreen(); // 添加页面遮罩
	$('#personalWrapper').css({'left': '40%', 'top': '22%'}).show();	// 我的资料dialog显示
	dlf.fn_onInputBlur();	// input的鼠标样式
	dlf.fn_jNotifyMessage('用户信息查询中' + WAITIMG, 'message', true); 
	dlf.fn_lockContent($('.personalContent')); // 添加内容区域的遮罩
	$.get_(PERSON_URL, '', function (data) {	// 获取最新的个人资料数据
		if ( data.status == 0 ) {
			var obj_data = data.profile,
				str_name = obj_data.name,
				str_newName = str_name;
				str_phone = obj_data.mobile,
				str_address = obj_data.address,
				str_email = obj_data.email,
				str_remark = obj_data.remark;
				
			$('#name').val(str_name).data('name', str_name);
			if ( str_name.length > 4 ) {	// 姓名长度大于4显示...
				str_newName = str_name.substr(0,4)+'...';
			}
			$('#spanWelcome').html('欢迎您，' + str_newName).attr('title', str_name);	// 更新主页用户名
			$('#phone').html(str_phone).data('phone', str_phone);
			$('#txtAddress').val(str_address).data('txtAddress', str_address);
			$('#email').val(str_email).data('email', str_email);
			$('#remark').val(str_remark).data('remark', str_remark);
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
	var f_warpperStatus = !$('#personalWrapper').is(':hidden'),
		n_num = 0,
		obj_personalData = {};
		
	$('.j_personal').each(function(index, dom) {
		var obj_input = $(dom),
			str_val = obj_input.val(),
			str_id = obj_input.attr('id'),
			str_data = $('#'+str_id).data(str_id);
			
		if ( str_val != str_data ) {
			if ( str_id == 'txtAddress' ) {
				obj_personalData.address = str_val;
			} else {
				obj_personalData[str_id] = str_val;
			}
		}
	});
	
	for(var param in obj_personalData) {	// 我的资料中修改项的个数
		n_num = n_num +1;
	}
	if ( n_num != 0 ) {	// 我的资料中如果有修改内容 ，向后台发送post请求，否则提示未做任何修改
		dlf.fn_jsonPut(PERSON_URL, obj_personalData, 'personal', '个人资料保存中');
	} else {
		dlf.fn_jNotifyMessage('您未做任何修改！', 'message', false, 4000); // 查询状态不正确,错误提示
		dlf.fn_unLockContent(); // 清除内容区域的遮罩
	}
}

/**
* 修改密码初始化
*/
window.dlf.fn_changePwd = function() {
	dlf.fn_lockScreen(); // 添加页面遮罩
	$('#pwdWrapper').css({'left': '38%', 'top': '22%'}).show();
	$('#pwdWrapper input[type=password]').val('');// 清除文本框数据
}

/**
* 短息通知
*/
window.dlf.fn_initSMSParams = function() {
	dlf.fn_lockScreen(); // 添加页面遮罩
	$('#smsWrapper').css({'left': '38%', 'top': '22%'}).show();
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
/**
* 用户点击退出按钮 
*/
window.dlf.fn_exit = function() {
	if ( confirm('您确定退出本系统吗？') ) {
		window.location.href = '/logout'; 
	}
}
})();

/**
* 当用户窗口改变时,地图做相应调整
*/
window.onresize = function () {
	setTimeout (function () {
		// 调整页面大小
		var n_windowHeight = $(window).height(), 
			n_windowWidth = $(window).width(),
			n_mapHeight = n_windowHeight - 161,
			n_trackLeft = ( n_windowWidth - 1028 )/2,
			n_banner = n_windowWidth - 249,
			n_mainContent = n_windowHeight - 104;
		if ( $.browser.msie ) { // 根据浏览器不同调整页面部分元素大小 
			n_banner = n_windowWidth - 249;
		}
		$('#banner').css('width', n_banner); // banner宽度设置
		$('#top, #main').css('width', n_windowWidth);
		$('#main').css('height', n_windowHeight - 123 );
		$('#left, #right').css('height', n_windowHeight - 123 );	// 左右栏高度
		$('#right, #navi, #mapObj, #trackHeader').css('width', n_windowWidth - 249);	// 右侧宽度
		$('.trackPos').css('padding-left', n_trackLeft); // 轨迹查询条件 位置调整
		$('#mapObj').css('height', n_mapHeight);
		dlf.fn_resizeWhitePop();	// 白名单未填提示
		
		var f_layer = $('.j_body').data('layer');
		if ( f_layer ) {
			dlf.fn_lockScreen();
		}
	}, 25);
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
		n_windowWidth = $(window).width(),
		n_mapHeight = n_windowHeight - 166,
		n_right = n_windowWidth - 249,
		n_trackLeft = ( n_windowWidth - 1028 )/2,
		n_banner = n_windowWidth - 249,
		obj_track = $('#trackHeader');
		
	if ( $.browser.msie ) { // 根据浏览器不同调整页面部分元素大小 
		n_banner = n_windowWidth - 249;
		n_right = n_windowWidth - 249;
	}
	$('#banner').css('width',  n_banner); // banner width
	$('#top, #main').css('width', n_windowWidth);
	$('#main').css('height', n_windowHeight - 123); // 内容域的高度
	$('#left, #right').css('height', n_windowHeight - 123 );	// 左右栏高度
	$('#right, #navi, #mapObj, #trackHeader').css('width', n_right);	// 右侧宽度
	$('.trackPos').css('padding-left', n_trackLeft); // 轨迹查询条件 位置调整
	$('#mapObj').css('height', n_mapHeight);
	
	dlf.fn_loadMap();	// 加载百度map
	
	/**
	* 页面的点击事件分流处理
	*/
	$('.j_click').click(function(event) {
		var str_id = event.currentTarget.id, 
			n_carNum = $('#carList li').length,
			str_trackStatus = $('#trackHeader').css('display');		
			
		if ( str_trackStatus != 'none' ) {	// 如果当前点击的不是轨迹按钮，先关闭轨迹查询
			if ( str_id == 'track' ) {
				return;
			}
			dlf.fn_closeTrackWindow();	// 关闭轨迹查询
		}
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
			case 'smsoption': // 短信设置
				dlf.fn_initSMSParams();
				break;
		}
	});
	
	dlf.fn_closeWrapper(); //吹出框关闭事件
	
	/**
	* dialogs 的拖动效果
	*/
	$('.j_drag').draggable({handle: '.wrapperTitle', containment: 'body',
		drag: function(event, ui) {
			var f_conStatus = !$('#jContentLock').is(':hidden'),
				str_currentId = event.target.id,
				obj_whitePop = $('#whitelistPopWrapper'),
				f_warpperStatus = !obj_whitePop.is(':hidden'),
				n_left = ui.position.left + 380,
				n_top = ui.position.top + 200;
				
			if ( f_conStatus ) {
				dlf.fn_lockContent($($(this).children().eq(1)));
			}
			
			if ( str_currentId == 'terminalWrapper' && f_warpperStatus ) {	// 终端设置dialog拖动时，白名单未填提示框跟着拖动
				obj_whitePop.css({left: n_left, top: n_top});
			}
		},
		stop: function(event, ui) {
			if ( ui.position.top < 0 ) {
				$(this).css('top', 0);
			}
	}});
	
	/**
	* 终端设置、个人资料、修改 input的焦点事件
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
		submitButtonID: 'personalSave', // 指定本form的submit按钮
		onError: function(msg) { 
			dlf.fn_jNotifyMessage(msg, 'message', false, 5000); 
		}, 
		onSuccess: function() { 
			dlf.fn_personalSave();
		}
	});
	
	$('#name').formValidator().inputValidator({max: 20, onError: '车主姓名最大长度是20个汉字或字符！'}).regexValidator({regExp: 'name', dataType: 'enum', onError: "车主姓名只能是由数字、英文、下划线或中文组成！"});  // 别名;
	$('#txtAddress').formValidator().inputValidator({max: 100, onError: '地址最大长度是100个汉字或字符！'});
	$('#email').formValidator({empty:true}).inputValidator({max: 100, onError: 'email最大长度是100个字符！'}).regexValidator({regExp: 'email', dataType: 'enum', onError: '您输入的邮箱格式不正确！'});
	$('#remark').formValidator().inputValidator({max: 100, onError: '备注最大长度是100个汉字或字符！'});
	
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
						  }; 
			//提交服务器
			dlf.fn_jsonPut(PWD_URL, obj_pwd, 'pwd', '密码保存中');
		}
	});
	
	$('#oldPwd').formValidator({validatorGroup: '2'}).inputValidator({min: 1, onError: '密码不能为空，请重新输入！'});
	$('#newPwd').formValidator({validatorGroup: '2'}).inputValidator({min: 1, onError: '密码不能为空，请重新输入！'});
	$('#newPwd2').formValidator({validatorGroup: '2'}).inputValidator({min: 1, onError: '重复密码不能为空，请重新输入！'}).compareValidator({desID: 'newPwd', operateor: '=', datatype: 'number', onError: '两次密码不一致，请重新输入！'});
	
	/** 
	* 终端参数的验证
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
			dlf.fn_baseSave();	// put请求
		}
	});
	
	$('#t_white_list_2').formValidator({empty:true, validatorGroup: '3'}).inputValidator({max: 14, onError: '车主手机号最大长度是11位！'}).regexValidator({regExp: 'owner_mobile', dataType: 'enum', onError: '您设置的白名单不正确，请输入正确的手机号！'}).compareValidator({desID: 't_white_list_1', operateor: '!=', datatype: 'string', onError: '白名单不能和车主号码相同！'});
	$('#t_cnum').formValidator({empty:true, validatorGroup: '3'}).inputValidator({max: 20, onError: '车牌号最大长度是20个汉字或字符！'}); // 区分大小写
	$('#t_alias').formValidator({empty:false, validatorGroup: '3'}).inputValidator({max: 20, onError: '终端别名最大长度是20个汉字或字符！'});  // 别名
	
	/**
	* 加载完成后，第一次发送switchcar请求
	*/
	var n_carNum = $('#carList li').length;
	if ( n_carNum > 0 ) {
		dlf.fn_switchCar($('#carList a').eq(0).attr('tid'), $($('#carList a')[0])); // 登录成功, 车辆列表切换
		dlf.fn_bindCarListItem();
	}
})