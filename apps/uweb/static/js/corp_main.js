/**
* 集团用户操作方法
* obj_carsData: 存储lastinfo中所有定位器的信息
* str_currentTid: 上次lastinfo的选中定位器tid
* arr_autoCompleteData: autocomplete 查询数据
* b_createTerminal： 标记是新增定位器操作 方便switchcar到该新增车辆
* n_onlineCnt：在线终端总数
* n_offlineCnt：离线终端总数
* arr_treeNodeChecked: 树中所有选中的终端
* arr_submenuGroups: 移动至组的所有组名
*/
var obj_carsData = {},
	str_currentTid = '',
	arr_autoCompleteData = [],
	b_createTerminal = false,
	n_onlineCnt = 0,
	n_offlineCnt = 0, 
	arr_treeNodeChecked = [],
	arr_submenuGroups = [];
	
(function() {

/**
*  创建右键菜单，设置每个节点的菜单右键菜单
*/
function customMenu(node) {
	var obj_node = $(node),
		obj_currentGroup = obj_node.parent().siblings('a'),
		str_currentGroupName = obj_currentGroup.attr('title'),	// 当前定位器所在组名
		str_groupId = obj_currentGroup.attr('groupId'),	// 当前所在组的组ID
		items = null,		// 菜单的操作方法
		submenuItems = {},	// 二级菜单
		subDefendItems = {},	// 批量设防撤防二级菜单
		renameLabel = '',	// 重命名lable
		createLabel = '',	// 新建lable
		batchImportLabel = '',	// 批量导入
		batchDeleteLabel = '',	// 批量删除
		moveToLabel = '',	// 移动至
		eventLabel = '',	// 告警查询
		terminalLabel = '',	// 参数设置
		deleteLabel = '',	// 删除lable
		batchDefendLabel = '',	// 批量设防*撤防
		singleDefendLabel = '';	// 单个定位器设防撤防
	
	if ( obj_node.hasClass('j_corp') ) {		// 集团右键菜单
		renameLabel = '重命名集团';
		createLabel = '新建分组';
		deleteLabel = '删除集团';
	} else if (obj_node.hasClass('j_group')) {	// 组右键菜单
		renameLabel = '重命名组';
		deleteLabel = '删除分组';
		createLabel = '添加单个定位器';
		batchImportLabel = '批量导入定位器';
		batchDeleteLabel = '批量删除定位器';
		batchDefendLabel = '批量设防/撤防';
	} else {									// 定位器右键菜单
		terminalLabel = '参数设置';
		deleteLabel = '删除定位器';
		eventLabel = '告警查询';
		moveToLabel = '移动定位器';
		singleDefendLabel = '设防/撤防';
	}
	// 定位器的移动至菜单项
	
	for ( var i in arr_submenuGroups ) {
		var obj_group = arr_submenuGroups[i],
			str_groupName = obj_group.groupName,
			str_groupId = obj_group.groupId;
		
		if ( str_currentGroupName != str_groupName ) {
			submenuItems['moveToGroup' + str_groupId ] = fn_createSubMenu(obj_group);
		}
	}
	// 右键菜单执行的操作
	items = {
		"create" : {
			"label" : createLabel,
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
		"event": {
			"label" : eventLabel,
			"action" : function(obj) {
				// todo 告警查询初始化
				dlf.fn_initRecordSearch('event');
			}
		},
		"terminalSetting": {	// 参数设置
			"label" : terminalLabel,
			"action" : function (obj) {
				dlf.fn_initCorpTerminal();
				return false;
			}
		},
		"defend": {	// 单个定位器设防撤防
			"label" : singleDefendLabel,
			"action" : function (obj) {
				dlf.fn_defendQuery(obj.children('a').text().substr(2));
			}
		},
		"batchImport": {	// 批量导入定位器操作菜单
			"label" : batchImportLabel,
			"action" : function (obj) {
				// todo 批量导入定位器操作
				var obj_batch = obj.children('a'),
					n_gid = obj_batch.attr('groupid'),
					str_gname = obj_batch.attr('title');
				fn_initBatchImport(n_gid, str_gname);
				return false;
			}
		},
		"batchDelete": {	// 批量删除选中定位器操作菜单
			"label" : batchDeleteLabel,
			"action" : function (obj) {
				fn_batchOperateValidate(obj, '删除');
			}
		},
		"batchDefend" : {
			"label" : batchDefendLabel,
			"submenu": {
				'defend0': {
					"label" : "批量设防",
					"action" : function (obj) {
						fn_batchOperateValidate(obj, '设防');
					}
				},
				'defend1': {
					"label" : "批量撤防",
					"action" : function (obj) {
						fn_batchOperateValidate(obj, '撤防');
					}
				}
			}
		},
		"rename" : {
			"label" : renameLabel,
			"action" : function(obj) {
				this.rename(obj);
			}
		},
		"moveTo": {
			"label" : moveToLabel,
			"submenu": submenuItems
		},
		"remove" : {
			"label" : deleteLabel,
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
	// 终端右键菜单菜单
   if ( obj_node.hasClass('j_leafNode') ) {
		delete items.create;
		delete items.batchImport;
		delete items.batchDelete;
		delete items.rename;
		delete items.batchDefend;
   }
   // 集团右键菜单删除菜单
   if ( obj_node.hasClass('j_corp')  ) {
		delete items.remove;
		delete items.batchImport;
		delete items.moveTo;	
		delete items.event;	
		delete items.batchDelete;
		delete items.terminalSetting;
		delete items.batchDefend;
		delete items.defend;
   }
   if ( obj_node.hasClass('j_group') ) {
		delete items.moveTo;
		delete items.event;
		delete items.terminalSetting;
		delete items.defend;
   }
   if ( $('#u_type').val() == USER_OPERATOR ) {	// 操作员屏蔽右键
		delete items.create;
		delete items.batchImport;
		delete items.batchDelete;
		delete items.remove;
		delete items.moveTo;
		delete items.event;	
		delete items.rename;
		delete items.terminalSetting;
		delete items.batchDefend;
		delete items.defend;
   }
   return items;
}

/**
* 批量操作的数据验证：批量删除、批量设防撤防 (判断是否选中的是定位器)
*/
function fn_batchOperateValidate(obj, str_msg) {
	var obj_currentGroupChildren = obj.children('ul'),
		str_gname = obj.children('a').text();	// 组名
	
	//  批量删除选中定位器操作
	if ( obj_currentGroupChildren.length <= 0 ) {	// 没有定位器，不能批量删除
		dlf.fn_jNotifyMessage('该组下没有定位器。', 'message', false, 3000); // 执行操作失败，提示错误消息
		return false;
	} else if ( obj.hasClass('jstree-unchecked') ) {	// 要删除定位器的组没有被选中
		dlf.fn_jNotifyMessage('没有选中要'+ str_msg +'的定位器。', 'message', false, 3000); // 执行操作失败，提示错误消息
		return false;
	} else {
		var arr_tids = [],
			arr_dataes = [],
			obj_params = {};
		// 当前组下选中的tid
		obj_currentGroupChildren.children('li').each(function() {
			var obj_checkedTerminal = $(this),
				obj_terminalALink = obj_checkedTerminal.children('a'),
				b_isChecked = obj_checkedTerminal.hasClass('jstree-checked'),
				str_tid = obj_terminalALink.attr('tid'),
				str_alias = obj_terminalALink.text(),	// tnum
				str_tmobile = obj_terminalALink.attr('title'),	// tmobile
				obj_carsData = $('.j_carList').data('carsData');
			
			if ( b_isChecked ) {
				arr_tids.push(str_tid);
				arr_dataes.push({'alias': str_alias, 'tmobile': str_tmobile, 'tid': str_tid, 'mennual_status': obj_carsData[str_tid].mannual_status});
			}
			obj_params['tids'] = arr_tids;
			obj_params['characters'] = arr_dataes;
			obj_params['gname'] = str_gname;
		});
		str_msg == '删除' ? fn_batchRemoveTerminals(obj_params) : dlf.fn_initBatchDefend(str_msg, obj_params);
	}
}

/**
* 生成二级菜单项
* obj_group: 二级菜单项要显示的内容对象
*/
function fn_createSubMenu(obj_group) {
	var str_groupName = obj_group.groupName,
		str_groupId = obj_group.groupId;
		
	return {
		"label": str_groupName, 
		"action": function(obj) {
			// 移动至组的方法实现
			var str_moveTid = obj.children('a').attr('tid');
			fn_moveGroup([str_moveTid], str_groupId, '', obj.attr('id'));
		}
	}
}

/**
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
		"plugins": [ "themes", "html_data", "ui", "contextmenu",'crrm', "types", 'dnd', 'checkbox'],
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
			if ( str_tid ) {	// 只有终端才可以移动到组
				arr_tids.push(str_tid);
				fn_moveGroup(arr_tids, str_groupId, data.rlbk);
			}
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
		// 将之前的checked状态填充 
		var n_treeNodeCheckLen = arr_treeNodeChecked.length;
		
		if ( n_treeNodeCheckLen > 0 ) {
			for ( var i = 0; i < n_treeNodeCheckLen; i++ ) {
				$('#corpTree').jstree('check_node', arr_treeNodeChecked[i]);
			}
			arr_treeNodeChecked = [];
		}		
	}).bind('contextmenu.jstree', function(event, data) {	// 右键除当前定位器外其余都不被选中
		var obj_current = fn_nodeCurrentNode(event.target);					
		
		$('.j_terminal[tid='+ str_currentTid +']').addClass(JSTREECLICKED);
		if ( obj_current.b_terminalClass ) {	// 如果选中的是定位器
			var str_tid = obj_current.attr('tid');
			
			if ( str_currentTid == str_tid ) {	// 如果是同辆车则不switchcar
				return;
			} else {
				obj_current.removeClass(JSTREECLICKED);
			}
		} else {
			obj_current.removeClass(JSTREECLICKED);
		}
	}).bind('click.jstree', function(event, data) {	// 选中节点事件
		var obj_current = fn_nodeCurrentNode(event.target);					
		
		if ( obj_current.b_terminalClass ) {	// 如果选中的是定位器
			var str_tid = obj_current.attr('tid');
			
			if ( str_currentTid == str_tid ) {	// 如果是同辆车则不switchcar
				return;
			}
			dlf.fn_switchCar(str_tid, obj_current); // 登录成功,   
		} else {	// 集团或组	如果选中集团或组的话没有被选中的样式、上一次选中的定位器还被选中			
			$('.j_terminal[tid='+ str_currentTid +']').addClass(JSTREECLICKED);
			obj_current.removeClass(JSTREECLICKED);
			return false;
		}
	}).bind('dblclick.jstree', function(event, data) {
		
		var obj_target = $(event.target),
			b_class = obj_target.hasClass('j_terminal')

		if ( b_class ) {	// 双击定位器
			dlf.fn_initCorpTerminal();
		} else {
			return false;
		}
	}).bind('check_node.jstree', function(obj) {
		// console.log(obj);	// 记住选中的
	});
}

/**
* jstree 的事件target对象获取
*/
function fn_nodeCurrentNode(target) {
	var str_nodeName = target.nodeName,
		obj_current = $(target),
		b_terminalClass = obj_current.hasClass('j_terminal');
					
	if ( str_nodeName == 'INS' ) {
		obj_current = $(target).parent();
		b_terminalClass = obj_current.hasClass('j_terminal');
	}
	obj_current.b_terminalClass = b_terminalClass;
	return obj_current;
}

/**
* 更新终端总数
* str_operation: add(新增定位器)、sub(删除定位器)
* num: 新增或删除定位器的个数
*/
function fn_updateTerminalCount(str_operation, num) {
	
	switch ( str_operation ) {
		case 'add':
			n_onlineCnt = n_onlineCnt + num;
			break;
		case 'sub':
			n_offlineCnt = n_offlineCnt - num;
			break;
		default:
			break;
	}
	// 更新定位器总数
	$('.carCount').html( n_onlineCnt + n_offlineCnt + '(全部)');
	$('.onlineCount').html(n_onlineCnt + '(在线)');
	$('.offlineCount').html(n_offlineCnt + '(离线)');
		
}

/**
* 无终端时车辆信息栏显示-
*/
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
	var obj_current = $('.j_leafNode a[class*='+ JSTREECLICKED +']'),
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
				str_html += '<li class="j_corp" id="treeNode_'+ str_corpId +'"><a title="'+ str_corpName +'" corpid="'+ str_corpId +'" class="corpNode" href="#">'+ str_corpName +'</a>';
			}
			
			arr_autoCompleteData = [];
			arr_submenuGroups = [];
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
					
					arr_submenuGroups.push({'groupId': str_groupId, 'groupName': str_groupName});
					str_html += '<li class="j_group" id="groupNode_'+ str_groupId +'"><a href="#" class="groupNode" groupId="'+ str_groupId +'" title="'+ str_groupName +'" id="group_'+ str_groupId +'">'+ str_groupName +'</a>';
					
					if ( n_carsLength > 0 ) {
						str_html += '<ul>';
						if ( str_tempFirstTid == '' ) {
							str_tempFirstTid = 'leaf_' + arr_groups[i].cars[0].tid;	// 第一个分组的第一个定位器 id
						}
						for ( var x = 0; x < n_carsLength; x++) {	// 添加组下面的定位器
							var obj_car = arr_cars[x],
								str_tid = obj_car.tid,
								str_alias= obj_car.alias,
								str_mobile = obj_car.mobile,	// 车主手机号
								str_login = obj_car.login;
								
							obj_carsData[str_tid] =  obj_car;
							arr_tempTids.push(str_tid); //tid组string 串
							if ( str_login == LOGINOUT ) {
								str_html += '<li class="jstree-leaf j_leafNode" id="leafNode_'+ str_tid +'"><a actiontrack="no" clogin="'+ obj_car.login+'" fob_status="" tid="'+ str_tid +'" keys_num="'+ obj_car.keys_num +'" title="'+ str_mobile +'" class="terminalNode j_terminal jstree-draggable" href="#" id="leaf_'+ str_tid +'">'+ str_alias +'</a></li>';
							} else {
								str_html += '<li class="jstree-leaf j_leafNode" id="leafNode_'+ str_tid +'"><a actiontrack="no" clogin="'+ obj_car.login+'" fob_status="" tid="'+ str_tid +'" keys_num="'+ obj_car.keys_num +'" title="'+ str_mobile +'" class="terminalNode j_terminal jstree-draggable" href="#" id="leaf_'+ str_tid +'">'+ str_alias +'</a></li>';	
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
				
				/**
				* 判断车辆是否选中
				*/
				var obj_loadTreePanel = $('#corpTree .loadTree');
					
				//当前车辆列表是否数据
				if ( dlf.fn_isEmptyObj(obj_loadTreePanel) ) {
					//如果有车获取车辆选中状态
					dlf.fn_eachCheckedNode('.j_group');
					dlf.fn_eachCheckedNode('.j_leafNode');
				}
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

/**
* 对node节点做遍历查找选中的节点
*/
window.dlf.fn_eachCheckedNode = function(str_eachNode) {
	$(str_eachNode).each(function(leafEvent) { 
		var str_tempLeafClass = $(this).attr('class'), 
			str_tempLeafId = '#' + $(this).attr('id');
	
		if ( str_tempLeafClass.search(JSTREECLICKED) != -1){
			arr_treeNodeChecked.push(str_tempLeafId);
		}
	});
}

/**
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
				str_crntTid = $('.j_leafNode a[class*='+ JSTREECLICKED +']').attr('tid');

			$('#txtautoComplete').val( ui.item.label);
			if ( str_crntTid == str_tid ) {
				return false;
			}
			dlf.fn_switchCar(str_tid, obj_itemLi);
			return false;
		}
	});
}

/**
* 更新树节点的数据
* obj_corp: 最新的集团数据
*/
function fn_updateTreeNode(obj_corp) {
	var arr_groups = obj_corp.groups,	// all groups 
		n_groupLength = arr_groups.length,	// group length
		str_corpName = obj_corp.name,	// corp name
		str_corpId = obj_corp.cid;		// corp id
	
	$('.j_corp a[corpId='+ str_corpId +']').html('<ins class="jstree-checkbox">&nbsp;</ins><ins class="jstree-icon">&nbsp;</ins>' + str_corpName).attr('title', str_corpName);	// 更新集团名 <img src="/static/images/corpImages/corp.png">
	for ( var gIndex in arr_groups ) {
		var obj_group = arr_groups[gIndex],
			str_groupName = obj_group.name,
			arr_cars = obj_group.cars,
			n_carLength = arr_cars.length;

		$('#group_'+ obj_group.gid).html('<ins class="jstree-checkbox">&nbsp;</ins><ins class="jstree-icon">&nbsp;</ins>' + str_groupName).attr('title', str_groupName);	// 更新组名<img src="/static/images/corpImages/gorup.png">
		
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
				obj_leaf.html('<ins class="jstree-checkbox">&nbsp;</ins><ins class="jstree-icon">&nbsp;</ins>' + str_alias).attr('title', str_tmobile).attr('clogin', n_login);	// 更新定位器名<img src="/static/images/corpImages/'+ str_imgUrl +'">
				
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
	$('.corpNode ins[class=jstree-icon]').css('backgroundPosition', '0px 0px');
}

/**
* 更新车辆状态
*/
function fn_updateAllTerminalLogin() {
	$('.j_terminal').each(function() {
		dlf.fn_updateTerminalLogin($(this));
	});
}

window.dlf.fn_updateTerminalLogin = function(obj_this) {
	var	str_login = obj_this.attr('clogin'),
		str_imgUrl = '',
		str_color = '',
		obj_ins = obj_this.children('ins[class=jstree-icon]');	// todo
	
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
* cnum: 要更新的定位器别名
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
	obj_current.html('<ins class="jstree-checkbox">&nbsp;</ins><ins class="jstree-icon">&nbsp;</ins>' + str_tempAlias);
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
* obj_newData: 最新的lastinfo数据
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
* cid: 集团id
* str_newName: 组名
* obj_rollBack: 如果新建失败要回滚的对象
* obj_newNode: 新增的组节点
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
					dlf.fn_corpGetCarData();	// 重新加载树
				} else {
					$.jstree.rollback(obj_rollBack);
				}
			});
		}
	}
}

/**
* 判断组名是否重复
*/
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
			if ( data.status == 0 ) {
				dlf.fn_corpGetCarData();	// 重新加载树
			} else {
				dlf.fn_jNotifyMessage(data.message, 'message', false, 3000); // 查询状态不正确,错误提示
				return false;
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
				dlf.fn_corpGetCarData();	// 重新加载树
			} else {
				dlf.fn_jNotifyMessage(data.message, 'message', false, 3000); // 查询状态不正确,错误提示
				return false;
			}
		});
	}
}

