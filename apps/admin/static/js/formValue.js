$(function () {
	/*
        *验证的事件,可选参数'keyup','blur'
        *inlineValidation: false; 是否即时验证
    */ 
	$("#formID").validationEngine();
});
// lengthbetween rules
function fn_lengthBetween(isFlag, abc) { // VALIDATE LENGTH BETWEEN
    var fieldLength = '';
	if (isFlag == undefined) {
		fieldLength = $("#logina").val().length;
		if (fieldLength < 6 || fieldLength > 20) {
			$.validationEngine.isError = true;
			return "*需要填写6-20个字";
		} 
	} else {
        if (isFlag == "pwd") {
		    fieldLength = $("#password").val().length;
        } else {
            fieldLength = $("#"+isFlag).val().length;
        }
		if (fieldLength < 6 || fieldLength > 64) {
			$.validationEngine.isError = true;
			return "*需要填写6-64个字符";
		}
	}
}
// 车主姓名验证 长度和格式
function fn_checkUserName() {
	var str_val = $('#name').val(),
		arr_rules = $.validationEngineLanguage.allRules['t_name'],
		n_valLength=0,
		n_len = str_val.length;
	if ( str_val &&  n_len > 0 ) {
		if ( !eval(arr_rules.regex).test(str_val) ) {
			$.validationEngine.isError = true;
			return arr_rules.alertText;
		}
	} else {
		$.validationEngine.isError = true;
		return '*车主姓名为必填项.';
	}
	for( var ii = 0; ii < n_len; ii++ ) {
		var word=str_val.substr(ii,1);
		if(/[^\x00-\xff]/g.test(word)){
			n_valLength+=2;
		}else{
			n_valLength++;
		}
	}
	if( n_valLength > 10 ){
		$.validationEngine.isError = true;
		return "*最大长度是5个汉字或11个字符";
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
		obj_tips.html('');
		obj_tips.hide();
		return true;
	} else {
		$.get(str_url, function (data) {
			// 修改时终端号码取反判断
			if (data.success == false) {
				obj_tips.html('号码不存在,请重新输入！');
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
