/*
*定位器设置相关操作方法
*/
var arr_slide = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9];
(function () {

/**
* 定位器参数设置初始化
*/
window.dlf.fn_initTerminal = function() {
	$('.j_input input').val('');

	dlf.fn_dialogPosition('terminal');  // 显示终端设置dialog	
	dlf.fn_lockScreen(); // 添加页面遮罩
	dlf.fn_initTerminalWR(); // 初始化加载参数
	// dlf.fn_onInputBlur();	// input的blur事件初始化
		// 标签初始化
	$('.j_tabs').removeClass('currentTab');
	$('#rTab').addClass('currentTab');
	$('.j_terminalcontent').hide();//css('display', 'none');
	$('#terminalList0').show();//css('display', 'block');
	/* 选项卡
	$('.j_tabs').unbind('click').click(function() {
		var obj_this = $(this),
			n_index  = obj_this.index(), // 当前li索引
			str_className = $(this)[0].className;
			
		if ( str_className.search('currentTab') != -1 ) {
			return;
		}
		$('.j_tabs').removeClass('currentTab'); //移除所有选中样式
		$(this).addClass('currentTab'); // 选中样式
		$('#terminalList'+n_index).show().siblings().hide(); // 显示当前内容 隐藏其他内容
		if ( n_index == 1 ) {
			obj_this.css('border-right', '0px');
			dlf.fn_initSMSParams();
		} else if ( n_index == 0 ) {
			dlf.fn_initTerminalWR(); // 初始化加载参数
		} else {
			$('.j_weekList').data('weeks', []);	// 每次打开移除data数据
			obj_this.css('border-right', '0px');
			dlf.fn_searchData('alertSetting');
			dlf.fn_initAlertSetting('alertSetting');
		}
	});	*/
}

/**
* 查询最新定位器参数
*/
window.dlf.fn_initTerminalWR = function () {
	dlf.fn_lockContent($('.terminalContent')); // 添加内容区域的遮罩
	dlf.fn_jNotifyMessage('定位器设置查询中' + WAITIMG , 'message', true); 
	var str_cTid = dlf.fn_getCurrentTid(),
		obj_vibl = $('t_vibl'),
		obj_static_mode = $('#alert_freq_mode'),
		obj_auto = $('.j_auto'),
		obj_common = $('.j_common'),
		obj_t_alert_freq = $('#t_alert_freq'),
		obj_static_tip = $('.j_alert_freq_tip');

	obj_static_mode.unbind('change').bind('change', function() {
		var n_alert_freq = $(this).val(),
			str_oldVal = obj_t_alert_freq.data('alert_freq');
		
		if ( n_alert_freq == 1 ) {
			str_oldVal = str_oldVal == 0 ? 30 : str_oldVal;
			obj_t_alert_freq.val(str_oldVal);
			obj_auto.show();
			obj_common.hide();
		} else {
			obj_t_alert_freq.val('0');
			obj_common.show();
			obj_auto.hide();
		}
	});
	
	$.get_(TERMINAL_URL + '?tid=' + str_cTid , '', function (data) {  
		if (data.status == 0) {	
			var obj_data = data.car_sets,
				n_whitelistLenth = 0,
				n_whitelistTip = 0;
				
			for(var param in obj_data) {
				var str_val = obj_data[param];
				
				if ( param ) {
					if ( param == 'push_status' ) {	// 客户端通知
						$('#tr_' + param + str_val ).attr('checked', 'checked'); 
					} else if ( param == 'parking_defend' ) {	// 停车设防
						$('#tr_' + param + str_val ).attr('checked', 'checked'); 
					} else if ( param == 'mobile' ) {	// 定位器号码
						$('#t_mobile').html(str_val);
					} else if ( param == 'corp_cnum' ) {	// 车牌号
						$('#t_cnum').val(str_val);	
						dlf.fn_updateAlias();	// 修改定位器别名
					} else if ( param == 'vibl' ) {	// 震动灵敏度
						$('#t_' + param).val(str_val);	
					} else if ( param == 'alert_freq' ) {	// 告警工作模式
						str_val = parseInt(str_val)/60;
						var n_mode = 0;
						// 如果大于0：智能模式；等于0:普通模式
						if ( str_val > 0 ) {
							n_mode = 1;
							obj_auto.show();
							obj_common.hide();
						} else {
							obj_common.show();
							obj_auto.hide();
						}
						obj_static_mode.val(n_mode);
						obj_t_alert_freq.val(str_val).data('alert_freq', str_val);
					}
					$('#' + param ).attr('t_val', str_val);	// 将每个定位器参数对应值保存在t_val中
				}
			}
			dlf.fn_closeJNotifyMsg('#jNotifyMessage');
		} else if ( data.status == 201 ) {	// 业务变更
			dlf.fn_showBusinessTip();
		} else { // 查询状态不正确,错误提示
			dlf.fn_jNotifyMessage(data.message, 'message', false, 5000);
			dlf.fn_closeDialog();
		}
		dlf.fn_unLockContent(); // 清除内容区域的遮罩
	}, 
	function (XMLHttpRequest, textStatus, errorThrown) {
		dlf.fn_serverError(XMLHttpRequest);
	});
}

/**
* 显示白名单提示框
*/
window.dlf.fn_showNotice = function() {
	$('#whitelistPopWrapper').show();
	dlf.fn_resizeWhitePop();	//  pop框位置随着wrapper的改变而改变
	/** 
	* 点击“我知道了”
	*/
	$('.noticeRemeber').unbind('click').bind('click', function() {
		var obj_whitelistPop = { 'white_pop': 1 };
		dlf.fn_jsonPut(TERMINAL_URL, obj_whitelistPop, 'whitelistPop');
	});
	/**
	* whitelistPop 关闭按钮事件
	*/
	$('.noticeClose').click(function() {
		$('#whitelistPopWrapper').hide();
	});
}

/**
* 保存定位器参数操作
*/
window.dlf.fn_baseSave = function() {
	var str_key = $('#bListSet').attr('terminalkey'), 
		obj_terminalData = {},
		n_num = 0,
		obj_listVal = $('.j_ListVal');
		
	/**
	* 遍历 td 查找text、radio、select
	*/
	$.each(obj_listVal, function(index, dom) {
		var obj_this = $(this),
			str_key = obj_this.attr('id'),
			str_class = obj_this.attr('class'),
			str_oldVal = obj_this.attr('t_val'),  // 原始值
			obj_text = obj_this.children(),
			str_newVal = obj_text.val(); 	// text of value
		
		if ( str_class.search('j_radio') != -1 ) {	// 上报间隔、基站定位
			str_newVal = parseInt($(this).children('input:checked').val());
		}
		if ( str_key == 'alert_freq' ) {	// 单独处理 告警工作模式
			str_newVal = $('#t_alert_freq').val();
		}
		if ( str_newVal != str_oldVal ) {	// 判断参数是否有修改
			if ( str_class.search('j_input') != -1 ) {	// 定位器别名、车牌号、白名单
				if ( str_class.search('j_whitelist') != -1 ) {	// 白名单 [车主手机号,白名单1,白名单2,...]
					var str_whitelist1 = $('#t_white_list_1').val();	// 车主手机号
						
					str_key = 'white_list';
					if ( str_newVal != '' ) { // 如果有白名单
						str_newVal = [str_whitelist1, str_newVal];
					} else {
						str_newVal = [str_whitelist1];
					}
				}
			}
			if ( str_key == 'freq' || str_key == 'vibl' ) {
				str_newVal = parseInt(str_newVal);
			} else if ( str_key == 'alert_freq' ) {	// 告警工作模式
				str_newVal = parseInt(str_newVal*60);
			}
			obj_terminalData[str_key] = str_newVal;
		}
	});
	var n_terminalNum = 0;
	for(var param in obj_terminalData) {	// 修改项的数目
		if ( param == 'white_list' ) {
			n_terminalNum++;
		}
		n_num = n_num +1;
	}
	
	if ( n_num != 0 ) {	// 如果有修改向后台发送数据,否则提示无任何修改
		obj_terminalData.tid = dlf.fn_getCurrentTid();
		dlf.fn_jsonPut(TERMINAL_URL, obj_terminalData, 'terminal', '定位器参数保存中');
	} else {
		dlf.fn_jNotifyMessage('您未做任何修改。', 'message', false, 4000); // 查询状态不正确,错误提示
		dlf.fn_unLockContent(); // 清除内容区域的遮罩
	}
}

/**
* pop框位置随着wrapper的改变而改变
*/
window.dlf.fn_resizeWhitePop = function() {
	var obj_terminalWrapperOffset = $('#terminalWrapper').offset(),
		obj_whitePop = $('#whitelistPopWrapper'),
		b_warpperStatus = !obj_whitePop.is(':hidden'),
		n_left = obj_terminalWrapperOffset.left + 380,
		n_top =  obj_terminalWrapperOffset.top + 60 ;
		
	if ( b_warpperStatus ) {
		obj_whitePop.css({left: n_left, top: n_top});
	}
}
})();
