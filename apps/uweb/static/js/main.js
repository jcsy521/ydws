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
		n_ovHeight = 0, // 车辆列表的蓝色线的高度
		n_windowHeight = $(window).height(); 
	
	if ( str_status == 'show' ) {
		obj_inList.hide();
		str_tmepSt = 'hide';
		n_mapHeight = obj_map.height()+90;
		n_ciHeight = 35;
		str_img = 'bt_top.png';
		n_ovHeight = n_windowHeight - 125;
	} else {
		obj_inList.show();
		str_tmepSt = 'show';
		n_mapHeight = obj_map.height()-90;
		n_ciHeight = 125;
		str_img = 'bt_bottom.png';
		n_ovHeight = n_windowHeight - 215;
	}
	
	obj_map.css('height', n_mapHeight); // 调整地图的高度
	$('#carInfo').css('height', n_ciHeight); // 车辆信息框的高度
	$('#ovLine').css('height', n_ovHeight); // 车辆列表的蓝色线的高度
	obj_infoStatus.attr('status', str_tmepSt).attr('src', '/static/images/'+str_img);; // 车辆信息框状态
}

// 车辆列表显示隐藏
window.dlf.fn_listov = function() {
	var str_img = 'ov_right.png', // 车辆列表右侧的箭头提示图片
		obj_map = $('#mapObj'),  // 地图对象
		obj_carList = $('#mainCar'),  // 车辆列表框对象
		obj_con = $('#mainContent'), // 内容区域对象
		obj_ovLine = $('#ovLine'), // 车辆列表框的线对象
		obj_listov = $('#listov'), // 车辆列表框提示对象
		obj_infoTitle = $('#infoTitle'), // 车辆信息框标题对象
		obj_infoStatus = $('#infoStatus'), // 车辆信息框箭头对象
		obj_mapAndCon = $('#mapObj, #mainContent'), // 地图和内容对象
		str_status = obj_listov.attr('status'), // 车辆列表框是否显示状态
		str_tmepSt = ''; // 状态的中间变量
		n_mapWidth = 0, //地图的宽度
		n_conPos = 0,  // 内容区域定位值 left
		n_ovPos = 0, // 车辆列表框定位 left
		n_infoWidth = obj_infoTitle.width(), // 车辆信息框标题宽度
		n_statusWidth = $(window).width(),
		n_windowHeight = $(window).height();  
	
	if ( str_status == 'show' ) {
		obj_carList.hide();
		obj_ovLine.show();
		str_tmepSt = 'hide';
		str_img = 'ov_right.png';
		n_mapWidth = obj_map.width() + 189; // 地图目前宽度+左侧车辆列表宽度-10
		n_conPos = 0;
		n_ovPos = 10;
		n_infoWidth += 189;
		n_statusWidth -= 179;
	} else { 
		obj_carList.show();
		obj_ovLine.hide();
		str_tmepSt = 'show';
		str_img = 'ov_left.png';
		n_mapWidth = obj_map.width() - 189;
		n_conPos = 189;
		n_ovPos = 189;
		n_infoWidth -= 189;
		n_statusWidth -= 328;
	}
	
	obj_mapAndCon.css('width', n_mapWidth); // 地图和右侧内容区域宽度
	obj_con.css('left', n_conPos); // 地图定位
	obj_listov.css('left', n_ovPos).attr('status', str_tmepSt); // 箭头定位
	$('#listov img').attr('src', '/static/images/'+str_img); // 箭头图片
	obj_infoTitle.css('width', n_infoWidth); // 车辆信息框标题宽度
	obj_infoStatus.css('left', n_statusWidth);
	$('#infoList').css('width', n_infoWidth-38);
}

