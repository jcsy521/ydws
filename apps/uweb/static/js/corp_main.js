/**
* 集团用户操作方法
* obj_carsData: 存储lastinfo中所有定位器的信息
* str_currentTid: 上次lastinfo的选中定位器tid
* arr_autoCompleteData: autocomplete 查询数据
* arr_staticsData： 告警统计查询数据
* pagecnt：告警统计总条数
* n_pageNum： 告警统计页码
* b_createTerminal： 标记是新增定位器操作 方便switchcar到该新增车辆
* n_onlineCnt：在线终端总数
* n_offlineCnt：离线终端总数
*/
var obj_carsData = {},
	str_currentTid = '',
	arr_autoCompleteData = [],
	arr_staticsData = [],	// 后台查询到的报警记录数据
	pagecnt = -1,	// 查询到数据的总页数,默认-1
	n_pageNum = 0,	// 当前所在页数
	b_createTerminal = false,
	n_onlineCnt = 0,
	n_offlineCnt = 0;
	
(function() {

/**
*  创建右键菜单，设置每个节点的菜单右键菜单
*/
function customMenu(node) {
	var obj_node = $(node),
		items = null,		// 菜单的操作方法
		renameLabel = '',	// 重命名lable
		createLable = '',	// 新建lable
		deleteLable = '';	// 删除lable
	
	if ( obj_node.hasClass('j_corp') ) {		// 集团右键菜单
		renameLabel = '重命名集团';
		createLable = '新建分组';
		deleteLable = '删除集团';
	} else if (obj_node.hasClass('j_group')) {	// 组右键菜单
		renameLabel = '重命名组';
		deleteLable = '删除分组';
		createLable = '添加定位器';
	} else {									// 定位器右键菜单
		renameLabel = '编辑定位器';
		deleteLable = '删除定位器';
	}
	// 右键菜单执行的操作
	items = {
		"create" : {
			"label" : createLable,
			"action" : function (obj) {
				var obj_this = $(obj).eq(0);
				
				if ( obj_this.hasClass('j_group') ) {	// 新增定位器
					fn_initCreateTerminal('', obj_this.children('a').eq(0).attr('groupId'));
					return false;
				} else if ( obj_this.hasClass('j_corp') ) {	// 新增分组
					this.create();
				}
			}
		},
		"rename" : {
			"label" : renameLabel,
			"action" : function(obj) {
				this.rename(obj);
			}
		},
		"remove" : {
			"label" : deleteLable,
			"action" : function (obj) {
				var obj_this = $(obj).eq(0);
				
				if ( obj_this.hasClass('j_group') ) {	// 删除组
					// 判断是否有定位器 
					var n_terminalLength = obj_this.children('ul').length,
						str_gid = obj_this.children('a').attr('groupid');
						
					if ( n_terminalLength > 0 ) {
						$('#vakata-contextmenu').hide();	// 隐藏右键菜单
						alert('该分组下有定位器不能删除.');
						return;
					} else {
						fn_removeGroup(obj);
						return false;
					}
				} else {	// 删除定位器
					fn_removeTerminal(obj);
					return false;
				}
			}
		}
	};
	// 终端右键菜单删除“新增”和“重命名”菜单
   if ( obj_node.hasClass('j_leafNode') ) {
		delete items.create;
		delete items.rename;
   }
   // 集团右键菜单删除 “删除”菜单
   if ( obj_node.hasClass('j_corp')  ) {
		delete items.remove;
   }
   /*if ( obj_node.hasClass('j_group') && obj_node.children('a').attr('title') == '默认组' ) {
		delete items.remove;
		delete items.rename;
   }*/
   return items;
}
	
/*
* jstree初始化，右键菜单事件处理、树加载完成事件处理、节点单击事件处理、双击事件处理
* str_checkedNodeId：默认要选中的节点id
* str_html：动态生成的树的html
* dnd: drag
* contextmenu: right-menu
* types: node icon
* crrm: create、remove、rename等
*/
window.dlf.fn_loadJsTree = function(str_checkedNodeId, str_html) {
	$('#corpTree').jstree({
		"plugins": [ "themes", "html_data", "ui", "contextmenu",'crrm', "types", 'dnd' ],
		'core': {
			'strings': {
				'new_node': '新建组'
			}
		},
		'html_data': {
			'data': str_html
		},
		"contextmenu" : {
			'items': customMenu,
			'select_node': true
		},
		'themes': {
			'theme': 'classic',
			'icons' : true
		},
		'ui': {
			'initially_select': str_checkedNodeId	// 设置默认选中的节点
		},
		"crrm" : {
			"move": {
				"check_move" : function (m) {
					var obj_currentNode = m.o,
						p = this._get_parent(obj_currentNode);
					
					if ( !p ) {
						return false;
					}
					p = p == -1 ? this.get_container() : p;
					
					if( p === m.np ) return true;	// 如果移动到自己的父节点下
					if( p[0] && m.np[0] && p[0] === m.np[0] ) {
						return true;
					}
					// 如果 要移动节点的父节点  和  目标节点  是同一级 则可以移动
					var obj_currentPrentNode = $(p[0]),
						obj_currentA = obj_currentNode.children('a').eq(0),
						str_tid = obj_currentA.attr('tid'),
						str_parent = obj_currentPrentNode.hasClass('j_group'),
						obj_targetNode = $(m.np[0]),
						str_targetGroupId = obj_targetNode.children('a').eq(0).attr('groupId'),
						str_target = $(m.np[0]).hasClass('j_group'),
						arr_tids = [];
					
					if ( str_parent && str_target ) {
						return true;
					}
					return false;
				}
			}
		}
	}).bind('move_node.jstree', function(e, data) {
		var obj_currentNode = data.rslt.o,
			obj_currentA = obj_currentNode.children('a').eq(0),
			str_tid = obj_currentA.attr('tid'),
			obj_target = data.rslt.np,
			str_groupId = $(obj_target).children('a').attr('groupid'),
			arr_tids = [];
			
			arr_tids.push(str_tid);
			fn_moveGroup(arr_tids, str_groupId);			
	}).bind('create.jstree', function(e, data) {
		var obj_rslt = data.rslt,
			obj_rollBack = data.rlbk,
			str_newName = obj_rslt.name;
			
		fn_createGroup($(obj_rslt.parent).children('a').attr('corpid'), str_newName, obj_rollBack, obj_rslt.obj);
	}).bind('rename.jstree', function(e, data) {	// 重命名
		var	obj_rslt = data.rslt,
			obj_currentNode = $(obj_rslt.obj[0]),
			obj_current = obj_currentNode.children('a').eq(0),
			str_newName = obj_rslt.new_name,
			b_flag = obj_currentNode.hasClass('j_leafNode');
			
		if ( str_newName == data.rslt.old_name && !b_flag ){	// 如果新名称和旧名称相同 不操作
			return;
		}
		if ( obj_currentNode.hasClass('j_group') ) {	// 重命名组	
			fn_renameGroup(obj_current.attr('groupid'), str_newName, data.rlbk);
		} else if ( obj_currentNode.hasClass('j_corp') ) {	// 重命名集团
			fn_renameCorp(obj_current.attr('corpid'), str_newName, data.rlbk)
		}
	}).bind('loaded.jstree', function(e, data) {	// 树节点加载完成事件
		 data.inst.open_all(-1);	// 默认展开所有的节点
		dlf.fn_setCorpIconDiffBrowser();
		// 更新定位器总数
		fn_updateTerminalCount();
		// 循环所有定位器 找到当前定位器并更新车辆信息
		var b_loop = true,
			n_num = 0;
			
		for ( var index in obj_carsData ) {
			n_num ++;
		}
		
		if ( n_num > 0 ) {
			for ( var param in obj_carsData ) {
				var obj_car = obj_carsData[param],
					n_clon = obj_car.clongitude/NUMLNGLAT,	
					n_clat = obj_car.clatitude/NUMLNGLAT;
					
				if ( n_clon != 0 && n_clat != 0 ) {
					dlf.fn_updateInfoData(obj_car); // 工具箱动态数据
				}
			}
			if ( str_currentTid != undefined && str_currentTid != '') {
				if ( b_createTerminal ) {	// 如果是新建终端 发起switchCar
					var obj_newTerminal = $('#leaf_' + str_currentTid);
					
					dlf.fn_switchCar(str_currentTid, obj_newTerminal);
					data.inst.open_all(0); // -1 opens all nodes in the container
				} else {
					for(var param in obj_carsData) {
						var obj_carInfo = obj_carsData[param], 
							str_tid = param;
						
						if ( str_currentTid == str_tid ) {	// 更新当前车辆信息
							dlf.fn_updateTerminalInfo(obj_carInfo);
							b_loop = false;
						}
					}
				}
			} else {	// 第一次发起switchCar启动lastinfo
				var obj_current = $('#' + data.inst.data.ui.to_select);
					
				str_currentTid = str_checkedNodeId.substr(5, str_checkedNodeId.length);
				dlf.fn_switchCar(str_currentTid, obj_current);
			}
			fn_updateAllTerminalLogin();
			$('.groupNode').css('color', '#000');
		} else {	// 无终端 启动lastinfo
			dlf.fn_updateLastInfo();
			fn_initCarInfo();
		}
	}).bind('click.jstree', function(event, data) {	// 选中节点事件
		var str_target = event.target.nodeName, 
			obj_current = $(event.target),
			b_terminalClass = obj_current.hasClass('j_terminal');
			
		if ( b_terminalClass && ( str_target == 'A' || str_target == 'INS') ) {                   
			var str_tid = obj_current.attr('tid');
			
			if ( str_currentTid == str_tid ) {	// 如果是同辆车则不switchcar
				return;
			}
			str_currentTid =  str_tid;	// todo
			str_checkedNodeId = 'leaf_' + str_tid;	
			dlf.fn_switchCar(str_tid, obj_current); // 登录成功,            
		} else {
			return false;
		}
	}).bind('dblclick.jstree', function(event, data) {
		
		var obj_target = $(event.target),
			b_class = obj_target.hasClass('j_terminal')

		if ( b_class ) {	// 双击定位器
			dlf.fn_initTerminal();
		} else {
			return false;
		}
	});
}

// 更新终端总数
function fn_updateTerminalCount(str_operation) {
	
	switch ( str_operation ) {
		case 'add':
			n_onlineCnt++;
			break;
		case 'sub':
			n_offlineCnt--;
			break;
		default:
			
			break;
	}
	// 更新定位器总数
	$('.carCount').html( n_onlineCnt + n_offlineCnt + '(全部)');
	$('.onlineCount').html(n_onlineCnt + '(在线)');
	$('.offlineCount').html(n_offlineCnt + '(离线)');
		
}
// 无终端时车辆信息栏显示-
function fn_initCarInfo() {
	$('#defendContent').html('-').attr('title', '');
	$('#defendStatus').css('background-image', '');
	$('#gpsContent').html('-').attr('title', '').css('background', 'inherit');
	$('#power').css('background-image', '');
	$('#powerContent').html('-').attr('title', '').css('background', 'inherit');
	$('#gsm').css('background-image', '');
	$('#gsmContent').html('-').attr('title', '').css('background', 'inherit');
	$('#gps').css('background-image', '');
	$('#locationTime').html('-');
	$('#tmobileContent').html('-').attr('title', '');
}
/**
* 集团用户 lastinfo
*/
window.dlf.fn_corpGetCarData = function() {
	var obj_current = $('.j_leafNode a[class*=jstree-clicked]'),
		str_checkedNodeId = obj_current.attr('id'),	// 上一次选中车辆的id
		str_trackStatus = $('#trackHeader').css('display'),
		str_tempTid = '',
		b_flg = false;
	
	if ( str_trackStatus != 'none' ) {	//如果当前正在进行轨迹操作,不进行lastinfo操作
		return;
	}
	str_checkedNodeId = str_checkedNodeId == undefined ? 'leaf_' + str_currentTid : str_checkedNodeId;
	str_tempTid = str_checkedNodeId.substr(5, str_checkedNodeId.length);
	str_currentTid = obj_current.attr('tid');	// load.jstree时更新选中的车
	
	$.post_(CORP_LASTINFO_URL, '', function (data) {	// 向后台发起lastinfo请求
		if ( data.status == 0 ) {
			var obj_corp = data.res,
				arr_groups = obj_corp.groups,	// all groups 
				n_groupLength = arr_groups.length,	// group length
				str_corpName = obj_corp.name,	// corp name
				str_corpId = obj_corp.cid,		// corp id
				str_html = '<ul>',
				arr_groupIds = [], // 组ID组
				arr_tids = [], 	// 组下的tid组
				str_tempFirstTid = '',	// 默认第一个tid
				str_groupFirstId = '',	// 默认第一个groupid
				obj_newData = {};
			
			/*if ( !dlf.fn_isEmptyObj(obj_corp) ) {
				return;
			}*/			
			n_onlineCnt = obj_corp.online,		// online count
			n_offlineCnt = obj_corp.offline;	// offline count
			
			if ( str_corpId && str_corpName ) {
				str_html += '<li class="j_corp"><a title="'+ str_corpName +'" corpid="'+ str_corpId +'" class="corpNode" href="#">'+ str_corpName +'</a>';
			}
			
			arr_autoCompleteData = [];
			if ( n_groupLength > 0 ) {
				str_html += '<ul>';
				str_groupFirstId = 'group_' + arr_groups[0].gid;
				
				for ( var i = 0; i < n_groupLength; i++ ) {	// 添加组
					var obj_group = arr_groups[i],
						str_groupName = obj_group.name,
						str_groupId = obj_group.gid,
						arr_cars = obj_group.cars,
						arr_tempTids = [], //tid组
						n_carsLength = arr_cars.length;
						//arr_tids = [];
						
					str_html += '<li class="j_group"><a href="#" class="groupNode" groupId="'+ str_groupId +'" title="'+ str_groupName +'" id="group_'+ str_groupId +'">'+ str_groupName +'</a>';
					
					if ( n_carsLength > 0 ) {
						str_html += '<ul>';
						if ( str_tempFirstTid == '' ) {
							str_tempFirstTid = 'leaf_' + arr_groups[i].cars[0].tid;	// 第一个分组的第一个定位器 id
						}
						for ( var x = 0; x < n_carsLength; x++) {	// 添加组下面的定位器
							var obj_car = arr_cars[x],
								str_tid = obj_car.tid,
								str_alias= obj_car.alias,
								str_mobile = obj_car.mobile,
								str_login = obj_car.login;
								
							obj_carsData[str_tid] =  obj_car;
							arr_tempTids.push(str_tid); //tid组string 串
							if ( str_login == LOGINOUT ) {
								str_html += '<li class="jstree-leaf j_leafNode"><a actiontrack="no" clogin="'+ obj_car.login+'" fob_status="" tid="'+ str_tid +'" keys_num="'+ obj_car.keys_num +'" title="'+ str_mobile +'" class="terminalNode j_terminal jstree-draggable" href="#" id="leaf_'+ str_tid +'">'+ str_alias +'</a></li>';
							} else {
								str_html += '<li class="jstree-leaf j_leafNode"><a actiontrack="no" clogin="'+ obj_car.login+'" fob_status="" tid="'+ str_tid +'" keys_num="'+ obj_car.keys_num +'" title="'+ str_mobile +'" class="terminalNode j_terminal jstree-draggable" href="#" id="leaf_'+ str_tid +'">'+ str_alias +'</a></li>';	
							}
							
							if ( str_tempTid != '' && str_tempTid == str_tid ) {
								b_flg = true;
							}
							/** 
							* 自动完成数据填充:根据旅客姓名和手机号进行搜索
							*/
							var str_tempLabel = str_mobile;
							if ( str_alias != str_mobile ) {
								str_tempLabel = str_alias + ' ' + str_mobile;
							}
							arr_autoCompleteData.push({label: str_tempLabel, value: str_tid});
						}
						str_html += '</ul>';
						// 填充本次数据 为了与下次lastinfo进行比较
						
						arr_tids[str_groupId] = arr_tempTids;
					} else {
						arr_tids[str_groupId] = [];
					}
					str_html += '</li>';
					arr_groupIds.push(str_groupId);
				}
				str_html += '</ul>';
				// 存储 gids , tids
				obj_newData = {'gids': arr_groupIds, 'tids': arr_tids, 'n_gLen': n_groupLength};
			}
			$('.j_carList').data('carsData', obj_carsData);	// 存储所有定位器信息
			str_html += '</li></ul>';
			var str_tempNodeId = '';
			/**
			* 设置jstree默认选中的节点
			*/
			if ( str_checkedNodeId == '' || str_checkedNodeId == 'leaf_' || str_checkedNodeId == ' leaf_undefined'  ) {		// 上次没有选中---第一次加载
				if ( str_tempFirstTid != '' ) {	// 拿第一个定位器
					str_tempNodeId = str_tempFirstTid;
				} else {
					str_tempNodeId = str_groupFirstId;
				}
			} else {
				if ( b_flg ) {
					str_tempNodeId = str_checkedNodeId;
				} else {
					str_tempNodeId = str_tempFirstTid == '' ? str_groupFirstId : str_tempFirstTid;
				}
			}
			
			if ( fn_lastinfoCompare(obj_newData) ) {	// lastinfo 与当前树节点对比 是否需要重新加载树节点
				dlf.fn_loadJsTree(str_tempNodeId, str_html);
				dlf.fn_initAutoComplete();
				$('#txtautoComplete').val('请输入车牌号或定位器号码').addClass('gray');
			} else {
				// 更新组名和集团名还有 在线离线状态
				fn_updateTreeNode(obj_corp);
			}
		} else if ( data.status == 201 ) {	// 业务变更
			dlf.fn_showBusinessTip();
		} else {
			dlf.fn_jNotifyMessage(data.message, 'message'); // 查询状态不正确,错误提示
		}
	},
	function (XMLHttpRequest, textStatus, errorThrown) {
		dlf.fn_serverError(XMLHttpRequest);
	});
}

/*
* 初始化autocomplete
*/
window.dlf.fn_initAutoComplete = function() {
	var obj_compelete = $('#txtautoComplete'),
		str_val = obj_compelete.val();
	
	if ( str_val == '' ) {
		str_val = '请输入车牌号';
	}
	// autocomplete	自动完成 初始化
	obj_compelete.keyup(function(event) {
		if ( event.keyCode === $.ui.keyCode.TAB && $(this).data('autocomplete').menu.active ) {
			event.preventDefault();
		}
		$(this).autocomplete('search');
	}).autocomplete({
		source: arr_autoCompleteData,
		select: function(event, ui) {
			var str_tid = ui.item.value,
				obj_itemLi = $('.j_carList a[tid='+ str_tid +']'),
				str_crntTid = $('.j_leafNode a[class*=jstree-clicked]').attr('tid');

			$('#txtautoComplete').val( ui.item.label);
			if ( str_crntTid == str_tid ) {
				return false;
			}
			dlf.fn_switchCar(str_tid, obj_itemLi);
			return false;
		}
	});
}

// 更新树节点的数据
function fn_updateTreeNode(obj_corp) {
	var arr_groups = obj_corp.groups,	// all groups 
		n_groupLength = arr_groups.length,	// group length
		str_corpName = obj_corp.name,	// corp name
		str_corpId = obj_corp.cid;		// corp id
	
	$('.j_corp a[corpId='+ str_corpId +']').html('<ins class="jstree-icon">&nbsp;</ins>' + str_corpName).attr('title', str_corpName);	// 更新集团名 <img src="/static/images/corpImages/corp.png">
	
	for ( var gIndex in arr_groups ) {
		var obj_group = arr_groups[gIndex],
			str_groupName = obj_group.name,
			arr_cars = obj_group.cars,
			n_carLength = arr_cars.length;

		$('#group_'+ obj_group.gid).html('<ins class="jstree-icon">&nbsp;</ins>' + str_groupName).attr('title', str_groupName);	// 更新组名<img src="/static/images/corpImages/gorup.png">
		
		if ( n_carLength > 0 ) {
			for ( var x = 0; x < arr_cars.length; x++ ) {
			
				var obj_car = arr_cars[x],
					str_tid = obj_car.tid,
					n_login = obj_car.login,
					str_tmobile = obj_car.mobile,
					str_alias = obj_car.alias,
					obj_leaf = $('#leaf_' + str_tid),
					str_imgUrl = '',
					n_clon = obj_car.clongitude/NUMLNGLAT,	
					n_clat = obj_car.clatitude/NUMLNGLAT;
				
				if ( n_login == LOGINOUT ) {
					str_imgUrl = 'offline.png';
				} else {
					str_imgUrl = 'online.png';
				}
				obj_leaf.html('<ins class="jstree-icon">&nbsp;</ins>' + str_alias).attr('title', str_tmobile).attr('clogin', n_login);	// 更新定位器名<img src="/static/images/corpImages/'+ str_imgUrl +'">
				
				if ( str_currentTid == str_tid  ) {
					dlf.fn_updateTerminalInfo(obj_car);
				}
				if ( n_clon != 0 && n_clat != 0 ) {
					dlf.fn_updateInfoData(obj_car); // 工具箱动态数据
				}
			}
		}
	}
	fn_updateAllTerminalLogin();
	dlf.fn_setCorpIconDiffBrowser();
}

window.dlf.fn_setCorpIconDiffBrowser = function () {
	/*if ( $.browser.msie && ($.browser.version == "7.0") ) {
		$('.corpNode ins').css('backgroundPosition', '0px 0px');
	} else {
		$('.corpNode ins').css('backgroundPosition', '0px');
	}*/
	$('.corpNode ins').css('backgroundPosition', '0px 0px');
}

// 更新车辆状态
function fn_updateAllTerminalLogin() {
	$('.j_terminal').each(function() {
		dlf.fn_updateTerminalLogin($(this));
	});
}

window.dlf.fn_updateTerminalLogin = function(obj_this) {
	var	str_login = obj_this.attr('clogin'),
		str_imgUrl = '',
		str_color = '',
		obj_ins = obj_this.children('ins');
	
	if ( str_login == LOGINOUT ) {
		str_imgUrl = 'offline.png';
		str_color = 'gray';
	} else {
		str_imgUrl = 'online.png';
		str_color = '#24d317';
	}
	obj_this.css('color', str_color);
	obj_ins.css('background', 'url("/static/images/corpImages/'+ str_imgUrl +'") no-repeat');
	if ( $.browser.msie ) {
		if ( $.browser.version == "7.0" ) {
			obj_ins.css('backgroundPosition', '0px -1px');
		} else if ( $.browser.version == "6.0"  ) {
			obj_ins.css('backgroundPosition', '0px 25px');
		} else {
			obj_ins.css('backgroundPosition', '0px 2px');
		}
	} else {
		obj_ins.css('backgroundPosition', '0px 2px');
	}
}

/**
* 集团用户 /terminal get和put的时候更新最新的定位器别名
*/
window.dlf.fn_updateCorpCnum = function(cnum) {
	var obj_current = $('.j_currentCar'),
		str_cnum = cnum['corp_cnum'] == undefined ? cnum : cnum['corp_cnum'],
		str_tmobile = obj_current.attr('title'),
		str_tempAlias = str_cnum,
		str_tid = str_currentTid;
	
	if ( str_cnum == '' ) {
		str_tempAlias = str_tmobile;
	}
	obj_current.html('<ins class="jstree-icon">&nbsp;</ins>' + str_tempAlias);
	dlf.fn_updateTerminalLogin(obj_current);
	for ( var index in arr_autoCompleteData ) {
		var obj_terminal = arr_autoCompleteData[index],
			str_newLabel = '',
			str_tempTid = obj_terminal.value,	// tid
			str_label = obj_terminal.label;	// alias 或 tmobile
		// 当前终端的、alias不是tmobile
		if ( str_tempTid == str_tid ) {
			if ( str_cnum == '' || str_cnum ==  str_tmobile ) {
				str_newLabel = str_tmobile;
			} else {
				str_newLabel = str_cnum + ' ' + str_tmobile;
			}
			obj_terminal.label = str_newLabel;
			dlf.fn_initAutoComplete();
		}
	}
}

/**
* 对比两次lastinfo的数据是否一致，不一致重新加载树
*/
function fn_lastinfoCompare(obj_newData) {
	var n_newDataLen = obj_newData.n_gLen,		// new lastinfo 的group数量
		obj_groups = $('.j_group'),
		n_oldDataLen = 0, 	// 所有分组数量
		arr_newGids = obj_newData.gids,	// 所有新分组
		arr_newTids = obj_newData.tids;	// 所有新tids
		
	if ( !obj_groups ) {
		return true;
	} else {
		n_oldDataLen = obj_groups.length
	}
	if ( n_newDataLen != n_oldDataLen ) {	// 分组数不同重新加载
		return true;
	}
	// valid gids
	for ( var gid in arr_newGids ) {
		var str_gid = arr_newGids[gid];
		
		if ( str_gid != '' ) {
			if ( $('#group_' + str_gid ).length <= 0 ) {	// 树节点上没有新的组
				return true;
			}
		}
	}
	// valid tids
	for ( var gid in arr_newTids ) {
		var arr_newStrTids = arr_newTids[gid],
			n_newTidLength = arr_newStrTids.length,
			n_treeLength = $('#group_'+  gid).siblings('ul').find('.j_terminal').length;
		
		if ( n_newTidLength != n_treeLength ) {
			return true;
		}
		for ( var tid in arr_newStrTids ) {
			var str_tid = arr_newStrTids[tid];
			
			if ( str_tid != '' ) {
				if ( $('#leaf_' + str_tid ).length <= 0 ) {
					str_currentTid = '';
					return true;
				}
			}
		}
	}
	return false;
}

/**
* 新建组
*/
function fn_createGroup(cid, str_newName, obj_rollBack, obj_newNode) {
	if ( str_newName == '' ) {
		dlf.fn_jNotifyMessage('分组名称不能为空。', 'message', false, 3000);
		$.jstree.rollback(obj_rollBack);
		return false;
	} else {
		if ( !fn_checkGroupName(str_newName, obj_rollBack) ) {
			var obj_param = {'name': str_newName, 'cid': cid};
			
			$.post_(GROUPS_URL, JSON.stringify(obj_param), function (data) {
				if ( data.status == 0 ) {
					var n_gid = data.gid;
					obj_newNode.addClass('j_group').children('a').attr('groupId', n_gid).addClass('groupNode').attr('id', 'group_' + n_gid).css('color', '#000000');
				} else {
					$.jstree.rollback(obj_rollBack);
				}
			});
		}
	}
}

function fn_checkGroupName(str_name, node, str_gid) {
	var b_flg = false;
	
	$('.groupNode[groupid != ' + str_gid+ ']').each(function() {
		if ( $.trim($(this).text()) == str_name  ) {
			if ( node ) {
				$.jstree.rollback(node);
			}
			dlf.fn_jNotifyMessage('该分组已存在。', 'message', false, 3000);
			b_flg = true;
		}
	});
	return b_flg;
}

/**
* 重命名组
*/
function fn_renameGroup(gid, str_name, node) {
	var obj_param = {'name': str_name, 'gid': gid};
	if ( !fn_checkGroupName(str_name, node, gid) ) {
		$.put_(GROUPS_URL, JSON.stringify(obj_param), function (data) {
			if ( data.status != 0 ) {
				dlf.fn_jNotifyMessage(data.message, 'message', false, 3000); // 查询状态不正确,错误提示
			}
		});
	}
}

/**
* 删除组
*/
function fn_removeGroup(node) {
	var str_param = node.children('a').attr('groupid');
	
	$('#vakata-contextmenu').hide();	// 右键菜单隐藏
	if ( confirm('确定要删除该分组吗？') ) {
		$.delete_(GROUPS_URL + '?ids=' + str_param, '', function (data) {
			if ( data.status == 0 ) {
				$("#corpTree").jstree('remove'); 
			}
		});
	}
}

/**
* 拖拽组
*/
function fn_moveGroup(arr_tids, n_newGroupId, node) {
	var obj_param = {'tids': arr_tids, 'gid': n_newGroupId}

	$.post_(GROUPTRANSFER_URL, JSON.stringify(obj_param), function (data) {
		if ( data.status != 0 ) {
			
		}
	});
}

/**
* 重命名集团名称 
*/
function fn_renameCorp(cid, str_name, node) {
	var obj_param = {'name': str_name, 'cid': cid};
	$.put_(CORP_URL, JSON.stringify(obj_param), function (data) {
		if ( data.status != 0 ) {
			dlf.fn_jNotifyMessage(data.message, 'message', false, 3000); // 查询状态不正确,错误提示
			$.jstree.rollback(node);
		}
	});
}

/**
* 新建定位器
*/
function fn_initCreateTerminal(obj_node, str_groupId) {
	dlf.fn_lockScreen(); // 添加页面遮罩
	dlf.fn_dialogPosition($('#cTerminalWrapper')); // 新增定位器dialog显示
	dlf.fn_onInputBlur();	// input的鼠标样式
	/**
	* 初始化报警查询选择时间
	*/
	$('#hidGroupId').val(str_groupId);	// 保存groupId
	/*var str_nowDate = dlf.fn_changeNumToDateString(new Date().getTime(), 'ymd'), 
		str_nextYearDate = dlf.fn_changeNumToDateString(fn_getNextYear(str_nowDate), 'ymd'),
		obj_stTime = $('#c_begintime'), 
		obj_endTime = $('#c_endtime');

	obj_stTime.click(function() {	// 初始化起始时间，并做事件关联
		WdatePicker({el: 'c_begintime', dateFmt: 'yyyy-MM-dd', readOnly: true, isShowClear: false, maxDate: '#F{$dp.$D(\'c_endtime\')}', qsEnabled: false});
	}).val(str_nowDate);
	
	obj_endTime.click(function() {	// 初始化结束时间，并做事件关联
		WdatePicker({el: 'c_endtime', dateFmt: 'yyyy-MM-dd', readOnly: true, isShowClear: false, minDate:'#F{$dp.$D(\'c_begintime\')}', qsEnabled: false});
	}).val(str_nextYearDate);	*/
	
	$('.j_corpData').val('');
	$('#hidTMobile').val('');
}

/**
* 保存定位器
*/
window.dlf.fn_cTerminalSave = function() {
	var str_tmobile = $('#c_tmobile').val(),
		str_umobile = $('#c_umobile').val(),
		str_beginTime = $('#c_begintime').val(),
		str_endTime = $('#c_endtime').val(),
		str_cnum = $('#c_cnum').val(),
		str_ctype = parseInt($('#c_type').val()),
		str_color = $('#c_color').val(),
		str_brand = $('#c_brand').val(),
		n_groupId = parseInt($('#hidGroupId').val()),
		str_email = '',
		str_address = '',
		str_uname = '',
		obj_corpData = {};
		
	obj_corpData['tmobile'] = str_tmobile;
	obj_corpData['group_id'] = n_groupId;
	obj_corpData['umobile'] = str_umobile;
	obj_corpData['cnum'] = str_cnum;
	obj_corpData['begintime'] = '';	// dlf.fn_changeDateStringToNum(str_beginTime + ' 00:00:00' );
	obj_corpData['endtime'] = '';	// dlf.fn_changeDateStringToNum(str_endTime + ' 23:59:59' );
	obj_corpData['ctype'] = '';	// str_ctype;
	obj_corpData['ccolor'] = '';	// str_color;
	obj_corpData['cbrand'] = '';	//str_brand;
	obj_corpData['email'] = str_email;
	obj_corpData['address'] = str_address;
	obj_corpData['uname'] = str_uname;
	dlf.fn_jsonPost(TERMINALCORP_URL, obj_corpData, 'cTerminal', '定位器信息保存中');
}
// 获取下一年的时间
function fn_getNextYear(str_nowDate) {
	var date = new Date(str_nowDate);
	date.setYear(date.getFullYear()+1);
	return date.getTime();
}

/**
* 修改定位器 todo delete
*/
function fn_initEditTerminal(str_tid) {
	dlf.fn_lockScreen(); // 添加页面遮罩
	dlf.fn_dialogPosition($('#cTerminalEditWrapper')); // 新增定位器dialog显示
	dlf.fn_onInputBlur();	// input的鼠标样式
	/**
	* 初始化选择时间
	*/
	var str_nowDate = dlf.fn_changeNumToDateString(new Date().getTime(), 'ymd'), 
		str_nextYearDate = dlf.fn_changeNumToDateString(fn_getNextYear(str_nowDate), 'ymd'),
		obj_stTime = $('#c_editbegintime'), 
		obj_endTime = $('#c_editendtime');

	obj_stTime.click(function() {	// 初始化起始时间，并做事件关联
		WdatePicker({el: 'c_editbegintime', dateFmt: 'yyyy-MM-dd', readOnly: true, isShowClear: false, maxDate: '#F{$dp.$D(\'c_editendtime\')}', qsEnabled: false});
	}).val(str_nowDate);
	
	obj_endTime.click(function() {	// 初始化结束时间，并做事件关联
		WdatePicker({el: 'c_editendtime', dateFmt: 'yyyy-MM-dd', readOnly: true, isShowClear: false, minDate:'#F{$dp.$D(\'c_editbegintime\')}', qsEnabled: false});
	}).val(str_nextYearDate);	
	$('.j_cterminalEdit').val('');
	$.get_(TERMINALCORP_URL + '?tid=' + str_tid, '', function(data) {
		if ( data.status == 0 ) {
			var obj_data = data.res,
				str_btime = dlf.fn_changeNumToDateString(obj_data.begintime * 1000, 'ymd'),
				str_etime = dlf.fn_changeNumToDateString(obj_data.endtime * 1000, 'ymd'),
				str_cnum = obj_data.cnum,
				str_type = obj_data.ctype,
				str_color = obj_data.ccolor,
				str_brand = obj_data.cbrand;
			
			$('.j_tmobile').html(obj_data.tmobile);
			$('.j_umobile').html(obj_data.umobile);
			$('#c_editbegintime').val(str_btime).data('c_editbegintime', str_btime);
			$('#c_editendtime').val(str_etime).data('c_editendtime', str_etime);
			$('#c_editcnum').val(str_cnum).data('c_editcnum', str_cnum);;
			$('#c_editctype').val(str_type).data('c_editctype', parseInt(str_type));
			$('#c_editccolor').val(str_color).data('c_editccolor', str_color);;
			$('#c_editcbrand').val(str_brand).data('c_editcbrand', str_brand);;
			$('#hidTid').val(str_tid);
		} else {
			dlf.fn_jNotifyMessage(data.message, 'message', false, 4000); // 查询状态不正确,错误提示
		}
	});
}

/**
* 编辑保存定位器
*/
window.dlf.fn_cEditTerminalSave = function() {
	var n_num = 0,
		obj_terminalData = {};
	$('.j_cterminalEdit').each(function(index, dom) {
		var obj_input = $(dom),
			str_val = obj_input.val(),
			str_id = obj_input.attr('id'),
			str_data = $('#'+str_id).data(str_id);
			
		if ( str_val != str_data ) {
			str_id = str_id.substr(6, str_id.length);
			if ( str_id == 'endtime' ) {
				str_val = dlf.fn_changeDateStringToNum(str_val + ' 23:59:59' );
			} else if ( str_id == 'begintime' ) {
				str_val = dlf.fn_changeDateStringToNum(str_val + ' 00:00:00' );
			}
			obj_terminalData[str_id] = str_val;
		}
	});
	
	for(var param in obj_terminalData) {	// 我的资料中修改项的个数
		n_num = n_num +1;
	}
	if ( n_num != 0 ) {	// 如果有修改内容 ，向后台发送post请求，否则提示未做任何修改
		obj_terminalData['tid'] = $('#hidTid').val();
		dlf.fn_jsonPut(TERMINALCORP_URL, obj_terminalData, 'cTerminalEdit', '定位器信息保存中');
	} else {
		dlf.fn_jNotifyMessage('您未做任何修改。', 'message', false, 4000); // 查询状态不正确,错误提示
		dlf.fn_unLockContent(); // 清除内容区域的遮罩
	}
}

/**
* 删除定位器
*/
function fn_removeTerminal(node) {
	var obj_target = node.children('a'),
		str_login = obj_target.attr('clogin'),
		str_param = obj_target.attr('tid');
	$('#vakata-contextmenu').hide();	// 右键菜单隐藏
	
	if ( confirm('确定要删除该定位器吗？') ) {
		$.delete_(TERMINALCORP_URL + '?ids=' + str_param, '', function (data) {
			if ( data.status == 0 ) {
				fn_updateTerminalCount('sub');				
				$("#corpTree").jstree('remove');				
				// 删除地图marker
				if ( obj_selfmarkers[str_param] ) {
					mapObj.removeOverlay(obj_selfmarkers[str_param]);
					delete obj_selfmarkers[str_param];
				}
				var obj_current = $('.jstree-clicked'),
					b_class = obj_current.hasClass('groupNode'),
					str_tid = obj_current.attr('tid') || $('.j_terminal').eq(0).attr('tid');
						
				if ( str_tid != undefined ) {
					if ( b_class ) {
						obj_current = $('.j_terminal').eq(0);
					}
					$('.jstree-clicked').removeClass('jstree-clicked');
					obj_current.addClass('jstree-clicked');
					dlf.fn_switchCar(str_tid, obj_current);
				} else {
					fn_initCarInfo();
				}
			}
		});
	}
}

/**
* 初始化告警统计
*/
window.dlf.fn_initStatics = function() {
	dlf.fn_lockScreen(); // 添加页面遮罩
	dlf.fn_dialogPosition($('#staticsWrapper')); // 新增定位器dialog显示
	/**
	* 初始化报警查询选择时间
	*/
	var str_nowDate = dlf.fn_changeNumToDateString(new Date().getTime(), 'ymd'), 
		str_nextYearDate = dlf.fn_changeNumToDateString(fn_getNextYear(str_nowDate), 'ymd'),
		obj_stTime = $('#c_eventbegintime'), 
		obj_endTime = $('#c_eventendtime');

	obj_stTime.click(function() {	// 初始化起始时间，并做事件关联
		WdatePicker({el: 'c_eventbegintime', dateFmt: 'yyyy-MM-dd HH:mm:ss', readOnly: true, isShowClear: false, maxDate: '#F{$dp.$D(\'c_eventendtime\')}', qsEnabled: false});
	}).val(str_nowDate + ' 00:00:00');
	
	obj_endTime.click(function() {	// 初始化结束时间，并做事件关联
		WdatePicker({el: 'c_eventendtime', dateFmt: 'yyyy-MM-dd HH:mm:ss', readOnly: true, isShowClear: false, minDate:'#F{$dp.$D(\'c_eventbegintime\')}', qsEnabled: false});
	}).val(str_nowDate+' '+dlf.fn_changeNumToDateString(new Date(), 'sfm'));
	
	$('#staticsTableHeader').nextAll().remove();	//清除页面数据
	n_pageNum = 0;
	pagecnt = -1;
	/** 
	* 上一页按钮 下一页按钮
	*/
	var obj_prevPage = $('#prevPage'), 
		obj_nextPage = $('#nextPage'), 
		obj_pageContainer = $('#staticsPage'),
		obj_currentPage = $('#currentPage'),
		obj_search = $('#staticsBtn');
		
	obj_search.show();
	obj_pageContainer.hide();
	/** 
	* 绑定按钮事件
	*/
	dlf.fn_setItemMouseStatus(obj_search, 'pointer', new Array('cx', 'cx2'));
	dlf.fn_setItemMouseStatus(obj_prevPage, 'pointer', new Array('prevPage2', 'prevPage1'));
	dlf.fn_setItemMouseStatus(obj_nextPage, 'pointer', new Array('nextPage2', 'nextPage1'));
	/**
	* 上下页事件绑定
	*/
	obj_prevPage.click(function() {
		if ( n_pageNum <= 0) {
			return;
		}
		obj_currentPage.text(--n_pageNum+1);
		fn_searchStatics(n_pageNum);
	});
	obj_nextPage.click(function() {
		if ( n_pageNum >= pagecnt-1 ) {
			return;
		}
		obj_currentPage.text(++n_pageNum+1);
		fn_searchStatics(n_pageNum);
	});
	
	obj_search.unbind('click').bind('click', function() {	// 告警记录查询事件
		pagecnt = -1;
		n_pageNum = 0;
		fn_searchStatics(n_pageNum);
	});
}

/**
* 查询统计
*/
function fn_searchStatics(n_num) {
	var n_startTime = $('#c_eventbegintime').val(), // 用户选择时间
		n_endTime = $('#c_eventendtime').val(), // 用户选择时间
		n_bgTime = dlf.fn_changeDateStringToNum(n_startTime), // 开始时间
		n_finishTime = dlf.fn_changeDateStringToNum(n_endTime), //结束时间
		n_category = $('#category').val(), 
		obj_staticsParam = {'start_time': n_bgTime, 'end_time': n_finishTime, 
				'pagenum': n_pageNum, 'pagecnt': pagecnt};
	
	dlf.fn_jNotifyMessage('告警统计查询中...', 'message', true);
	
	$.post_(STATICS_URL, JSON.stringify(obj_staticsParam), function(data) {	// 获取告警记录信息
		if ( data.status == 0 ) {  // success
			var obj_prevPage = $('#prevPage'), 
				obj_nextPage = $('#nextPage'),
				n_eventDataLen = 0,
				str_tbodyText = '';
				
			$('#staticsTableHeader').nextAll().remove();	//清除页面数据
			pagecnt = data.pagecnt;
			arr_staticsData = data.res;
			n_eventDataLen = arr_staticsData.length; 	//记录数
			
			if ( n_eventDataLen > 0 ) {	// 如果查询到数据
				$('#staticsPage').show(); //显示分页
				if ( pagecnt > 1 ) {	// 总页数大于1 
					if ( n_num > 0 && n_num < pagecnt-1 ) {  //上下页都可用 
						dlf.fn_setItemMouseStatus(obj_prevPage, 'pointer', new Array('prevPage0', 'prevPage1'));
						dlf.fn_setItemMouseStatus(obj_nextPage, 'pointer', new Array('nextPage0', 'nextPage1'));
					} else if ( n_num >= pagecnt-1 ) {	//下一页不可用						
						dlf.fn_setItemMouseStatus(obj_prevPage, 'pointer', new Array('prevPage0', 'prevPage1'));
						dlf.fn_setItemMouseStatus(obj_nextPage, 'default', 'nextPage2');
					} else {	//上一页不可用					
						dlf.fn_setItemMouseStatus(obj_prevPage, 'default', 'prevPage2');
						dlf.fn_setItemMouseStatus(obj_nextPage, 'pointer', new Array('nextPage0', 'nextPage1'));
					}				
				} else {	//总页数小于1  上下页都不可用
					dlf.fn_setItemMouseStatus(obj_prevPage, 'default', 'prevPage2');
					dlf.fn_setItemMouseStatus(obj_nextPage, 'default', 'nextPage2');
				}
				
				if ( n_num == 0 ) {	// 只有在点击查询按钮时才重新显示总页数
					$('#pageCount').text(data.pagecnt); //总页数
					$('#currentPage').html('1');	//当前页数
				}
				for(var i = 0; i < n_eventDataLen; i++) {
					var obj_statics = arr_staticsData[i], 
						str_alias = obj_statics.alias,	// 定位器手机号
						str_illegalmove = obj_statics.illegalmove + '次',	// 非法移动
						str_sos = obj_statics.sos + '次',	// sos
						str_illegashake =  obj_statics.illegashake + '次', // 震动
						str_heartbeat_lost = obj_statics.heartbeat_lost + '次',	// 心跳
						str_powerlow = obj_statics.powerlow + '次';	// 低电
						//str_html = str_illegalmove + str_sos + str_illegashake + str_heartbeat_lost + str_powerlow;
					
					/**
					* 拼接table
					*/
					str_tbodyText+= '<tr>';
					str_tbodyText+= '<td>'+ str_alias +'</td>';	// 定位器
					str_tbodyText+= '<td>'+ str_illegalmove +'</td>';	// 告警详情
					/*str_tbodyText+= '<td>'+ str_sos +'</td>';	// 告警详情	暂不显示	*/
					str_tbodyText+= '<td>'+ str_illegashake +'</td>';	// 告警详情		
					str_tbodyText+= '<td>'+ str_heartbeat_lost +'</td>';	// 告警详情		
					str_tbodyText+= '<td>'+ str_powerlow +'</td>';	// 告警详情				
					str_tbodyText+= '</tr>';
				}
				$('#staticsTableHeader').after(str_tbodyText);
				/** 
				* 初始化奇偶行
				*/
				$('.dataTable tr').mouseover(function() {
					$(this).css('background-color', '#FFFACD');
				}).mouseout(function() {
					$(this).css('background-color', '');
				});		
				dlf.fn_closeJNotifyMsg('#jNotifyMessage');
			} else {
				$('#staticsPage').hide(); //显示分页
				dlf.fn_jNotifyMessage('该时间段没有告警记录，请选择其它时间段。', 'message', false, 6000);
			}
		} else if ( data.status == 201 ) {	// 业务变更
			dlf.fn_showBusinessTip('event');
		} else {
			dlf.fn_jNotifyMessage(data.message, 'message', false, 3000);	
		}
	},
	function(XMLHttpRequest, textStatus, errorThrown) {
		dlf.fn_serverError(XMLHttpRequest);
	});
}

/**
* 验证定位器手机号
*/
window.dlf.fn_checkTMobile = function(str_tmobile) {
	$.get_(CHECKMOBILE_URL + '/' + str_tmobile, '', function(data){
		if ( data.status != 0 ) {
			$('#hidTMobile').val('1');
			dlf.fn_jNotifyMessage('定位器手机号已存在。', 'message', false, 5000);
			return;
		} else {
			$('#hidTMobile').val('');
		}
	});
}
/**
* 验证集团名是否重复
*/
window.dlf.fn_checkCName = function(str_cname) {
	$.get_(CHECKCNAME_URL + '/' + str_cname, '', function(data){
		if ( data.status != 0 ) {
			$('#hidCName').val('1');
			dlf.fn_jNotifyMessage('集团名称已存在。', 'message', false, 5000);
			return;
		} else {
			$('#hidCName').val('');
		}
	});
}
})();