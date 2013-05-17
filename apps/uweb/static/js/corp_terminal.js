/*
*定位器设置相关操作方法
*/
var arr_slide = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9];
(function () {

/**
* 定位器参数设置初始化
*/
window.dlf.fn_initCorpTerminal = function(str_tid) {
	dlf.fn_dialogPosition('corpTerminal');  // 显示定位器设置dialog	
	dlf.fn_lockScreen(); // 添加页面遮罩
	$('.j_input input[type=text]').val('');
	dlf.fn_initTerminalWR(str_tid); // 初始化加载参数
	fn_initCorpSMS(str_tid);	// 初始化SMS通知
	dlf.fn_onInputBlur();	// input的blur事件初始化
}

/**
* 查询最新定位器参数
*/
window.dlf.fn_initTerminalWR = function (str_tid) {
	dlf.fn_lockContent($('.terminalContent')); // 添加内容区域的遮罩
	dlf.fn_jNotifyMessage('定位器设置查询中' + WAITIMG , 'message', true); 
	// todo  + '?tid=' + str_tid
	$.get_(TERMINAL_URL, '', function (data) {  
		if (data.status == 0) {	
			var obj_data = data.car_sets,
				n_whitelistLenth = 0,
				n_whitelistTip = 0;
				
			for(var param in obj_data) {
				var str_val = obj_data[param];
				
				if ( param ) {
					if ( param == 'owner_mobile' ) {	// 车主号码
						$('#t_corp_owner_mobile').val(str_val);
						$('#t_corp_c_umobile').attr('t_val', str_val);
					} else if ( param == 'push_status' ) {
						$('#tr_corp_' + param + str_val ).attr('checked', 'checked'); 
					} else if ( param == 'icon_type' ) {	// 图标
						$('#icon_type' + str_val).attr('checked', true);
					} else {
						if ( param == 'alias' || param == 'freq' ) {	// 定位器别名、上报频率
							$('#t_corp_' + param ).val(str_val);
						} else if ( param == 'white_pop' ) {	// 白名单弹出框
							n_whitelistTip = str_val;
						} else if ( param == 'corp_cnum' && dlf.fn_userType() ) {	// 车牌号
							$('#t_corp_' + param ).val(str_val);
							dlf.fn_updateCorpCnum(str_val);	// 更新最新的车牌号
						} else {
							$('#t_corp_' + param ).html(str_val);
						}
					}
					$('#corp_' + param ).attr('t_val', str_val);	// 将每个定位器参数对应值保存在t_val中
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
function fn_initCorpSMS(str_tid) {
	// todo  + '?tid=' + str_tid
	$.get_(SMS_URL, '', function(data) {
		if ( data.status == 0 ) {
			var obj_data = data.sms_options;
			
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
		n_smsNum = 0,
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
		if ( str_newVal != str_oldVal ) {	// 判断参数是否有修改
			if ( str_class.search('j_white_list') != -1 ) {	// 白名单 [车主手机号,白名单1,白名单2,...]
				str_key = 'owner_mobile';
			} else if ( str_key == 'corp_freq' ) {
				str_key = 'freq';
				str_newVal = parseInt(str_newVal);
			} else if ( str_key == 'corp_push_status' ) {
				str_key = 'push_status';
			} else if ( str_key == 'corp_corp_cnum' ) {
				str_key = 'corp_cnum';
			} else if ( str_key == 'corp_icon_type' ) {
				str_key = 'icon_type';
			}
			obj_terminalData[str_key] = str_newVal;
		}
	});
	
	for(var param in obj_terminalData) {	// 修改项的数目
		n_num = n_num +1;
	}
	if ( n_num != 0 ) {	// 如果有修改向后台发送数据,否则提示无任何修改
		dlf.fn_jsonPut(TERMINAL_URL, obj_terminalData, 'corpTerminal', '定位器参数保存中');
	} else {
		dlf.fn_jNotifyMessage('您未做任何修改。', 'message', false, 4000); // 查询状态不正确,错误提示
		dlf.fn_unLockContent(); // 清除内容区域的遮罩
	}
	//判断短信通知是否要提交
	
	var obj_checkbox = $('.j_corp_checkbox'),
		obj_smsData = {};
		
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
		dlf.fn_jsonPut(SMS_URL, obj_smsData, 'corpTerminal', '短信告警参数保存中');
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
		f_warpperStatus = !obj_whitePop.is(':hidden'),
		n_left = obj_terminalWrapperOffset.left + 380,
		n_top =  obj_terminalWrapperOffset.top + 60 ;
		
	if ( f_warpperStatus ) {
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
			dlf.fn_corpBaseSave();	// put请求
		}
	});
	$('#t_corp_owner_mobile').formValidator({validatorGroup: '7'}).inputValidator({max: 11, onError: '短信接收号码最大长度是11位！'}).regexValidator({regExp: 'owner_mobile', dataType: 'enum', onError: '短信接收号码不合法，请重新输入！'});
	$('#t_corp_corp_cnum').formValidator({empty:true, validatorGroup: '7'}).inputValidator({max: 20, onError: '车牌号最大长度为20个汉字或字符！'});  // 别名;
})
