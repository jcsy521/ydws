/*
*终端设置相关操作方法
*/
(function () {

// 终端参数设置初始化页面
window.dlf.fn_initTerminal = function() {
	dlf.fn_lockScreen(); // 添加页面遮罩
	$('#terminalWrapper').css({'left': '38%', 'top': '20%'}).show(); // 显示终端设置窗口
	// 终端参数的验证
	$.formValidator.initConfig({
		formID: 'terminalForm', //指定from的ID 编号
		debug: true, // 指定调试模式,不提交form
		validatorGroup: '3', // 指定本form组编码,默认为1, 多个验证组时使用
		submitButtonID: 'terminalSave', // 指定本form的submit按钮
		onError: function(msg) {
			dlf.fn_jNotifyMessage(msg, 'message', false, 4000); 
		}, 
		onSuccess: function() { 
			dlf.fn_baseSave();	// put请求
		}
	});
	$('#t_freq').formValidator({validatorGroup: '3'}).inputValidator({max: 4, onError: '上报频率最大长度为4位数字！'}).regexValidator({regExp: 'freq', dataType: 'enum', onError: '您设置的上报频率不正确，范围(5-3600秒)！'});
	$('#t_pulse').formValidator({validatorGroup: '3'}).inputValidator({max: 4, onError: '心跳时间最大长度为4位数字！'}).regexValidator({regExp: 'pulse', dataType: 'enum', onError: '您设置的终端的心跳时间不正确，范围(1-1800秒)！'});;
	//$('#t_white_list1').formValidator({empty:true, validatorGroup: '3'}).inputValidator({max: 11, onError: '车主手机号最大长度是11位！'}).regexValidator({regExp: 'owner_mobile', dataType: 'enum', onError: '您设置的车主号码不正确，请输入正确的手机号！'});
	$('#t_white_list2').formValidator({empty:true, validatorGroup: '3'}).inputValidator({max: 11, onError: '车主手机号最大长度是11位！'}).regexValidator({regExp: 'owner_mobile', dataType: 'enum', onError: '您设置的车主号码不正确，请输入正确的手机号！'}).compareValidator({desID: 't_white_list1', operateor: '!=', datatype: 'string', onError: '白名单2不能和白名单1相同'});;
	$('#t_cnum').formValidator({empty:true, validatorGroup: '3'}).inputValidator().regexValidator({regExp: 'licensenum', dataType: 'enum', onError: '车牌号输入错误，正确格式:汉字+大写字母+数字！', param:'g'}); // 区分大小写
	$('#t_alias').formValidator({empty:true, validatorGroup: '3'}).inputValidator({max: 20, onError: '终端别名最大长度为10位汉字，20位字符！'}).regexValidator({regExp: 'alias', dataType: 'enum', onError: "终端别名只能是英文、数字、下划线或中文"});  // 别名
	$('#t_vibchk').formValidator({validatorGroup: '3'}).inputValidator().regexValidator({regExp: 'vibchk', dataType: 'enum', onError: '配置在 X 秒时间内产生了Y次震动，才产生震动告警，范围(1:1--60:60)！'}); // 区分大小写
	
	// 参数刷新
	$('#refresh').unbind('click').click(function() {
		dlf.fn_initTerminalWR('f');
	});
	dlf.fn_initTerminalWR(); // 初始化加载参数
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
			$('#white_list1').attr('t_val', str_white_list1);
			$('#white_list2').attr('t_val', str_white_list2);
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
