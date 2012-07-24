/*
*终端设置相关操作方法
*/
(function () {
// 终端参数设置初始化页面
window.dlf.fn_initTerminal = function() {
	//dlf.fn_clearMapComponent(); //清除地图上的图形
	dlf.fn_lockScreen(); // 添加页面遮罩
	// 标签初始化
	$('.j_tabs').removeClass('currentTab');
	$('#rTab').addClass('currentTab');
	$('.j_terminalcontent').hide();//css('display', 'none');
	$('#terminalList0').show();//css('display', 'block');
	
	$('#terminalWrapper').css({'left': '38%', 'top': '20%'}).show(); // 显示终端设置窗口
	
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
		if ( n_index == 1 ) {
			param = 'w';
		} else {
			param = 'r';
			$('#refresh').addClass('hide'); // 刷新按钮隐藏
		}
		dlf.fn_initTerminalWR(param); // 初始化加载可编辑参数查询
	});
	// 对文本输入框进行验证
	$('#bListVal').unbind('keyup').keyup(function(event) {
		var str_key = $('#bListSet').attr('terminalkey'), 
			obj_listVal = $('#bListVal'), 
			obj_reg = ARR_TERMINAL_REG[str_key], 
			n_maxLen = obj_reg.maxLen,
			str_val = $(this).val(), 
			n_cLen = str_val.length;
		if ( n_cLen > n_maxLen ) {
			$(this).val(str_val.substr(0, n_maxLen));
			dlf.fn_jNotifyMessage(obj_reg.alertText, 'message', true);	// 正则验证出错
		}
	});
	dlf.fn_initTerminalWR('r'); // 初始化加载可查询参数查询
	
	// 绑定点击事件
	$('#bListSet, #bDropDownbox').unbind('click').click(function() {
		fn_initBaseListItem();
	});
	// 保存参数设置
	$('#terminalSave').unbind('click').click(fn_baseSave);
	// 参数刷新
	$('#refresh').unbind('click').click(function() {
		dlf.fn_initTerminalWR('f', $('.j_terminalList').data('rid'));
	});
}
/* 刷新替换td的值
*	str_key: 后台发送的参数的key
*	str_val0: 参数值0
*	str_val1: 参数值1
*	str_val2: 参数值2
**/
function fn_replaceTd(str_key, str_val0, str_val1, str_val2) {
	if ( str_val0 != undefined ) {
		$('.j_'+str_key)[0].innerHTML = str_val0;
	} 
	if ( str_val1 != undefined ) {
		$('.j_'+str_key)[1].innerHTML = str_val1;
	} 
	if ( str_val2 != undefined ) {
		$('.j_'+str_key)[2].innerHTML = str_val2;
	}
}
// 替换null为空
function fn_replaceNull(str_val) {
	if ( str_val == null || str_val == '' ) {
		return '';
	} else {
		return str_val;
	}
}
/* 拆分 可查询参数
*	obj_data: 后台发送的数据集
*	type: 刷新f 或者 查询r
**/
function fn_keySplit(obj_data, type) {
	var	str_key = obj_data.key, 
		str_name = obj_data.name, 
		str_val = obj_data.value, 
		str_html = '',
		str_ids = '',	// 卫星编码
		str_strength = '',	// 卫星信号强度
		obj_nameList = '';	// 参数名称
	switch (str_key) {	
		case 'gps' :	// GPS卫星编号和强度
			var str_newVal = fn_replaceNull(str_val);
			obj_nameList = str_newVal.split(' ');
			for (var j = 0; j < obj_nameList.length; j++ ) {
				str_ids += obj_nameList[j].substr(0,2) + ' '; // 卫星编号
				str_strength += obj_nameList[j].substr(2,2) + ' '; // 卫星强度
			}
			if ( type == 'f' ) { // 刷新 改变td的值
				fn_replaceTd(str_key, str_ids, str_strength);
			} else { // 查询 添加新的td
				str_html += '<tr><td class="terminalTdL">GPS卫星编号:</td><td class="j_'+str_key+'">' + str_ids + '</td></tr>';
				str_html += '<tr><td class="terminalTdL">卫星信号强度:</td><td class="j_'+str_key+'">' + str_strength +'</td></tr>';
			}
			break;
		case 'vbat' :	// 电池电压，充电电压，充电电流
			var str_bv = '' , // 电池电压
				str_cv = '', // 充电电压
				str_cc = '', // 充电电流
				n_voltage = 10000;	
			// 如果值为空
			if ( str_val != null && str_val != '' ) {
				obj_nameList = str_val.split(':');
				str_bv = Math.round(obj_nameList[0]/n_voltage)/100 + 'V',
				str_cv = Math.round(obj_nameList[1]/n_voltage)/100 + 'V', 
				str_cc = Math.floor(obj_nameList[2]/1000) + 'mA' ;
			}
			if ( type == 'f' ) { // 刷新 改变td的值
				fn_replaceTd(str_key, str_bv, str_cv, str_cc);
			} else {
				str_html += '<tr><td class="terminalTdL">电池电压:</td><td class="j_'+str_key+'">' + str_bv +'</td></tr>';
				str_html += '<tr><td class="terminalTdL">充电电压:</td><td class="j_'+str_key+'">' + str_cv +'</td></tr>';
				str_html += '<tr><td class="terminalTdL">充电电流:</td><td class="j_'+str_key+'">' + str_cc +'</td></tr>';
			}
			break;
		case 'vin' :	// 外接电源输入电压
			var str_iv = '';
			if ( str_val != null && str_val != '' ) { 
				str_iv= Math.ceil(str_val/1000000) + 'V左右';
			}
			if ( type == 'f' ) { // 刷新 改变td的值
				fn_replaceTd(str_key, str_iv);
			} else {
				str_html += '<tr><td class="terminalTdL">外接电源输入电压:</td><td class="j_'+str_key+'">' +  str_iv +'</td></tr>';
			}
			break;
		case 'login' :	// 是否连接到平台
			var str_loginStatus = ' ';
			if ( str_val == '1' ) {
				str_loginStatus = '连接成功';
			} else {
				str_loginStatus = '连接失败';
			}
			if ( type == 'f' ) { // 刷新 改变td的值
				fn_replaceTd(str_key, str_loginStatus);
			} else {
				str_html += '<tr><td class="terminalTdL">是否连接到平台:</td><td class="j_'+str_key+'">'+ str_loginStatus +'</td></tr>';
			}
			break;
		default :
			var str_newVal = fn_replaceNull(str_val);
			if ( type == 'f' ) { // 刷新 改变td的值
				fn_replaceTd(str_key, str_newVal);
			} else {
				str_html += '<tr><td class="terminalTdL">'+str_name+':</td><td class="tdLeft j_'+str_key+'">' + str_newVal + '</td></tr>';		
			}	
			break;
	}
	return str_html;
}

