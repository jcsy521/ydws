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
	var str_annoucement = '尊敬的用户：2013年11月2日起，安捷通将于2013年11月1日22：00至24：00期间将进行系统升级。给您带来的不便，尽请谅解。特此公告。',
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
 