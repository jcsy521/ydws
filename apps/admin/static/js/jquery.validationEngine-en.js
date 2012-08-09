(function($) {
	$.fn.validationEngineLanguage = function() {};
	$.validationEngineLanguage = {
		newLang: function() {
			$.validationEngineLanguage.allRules = 	{
				"required":{ // Add your regex rules here, you can take telephone as an example
					"regex":"none",
					"alertText":"* 此栏为必填项",
					"alertTextCheckboxMultiple":"请选择一项",
					"alertTextCheckboxe":"请选择一项"},
				"length":{
						"regex":"none",
						"alertText":"* 请输入 ",
						"alertText2":" 至 ",
						"alertText3": " 位数字/字符"},
				"fn_lengthBetween":{
					"name":"fn_lengthBetween",
					"regex":"none",
					"alertText":"*"},
				"maxCheckbox":{
					"regex":"none",
					"alertText":"* 请选择"},	
				"minCheckbox":{
					"regex":"none",
					"alertText":"* 至少选择",
					"alertText2":"项."},	
				"confirm":{
					"regex":"none",
					"alertText":"* 内容不一致"},		
				"mobile":{
					"regex":"/^0{0,1}(13[4-9]|15[7-9]|15[0-2]|18[2378]|147)[0-9]{8}$/",
					"alertText":"* 只能填写移动号码"},
				"phone":{
					"regex":"/^(0[0-9]{2,3}\-)?([1-9][0-9]{6,7})$/",
					"alertText":"* 固定电话格式填写错误"
					},
				"email":{
					"regex":"/^[a-zA-Z0-9_\.\-]+\@([a-zA-Z0-9\-]+\.)+[a-zA-Z0-9]{2,4}$/",
					"alertText":"* 请输入正确的邮箱格式!"},	
				"date":{
					 "regex":"/^[0-9]{4}\-\[0-9]{1,2}\-\[0-9]{1,2}$/",
					 "alertText":"* 格式如:2008-08-08"},
				"onlyNumber":{
					"regex":"/^[0-9\ ]+$/",
					"alertText":"* 只能填写数字"},	
				"noSpecialCaracters":{
					"regex":"/^[0-9a-zA-Z]+$/",
					"alertText":"* 只能填写字母或数字"},	
				"ajaxUser":{
					"file":"/administrator/checkloginname/",
					"extraData":"login=eric",
					"alertTextOk":"可以使用.",	
					"alertTextLoad":"请稍候...",
					"alertText":"已存在"},	
				"ajaxName":{
					"file":"/administrator/checkprivilegegroupname/",
					"alertTextOk":"可以使用.",	
					"alertTextLoad":"请稍候...",
					"alertText":"已被使用"},							
				"onlyLetter":{
					"regex":"/^[a-zA-Z\ \']+$/",
					"alertText":"*Letters only"},
				"sp_char":{
					"regex":"/[^a-zA-Z0-9\u4e00-\u9fa5]/g",
					"alertText":"* 请不要填写特殊字符"},
				"sp_char_space":{
					"regex":"/^[a-zA-Z0-9\u4e00-\u9fa5\]$/",
					"alertText":"* 请不要填写特殊字符"},
				"sp_char_userName":{
					"regex":"/[^a-zA-Z0-9\ ]/g",
					"alertText":"* 只能填写字母或数字"},
				"t_name":{
					"regex":"/^[a-zA-Z0-9_\u4e00-\u9fa5]+$/",
					"alertText":"* 只能是中文数字下划线和中文"},
				"cnum":{
					"regex":"/^[\u4e00-\u9fa5]{1}[A-Z]{1}[A-Z0-9]+$/",
					"alertText":"* 您输入的车牌号错误"},	// 车牌号
				"ajaxMobile":{
					"file":"/business/checkmobile/",
					"alertTextOk":"可以使用.",	
					"alertTextLoad":"请稍候...",
					"alertText":"已存在"
				},
				"ajaxTMobile":{
					"file":"/business/checktmobile/",
					"alertTextOk":"可以使用.",	
					"alertTextLoad":"请稍候...",
					"alertText":"终端已注册"
				}
			}	
		}
	}
})(jQuery);
$(document).ready(function() {	
	$.validationEngineLanguage.newLang()
});