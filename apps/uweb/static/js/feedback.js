/**
* 意见反馈页面
*/
$(function() {
	$('.j_feedback').focus(function() {	// 文本框添加特效
		$(this).css('border-color', '#FF6600');
	}).blur(function() {
		$(this).css('border-color', '#DDE1EE');
	});
	
	$('#btnCancle').click(function() {	// 取消按钮事件
		if ( confirm('确定要取消吗？') ) {
			window.close();
		}
	});
	
	/**
	* 意见反馈的验证
	*/
	$.formValidator.initConfig({
		formID: 'feedbackForm', //指定from的ID 编号
		debug: true, // 指定调试模式,不提交form
		wideWord: false,
		submitButtonID: 'btnSubmit', // 指定本form的submit按钮
		onError: function(msg, obj) {
			dlf.fn_jNotifyMessage(msg, 'message', false, 5000); 
			$(obj).addClass('borderRed');
		}, 
		onSuccess: function(obj) { 
			
			var str_feedback = $.trim($('#content').val());
			
			if ( str_feedback.length > 300 ) {
				dlf.fn_jNotifyMessage('反馈内容不能大于300个字。', 'message', false, 5000); 
				return;
			} else if ( str_feedback.length <= 0 ) {
				dlf.fn_jNotifyMessage('请输入反馈内容。', 'message', false, 5000); 
				return;
			} else if ( str_feedback.length < 10 ) {
				dlf.fn_jNotifyMessage('反馈内容不能小于10个字。', 'message', false, 5000); 
				return;
			} else {
				fn_fbsave();
			}
		}
	});
	$('#contact').formValidator({empty:true}).inputValidator({max: 50, onError: '联系人不能大于50个字符。'}); // 区分大小写
	$('#email').formValidator().inputValidator({max: 50, onError: '邮箱地址的最大长度是50个字符。'}).regexValidator({regExp: 'email', dataType: 'enum', onError: "请输入正确的邮箱地址。"});  // 邮箱验证
	$('#feedback_mobile').formValidator().regexValidator({regExp: 'owner_mobile', dataType: 'enum', onError: "手机号输入不合法，请重新输入！"}); 
	$('#content').formValidator().inputValidator({min: 10, onError: '反馈内容不能小于10个字。'}); // 区分大小写	
});

/**
* 保存按钮的事件
*/
function fn_fbsave() {
	var str_contact = $('#contact').val(),
		str_email = $('#email').val(),
		str_fmobile= $('#feedback_mobile').val(),
		str_content = $('#content').val(),
		obj_feedback = {'contact': str_contact, 'email': str_email, 'content': str_content, 'category': 0, 'mobile': str_fmobile };
		
	$.post_('feedback', JSON.stringify(obj_feedback), function(data) {
		if ( data.status == 0 ) {
			dlf.fn_jNotifyMessage('您的反馈内容已经提交成功。', 'message', false, 5000); 
			$('input[type=text], textarea').val('');
		} else {
			dlf.fn_jNotifyMessage(data.message, 'message', false, 5000); 
		}
	}, 
	function (XMLHttpRequest, textStatus, errorThrown) {
		//dlf.fn_serverError(XMLHttpRequest);
	});
}