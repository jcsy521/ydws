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
	var str_url  =  TERMINAL_URL;
	if ( param ) {
		 str_url = str_url + '?terminal_info=' +  param;
	}
	$.get_(str_url, '', function (data) {  
		if (data.status == 0) {	
			var obj_data = data.car_sets,
				n_gsm = obj_data.gsm,
				str_gsm = '',
				n_gps = obj_data.gps,
				str_gps = '',
				n_pbat = obj_data.pbat,
				str_pbat = n_pbat + '%',
				str_freq = obj_data.freq,
				str_pulse = obj_data.pulse,
				str_white_list1 = obj_data.whitelist_1,
				str_white_list2 = obj_data.whitelist_2,
				str_cnum = obj_data.cnum,
				str_alias = obj_data.alias,
				str_vibchk = obj_data.vibchk,
				str_track = obj_data.trace,	// 开启追踪
				str_cellid_status = obj_data.cellid_status,	// 开启基站定位
				str_service_status = obj_data.service_status;	// 终端服务状态
			// gsm init
			if ( n_gsm >= 0 && n_gsm < 3 ) {
				str_gsm = '弱';
			} else if ( n_gsm >= 3 && n_gsm < 6 ) {
				str_gsm = '较弱';
			} else {
				str_gsm = '强';
			}
			// gps init
			if ( n_gps >= 0 && n_gps < 10 ) {
				str_gps = '弱';
			} else if ( n_gps >= 10 && n_gps < 20 ) {
				str_gps = '较弱';
			} else if ( n_gps >= 20 && n_gps < 30 ) {
				str_gps = '较强';
			} else {
				str_gps = '强';
			}
			$('#t_gsm').html(str_gsm);
			$('#t_gps').html(str_gps);
			$('#t_pbat').html(str_pbat);
			// allow edit params
			$('#t_freq').val(str_freq);
			$('#t_pulse').val(str_pulse);
			$('#t_white_list1').val(str_white_list1);
			$('#t_white_list2').val(str_white_list2);
			$('#t_cnum').val(str_cnum);
			$('#t_alias').val(str_alias);
			$('#t_vibchk').val(str_vibchk);
			$('#tr_trace' + str_track).attr('checked', 'checked');
			$('#tr_service_status' + str_service_status).attr('checked', 'checked');
			$('#tr_cellid_status' + str_cellid_status).attr('checked', 'checked');
			// original value
			$('#gsm').attr('t_val', n_gsm);
			$('#gps').attr('t_val', n_gps);
			$('#pbat').attr('t_val', n_pbat);
			$('#freq').attr('t_val', str_freq);
			$('#pulse').attr('t_val', str_pulse);
			$('#whitelist_1').attr('t_val', str_white_list1);
			$('#whitelist_2').attr('t_val', str_white_list2);
			$('#cnum').attr('t_val', str_cnum);
			$('#alias').attr('t_val', str_alias);
			$('#vibchk').attr('t_val', str_vibchk);
			
			$('#trace').attr('t_val', str_track);
			$('#service_status').attr('t_val', str_service_status);
			$('#cellid_status').attr('t_val', str_cellid_status);
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

/**
*验证内容后台是否存在
*obj_data: 要验证的数据
*str_msg: 难正不通过的提示信息
*/
function fn_validAjaxText(obj_data, str_msg) {
	var f_returnData = true;
	if ( obj_data ) {
		$.ajax({
			url: TERMINAL_URL,
			type: 'POST',
			dataType: 'json',
			async: false,
			data: JSON.stringify(obj_data),
			processData: false,
			success: function(data){
				if ( data.status != 0 ) {
					dlf.fn_jNotifyMessage(str_msg+'已存在，请重新输入！', 'message', false, 5000);
					f_returnData = false;
				}
			}
		});
	}
	return f_returnData;
}
})();
