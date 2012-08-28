/*
*终端设置相关操作方法
*/
(function () {
	

// 终端参数设置初始化页面
window.dlf.fn_initTerminal = function() {
	dlf.fn_lockScreen(); // 添加页面遮罩
	$('#terminalWrapper').css({'left': '38%', 'top': '20%'}).show(); // 显示终端设置窗口
	dlf.fn_setItemMouseStatus($('#refresh'), 'pointer', new Array('sx', 'sx2', 'sx'));	// 刷新按钮鼠标滑过样式
	// 参数刷新
	$('#refresh').unbind('click').click(function() {
		dlf.fn_initTerminalWR('f');
	});
	dlf.fn_initTerminalWR(); // 初始化加载参数
}
// 刷新终端参数、查询终端参数
window.dlf.fn_initTerminalWR = function (param) {
	// 获取参数数据
	dlf.fn_lockContent($('.terminalContent')); // 添加内容区域的遮罩
	// 获取用户数据
	//dlf.fn_jNotifyMessage('终端参数查询中...<img src="/static/images/blue-wait.gif" />', 'message', true); 
	var str_url  =  TERMINAL_URL;
	if ( param ) {
		 str_url = str_url + '?terminal_info=' +  param;
	}
	// get request
	$.get_(str_url, '', function (data) {  
		if (data.status == 0) {	
			var obj_data = data.car_sets;
			// for : key value
			for(var param in obj_data) {
				var str_val = obj_data[param];
				if ( param ) {
					if ( param == 'service_status' || param == 'trace' || param == 'cellid_status' ) {
						$('#tr_' + param + str_val ).attr('checked', 'checked'); 	// radio value
						
					} else if ( param == 'white_list' ) {
						var n_length = str_val.length;
						for ( var x = 0; x < n_length; x++ ) {
							var str_name = param  + '_' + (x+1),
								obj_whitelist = $('#t_' + str_name),
								obj_oriWhitelist = $('#' + str_name),
								str_value = str_val[x];
							obj_whitelist.val(str_value);	// whitelist
							obj_oriWhitelist.attr('t_val', str_value);	// save original value
						}
					} else {
						$('#t_' + param ).val(str_val);	// other input value
					}
					$('#' + param ).attr('t_val', str_val);	// save original value
				}
			}
			//dlf.fn_closeJNotifyMsg('#jNotifyMessage'); // 关闭消息提示
		} else { // 查询状态不正确,错误提示
			dlf.fn_jNotifyMessage(data.message, 'message', false, 5000);
		}
		dlf.fn_unLockContent(); // 清除内容区域的遮罩
	}, 
	function (XMLHttpRequest, textStatus, errorThrown) {
		dlf.fn_serverError(XMLHttpRequest);
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
			obj_input = obj_this.children('input[type=text]').eq(0),	// 文本框
			obj_radio = obj_this.children('input[type=radio][checked]').eq(0),	 // 单选按钮
			n_len = obj_radio.length,
			str_val = obj_input.val(), 	// text of value
			str_radio = obj_radio.val();	// radio of value
		if ( n_len > 0 ) {
			if ( str_radio != str_t_val  ) {
				obj_terminalData[str_key] = str_radio;
			}
		} else {
			if ( str_val != str_t_val ) {
				// 白名单 [车主手机号,白名单1,白名单2,...]
				if ( str_class.search('j_whitelist') != -1 ) {
					obj_terminalData['white_list'] = [str_whitelist1, str_val];
				} else {
					obj_terminalData[str_key] = str_val;
				}
			}
		}
	});
	dlf.fn_jsonPut(TERMINAL_URL, obj_terminalData, 'terminal', '终端参数保存中');
}
})();
