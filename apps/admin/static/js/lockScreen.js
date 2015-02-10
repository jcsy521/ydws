// 添加遮罩


// 拿到遮罩层
var obj_adminMask = parent.document.getElementById('maskLayer'),
	obj_adminMsgPanel = parent.document.getElementById('msg'),
	obj_adminMsgContent = parent.document.getElementById('layerMsgContent');

function fn_lockScreen(str_layerMsg) {

	obj_adminMask.style.height = parent.document.documentElement.clientHeight + 'px';
	obj_adminMask.style.display = 'block';
	obj_adminMsgPanel.style.display = 'block';
	$('#maskLayer').data('lock', true);

	if (str_layerMsg) {
		obj_adminMsgContent.innerHTML = str_layerMsg;
	} else {
		obj_adminMsgContent.innerHTML = '页面数据正在加载中...';
	}
}

// 去掉遮罩
function fn_unLockScreen() {

	obj_adminMask.style.display = 'none';
	obj_adminMsgPanel.style.display = 'none';

	$('#maskLayer').data('lock', false);
}

/**
 * 当用户窗口改变时,地图做相应调整
 */
window.onresize = function() {
	var f_lock = $('#maskLayer').data('lock');

	if (f_lock) {
		fn_lockScreen();
	}
}