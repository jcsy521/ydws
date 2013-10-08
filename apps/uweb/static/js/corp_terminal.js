/*
*定位器设置相关操作方法
*/
var arr_slide = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9];
(function () {

/**
* 定位器参数设置初始化
*/
window.dlf.fn_initCorpTerminal = function(str_tid) {
	var str_tid = $($('.j_carList a[class*=j_currentCar]')).attr('tid'),
		b_trackStatus = $('#trackHeader').is(':visible'),	// 轨迹是否打开着
		str_bizType = $('#hidBizCode').val(),
		n_height = 440,
		n_btnTop = 410;

	dlf.fn_dialogPosition('corpTerminal');  // 显示定位器设置dialog	
	dlf.fn_lockScreen(); // 添加页面遮罩
	$('.j_input input[type=text]').blur().css('color', '#000').val('');
	$('#t_corp_mobile').focus();
	dlf.fn_initTerminalWR(str_tid); // 初始化加载参数
	if ( str_bizType == 'znbc' ) {
		dlf.fn_initBindLine(str_tid);// 初始化终端绑定的线路
		n_height = 512;
		n_btnTop = 517;
	}
	$('.corpTerminalContent').css('height', n_height);
	$('#corp_terminalSave').css('top', n_btnTop);
	dlf.fn_onInputBlur();	// input的blur事件初始化
	
	// 标签初始化
	$('.j_tabs').removeClass('currentTab');
	$('#corp_terminalTab').addClass('currentTab');
	
	$('.j_terminalcontent').hide();
	$('#corpTerminalList0').show();
	
	// 选项卡
	$('.j_tabs').unbind('click').click(function() {
		var obj_this = $(this),
			n_index  = obj_this.index(), // 当前li索引
			str_className = $(this)[0].className;
			
		if ( str_className.search('currentTab') != -1 ) {
			return;
		}
		$('.j_tabs').removeClass('currentTab'); //移除所有选中样式
		$(this).addClass('currentTab'); // 选中样式
		$('#corpTerminalList'+n_index).show().siblings().hide(); // 显示当前内容 隐藏其他内容
		if ( n_index == 1 ) {
			$('.j_weekList').data('weeks', []);	// 每次打开移除data数据
			obj_this.css('border-right', '0px');
			dlf.fn_searchData('corpAlertSetting');
			dlf.fn_initAlertSetting('corpAlertSetting');
		} else if ( n_index == 0 ) {
			dlf.fn_initTerminalWR(); // 初始化加载参数
		}
	});
}

/**
* 集团用户短信设置初始化
*/
window.dlf.fn_initSMSOption = function() {
	dlf.fn_dialogPosition('corpSMSOption');  // 显示短信设置dialog	
	dlf.fn_lockScreen(); // 添加页面遮罩
	fn_initCorpSMS();	// 初始化SMS通知
}

/**
* 查询最新定位器参数
*/
window.dlf.fn_initTerminalWR = function (str_tid) {
	dlf.fn_lockContent($('.terminalContent')); // 添加内容区域的遮罩
	dlf.fn_jNotifyMessage('定位器设置查询中' + WAITIMG , 'message', true); 
	// todo  + '?tid=' + str_tid
	var obj_static_mode = $('#corp_alert_freq_mode'),
		obj_auto = $('.j_corp_auto'),
		obj_common = $('#corp_common'),
		obj_t_alert_freq = $('#t_corp_alert_freq'),
		obj_static_tip = $('.j_corp_alert_freq_tip');

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
		
	$.get_(TERMINAL_URL + '?tid=' + dlf.fn_getCurrentTid(), '', function (data) {  
		if (data.status == 0) {	
			var obj_data = data.car_sets,
				n_whitelistLenth = 0,
				n_whitelistTip = 0;
				
			for(var param in obj_data) {
				var str_val = obj_data[param],
					obj_param = $('#t_corp_' + param );
				
				if ( param ) {
					if ( param == 'owner_mobile' ) {	// 车主号码
						$('#t_corp_owner_mobile').val(str_val);
						$('#t_corp_c_umobile').attr('t_val', str_val);
					} else if ( param == 'push_status' ) {
						$('#tr_corp_' + param + str_val ).attr('checked', 'checked'); 
					} else if ( param == 'icon_type' ) {	// 图标
						$('#icon_type' + str_val).attr('checked', true);
						var obj_currentCar = $('.j_currentCar');
						
						obj_currentCar.attr('icon_type', str_val);
						dlf.fn_updateTerminalLogin(obj_currentCar);
					} else if ( param == 'login_permit' ) {
						$('#login_permit' + str_val).attr('checked', true);
					} else {
						if ( param == 'alias' || param == 'freq' || param == 'vibl' || param == 'alert_freq' ) {	// 定位器别名、上报频率、震动灵敏度、告警工作模式
							if ( param == 'alert_freq' ) {
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
								obj_t_alert_freq.data('alert_freq', str_val);
							}
							obj_param.val(str_val);
						} else if ( param == 'white_pop' ) {	// 白名单弹出框
							n_whitelistTip = str_val;
						} else if ( param == 'corp_cnum' && dlf.fn_userType() ) {	// 车牌号
							obj_param.val(str_val);
							$('#corp_' + param ).attr('t_val', str_val);	// 将每个定位器参数对应值保存在t_val中
							if ( str_val == '' ) {
								str_val = obj_data['mobile'];
							}
							dlf.fn_updateCorpCnum(str_val);	// 更新最新的车牌号
						} else {
							obj_param.html(str_val);
						}
					}
					if ( param != 'corp_cnum' ) {
						$('#corp_' + param ).attr('t_val', str_val);	// 将每个定位器参数对应值保存在t_val中
					}
				}
			}
			/*if ( n_whitelistLenth <= 1 && n_whitelistTip == 0 ) {	// 白名单提示 没有设置白名单一直提示
				dlf.fn_showNotice();
			} else {
				$('#whitelistPopWrapper').hide();
			}*/
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
* 初始化SMS通知
*/
function fn_initCorpSMS() {
	// 短信接收号码 change事件 加载对应的短信通知项
	$('#smsOwerMobile').unbind('change').bind('change', function() {
		var str_val = $(this).val(),
			obj_smsOptions = $('#smsOwerMobile option[value='+ str_val +']').data('smsList');
		
		fn_changeSMSCheckbox(obj_smsOptions);
	});
	
	$.get_(CORP_SMS_URL, '', function(data) {
		if ( data.status == 0 ) {
			var obj_data = data.sms_options,
				obj_smsOwerMobile = $('#smsOwerMobile'),
				str_selectOptions = '',
				b_selected = false,
				n_num = 0,
				str_currentMobile = '';
				
			obj_smsOwerMobile.html('');
			for( var param in obj_data ) {	// 获取短信设置项的数据，进行更新
				n_num ++;
				var obj_smsData = obj_data[param];
				
				if ( n_num == 1 ) {	// 默认加载第一个号码的短信设置项
					fn_changeSMSCheckbox(obj_smsData);
					str_currentMobile = param;
				}
				obj_smsOwerMobile.append('<option value="'+ param +'">'+ param +'</option>');
				$('#smsOwerMobile option[value='+ param +']').data('smsList', obj_smsData);// 临时存储短信设置数据  下拉列表change时获取数据
				
			}
			dlf.fn_closeJNotifyMsg('#jNotifyMessage'); // 关闭消息提示
		} else if ( data.status == 201 ) {	// 业务变更
			dlf.fn_showBusinessTip();
		} else { 
			dlf.fn_jNotifyMessage(data.message, 'message', false, 5000); // 查询状态不正确,错误提示
		}
		dlf.fn_unLockContent(); // 清除内容区域的遮罩	
	});
}

/**
* 改变对应车主号码 checkbox的选中状态
* obj_data: 各短信设置项
*/
function fn_changeSMSCheckbox(obj_data) {
	for(var param in obj_data) {	// 获取短信设置项的数据，进行更新
		var n_val = obj_data[param],
			obj_param = $('#corp_' + param);
			
		obj_param.attr('t_checked', n_val);
		if ( n_val == 1 ) {
			obj_param.attr('checked', true)
		} else {
			obj_param.attr('checked', false)
		}
	}
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
window.dlf.fn_corpBaseSave = function() {
	var obj_terminalData = {},
		n_num = 0,
		obj_listVal = $('.j_corp_ListVal');
		
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
		
		if ( str_class.search('j_radio') != -1 ) {	// 上报间隔、基站定位、图标
			str_newVal = parseInt($(this).children('input:checked').val());
		}
		if ( str_key == 'corp_alert_freq' ) {	// 单独处理 告警工作模式
			str_newVal = $('#t_corp_alert_freq').val();
		}
		if ( str_newVal != str_oldVal ) {	// 判断参数是否有修改
			if ( str_class.search('j_white_list') != -1 ) {	// 白名单 [车主手机号,白名单1,白名单2,...]
				str_key = 'owner_mobile';
			} else {
				str_key = str_key.substr(5, str_key.length);
			}
			
			if ( str_key == 'freq' || str_key == 'vibl' ) {
				str_newVal = parseInt(str_newVal);
			} else if ( str_key == 'alert_freq' ) {
				str_newVal = parseInt(str_newVal)*60;
			}
			obj_terminalData[str_key] = str_newVal;
		}
	});
	
	for(var param in obj_terminalData) {	// 修改项的数目
		n_num = n_num +1;
	}
	if ( n_num != 0 ) {	// 如果有修改向后台发送数据,否则提示无任何修改
		obj_terminalData.tid = dlf.fn_getCurrentTid();
		dlf.fn_jsonPut(TERMINAL_URL, obj_terminalData, 'corpTerminal', '定位器参数保存中');
	} else {
		dlf.fn_jNotifyMessage('您未做任何修改。', 'message', false, 4000); // 查询状态不正确,错误提示
		dlf.fn_unLockContent(); // 清除内容区域的遮罩
	}
}

/**
* 短信设置保存
*/
window.dlf.fn_smsOptionSave = function() {
	
	//判断短信通知是否要提交
	
	var obj_checkbox = $('.j_corp_checkbox'),
		obj_smsData = {},
		n_smsNum = 0;
		
	$.each(obj_checkbox, function(index, dom) {
		var obj_this = $(dom),
			str_nowVal = obj_this.attr('checked') == 'checked' ? 1 : 0,
			str_oldVal = parseInt(obj_this.attr('t_checked')),
			str_id = obj_this.attr('id').substr(5);
			
		if ( str_nowVal != str_oldVal ) {
			obj_smsData[str_id] = str_nowVal;
		}
	});
	/**
	* 只保存有修改的数据
	*/
	for(var param in obj_smsData) {	// 修改项的数目
		n_smsNum = n_smsNum + 1;
	}
	if ( n_smsNum != 0 ) {	// 如果有修改向后台发送数据,否则提示无任何修改
		obj_smsData.owner_mobile = $('#smsOwerMobile').val();
		dlf.fn_jsonPut(CORP_SMS_URL, obj_smsData, 'corpSMSOption', '短信告警参数保存中');
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

$(function() {
	/** 
	* 定位器参数的验证
	*/
	$.formValidator.initConfig({
		formID: 'corp_terminalForm', //指定from的ID 编号
		debug: true, // 指定调试模式,不提交form
		validatorGroup: '7', // 指定本form组编码,默认为1, 多个验证组时使用
		wideWord: false, // 一个汉字当一个字节
		submitButtonID: 'corp_terminalSave', // 指定本form的submit按钮
		onError: function(msg) {
			dlf.fn_jNotifyMessage(msg, 'message', false, 4000); 
		}, 
		onSuccess: function() {
			var str_val = $('#t_corp_corp_cnum').val(),
				str_alert_freq = $('#t_corp_alert_freq').val(),
				str_mode = $('#corp_alert_freq_mode').val();
			
			if ( str_val.length > 0 && $.trim(str_val).length == 0 ) {
				dlf.fn_jNotifyMessage('车牌号不能只输入空格。', 'message', false, 3000);
				return;
			}
			if ( str_mode == '1' ) {
				if ( str_alert_freq <= 0 ) {
					dlf.fn_jNotifyMessage('告警工作模式只能是大于0的整数！', 'message', false, 3000);
					return;
				} else if ( str_alert_freq > 1440 ) {
					dlf.fn_jNotifyMessage('告警工作模式最大不能超过24小时！', 'message', false, 3000);
					return;
				} else {
					if ( !/^[0-9]*[1-9][0-9]*$/.test(str_alert_freq) ) {
						dlf.fn_jNotifyMessage('告警工作模式只能是正整数', 'message', false, 3000);
						return;
					}
				}
			}
			dlf.fn_corpBaseSave();	// put请求
		}
	});
	$('#t_corp_owner_mobile').formValidator({validatorGroup: '7'}).inputValidator({max: 11, onError: '短信接收号码最大长度是11位！'}).regexValidator({regExp: 'owner_mobile', dataType: 'enum', onError: '短信接收号码不合法，请重新输入！'});
	$('#t_corp_corp_cnum').formValidator({empty:true, validatorGroup: '7'}).inputValidator({max: 20, onError: '车牌号最大长度为20个汉字或字符！'}).regexValidator({regExp: 'licensenum', dataType: 'enum', onError: '车牌号只能由汉字、数字、大写英文、空格组成！'});   // 别名;
	
	/** 
	* 短息设置的验证
	*/
	$.formValidator.initConfig({
		formID: 'corp_smsOptionForm', //指定from的ID 编号
		debug: true, // 指定调试模式,不提交form
		validatorGroup: '12', // 指定本form组编码,默认为1, 多个验证组时使用
		wideWord: false, // 一个汉字当一个字节
		submitButtonID: 'corp_smsOptionSave', // 指定本form的submit按钮
		onError: function(msg) {
			dlf.fn_jNotifyMessage(msg, 'message', false, 4000); 
		}, 
		onSuccess: function() { 
			dlf.fn_smsOptionSave();	// put请求
		}
	});
	
})
