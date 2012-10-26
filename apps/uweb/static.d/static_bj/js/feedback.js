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
		onError: function(msg) {
			dlf.fn_jNotifyMessage(msg, 'message', false, 5000); 
		}, 
		onSuccess: function() { 
			fn_fbsave();
		}
	});
	$('#contact').formValidator({empty:true}).inputValidator(); // 区分大小写
	$('#email').formValidator().inputValidator({max: 50, onError: '邮箱地址的最大长度是50个字符。'}).regexValidator({regExp: 'email', dataType: 'enum', onError: "请输入正确的邮箱地址。"});  // 邮箱验证
	$('#content').formValidator().inputValidator({min: 10, max: 300, onError: '您的反馈内容最小长度为10，最大长度是300。'}); // 区分大小写	
});

/**
* 保存按钮的事件
*/
function fn_fbsave() {
	var str_contact = $('#contact').val(),
		str_email = $('#email').val(),
		str_content = $('#content').val(),
		obj_feedback = {'contact': str_contact, 'email': str_email, 'content': str_content, 'category': 0 };
		
	$.post_('feedback', JSON.stringify(obj_feedback), function(data) {
		if ( data.status == 0 ) {
			dlf.fn_jNotifyMessage('您的反馈内容已经提交成功。', 'message', false, 5000); 
		} else {
			dlf.fn_jNotifyMessage(data.message, 'message', false, 5000); 
		}
	});
}