/**
* 拖拽组、移动至其他组
*/
function fn_moveGroup(arr_tids, n_newGroupId, obj_rlbk, node_id) {
	var obj_param = {'tids': arr_tids, 'gid': n_newGroupId}

	if ( node_id ) {
		$('#corpTree').jstree('move_node', '#' + node_id, '#groupNode_' + n_newGroupId);
	} else {
		$.post_(GROUPTRANSFER_URL, JSON.stringify(obj_param), function (data) {
			if ( data.status == 0 ) {
				dlf.fn_corpGetCarData();	// 重新加载树
			} else {
				dlf.fn_jNotifyMessage(data.message, 'message', false, 3000); // 执行操作失败，提示错误消息
				$.jstree.rollback(obj_rlbk);
			}
		});
	}
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
* 添加单个定位器
*/
function fn_initCreateTerminal(obj_node, str_groupId) {
	dlf.fn_dialogPosition('cTerminal'); // 新增定位器dialog显示
	dlf.fn_lockScreen(); // 添加页面遮罩
	dlf.fn_onInputBlur();	// input的鼠标样式
	/**
	* 初始化报警查询选择时间
	*/
	$('#hidGroupId').val(str_groupId);	// 保存groupId
	$('.j_corpData').val('');
	$('#hidTMobile').val('');
}

/**
* 保存单个定位器
*/
window.dlf.fn_cTerminalSave = function() {
	var str_tmobile = $('#c_tmobile').val(),
		str_umobile = $('#c_umobile').val(),
		str_cnum = $('#c_cnum').val(),
		n_groupId = parseInt($('#hidGroupId').val()),
		obj_corpData = {};
		
	obj_corpData['tmobile'] = str_tmobile;
	obj_corpData['group_id'] = n_groupId;
	obj_corpData['umobile'] = str_umobile;
	obj_corpData['cnum'] = str_cnum;
	dlf.fn_jsonPost(TERMINALCORP_URL, obj_corpData, 'cTerminal', '定位器信息保存中');
}

/**
* 获取下一年的时间
*/
function fn_getNextYear(str_nowDate) {
	var date = new Date(str_nowDate);
	date.setYear(date.getFullYear()+1);
	return date.getTime();
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
		$.delete_(TERMINALCORP_URL + '?tid=' + str_param, '', function (data) {
			if ( data.status == 0 ) {
				fn_updateTerminalCount('sub', 1);				
				$("#corpTree").jstree('remove');				
				// 删除地图marker
				if ( obj_selfmarkers[str_param] ) {
					mapObj.removeOverlay(obj_selfmarkers[str_param]);
					delete obj_selfmarkers[str_param];
				}
				var obj_current = $('.' + JSTREECLICKED),
					b_class = obj_current.hasClass('groupNode'),
					str_tid = obj_current.attr('tid') || $('.j_terminal').eq(0).attr('tid');
						
				if ( str_tid != undefined ) {
					if ( b_class ) {
						obj_current = $('.j_terminal').eq(0);
					}
					$('.' + JSTREECLICKED).removeClass(JSTREECLICKED);
					obj_current.addClass(JSTREECLICKED);
					dlf.fn_switchCar(str_tid, obj_current);
				} else {
					fn_initCarInfo();
				}
			} else {
				dlf.fn_jNotifyMessage(data.message, 'message', false, 3000); // 查询状态不正确,错误提示
				return false;
			}
		});
	}
}

