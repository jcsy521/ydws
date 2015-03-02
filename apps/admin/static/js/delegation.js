var flag = true; //是否允许用户进行表单的提交
$(function() {
	$('.cDeleg').css({
		'margin-left': ($('body').width() - 500) / 2 + 'px'
	});
});


// 代客操作（终端）
function showMsgAndSendMsg() {
	//验证合法性
	getChildName();
	if (flag) {
		var name = $('#parentName strong').text();
		if (confirm('系统将会向车主发送代理操作信息，请点击"确定"按钮。')) {
			return true;
		}
	}
	return false;
}


// 代客操作（个人）
function showMsgAndSendMsgIn() {
    var $uid = $('#uid');
	return false;
}

// 代客操作（集团）
function showMsgAndSendMsgEn() {
	var $cid = $('#cid');
	return false;
}

//验证合法性
function getChildName() {
	var $mobile = $('#tmobile'),
		str_mobile = '',
		rules = $.validationEngineLanguage.allRules,
		regex = '';

	if ($mobile) {
		str_mobile = $.trim($mobile.val());
		regex = eval(rules.mobile.regex);
		alertText = rules.mobile.alertText;

		if (str_mobile != '') {
			if (!regex.test(str_mobile)) {
				alert(alertText);
				$mobile.val('');
				flag = false;
			} else {
				flag = true;
			}
		} else {
			alert('请输入终端手机号.');
			flag = false;
		}
	}
}
