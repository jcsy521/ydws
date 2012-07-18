$(function() {
	$.ajaxSetup({ cache: false }); // 不保存缓存
	$('#registerForm input[type=text], input[type=password]').val(''); // 数据清空
	// 加载验证
	$.formValidator.initConfig({
		formID: 'registerForm', //指定from的ID 编号
		
		onSuccess: function() { 
			var obj_name = $('#name'), 
				str_name = obj_name.val(), 
				str_tMobile = $('#mobile').val(),
				str_tid = $('#tid').val(), 
				str_psw = $('#psw').val(),
				n_mobileLen = $.trim(str_tMobile).length,
				n_tidLen = $.trim(str_tid).length,
				n_pswLen = $.trim(str_psw).length, 
				obj_regex = regexEnum, 
				obj_tMobileReg = new RegExp(regexEnum.mobile, 'g'), 
				obj_tIdReg = new RegExp(regexEnum.letter_un, 'g'), 
				obj_pswReg = new RegExp('^[0-9]{6}$', 'g');
			
			if ( n_tidLen > 0 ) {
				var obj_tTip = $('#tidTip');
				
				if ( !obj_tIdReg.test(str_tid) ) {
					obj_tTip.html('请输入正确的终端序列号！');
					return false;
				} else {
					obj_tTip.html('');
					return true;
				}
			}
			if ( str_name == '' ) {
				obj_name.val($('#mobile').val());
			}
			return true;
		}
	});
	$('#uid').formValidator({onFocus: '请输入用户名！', onShow: '请输入用户名！', onCorrect: '<font color="#000">用户名正确！</font>'})
	.inputValidator({min: 6, max: 16, onError: '用户名范围(6-16)！'})
	.regexValidator({regExp: 'username', dataType: 'enum', onError:'用户名只能由6-16位数字、26个英文字母或者下划线组成。'})
	.ajaxValidator({
		dataType : "json",
		type: 'PUT', 
		url : '/register',
		success : function(data){
            if( data.status == 0 ) return true;
			return data.message;
		},
		error: function(jqXHR, textStatus, errorThrown){alert("服务器没有返回数据，可能服务器忙，请重试"+errorThrown);},
		onError : "该用户名不可用，请重新输入",
		onWait : "正在进行合法性校验，请稍候..."
	});;
	
	$('#mobile').formValidator({onFocus: '请输入11位用户手机号！', onShow: '请输入11位用户手机号！', onCorrect: '<font color="#000">用户手机号正确</font>'}).inputValidator({min: 11, max: 11, onError: '请输入正确的11位手机号！'})
	.regexValidator({regExp: 'mobile', dataType: 'enum', onError:'请输入正确的11位手机号！'})
	.ajaxValidator({
		dataType : "json",
		type: 'PUT', 
		url : '/register',
		success : function(data){
            if( data.status == 0 ) return true;
			return data.message;
		},
		error: function(jqXHR, textStatus, errorThrown){alert("服务器没有返回数据，可能服务器忙，请重试"+errorThrown);},
		onError : "该用户名手机号不可用，请重新输入",
		onWait : "正在进行合法性校验，请稍候..."
	});
	
	$('#password').formValidator({onFocus: '请输入密码！', onShow: '请输入密码！', onCorrect: '<font color="#000">密码正确</font>'})
	.inputValidator({min: 6, max: 16, onError: '密码长度范围(6-16)！'});
	
	$('#pwd2').formValidator({onFocus: '请输入确认密码！', onShow: '请输入确认密码！', onCorrect: '<font color="#000">确认密码正确</font>'})
	.inputValidator({min: 6, max: 16, onError: '密码长度范围(6-16)！'})
	.compareValidator({desID: 'password', operateor: '=', datatype: 'number', onError: '两次密码不一致，请重新输入！'});
	
	$('#email').formValidator({onFocus: '请输入正确的邮箱！', onShow: '请输入正确的邮箱！', onCorrect: '<font color="#000">邮箱正确</font>'})
	.inputValidator({max: 255, onError: '！'}).regexValidator({regExp: 'email', dataType: 'enum', onError: '您输入的邮箱格式不正确！'});	
});