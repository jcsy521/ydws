/*
*终端设置相关操作方法
*/
(function () {
	

// 终端参数设置初始化页面
window.dlf.fn_initTerminal = function() {
	dlf.fn_lockScreen(); // 添加页面遮罩
	$('#terminalWrapper').css({'left': '38%', 'top': '20%'}).show(); // 显示终端设置窗口
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
	dlf.fn_jNotifyMessage('终端参数查询中...<img src="/static/images/blue-wait.gif" />', 'message', true); 
	var str_url  =  TERMINAL_URL;
	if ( param ) {
		 str_url = str_url + '?terminal_info=' +  param;
	}
	// get request
	$.get_(str_url, '', function (data) {  
		if (data.status == 0) {	
			var obj_data = data.car_sets;
			// for : key value
			for ( var i = 0; i < obj_data.length; i++ ) {
				var str_key = obj_data[i].key,
					str_val = obj_data[i].value;
				if ( str_key ) {
					if ( str_key == 'service_status' || str_key == 'trace' || str_key == 'cellid_status' ) {
						$('#tr_' + str_key + str_val ).attr('checked', 'checked'); 	// radio value
					}
					/*  else if ( str_key == 'gsm' ) {// gsm 
						var str_gsm = dlf.fn_changeData(str_key, str_val);
						$('#t_' + str_key ).val(str_gsm);	
					} else if ( str_key == 'gps' ) {	// gps 
						var str_gps = dlf.fn_changeData(str_key, str_val);
						$('#t_' + str_key ).val(str_gps);	// input value
					} else if ( str_key == 'pbat' ) {	// pbat
						$('#t_' + str_key ).val(str_val + '%');	// input value
					} 
					*/
					else {
						$('#t_' + str_key ).val(str_val);	// other input value
					}
					$('#' + str_key ).attr('t_val', str_val);	// save original value
				}
			}
			dlf.fn_closeJNotifyMsg('#jNotifyMessage'); // 关闭消息提示
		} else { // 查询状态不正确,错误提示
			dlf.fn_jNotifyMessage(data.message, 'message');
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
				obj_terminalData[str_key] = str_val;
			}
		}
	});
	dlf.fn_jsonPut(TERMINAL_URL, obj_terminalData, 'terminal', '终端参数保存中');
}
})();
