/*
*终端设置相关操作方法
*/

var arr_slide = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9];
(function () {
// 终端参数设置初始化页面
window.dlf.fn_initTerminal = function() {
	dlf.fn_lockScreen(); // 添加页面遮罩
	$('#terminalWrapper').css({'left': '40%', 'top': '20%'}).show(); // 显示终端设置窗口	
	dlf.fn_initTerminalWR(); // 初始化加载参数
	// 轨迹上报开启状态：可以编辑上报间隔  反之不能编辑
	$('.j_trace').unbind('click').bind('click', function() {
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
	// j_keyup : 只能输入数字
	dlf.fn_onkeyUp();
}
// 刷新终端参数、查询终端参数
window.dlf.fn_initTerminalWR = function () {
	// 获取参数数据
	dlf.fn_lockContent($('.terminalContent')); // 添加内容区域的遮罩
	// 获取用户数据
	dlf.fn_jNotifyMessage('终端设置查询中...<img src="/static/images/blue-wait.gif" />', 'message', true); 
	var str_url  =  TERMINAL_URL;
	// get request
	$.get_(str_url, '', function (data) {  
		if (data.status == 0) {	
			var obj_data = data.car_sets,
				n_whitelistLenth = 0,
				n_whitelistTip = 0;
			// for : key value
			for(var param in obj_data) {
				var str_val = obj_data[param];
				if ( param ) {
					if ( param == 'trace' || param == 'cellid_status' ) {	// 单选按钮
						// 如果轨迹上报为关闭状态  上报间隔不可编辑
						if ( param == 'trace' ) {
							if ( str_val == 0 ) {
								$('#t_freq').attr('disabled', true);
							} else {
								$('#t_freq').attr('disabled', false);
							}
						}
						$('#tr_' + param + str_val ).attr('checked', 'checked'); 	// radio value
					} else if ( param == 'white_list' ) {	// 白名单
						n_whitelistLenth = str_val.length;
						$('.j_white_list input[type=text]').val('');
						$('.j_white_list').attr('t_val', '');
						for ( var x = 0; x < n_whitelistLenth; x++ ) {
							var str_name = param  + '_' + (x+1),
								obj_whitelist = $('#t_' + str_name),
								obj_oriWhitelist = $('#' + str_name),
								str_value = str_val[x];
							obj_whitelist.val(str_value);	// whitelist
							obj_oriWhitelist.attr('t_val', str_value);	// save original value
							
						}
					} else if ( param == 'vibl' || param == 'freq' || param == 'vibchk' ) {		// 震动灵敏度   上报间隔
						$('#t_' + param).val(str_val);
					} else {
						if ( param == 'alias' || param == 'cnum' ) {
							$('#t_' + param ).val(str_val);	// other input value
						} else if ( param == 'white_pop' ) {
							n_whitelistTip = str_val;
						} else {
							$('#t_' + param ).html(str_val);	// other label value
						}
					}
					$('#' + param ).attr('t_val', str_val);	// save original value
				}
			}
			// 白名单提示 没有设置白名单&一直提示
			if ( n_whitelistLenth <= 1 && n_whitelistTip == 0 ) {
				dlf.fn_showNotice();
			} else {
				$('#whitelistPopWrapper').hide();
			}
			dlf.fn_updateAlias();
			dlf.fn_closeJNotifyMsg('#jNotifyMessage'); // 关闭消息提示
		} else if ( data.status == 201 ) {
			dlf.fn_showBusinessTip();
		} else { // 查询状态不正确,错误提示
			dlf.fn_jNotifyMessage(data.message, 'message', false, 5000);
			dlf.fn_closeDialog(); // 窗口关闭
		}
		dlf.fn_unLockContent(); // 清除内容区域的遮罩
	}, 
	function (XMLHttpRequest, textStatus, errorThrown) {
		dlf.fn_serverError(XMLHttpRequest);
	});
}
// 显示白名单提示框
window.dlf.fn_showNotice = function() {
	$('#whitelistPopWrapper').show();
	dlf.fn_resizeWhitePop();
	// 点击“我知道了”
	$('.noticeRemeber').unbind('click').bind('click', function() {
		var obj_whitelistPop = { 'white_pop': 1 };
		dlf.fn_jsonPut(TERMINAL_URL, obj_whitelistPop, 'whitelistPop');
	});
	$('.noticeClose').click(function() {
		$('#whitelistPopWrapper').hide();
	});
}
// 保存终端参数操作
window.dlf.fn_baseSave =function() {
	var f_warpperStatus = !$('#terminalWrapper').is(':hidden'), 
		str_key = $('#bListSet').attr('terminalkey'), 
		obj_terminalData = {},
		obj_listVal = $('.j_ListVal'); // td t_val 
	// 遍历 td 查找text和radio
	$.each(obj_listVal, function(index, dom) {
		var obj_this = $(this),
			str_key = obj_this.attr('id'),
			str_class = obj_this.attr('class'),
			str_whitelist1 = $('#t_white_list_1').val(),
			str_t_val = obj_this.attr('t_val'),  // 原始值
			obj_text = obj_this.children('input[type=text]'),
			obj_input = obj_text.eq(0),	// 文本框
			obj_input1 = obj_text.eq(1),	// 文本框1
			obj_radio = obj_this.children('input[type=radio][checked]').eq(0),	 // 单选按钮
			n_len = obj_radio.length,
			str_val = obj_input.val(), 	// text of value
			str_radio = obj_radio.val();	// radio of value
		if ( n_len > 0 ) {
			if ( str_radio != str_t_val  ) {
				obj_terminalData[str_key] = parseInt(str_radio);
			}
		} else if ( str_class.search('j_vibchk') != -1 ) {
			var str_vibchk = $('#t_vibchk').val();
			if ( str_t_val != str_vibchk ) {
				obj_terminalData['vibchk'] = str_vibchk; 
			}
		} else if ( str_class.search('j_vibl') != -1 ) {
			var str_vibl = $('#t_vibl').val();
			if ( str_t_val != str_vibl ) {
				obj_terminalData['vibl'] = str_vibl; 
			}
		} else if ( str_class.search('j_freq') != -1 ) {
			var str_freq = $('#t_freq').val();
			if ( str_t_val != str_freq ) {
				obj_terminalData['freq'] = str_freq; 
			}
		} else {
			if ( str_val != str_t_val ) {
				// 白名单 [车主手机号,白名单1,白名单2,...]
				if ( str_class.search('j_whitelist') != -1 ) {
					if ( str_val != '' ) {
						obj_terminalData['white_list'] = [str_whitelist1, str_val];
					} else {
						obj_terminalData['white_list'] = [str_whitelist1];
					}
				} else {
					obj_terminalData[str_key] = str_val;
				}
			}
		}
	});
	dlf.fn_jsonPut(TERMINAL_URL, obj_terminalData, 'terminal', '终端参数保存中');
}
})();
