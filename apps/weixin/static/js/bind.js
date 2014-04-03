/*
* 绑定/解绑
*/

$(function() {
	var str_pagetype = $('#pagetype').val();

	if ( str_pagetype == 'bind' ) { // 绑定页面初始化
		$('#userMobile, #userPwd').val('');
		$('#bindContent').hide();
		
		$('#userSaveBtn').click(function(e) {
			var str_userName = $.trim($('#userMobile').val()),
				str_userPwd =  $.trim($('#userPwd').val()),
				str_openid = $('#openid').val(),
				obj_bindData = {'openid': str_openid, 'username': str_userName, 'password': str_userPwd};
			
			// 验证
			if ( str_userName == '' ) {
				alert('请输入用户名！');
				return;
			}
			if ( str_userPwd == '' ) {
				alert('请输入密码！');
				return;
			}
			
			fn_dialogMsg('绑定中'+'<img src="/static/images/blue-wait.gif" />');
			$.post_('/bind', JSON.stringify(obj_bindData), function(data) {
				fn_closeDialogMsg();
				if ( data.status == 0 ) { 
					$('#userMobile, #userPwd').val('');
					$('#content').hide();
					
					$('#bindContent').show().html('绑定成功，请返回。'); 
				} else {
					alert(data.message);
				}
			});
		});
	} else { // 解绑页面初始化
		$('#unbind_userPwd').val('');
		$('#unbindContent').hide();
		
		$('#unbind_userSaveBtn').click(function(e) {
			var str_userName = $.trim($('#unbind_userMobile').val()),
				str_userPwd =  $.trim($('#unbind_userPwd').val()),
				str_openid = $('#openid').val(),
				obj_bindData = {'openid': str_openid, 'username': str_userName, 'password': str_userPwd};
			
			// 验证
			if ( str_userPwd == '' ) {
				alert('请输入密码！');
				return;
			}
			
			fn_dialogMsg('解绑中'+'<img src="/static/images/blue-wait.gif" />');
			$.post_('/unbind', JSON.stringify(obj_bindData), function(data) {
				fn_closeDialogMsg();
				if ( data.status == 0 ) {
					$('#unbind_userPwd').val('');
					$('#content').hide();
					$('#unbindContent').show().html('解绑成功，谢谢使用。'); 
				} else {
					alert(data.message);
				}
			});
		});
	}
	

});
