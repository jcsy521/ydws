/*
*终端设置相关操作方法
*/
var arr_slide = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9];
(function () {

/**
* 终端参数设置初始化
*/
window.dlf.fn_initTerminal = function() {
	dlf.fn_lockScreen(); // 添加页面遮罩
	$('#terminalWrapper').css({'left': '40%', 'top': '20%'}).show(); // 显示终端设置dialog	
	dlf.fn_initTerminalWR(); // 初始化加载参数
	dlf.fn_onInputBlur();	// input的blur事件初始化
	
	$('.j_trace').unbind('click').bind('click', function() {	// 轨迹上报开启状态：可以编辑上报间隔  反之不能编辑
		var obj_this = $(this),
			obj_freq = $('#t_freq'),
			str_val = obj_this.val(),
			str_oldVal = $('#freq').attr('t_val');
			
		if ( str_val == 0 ) {
			str_oldVal = str_oldVal=='0'?'':str_oldVal;
			obj_freq.val(str_oldVal);
			obj_freq.attr('disabled', true);
		} else {
			$('#t_freq').attr('disabled', false);
		}
	});
}

/**
* 查询最新终端参数
*/
window.dlf.fn_initTerminalWR = function () {
	dlf.fn_lockContent($('.terminalContent')); // 添加内容区域的遮罩
	dlf.fn_jNotifyMessage('终端设置查询中' + WAITIMG , 'message', true); 
	$.get_(TERMINAL_URL, '', function (data) {  
		if (data.status == 0) {	
			var obj_data = data.car_sets,
				n_whitelistLenth = 0,
				n_whitelistTip = 0;
				
			for(var param in obj_data) {
				var str_val = obj_data[param];
				
				if ( param ) {
					if ( param == 'trace' || param == 'cellid_status' ) {	// 单选按钮: 轨迹上报、基站定位
						if ( param == 'trace' ) {	// 如果轨迹上报为关闭状态  上报间隔不可编辑
							if ( str_val == 0 ) {
								$('#t_freq').attr('disabled', true);
							} else {
								$('#t_freq').attr('disabled', false);
							}
						}
						$('#tr_' + param + str_val ).attr('checked', 'checked'); 
					} else if ( param == 'white_list' ) {	// 白名单
						n_whitelistLenth = str_val.length;
						$('.j_white_list input[type=text]').val('');	// 先清空白名单
						$('.j_white_list').attr('t_val', '');
						for ( var x = 0; x < n_whitelistLenth; x++ ) {	// 遍历所有白名单并填充数据
							var str_name = param  + '_' + (x+1),
								obj_whitelist = $('#t_' + str_name),
								obj_oriWhitelist = $('#' + str_name),
								str_value = str_val[x];
							obj_whitelist.val(str_value);
							obj_oriWhitelist.attr('t_val', str_value);					
						}
					} else if ( param == 'vibl' || param == 'freq' || param == 'vibchk' ) {		// 下拉列表：震动灵敏度、振动频率、上报间隔
						$('#t_' + param).val(str_val);
					} else {
						if ( param == 'alias' || param == 'cnum' ) {	// 终端别名、车牌号
							$('#t_' + param ).val(str_val);
						} else if ( param == 'white_pop' ) {	// 白名单弹出框
							n_whitelistTip = str_val;
						} else {
							$('#t_' + param ).html(str_val);
						}
					}
					$('#' + param ).attr('t_val', str_val);	// 将每个终端参数对应值保存在t_val中
				}
			}
			if ( n_whitelistLenth <= 1 && n_whitelistTip == 0 ) {	// 白名单提示 没有设置白名单一直提示
				dlf.fn_showNotice();
			} else {
				$('#whitelistPopWrapper').hide();
			}
			dlf.fn_updateAlias();	// 更新最新的终端别名
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
* 保存终端参数操作
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
			
		if ( str_newVal != str_oldVal ) {	// 判断参数是否有修改
			if ( str_class.search('j_input') != -1 ) {	// 终端别名、车牌号、白名单
				if ( str_class.search('j_whitelist') != -1 ) {	// 白名单 [车主手机号,白名单1,白名单2,...]
					var str_whitelist1 = $('#t_white_list_1').val();	// 车主手机号
						
					if ( str_newVal != '' ) { // 如果有白名单
						str_newVal = [str_whitelist1, str_newVal];
					} else {
						str_newVal = [str_whitelist1];
					}
				}
			}
			obj_terminalData[str_key] = str_newVal;
		}	
	});
	for(var param in obj_terminalData) {	// 修改项的数目
		n_num = n_num +1;
	}
	
	if ( n_num != 0 ) {	// 如果有修改向后台发送数据,否则提示无任何修改
		dlf.fn_jsonPut(TERMINAL_URL, obj_terminalData, 'terminal', '终端参数保存中');
	} else {
		dlf.fn_jNotifyMessage('您未做任何修改！', 'message', false, 4000); // 查询状态不正确,错误提示
		dlf.fn_unLockContent(); // 清除内容区域的遮罩
	}
}
/**
* pop框位置随着wrapper的改变而改变
*/
window.dlf.fn_resizeWhitePop = function() {
	var obj_terminalWrapperOffset = $('#terminalWrapper').offset(),
		obj_whitePop = $('#whitelistPopWrapper'),
		f_warpperStatus = !obj_whitePop.is(':hidden'),
		n_left = obj_terminalWrapperOffset.left + 380,
		n_top =  obj_terminalWrapperOffset.top + 200 ;
		
	if ( f_warpperStatus ) {
		obj_whitePop.css({left: n_left, top: n_top});
	}
}
})();
