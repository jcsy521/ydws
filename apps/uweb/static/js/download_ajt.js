/**
* ajt���ع���
*/
$(function() { 
	var obj_userAgent = navigator.userAgent;
	
	$('.androidContent').show();
	return;
	if ( obj_userAgent.match('Android') || obj_userAgent.match('Linux') ) {
		$('.androidContent').show();
	} else {
		$('.iosContent').show();
	}
});