/**
* 短信下发指令相关操作
*/
$(function () {
	fn_setTitleName();  // 调整标题用户名位置
	$('#sms_type_panel input[id="sms_jh"]').attr('checked', 'checked'); // 刷新页面及加载页面时设置激活为选中状态
	//短信类型添加事件
	$('#sms_type_panel input[name="sms_type"]').click(function(e) { 
		fn_validCookie();
		
		var str_id = $(this).attr('id'), 
			obj_isclear = $('#sms_jb_clear_panel'),
			obj_jhuPanel = $('#sms_jh_umobile_panel'),
			obj_domainPanel = $('#sms_domain_panel');
			
		$('#umobile').val(''); // 切换短信类型时,清除车主手机号
		
		if ( str_id == 'sms_jb' ) { // 如果是解绑,则提示是否清除历史数据
			obj_isclear.show();
		} else { // 如果是其他,则隐藏
			obj_isclear.hide();
		}
		
		if ( str_id == 'sms_jh' ) { // 如果是激活,显示车主手机号输入框
			obj_jhuPanel.show();
		} else {
			obj_jhuPanel.hide();
		}
		
		if ( str_id == 'sms_domain' ) { // 如果是服务器设置
			obj_domainPanel.show();
		} else {
			obj_domainPanel.hide();
		}
	});
	// 发送按钮 事件侦听 
	$('#sms_send').click(function(e) {
		fn_validCookie();
		
		var str_umobile = $('#umobile').val(),
			str_tmobile = $('#tmobile').val(),
			str_domain = $('#domain').val(),
			str_smsType = $('#sms_type_panel input[name="sms_type"]input:checked').val(), 
			str_dataClear = $('#sms_jb_clear_panel input[name="data_clear"]input:checked').val(),
			obj_conditionData = {'umobile': '', 'tmobile': str_tmobile, 'sms_type': str_smsType, 'is_clear': str_dataClear, 'domain': ''};
		
		if ( !fn_validMobile(str_tmobile) ) {
			return;
		}
		
		if ( str_smsType == 'JH' ) { // 只有激活时需要使用车主手机号
			if ( !fn_validMobile(str_umobile, '车主') ) {
				return;
			}
			obj_conditionData.umobile = str_umobile;
		}
		
		if ( str_smsType == 'DOMAIN' ) { // domain设置
			obj_conditionData.domain = str_domain;
		}
		$.post('/smssend',  JSON.stringify(obj_conditionData), function (data) { 
			if ( data.status == 0) {
				if ( str_smsType == 'DEL' ) {
					alert('操作成功。');
				} else {
					alert('短信发送成功。');
				}
			} else {
				alert(data.message);
			}
			
		});
		
	});
});