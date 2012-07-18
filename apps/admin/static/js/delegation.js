var flag = true;//是否允许用户进行表单的提交
$(function () {
	$('.cDeleg').css({
        'margin-left' : ($('body').width()-500)/2+'px'
    });
});
function showMsgAndSendMsg() {
	getChildName();
	if ( flag ) {
		var name = $('#parentName strong').text();
		if (confirm('系统将会向家长发送代理操作信息，请点击"确定"按钮。')) {
			return true;
		}
	} 
	return false;
}
//验证合法性
function getChildName() {
	var $mobile = $('#targetmobile'),
		str_mobile = '',
		rules = $.validationEngineLanguage.allRules, 
		regex = '';
	if ( $mobile ) {
		str_mobile = $.trim($mobile.val());
		regex = eval(rules.mobile.regex);
		alertText = rules.mobile.alertText;
		if ( str_mobile != '' ) {
			if(!regex.test(str_mobile)) {
				alert(alertText);
				$mobile.val('');
				flag = false;
			} else {
				flag = true;
			}
		} else {
			alert('请输入儿童号码.');
			flag = false;
		}
	}
}
