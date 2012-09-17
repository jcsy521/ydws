/*
*终端设置相关操作方法
*/

var arr_slide = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9];
(function () {
// 终端参数设置初始化页面
window.dlf.fn_initTerminal = function() {
	dlf.fn_lockScreen(); // 添加页面遮罩
	$('#terminalWrapper').css({'left': '40%', 'top': '20%'}).show(); // 显示终端设置窗口
	dlf.fn_setItemMouseStatus($('#refresh'), 'pointer', new Array('sx', 'sx2', 'sx'));	// 刷新按钮鼠标滑过样式
	// 标签初始化
	$('.j_tabs').removeClass('currentTab');
	$('#rTab').addClass('currentTab');
	$('.j_terminalcontent').hide();//css('display', 'none');
	$('#terminalList0').show();//css('display', 'block');
	
	// 选项卡
	$('.j_tabs').unbind('click').click(function() {
		var n_index  = $(this).index(), // 当前li索引
			str_className = $(this)[0].className, 
			param = 'w';
			
		if ( str_className.search('currentTab') != -1 ) {
			return;
		}
		$('.j_tabs').removeClass('currentTab'); //移除所有选中样式
		$(this).addClass('currentTab'); // 选中样式
		$('#terminalList'+n_index).show().siblings().hide(); // 显示当前内容 隐藏其他内容
		if ( n_index == 0 ) {
			dlf.fn_initTerminalWR(); // 初始化 终端参数
		} else {
			// 初始化  短信参数
			dlf.fn_initSMSParams();
		}
	});
	// 灵敏度
	$('#viblSlider').slider({
		min: 0,
		max: 9,
		values: 1,
		range: false,
		slide: function (event, ui) {
			var n_val = ui.value;
			n_vibl = arr_slide[n_val];
			$('#viblSlider').attr('title', '震动灵敏度值：' + n_vibl);
			$('#viblTip').html(dlf.fn_changeData('vibl', n_vibl));
		}
	}).slider('option', 'value', 1);
	
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
			obj_freq.attr('disabled', true).css({'background': '#F2F2F2'});
		} else {
			$('#t_freq').attr('disabled', false).css({'background': '#FFF'});
		}
	});
}
// 刷新终端参数、查询终端参数
window.dlf.fn_initTerminalWR = function (param) {
	// 获取参数数据
	dlf.fn_lockContent($('.terminalContent')); // 添加内容区域的遮罩
	// 获取用户数据
	dlf.fn_jNotifyMessage('终端设置查询中...<img src="/static/images/blue-wait.gif" />', 'message', true); 
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
					if ( param == 'trace' || param == 'cellid_status' ) {	// 单选按钮
						// 如果轨迹上报为关闭状态  上报间隔不可编辑
						if ( param == 'trace' ) {
							if ( str_val == 0 ) {
								$('#t_freq').attr('disabled', true).css({'background': '#F2F2F2'});
							} else {
								$('#t_freq').attr('disabled', false);
							}
						}
						$('#tr_' + param + str_val ).attr('checked', 'checked'); 	// radio value
					} else if ( param == 'white_list' ) {	// 白名单
						var n_length = str_val.length;
						$('.j_whitelist input[type=text]').val('');
						for ( var x = 0; x < n_length; x++ ) {
							var str_name = param  + '_' + (x+1),
								obj_whitelist = $('#t_' + str_name),
								obj_oriWhitelist = $('#' + str_name),
								str_value = str_val[x];
							obj_whitelist.val(str_value);	// whitelist
							obj_oriWhitelist.attr('t_val', str_value);	// save original value
						}
					} else if ( param == 'vibchk' ) {	// 震动频率
						var arr_vibchk = str_val.split(':');
						$('#t_vibchk0').val(arr_vibchk[0]);
						$('#t_vibchk1').val(arr_vibchk[1]);
					} else if ( param == 'vibl' ) {
						// 震动灵敏度
						$('#viblSlider').slider('option', 'value', str_val).attr('title', '震动灵敏度值：' + arr_slide[parseInt(str_val)]);
						$('#viblTip').html(dlf.fn_changeData('vibl', str_val));
					} else if ( param == 'freq' ) {	// 上报间隔
						if ( str_val == 0 ) {
							str_val = '';
						}
						$('#t_' + param ).val(str_val);	// other input value
					} else {
						$('#t_' + param ).val(str_val);	// other input value
					}
					$('#' + param ).attr('t_val', str_val);	// save original value
					dlf.fn_updateAlias();
				}
			}
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
			var str_vibchk = $('#t_vibchk0').val() + ':' + $('#t_vibchk1').val();
			if ( str_vibchk != str_t_val ) {
				obj_terminalData['vibchk'] = str_vibchk; 
			}
		} else if ( str_class.search('j_vibl') != -1 ) {
			var str_vibl = $('#viblSlider').slider('option', 'value');
			if ( str_t_val != str_vibl ) {
				obj_terminalData['vibl'] = str_vibl; 
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
				} else if ( str_class.search('j_freq') != -1 ) {	// 上报频率
					if ( str_val == '' ) {
						str_val = 0;
					}
					obj_terminalData['freq'] = parseInt(str_val);
				} else {
					obj_terminalData[str_key] = str_val;
				}
			}
		}
	});
	dlf.fn_jsonPut(TERMINAL_URL, obj_terminalData, 'terminal', '终端参数保存中');
}
})();