/**
* 批量删除数据回显
*/
function fn_initBatchDeleteData(obj_params) {
	var obj_param = {'tids': obj_params.tids};
	
	dlf.fn_echoData('batchDeleteTable', obj_params, '删除');
	$('.j_batchDeleteHead').html(obj_params.gname);	// 表头显示组名
	
	$('.j_batchDelete').unbind('click').bind('click', function() {
		if ( confirm('确定要删除以上定位器吗？') ) {
			dlf.fn_jNotifyMessage('定位器正在删除中' +　WAITIMG, 'message', false, 3000); // 查询状态不正确,错误提示
			$.post_(BATCHDELETE_URL, JSON.stringify(obj_param), function (data) {
				var arr_res = data.res,	
					arr_success = [],
					n_successLen = 0;
				
				if ( data.status == 0 ) {
					dlf.fn_closeJNotifyMsg('#jNotifyMessage');
					// 返回数据res中提取删除成功的终端
					for ( var i in arr_res ) {
						var obj_result = arr_res[i],
							n_success = obj_result.status,
							str_tid = obj_result.tid,
							str_status = '',
							obj_updateTd = $('.batchDeleteTable tr td[tid='+ str_tid +']');
							
						if ( n_success == 0 ) {
							arr_success.push(str_tid);
							str_status = '删除成功';
							obj_updateTd.addClass('fileStatus4');
						} else if ( n_success == -1 ) {
							str_status = '删除失败';
							obj_updateTd.addClass('fileStatus3');
						}
						obj_updateTd.html(str_status);	// 更新保存状态
					}
					n_successLen = arr_success.length;	// 成功删除的终端个数
					fn_updateTerminalCount('sub', n_successLen);
					$('.j_batchDelete').removeClass('operationBtn').addClass('btn_delete').attr('disabled', true);	// 批量删除按钮变成灰色并且不可用
					/**
					* 删除节点
					*/
					for ( var i in arr_success ) {
						var str_tid = arr_success[i];
						
						$("#corpTree").jstree('remove', '#leafNode_' + str_tid );
					}
					//$("#corpTree").jstree('remove');				
					// 删除地图marker
					for ( var i = 0; i < n_successLen; i++ ) {
						var str_tid = arr_success[i];
						
						if ( obj_selfmarkers[str_tid] ) {
							mapObj.removeOverlay(obj_selfmarkers[str_tid]);
							delete obj_selfmarkers[str_tid];
						}
					}
					var obj_current = $('.'+ JSTREECLICKED),
						b_class = obj_current.hasClass('groupNode'),
						str_tid = obj_current.attr('tid') || $('.j_terminal').eq(0).attr('tid');
							
					if ( str_tid != undefined ) {
						if ( b_class ) {
							obj_current = $('.j_terminal').eq(0);
						}
						$('.'+ JSTREECLICKED ).removeClass(JSTREECLICKED);
						obj_current.addClass(JSTREECLICKED);
						dlf.fn_switchCar(str_tid, obj_current);
					} else {
						fn_initCarInfo();
					}
				} else {
					dlf.fn_jNotifyMessage(data.message, 'message', false, 3000); // 查询状态不正确,错误提示
					return false;
				}
			});
		}
	});
	
}

