$(function () {
	/*
        *验证的事件,可选参数'keyup','blur'
        *inlineValidation: false; 是否即时验证
    */ 
	$("#formID").validationEngine({
		validationEventTriggers:"blur"
	});
});
// lengthbetween rules
function fn_lengthBetween(isFlag) { // VALIDATE LENGTH BETWEEN
    var fieldLength = '';
	if (isFlag == undefined) {
		fieldLength = $("#logina").val().length;
		if (fieldLength < 6 || fieldLength > 20) {
			$.validationEngine.isError = true;
			return "需要填写6-20个字";
		} 
	} else {
        if (isFlag == "pwd") {
		    fieldLength = $("#password").val().length;
        } else {
            fieldLength = $("#"+isFlag).val().length;
        }
		if (fieldLength < 6 || fieldLength > 64) {
			$.validationEngine.isError = true;
			return "需要填写6-64个字";
		} 
	}
}
// business : check mobile and tmobile 
function fn_checkMobile(id) {
	var obj_this = $('#' + id),
		str_mobile = obj_this.attr('mobile'),
		str_val = obj_this.val(),
		str_url = '',
		obj_tips = obj_this.siblings('.j_tips');
	if ( id == 'mobile' ) {
		str_url = '/business/checkmobile/' + str_val;
	} else {
		str_url = '/business/checktmobile/' + str_val;
	}
	if ( str_mobile == str_val ) {
		return true;
	} else {
		$.get(str_url, function (data) {
			if (data.success == true) {
				obj_tips.html('已存在');
				obj_tips.show(function() {
					obj_this.val(str_mobile);
				});
				return false;
			} else {
				obj_tips.html('');
				obj_tips.hide();
				return true;
			}
		});
	}
}
