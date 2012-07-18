// 添加遮罩
function fn_lockScreen() {
	// 拿到遮罩层
	var str_mask = parent.document.getElementById('maskLayer'), 
		str_msg = parent.document.getElementById('msg'); 
	str_mask.style.height = parent.document.documentElement.clientHeight+'px';
	str_mask.style.display = 'block';
	str_msg.style.display = 'block';
}

// 去掉遮罩
function fn_unLockScreen() {
	var str_mask = parent.document.getElementById('maskLayer'), 
		str_msg = parent.document.getElementById('msg');
	str_mask.style.display = 'none';
	str_msg.style.display = 'none';
}
