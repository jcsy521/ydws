/**
* ajt���ع���
*/
$(function() { 
	var obj_userAgent = navigator.userAgent;
	
	if ( obj_userAgent.match('Android') || obj_userAgent.match('Linux') ) {
		$('.androidContent').show();
	} else {
		$('.iosContent').show();
	}
});