// 可编辑参数查询
window.dlf.fn_initTerminalWR = function (param, id) {
	// 获取参数数据
	dlf.fn_lockContent($('.terminalContent')); // 添加内容区域的遮罩
	var str_url  = TERMINAL_URL + '?terminal_info=' +  param, 
		str_msg = '终端参数查询中，请稍后';
	if ( param == 'f' ) {
		str_msg = '终端参数刷新中，请稍后';
	}
	$('#radioTip').hide();
	dlf.fn_jNotifyMessage(str_msg+'...<img src="/static/images/blue-wait.gif" />', 'message', true);
	if ( id != 0 && id != undefined) {
		str_url += '&id=' + id;
	}
	$.get_(str_url, '', function (data) {  
		if (data.status == 0) {	
			
			$('.j_radio').addClass('hide');
			$('.j_tInput').removeClass('hide');
			var obj_tempData = data.car_sets, 
				n_len = obj_tempData.length, 
				str_html = '';
				
			if ( param == 'w' ) { //可编辑参数
				for (var i = 0; i < n_len; i++ ) {
					str_html += '<li t_val="'+obj_tempData[i].value+'" t_id="'+obj_tempData[i].key+'" t_unit="'+obj_tempData[i].unit+'">'+obj_tempData[i].name+'</li>';
				}
				$('#baseList').html(str_html); // 填空列表数据
				// 设置默认值 
				var obj_blistFirst = $($('#baseList li')[0]), 
					str_tid = obj_blistFirst.attr('t_id'), 
					n_maxLen = ARR_TERMINAL_REG[str_tid].maxLen,
					str_alertText = '* 功能说明：';     //ARR_TERMINAL_REG[str_tid].alertText; 
				
				$('#bListSet').val(obj_blistFirst.text()).attr('terminalkey', str_tid); // 填充默认显示值 
				$('#bListVal').val(obj_blistFirst.attr('t_val'));
				$('#terminalUnit').html(obj_blistFirst.attr('t_unit'));
				$('.j_terminalList').data('wid', data.id);
				$('#terminalListTip').html(str_alertText);
			} else {
				if ( param == 'r' ){ // 可查询参数
					for (var i = 0; i < n_len; i++ ) {
						str_html += fn_keySplit(obj_tempData[i], param); //  拼装要显示的消息
					}
					$('#bListR').html(str_html); // 容器填充数据
					$('.j_terminalList').data('rid', data.id);
					$('#refresh').removeClass('hide'); // 显示数据后 刷新按钮才显示
				} else { // 刷新可查询参数
					for (var i = 0; i < n_len; i++ ) {
						fn_keySplit(obj_tempData[i], param); // 拼装要显示的消息
					}
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
// 基本参数选择操作
function fn_initBaseListItem() {
	var obj_bList = $('#baseList');
	obj_bList.show();
	
	$('#baseList li').mouseout(function() { 
		obj_bList.hide();
		$(this).removeClass('listHover');
	}).mouseover(function() { 
		$(this).addClass('listHover');
		obj_bList.show();
	}).unbind('mousedown').mousedown(function (event) { 
		var str_key = $(this).attr('t_id'), 
			obj_listVal = $('#bListVal'), 
			n_maxLen = ARR_TERMINAL_REG[str_key].maxLen,
			obj_radio = ARR_TERMINAL_REG[str_key].radio,
			str_alertText = '* 功能说明：';          //ARR_TERMINAL_REG[str_key].alertText,
			str_val = $(this).attr('t_val'), 
			obj_tempRadio = null,
			str_radioTip = '';
			
		$('#terminalListTip').html(str_alertText);	// 提示信息
		dlf.fn_closeJNotifyMsg('#jNotifyMessage'); // 关闭消息提示	
		$('#bListSet').val($(this).text()).attr('terminalkey', str_key);
		obj_listVal.val($(this).attr('t_val'));
		$('#terminalUnit').html($(this).attr('t_unit'));
		$('#radioTip').hide();
		// 对radio和input进行切换 
		if ( obj_radio != null ) {
			if ( str_val == '1' ) {
				obj_tempRadio = $('#tRadioVal1');
				str_radioTip = obj_radio[0];
			} else {
				obj_tempRadio = $('#tRadioVal2');
				str_radioTip = obj_radio[1];
			}
			// radio提示用户选中的状态
			$('#radioTip').html('您上次保存的状态是：' +  str_radioTip ).show();
			obj_tempRadio.attr('checked', 'checked');
			$('#tRadioLable1').html(obj_radio[0]);
			$('#tRadioLable2').html(obj_radio[1]);
			$('.j_tInput').addClass('hide');
			$('.j_radio').removeClass('hide');
			// radio check function
			$('.j_radio input[type=radio]').unbind('click').click(function() {
				obj_listVal.val($(this).val());
			});
		} else {
			$('.j_radio').addClass('hide');
			$('.j_tInput').removeClass('hide');
		}
		
		$(this).removeClass('listHover');
		obj_bList.hide();
	});
}
// 保存用户操作
function fn_baseSave() {
	var f_warpperStatus = !$('#terminalWrapper').is(':hidden'), 
		str_tId = $('.j_terminalList').data('wid'), 
		str_key = $('#bListSet').attr('terminalkey'), 
		str_val = $('#bListVal').val(), 
		obj_reg = ARR_TERMINAL_REG[str_key], 
		str_regex = obj_reg.regex, 
		obj_terminalData = {
				'id': str_tId,
				'car_sets': {
					'key': str_key,
					'value': str_val
				}
			};
	
	// 对要提交的参数进行正则验证
	if ( !eval(str_regex).test(str_val) ) {
		dlf.fn_jNotifyMessage(obj_reg.alertText, 'message', true);	// 正则验证出错
		return;
	}
	
	dlf.fn_jsonPut(TERMINAL_URL, obj_terminalData, 'terminal', '终端参数保存中');
}

//--------------
// 添加终端操作
window.dlf.fn_initTerminalList = function() {
	//dlf.fn_clearMapComponent(); //清除地图上的图形
	dlf.fn_lockScreen(); // 添加页面遮罩
	$('#terminalListWrapper').css({'left': '38%', 'top': '20%'}).show(); // 显示终端设置窗口
	// 添加验证事件及数据初始化  终端手机号 终端序列号 终端密码
	$('.j_mobile, .j_tid').val('').unbind('blur').blur(function(event) { 
		fn_validTerminalListVal($(this));
	});
	// 保存列表
	$('#tlSave').unbind('click').click(function() {
		var n_clistLen = $('#carList li').length;
		if ( n_clistLen < 20 ) {
			fn_tlSave();
		} else {
			dlf.fn_jNotifyMessage('终端添加数量已达最大！', 'message', false, 4000); 
		}
	});
}
// 终端添加的保存操作
function fn_tlSave() {
	var obj_postData = [],
		str_who = 'terminalList',
		str_msg = '终端数据发送中',
		obj_tlTid = $('#tlTid'), 
		obj_tlPhone = $('#tlmobile'),
		str_tid = obj_tlTid.val(),
		str_phone = obj_tlPhone.val();
		
	if ( !fn_validTerminalListVal(obj_tlPhone) ) {
		return;
	} else if ( !fn_validTerminalListVal(obj_tlTid) ) {
		return;
	} else { 
		obj_postData[0] = {'id':null, 'tid': str_tid, 'mobile': str_phone};
		dlf.fn_jsonPost(TERMINALLIST_URL, obj_postData, str_who, str_msg);
	}
}
// 删除终端
window.dlf.fn_tlDel = function(obj_item) {
	var n_delID = obj_item.attr('tlid'), 
		obj_liItem = obj_item.parent();
	if ( n_delID && confirm('您确定删除该终端吗？') ) {
		dlf.fn_jNotifyMessage('正在删除终端数据...<img src="/static/images/blue-wait.gif" />', 'message', true);
		$.delete_(TERMINALLIST_URL +'?ids='+ n_delID, '', function (data) {
			if ( data.status == 0 ) {
				// 删除成功后数据清除
				$('#terminalDownItem').hide();
				obj_liItem.remove();
				var str_cListClassName = obj_liItem[0].className;
				var n_carNum = $('#carList li').length;
				if ( n_carNum <= 0 ){
					// 没有绑定车辆
					dlf.fn_showTerminalMsgWrp();
					$('#terminalId, #timesTamp').html('');
					$('#carSpeed').html(0);
					$('#defendStatus').html('未设防');
					$('#eventStatus').html('无报警');
				} else {
					if ( str_cListClassName.search('carCurrent') != -1 ) {
						dlf.fn_switchCar($($('#carList li a')[0]).attr('tid'), $($('#carList li')[0]));
					}
				}
				dlf.fn_jNotifyMessage(data.message, 'message', false, 1000);
			} else {
				dlf.fn_jNotifyMessage(data.message, 'message');
			}
		},
		function (XMLHttpRequest, textStatus, errorThrown) {
			dlf.fn_serverError(XMLHttpRequest);
		});
	}
}
/**
*验证终端列表中的终端手机号,终端序列号,终端密码是否正确 
*obj_item: 当前项对象
*/
function fn_validTerminalListVal(obj_item) {
	var str_className = obj_item[0].className, 
		str_val = obj_item.val(),
		str_regex = '', 
		obj_tempData = null;
		n_cNum = dlf.fn_getNumber(obj_item[0].id), 
		str_msg = '您输入的';
	
	// 用户输入为空提示
	if ( str_val == '' ) {
		dlf.fn_jNotifyMessage(str_msg+'不能设置为空！', 'message', false, 5000);
		return false;
	}
	
	if ( str_className.search('j_mobile') != -1 ) {
		str_regex = /^1(3[0-9]|5[012356789]|8[0256789]|47)\d{8}$/;
		str_msg += '终端手机号';
		obj_tempData = {'check_key': 'mobile', 'check_value': str_val};
	} else if ( str_className.search('j_tid') != -1 ) {
		str_regex = /^[A-Z0-9]{18}$/;
		str_msg += '终端序列号';
		obj_tempData = {'check_key': 'tid', 'check_value': str_val};
	}
	// 用户输入的内容正则校验
	if ( !str_regex.test(str_val) ) {
		dlf.fn_jNotifyMessage(str_msg+'格式错误！', 'message', false, 5000);
		return false;
	} else if ( !fn_validAjaxText(obj_tempData, str_msg) ) {
		return false;
	}
	
	// 验证通过清除消息提示
	dlf.fn_closeJNotifyMsg('#jNotifyMessage'); // 关闭消息提示
	return true;
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
//重启终端初始化
window.dlf.fn_reboot = function() {
	//dlf.fn_clearMapComponent(); //清除地图上的图形
	dlf.fn_lockScreen(); //添加页面遮罩
	$('#rebootMsg').html('您确定要重启爱车保吗？');
	$('#rebootWrapper').css({'left': '38%', 'top': '22%'}).show(); // 显示重启终端窗口 
	$('#rebootBtn').unbind('click').click(function() {
		fn_remoteSave('REBOOT', 'reboot', '终端重启中');
	});
}
/**重启终端保存
* action: LOCK/REBOOT
* str_who : 所要进行的操作 lock, reboot
*/
function fn_remoteSave(action, str_who, str_alertMsg) {
	var obj_wrapper = $('.'+str_who+'Wrapper'), 
		obj_content = $('.'+str_who+'Content'), 
		param = {'action': action}, 
		f_warpperStatus = !obj_wrapper.is(':hidden'); //参数
		dlf.fn_jsonPost(REMOTE_URL, param, str_who, str_alertMsg);
}
})();
