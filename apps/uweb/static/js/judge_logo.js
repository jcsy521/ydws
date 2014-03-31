/**
* LOGO еп╤о 
*/
var str_logUrl = '';

if ( DOMAIN_HOST == 'ajt.ydcws.com' ) { 
	str_logUrl = 'bannerAd_ajt.png';
} else {
	str_logUrl = 'bannerAd.png';
}
$('#ads').css('background-image', 'url(/static/images/'+ str_logUrl +')');