/**
* 批量删除定位器
*/
function fn_batchRemoveTerminals(obj_params) {
	$('#vakata-contextmenu').hide();	// 右键菜单隐藏
	$('#batchDeleteDialog').attr('title', '批量删除定位器').dialog('option', 'title', '批量删除定位器').dialog("open");
	// 数据回显
	$('.j_batchDelete').removeClass('btn_delete').addClass('operationBtn').attr('disabled', false);	// 批量删除按钮变成绿色并且可用
	fn_initBatchDeleteData(obj_params);
}

/**
*二级菜单事件
*/
window.dlf.fn_fillNavItem = function() {
	var obj_navItemUl = $('.j_countNavItem'),
		obj_navOffset = $('#recordCount').offset();
		
	obj_navItemUl.css('left',obj_navOffset.left - 5).show(); // 二级单显示
	
	/*二级菜单的滑过样式*/
	$('.j_countNavItem li a').unbind('mousedown mouseover mouseout').mouseout(function(event) { 
		$(this).removeClass('countUlItemHover');
		obj_navItemUl.hide();
	}).mouseover(function(event) { 
		$(this).addClass('countUlItemHover');
		obj_navItemUl.show();
	}).mousedown(function(event) {
		var str_id = event.currentTarget.id;
		
		 dlf.fn_closeTrackWindow(true);      // 关闭轨迹查询
		dlf.fn_initRecordSearch(str_id);
		obj_navItemUl.hide();
	});
}

