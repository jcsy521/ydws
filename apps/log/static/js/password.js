/**
* 密码修改及验证相关操作
*/
$(function () {
	fn_setTitleName();  // 调整标题用户名位置
	$('input[type="password"]').val(''); // 刷新页面及加载页面时清除密码框内容
	
	// 保存密码
	$('#pwd_save').click(function(e) {
		var old_pwd = $('#old_password').val(),
			new_pwd = $('#new_password').val(),
			new_pwd2 = $('#new_password2').val(),
			obj_conditionData = {'old_password' : old_pwd, 'new_password' : new_pwd };
		
		// 所有密码不能为空
		if ( old_pwd == '' ) {
			alert('当前密码不能为空。');
			return;
		} 
		if ( new_pwd == '' ) {
			alert('新密码不能为空。');
			return;
		} 
		if ( new_pwd2 == '') {
			alert('确定密码不能为空。');
			return;
		} 
		
		// 新密码是否相同
		if ( new_pwd != new_pwd2 ) {
			alert('两次密码不一致。');
			return;
		}
		
		$.ajax({ 
				url: '/password', 
				type: 'PUT',
				dataType: 'json', 
				data: JSON.stringify(obj_conditionData),
				success: function(data){
					alert(data.message);
					if ( data.status == 0 ) {
						if (confirm('您要重新登录本系统吗？')) {
							window.location.href = '/login'; 
						}
					}
				}
		});
			
	}); 
	// 密码重置
	$('#pwd_reset').click(function(e) {
		$('input[type="password"]').val('');
	}); 
	
});