// 个人信息框 
window.dlf.fn_personalData = function() {
	dlf.fn_clearMapComponent(); //清除地图上的图形
	dlf.fn_lockScreen(); // 添加页面遮罩
	$('#personalWrapper').css({'left': '38%', 'top': '22%'}).show();
	// 获取用户数据
	dlf.fn_jNotifyMessage('用户信息查询中...<img src="/static/images/blue-wait.gif" />', 'message', true); 
	dlf.fn_lockContent($('.personalContent')); // 添加内容区域的遮罩
	
	$.get_(PERSON_URL, '', function (data) {
		if ( data.status == 0 ) {
			var obj_data = data.details;
			$('#personalForm').data({'personalid': data.id, 'uid': obj_data.uid});
			$('#name').val(obj_data.name);
			$('#phone').val(obj_data.mobile);
			$('#address').val(obj_data.address);
			$('#email').val(obj_data.email);
			$('#corporation').val(obj_data.corporation);
			$('#remark').val(obj_data.remark);
			dlf.fn_closeJNotifyMsg('#jNotifyMessage'); // 关闭消息提示
		} else { // 查询状态不正确,错误提示
			dlf.fn_jNotifyMessage(data.message, 'error');
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
	dlf.fn_clearMapComponent(); //清除地图上的图形
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
		var n_windowWidth = $(window).width(), 
			n_windowHeight = $(window).height(), 
			obj_infoTitle = $('#infoTitle'), 
			str_ovStatus = $('#listov').attr('status'), 
			str_infoStatus = $('#infoStatus').attr('status'), // 车辆信息框是否显示状态
			n_mapHeight = n_windowHeight,
			n_ovHeight = 0,
			n_conWidth = 0, 
			n_infoWidth = 0;
		
		// 根据车辆列表的显示状态设置地图宽度
		if ( str_ovStatus == 'show' ) {
			n_conWidth = n_windowWidth - 200;
			n_infoWidth = n_windowWidth - 200;
		} else {
			n_conWidth = n_windowWidth-10;
			n_infoWidth = n_windowWidth-10;
		}
		// 根据车辆详细信息显示状态设置地图高度
		if ( str_infoStatus == 'show' ) {
			n_mapHeight = n_windowHeight - 215;
			n_ovHeight = n_windowHeight - 215;
		} else {
			n_mapHeight = n_windowHeight - 125;
			n_ovHeight = n_windowHeight - 125;
		}
		$('.mnNavCenter').css('width', n_windowWidth-217);
		$('#mapObj, #mainContent').css('width', n_conWidth);
		obj_infoTitle.css('width', n_infoWidth);
		$('#infoStatus').css('left', n_infoWidth - 80);	
		$('.navi').css('width', n_windowWidth);
		$('#mapObj').css('height', n_mapHeight);
		$('.main').css('width', n_windowWidth);
		$('.main').css('height', n_windowHeight - 90);
		$('#mainCar').css('height', n_windowHeight - 90);
		$('.carContent').css('height', n_windowHeight - 119);
		$('#ovLine').css('height', n_ovHeight);
		$('#infoList').css('width', n_infoWidth-38);
		
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
	var n_windowWidth = $(window).width(), 
		n_windowHeight = $(window).height(),
		n_navWidth = n_windowWidth,
		n_mapWidth = n_windowWidth - 189,
		n_navCenterWidth = n_windowWidth - 217,
		n_infoWidth = n_windowWidth - 189,
		n_mapHeight = n_windowHeight - 215;
	
	if ( $.browser.msie ) { // 根据浏览器不同调整页面部分元素大小 
		n_navWidth = n_windowWidth,
		n_mapWidth = n_windowWidth - 190,
		n_infoWidth = n_windowWidth - 189,
		n_mapHeight = n_windowHeight - 220;
	}
	$('.mnNavCenter').css('width', n_navCenterWidth);
	$('#mapObj, #mainContent').css('width', n_mapWidth); // 地图宽度
	$('#mapObj').css('height', n_mapHeight); // 地图高度
	$('#infoTitle').css('width', n_infoWidth); // 车辆信息标题的宽度
	$('#infoStatus').css('left', $('#infoTitle').width() - 80); // 车辆信息标题的隐藏按钮位置
	$('.navi').css('width', n_navWidth); // 导航的宽度
	$('.main').css('width', n_windowWidth);
	$('.main').css('height', n_windowHeight - 90); // 内容域的高度
	$('#mainCar').css('height', n_windowHeight - 90); // 车辆列表的高度
	$('.carContent').css('height', n_windowHeight - 119); // 内容右侧的高度
	$('#ovLine').css('height', n_windowHeight - 215); // 车辆列表的蓝色线的高度
	
	// 加载ABCMAP
	dlf.fn_loadMap();
		
	// 车辆信息及车辆列表显示框状态初始化
	$('#infoStatus, #listov').attr('status', 'show');
	
	// 页面的点击事件分流处理
	$('.j_click').click(function(event) {
		var str_id = event.currentTarget.id, 
			n_carNum = $('#carList li').length;
		// 检测当前是否有车辆信息
		if ( n_carNum <= 0 ){
			if ( str_id != 'addCar' && str_id != 'personalData' && str_id != 'changePwd' && str_id != 'infoStatus' && str_id != 'listov' ) {
				// 没有绑定车辆
				dlf.fn_showTerminalMsgWrp();
				return false;
			}
		}
		$('#terminalMsgWrapper').hide();
		switch (str_id) {
			case 'infoStatus': // 车辆详细信息显示隐藏
				dlf.fn_infoStatus();
				break;
			case 'listov':  // 车辆列表信息显示隐藏
				dlf.fn_listov();
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
			case 'lock': // 解锁/开锁
				dlf.fn_lock();
				break;
			case 'reboot': // 重启中断
				dlf.fn_reboot();
				break;
			case 'addCar': // 添加终端
				dlf.fn_initTerminalList();
				break;
			/*
			case 'track': // 轨迹查询
				dlf.fn_initTrack();
				break;
			*/
		}
	});
	
	// 添加鼠标滑过 "远程操作" 导航样式
	$('.j_remoteMenu').mouseover(function() {
		$('#remoteWrapper').show();
		$(this).css({'color':'#000000', 'width': '103px', 'line-height': '20px'});
	}).mouseout(function() {
		var status = $('#remoteWrapper').css('display');
		if( status != 'none' ) {
			$('#remoteWrapper').hide();
		}
		$('.j_remoteMenu').css({'color':'#FFFFFF', 'width': '89px', 'line-height': '50px'});
	});
	
	$('.j_remoteMouse').mouseover(function() {
		$(this).addClass('rw_active').css('color', '#FFFFFF');
		$('.j_remoteMenu').addClass('mnHover').css({'color':'#000000', 'width': '103px', 'line-height': '20px'});
	}).mouseout(function() {
		$(this).removeClass('rw_active').css('color', '#B4B4B4');
		$('.j_remoteMenu').removeClass('mnHover').css({'color':'#FFFFFF', 'width': '89px', 'line-height': '50px'});
	});
	// 二级菜单样式
	$('#remoteWrapper').mouseover(function() {
		$('.j_remoteMenu').addClass('mnHover').css({'color':'#000000', 'width': '103px', 'line-height': '20px'});
		$(this).show();
	}).mouseout(function() {
		$('.j_remoteMenu').removeClass('mnHover').css({'color':'#FFFFFF', 'width': '89px', 'line-height': '50px'});
		$(this).hide();
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
	//车辆列表鼠标滑过样式
	$('#carList li').mouseover(function() {
		$(this).addClass('carListHover');
	}).mouseout(function() {
		$(this).removeClass('carListHover');
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
					'uid': obj_pFrom.data('uid'),
					'mobile': $('#phone').val(),
					'address': $('#address').val(),
					'email': $('#email').val(),
					'corporation': $('#corporation').val(),
					'remark': $('#remark').val()
				};
			dlf.fn_personalSave(obj_personalData);
		}
	});
	$('#name').formValidator().inputValidator({max: 11, onError: '车主姓名过长，请重新输入！'});
	$('#address').formValidator().inputValidator({max: 255, onError: '地址过长，请重新输入！'});
	$('#email').formValidator().inputValidator({max: 255, onError: '你输入的邮箱长度非法,请确认！'}).regexValidator({regExp: 'email', dataType: 'enum', onError: '你输入的邮箱格式不正确！'});
	$('#corporation').formValidator().inputValidator({max: 255, onError: '公司名称过长，请重新输入！'});
	$('#remark').formValidator().inputValidator({max: 255, onError: '备注过长，请重新输入！'});
	
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
		dlf.fn_switchCar($($('#carList li a')[0]).attr('tid'), $($('#carList li')[0])); // 登录成功, 车辆列表切换
		dlf.fn_bindCarListItem();
	} else { // 提示添加终端车辆
		dlf.fn_showTerminalMsgWrp();
	}
})