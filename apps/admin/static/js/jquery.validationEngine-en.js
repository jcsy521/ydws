(function($) {
	//$.fn.validationEngineLanguage = function() {};
	$.validationEngineLanguage = {
		newLang: function() {
			$.validationEngineLanguage.allRules = {
				"required":{ // Add your regex rules here, you can take telephone as an example
					"regex":"none",
					"alertText":"没有填写",
					"alertTextCheckboxMultiple":"请选择一项",
					"alertTextCheckboxe":"请选择一项"},
				"length":{
					"regex":"none",
					"alertText":"长度最大是"},
				"fn_lengthBetween":{
					"name":"fn_lengthBetween",
					"regex":"none",
					"alertText":"*"},
				"maxCheckbox":{
					"regex":"none",
					"alertText":"请选择"},	
				"minCheckbox":{
					"regex":"none",
					"alertText":"至少选择",
					"alertText2":"项."},	
				"confirm":{
					"regex":"none",
					"alertText":"内容不一致"},		
				"mobile":{
					"regex":"/^0{0,1}(13[4-9]|15[7-9]|15[0-2]|18[2378]|147)[0-9]{8}$/",
					"alertText":"只能填写移动号码"},
				"phone":{
					"regex":"/^(0[0-9]{2,3}\-)?([1-9][0-9]{6,7})$/",
					"alertText":"固定电话格式填写错误"
					},
				"email":{
					"regex":"/^[a-zA-Z0-9_\.\-]+\@([a-zA-Z0-9\-]+\.)+[a-zA-Z0-9]{2,4}$/",
					"alertText":"格式填写错误"},	
				"date":{
					 "regex":"/^[0-9]{4}\-\[0-9]{1,2}\-\[0-9]{1,2}$/",
					 "alertText":"格式如:2008-08-08"},
				"onlyNumber":{
					"regex":"/^[0-9\ ]+$/",
					"alertText":"只能填写数字"},	
				"noSpecialCaracters":{
					"regex":"/^[0-9a-zA-Z]+$/",
					"alertText":"只能填写字母或数字"},	
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
					"alertText":"请不要填写特殊字符"},
				"sp_char_space":{
					"regex":"/[^a-zA-Z0-9\u4e00-\u9fa5\ ]/g",
					"alertText":"请不要填写特殊字符"},
				"sp_char_userName":{
					"regex":"/[^a-zA-Z0-9\ ]/g",
					"alertText":"只能填写字母或数字"}
			}	
		}
	}
})(jQuery);

