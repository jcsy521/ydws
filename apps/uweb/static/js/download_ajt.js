/**
* ajtÏÂÔØ¹¦ÄÜ
*/
$(function() { 
	var obj_userAgent = navigator.userAgent;
	
	$('.androidContent').show();
	
	if ( obj_userAgent.match('Android') || obj_userAgent.match('Linux') ) {
		$('.androidContent').show();
		$('.iosContent').hide();
	} else {
		$('.androidContent').hide();
		$('.iosContent').show();
	}
});