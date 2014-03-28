/*
* 绑定/解绑
*/

$(function() {
	var str_pagetype = $('#pagetype').val();

	if ( str_pagetype == 'bind' ) { // 绑定页面初始化
		$('#userMobile, #userPwd').val('');
		
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
			$.post_('/bind', JSON.stringify(obj_bindData), function(data) {
				if ( data.status == 0 ) {
					alert('绑定成功！');
					$('#userMobile, #userPwd').val('');
				} else {
					alert(data.message);
				}
			});
		});
	} else { // 解绑页面初始化
		$('#unbind_userPwd').val('');
		
		$('#unbind_userSaveBtn').click(function(e) {
			var str_userName = $.trim($('#unbind_uMobile').val()),
				str_userPwd =  $.trim($('#unbind_userPwd').val()),
				str_openid = $('#openid').val(),
				obj_bindData = {'openid': str_openid, 'username': str_userName, 'password': str_userPwd};
			
			// 验证
			if ( str_userPwd == '' ) {
				alert('请输入密码！');
				return;
			}
			$.post_('/bind', JSON.stringify(obj_bindData), function(data) {
				if ( data.status == 0 ) {
					alert('解除绑定成功！');
					$('#unbind_userPwd').val('');
				} else {
					alert(data.message);
				}
			});
		});
	}
	

});