/**
* 判断二级菜单是否显示,如果显示进行隐藏
*/
window.dlf.fn_secondNavValid = function() { 
	var obj_navItem = $('.j_countNavItem'),
		n_item = obj_navItem.length;
	
	for ( var i = 0; i < n_item; i++ ) {
		var obj_tempNavItem = $(obj_navItem[i]), 
			f_hidden = obj_tempNavItem.is(':hidden');
		
		if ( !f_hidden ) {
			obj_tempNavItem.hide();
		}
	}
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
* 验证定位器手机号
*/
window.dlf.fn_checkOperatorMobile = function(str_tmobile) {
	$.get_(CHECKOPERATORMOBILE_URL + '/' + str_tmobile, '', function(data){
		if ( data.status != 0 ) {
			dlf.fn_jNotifyMessage('操作员手机号已存在。', 'message', false, 5000);
			$('#hidOperatorMobile').val('1');
			return;
		} else {
			$('#hidOperatorMobile').val('');
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

/**
* 批量导入文件
*/
function fn_initBatchImport(gid, gname) {
	$('.fileInfoTable').html('');
	$('#fileUploadTable').html('');
	$('#fileUploadDialog').removeData('resource').attr('title', '批量导入文件').dialog('option', 'title', '批量导入文件').dialog("open");
	$('#hidGid').val(gid);
	$('#hidGName').val(gname);
	$('#fileUploadIframe').attr('src', BATCHIMPORT_URL);
}

/**
* 数据回显：批量删除定位器、批量设防撤防
*/
window.dlf.fn_echoData = function(str_tableName, obj_params, str_msg) {
	var arr_dataes = obj_params.characters;
		obj_table = $('.' + str_tableName + ' tbody'),
		obj_head = $('.' + str_tableName + ' thead th');
	
	obj_table.html('');	// 清空表格数据
	for ( var i = 0; i < arr_dataes.length; i++ ) {
		var obj = arr_dataes[i],
			str_defendMsg = obj.mennual_status == 1 ? '已设防' : '未设防',
			str_html = '';
		
		str_html = '<tr><td>'+ obj.alias +'</td><td>'+ obj.tmobile +'</td>';
		if ( str_msg != '删除' ) {	// 设防或撤防
			str_html += '<td>'+ str_defendMsg +'</td>';
		}
		str_html += '<td tid='+ obj.tid +' class="fileStatus1">等待'+ str_msg +'</td>'
		str_html += '</tr>';
		obj_table.append(str_html);	// 填充要删除的数据
	}
	obj_head.html(obj_params.gname);	// 表头显示组名
}
})();

$(function() {
	// 批量导入、批量删除数据回显文件、批量设防撤防数据回显 初始化dialog
	$('#fileUploadDialog, #batchDeleteDialog, #batchDefendWrapper').dialog({
		autoOpen: false,
		height: 500,
		width: 600,
		modal: true,
		resizable: false
	});
});