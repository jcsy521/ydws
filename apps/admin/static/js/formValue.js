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
