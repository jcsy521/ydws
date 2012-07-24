/*
*主页面方法
*/

(function () {

// 车辆详细信息显示隐藏
window.dlf.fn_infoStatus = function() {
	var str_img = 'bt_top.png', // 车辆详细信息右侧的箭头提示图片
		obj_map = $('#mapObj'),  // 地图对象
		obj_inList = $('#infoList'), // 信息框对象
		obj_infoStatus = $('#infoStatus'), // 车辆信息框对象
		str_status = obj_infoStatus.attr('status'), // 车辆信息框是否显示状态
		str_tmepSt = ''; // 状态的中间变量
		n_mapHeight = 0, //地图的高度
		n_ciHeight = 0,  // 车辆信息框的高度
		n_windowHeight = $(window).height(); 
	
	if ( str_status == 'show' ) {
		obj_inList.hide();
		str_tmepSt = 'hide';
		n_mapHeight = n_windowHeight - 141;
		n_ciHeight = 35;
		str_img = 'bt_top.png';
	} else {
		obj_inList.show();
		str_tmepSt = 'show';
		n_mapHeight = n_windowHeight - 231;
		n_ciHeight = 125;
		str_img = 'bt_bottom.png';
	}
	obj_map.css('height', n_mapHeight); // 调整地图的高度
	$('#carInfo').css('height', n_ciHeight); // 车辆信息框的高度
	obj_infoStatus.attr('status', str_tmepSt).attr('src', '/static/images/'+str_img);; // 车辆信息框状态
}

// 个人信息框 
window.dlf.fn_personalData = function() {
	dlf.fn_lockScreen(); // 添加页面遮罩
	$('#personalWrapper').css({'left': '38%', 'top': '22%'}).show();
	// 获取用户数据
	dlf.fn_jNotifyMessage('用户信息查询中...<img src="/static/images/blue-wait.gif" />', 'message', true); 
	dlf.fn_lockContent($('.personalContent')); // 添加内容区域的遮罩
	$.get_(PERSON_URL, '', function (data) {
		if ( data.status == 0 ) {
			var obj_data = data.details;
			$('#personalForm').data({'personalid': data.id});
			$('#name').val(obj_data.name);
			$('#phone').val(obj_data.mobile);
			$('#licenseNum').val(obj_data.cid);	// 车牌号
			$('#address').val(obj_data.address);
			$('#email').val(obj_data.email);
			$('#corporation').val(obj_data.corporation);
			$('#remark').val(obj_data.remark);
			dlf.fn_closeJNotifyMsg('#jNotifyMessage'); // 关闭消息提示
		} else { 
			dlf.fn_jNotifyMessage(data.message, 'error'); // 查询状态不正确,错误提示
		}	
		dlf.fn_unLockContent(); // 清除内容区域的遮罩	
	}, 
	function (XMLHttpRequest, textStatus, errorThrown) {
		dlf.fn_serverError(XMLHttpRequest);
	});
}

// 个人信息保存 
window.dlf.fn_personalSave = function(obj_personalData) { 
	dlf.fn_lockContent($('.personalContent')); // 添加内容区域的遮罩	
	var f_warpperStatus = !$('#personalWrapper').is(':hidden');
	dlf.fn_jsonPut(PERSON_URL, obj_personalData, 'personal', '个人资料保存中');
}

//  修改密码框显示
window.dlf.fn_changePwd = function() {
	dlf.fn_lockScreen(); // 添加页面遮罩
	$('#pwdWrapper').css({'left': '38%', 'top': '22%'}).show();
	$('#pwdWrapper input[type=password]').val('');// 清除文本框数据
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
			str_infoStatus = $('#infoStatus').attr('status'), // 车辆信息框是否显示状态
			n_mapHeight = n_windowHeight,
			n_mainContent = n_windowHeight - 104;
		// 根据车辆详细信息显示状态设置地图高度
		if ( str_infoStatus == 'show' ) {
			n_mapHeight =n_mainContent - 129;
		} else {
			n_mapHeight = n_mainContent - 35;
		}
		$('.main, #mainContent, .navi, .menumList, .carContainer').css('width', n_windowWidth);
		$('.mnNav').css('width', n_windowWidth-300); // 菜单宽度
		$('#trackHeader').css('margin-left', n_windowWidth/5); // 轨迹查询条件 位置调整
		$('#infoStatus').css('left', $('#infoTitle').width()/2);	
		$('#mapObj').css('height', n_mapHeight);
		$('.main, #mainContent').css('height', n_mainContent);
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
		n_mapHeight = n_windowHeight - 231;
	if ( $.browser.msie ) { // 根据浏览器不同调整页面部分元素大小 
		n_mapHeight = n_windowHeight - 231;
	}
	$('.main, #mainContent, .navi, .menumList, .carContainer').css('width', n_windowWidth);
	$('.mnNav').css('width', n_windowWidth-300); // 菜单宽度
	$('#trackHeader').css('margin-left', n_windowWidth/5); // 轨迹查询条件 位置调整
	$('#mapObj').css('height', n_mapHeight); // 地图高度
	$('#infoStatus').css('left', $('#infoTitle').width()/2); // 车辆信息标题的隐藏按钮位置
	$('.main, #mainContent').css('height', n_windowHeight - 104); // 内容域的高度
	// 加载ABCMAP
	dlf.fn_loadMap();
		
	// 车辆信息及车辆列表显示框状态初始化
	$('#infoStatus').attr('status', 'show');
	
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
		if ( str_trackStatus != 'none' ) {
			dlf.fn_closeTrackWindow();	// 关闭轨迹查询
		}
		$('#terminalMsgWrapper').hide();
		switch (str_id) {
			case 'infoStatus': // 车辆详细信息显示隐藏
				dlf.fn_infoStatus();
				break;
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
			case 'reboot': // 重启中断
				dlf.fn_reboot();
				break;
			case 'track': // 轨迹查询
				dlf.fn_initTrack();
				break;
		}
	});
	
	//菜单的mouseOver和mouseOut
	function fn_mouseOverOrOut(obj, isOver) {
		var str_src = '../static/images/',
			obj_currentImg = obj.children('img').eq(0),
			n_index =obj.parent().index()+1;
		if ( isOver ) {
			str_src =str_src + 'menuH' + n_index + '.png';
		} else {
			str_src =str_src + 'menu' + n_index + '.png';
		}
		obj_currentImg.attr('src', str_src);
	}
	
	// 导航菜单鼠标样式
	$('.menuNav .j_click').mouseover(function() {
		fn_mouseOverOrOut($(this), true);
	}).mouseout(function() {
		fn_mouseOverOrOut($(this), false);
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
	
	
	//选择车辆列表
	$('#carList li').click(function() {
		// 轨迹查询隐藏
		$('#trackHeader').hide();
		var obj_currentCar = $('#currentCar');
		obj_currentCar.html($(this).html());
		$('#carList').hide();
		var str_login = $(this).attr('clogin');
		if ( str_login == '1' ) {
			obj_currentCar.removeClass('carlogout').addClass('carlogin').attr('title', '在线');
		} else {
			obj_currentCar.removeClass('carlogin').addClass('carlogout').attr('title', '离线');
		}
	}).mouseover(function() {
		$('#carList').show();
	}).mouseout(function() {
		$('#carList').hide();
	});
	$('#carSet').click(function() {
		var status = $('#carList').css('display');
		if ( status == 'none' ) { 
			$('#carList').show();
		} else {
			$('#carList').hide();
		}
	});
	
	// 个人信息的验证
	$.formValidator.initConfig({
		formID: 'personalForm', //指定from的ID 编号
		debug: true, // 指定调试模式,不提交form
		submitButtonID: 'personalSave', // 指定本form的submit按钮
		onError: function(msg) { 
			dlf.fn_jNotifyMessage(msg, 'error', true); 
		}, 
		onSuccess: function() { 
			var obj_pFrom = $('#personalForm'), 
				obj_personalData = {
					'id': obj_pFrom.data('personalid'),
					'name': $('#name').val(),
					'mobile': $('#phone').val(),
					'address': $('#address').val(),
					'email': $('#email').val(),
					'corporation': $('#corporation').val(),
					'remark': $('#remark').val(),
					'cid': $('#licenseNum').val()
				};
			dlf.fn_personalSave(obj_personalData);
		}
	});
	$('#name').formValidator().inputValidator({max: 11, onError: '车主姓名过长，请重新输入！'});
	$('#address').formValidator().inputValidator({max: 255, onError: '地址过长，请重新输入！'});
	$('#email').formValidator().inputValidator({max: 255, onError: '你输入的邮箱长度非法,请确认！'}).regexValidator({regExp: 'email', dataType: 'enum', onError: '你输入的邮箱格式不正确！'});
	$('#corporation').formValidator().inputValidator({max: 255, onError: '公司名称过长，请重新输入！'});
	$('#remark').formValidator().inputValidator({max: 255, onError: '备注过长，请重新输入！'});
	$('#licenseNum').formValidator().inputValidator({max: 8, onError: '你输入的车牌号长度非法,请确认！'}).regexValidator({regExp: 'licensenum', dataType: 'enum', onError: '车牌号输入错误，正确格式:汉字+大写字母+数字', param:'g'}); // 区分大小写
	// 密码进行验证
	$.formValidator.initConfig({
		formID: 'pwdForm', //指定from的ID 编号
		debug: true, // 指定调试模式,不提交form
		validatorGroup: '2', // 指定本form组编码,默认为1, 多个验证组时使用
		submitButtonID: 'pwdSave', // 指定本form的submit按钮
		onError: function(msg) { 
			dlf.fn_jNotifyMessage(msg, 'error', true); 
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
	
	// 如果没有车辆信息,让用户进行新增绑定
	var n_carNum = $('#carList li').length;
	if ( n_carNum > 0 ) {
		dlf.fn_switchCar($('#carList li').eq(0).attr('tid'), $($('#carList li')[0])); // 登录成功, 车辆列表切换
		dlf.fn_bindCarListItem();
	} else { // 提示添加终端车辆
		dlf.fn_showTerminalMsgWrp();
	}
})