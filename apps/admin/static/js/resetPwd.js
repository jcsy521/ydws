/**
* 用户密码管理相关操作
*/
$(function () {
	$('#resetPwd_radioPanel input[id="resetPwd_group"]').attr('checked', 'checked'); // 刷新页面及加载页面时设置激活为选中状态
	$('#resetPwd_mobile').val('');
	
	// 发送按钮 事件侦听 
	$('#userPwd_saveBtn').click(function(e) {
		fn_validCookie();
		
		var str_umobile = $('#resetPwd_mobile').val(),
			str_uType = $('#resetPwd_radioPanel input[name="resetPwd_radioType"]input:checked').val(), 
			obj_conditionData = {'mobile': str_umobile, 'user_type': str_uType};
		
		if ( !fn_validMobile(str_umobile) ) {
			return;
		}
		$.post('/resetpassword',  JSON.stringify(obj_conditionData), function (data) { 
			if ( data.status == 0 ) {
				alert('密码已重置，请查看。');
			} else {
				alert(data.message);
			}
		});
		
	});
	fn_unLockScreen();
});

// 验证cookie是否超时
function fn_validCookie() {
	if(!$.cookie('ACBADMIN')) {
		alert('本次登录已经超时，系统将重新进入登录页面。');
		parent.window.location.replace('/login'); // redirect to the index.
		return true;
	}
	return false;
}

/*
* 验证手机号是否合法
*/
function fn_validMobile(str_mobile) {
	var MOBILEREG = /^[0-9]{11}$/;
	// var MOBILEREG = /^(\+86){0,1}1(3[0-9]|5[012356789]|8[023456789]|47)\d{8}$/;
	
	if ( str_mobile == '' ) {
		alert('请输入用户手机号！');
		return false;
	}
	
	if ( !MOBILEREG.test(str_mobile) ) {	// 手机号合法性验证
		alert('您输入的用户手机号不合法，请重新输入！');
		return false;
	}
	return true;
}
