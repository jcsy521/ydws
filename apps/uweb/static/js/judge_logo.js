/**
* LOGO �ж� 
*/
var str_logUrl = '';

if ( DOMAIN_HOST == 'ajt.ydcws.com' || DOMAIN_HOST == 'ajt.ichebao.net' ) { 
	str_logUrl = 'bannerAd_ajt.png';
} else {
	str_logUrl = 'bannerAd.png';
}
$('#ads').css('background-image', 'url(/static/images/'+ str_logUrl +')');