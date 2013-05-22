$(function() {
	Run();
});
var time,
	possion=1,
	x=0,
	y=0,
	n_time = 0,
	n_interval = 0;

function Run() {
	var str_annoucement = '移动车卫士业务将于2013年5月22日晚22点-24点进行升级维护，期间将暂停服务。。。',
		n_timeout = 450;
	
	$('#announcement').html(str_annoucement.substring(possion-50,possion));
	
	if ( possion++ == str_annoucement.length ) {
		possion=0;
		// 暂停3秒后重新开始
		clearTimeout(time);
		n_interval = setInterval(function() {
			n_time ++;
			if ( n_time >= 3 ) {
				n_time = 0;
				clearTimeout(n_interval);
				time=setTimeout("Run()", n_timeout);
			}
		}, 1000);
	} else {
		time=setTimeout("Run()", n_timeout);
	}
	if ( y == 1 ) {   //如果鼠标走了就不要再跑
		$('#announcement').html('');
		clearTimeout(time);
		y=0;
		x=0;
		possion=0;
		return;
	}
}
function start() { //鼠标来了赶紧跑
	x++;
	if(x==1)//如果它没离开过
	  Run();
}
function stop() {
   y=1;
}
 