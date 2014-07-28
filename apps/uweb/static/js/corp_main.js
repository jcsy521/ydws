/**
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
* obj_tracePolylines: 甩尾轨迹线
* arr_tracePoints: 甩尾数据点
* n_addMarkerInterval: 选中节点每隔50毫秒添加终端
*/
var str_currentTid = '',
	arr_autoCompleteData = [],
	b_createTerminal = false,
	n_onlineCnt = 0,
	n_offlineCnt = 0, 
	arr_treeNodeChecked = [],
	arr_submenuGroups = [],
	obj_tracePolylines = {},
	arr_tracePoints = [],
	b_uncheckedAll = true,
	b_checkedAll = true,
	n_addMarkerInterval = 0;
	
(function() {

/**
*  创建右键菜单，设置每个节点的菜单右键菜单
*/
function customMenu(node) {
	var obj_node = $(node),
		obj_currentGroup = obj_node.parent().siblings('a'),
		str_currentGroupName = obj_currentGroup.attr('title'),	// 当前定位器所在组名
		str_currentGroupIdForBatchMove = obj_node.attr('id').substr(10),//当前组的名称
		str_groupId = obj_currentGroup.attr('groupId'),	// 当前所在组的组ID
		str_userType = $('.j_body').attr('userType'),	// 用户类型
		items = null,		// 菜单的操作方法
		submenuItems = {},	// 二级菜单
		submenuItemsForGroup = {},	// 二级菜单--组移动分组
		subDefendItems = {},	// 批量设防撤防二级菜单
		renameLabel = '',	// 重命名lable
		createLabel = '',	// 新建lable
		batchImportDeleteLabel = '',	// 批量导入
		batchDeleteLabel = '',	// 批量删除
		moveToLabel = '',	// 移动至
		moveToLabelForGroup = '',	// 批量移动至
		eventLabel = '',	// 告警查询
		terminalLabel = '',	// 参数设置
		wakeupLabel = '',	// 重新激活终端
		deleteLabel = '',	// 删除lable
		batchDefendLabel = '',	// 批量设防*撤防
		batchRegionLabel = '',	// 批量设置电子围栏
		singleDeleteLabel = '',	// 删除单个定位器
		singleCreateLabel = '',	// 单个定位器的添加
		singleDefendLabel = '',	// 单个定位器设防撤防
		accStatusLabel = '', //远程控制
		realtimeLabel = '',	// 单个定位器实时定位
		trackLabel = '',	// 单个定位器轨迹查询
		staticsLabel = '',	// 单个定位器统计报表
		bindLineLabel = '', // 绑定线路
		bindRegionLabel = '', // 绑定围栏
		batchTrackLabel = '',	// 开启追踪
		batchCancleTrack = '',	// 取消追踪
		mileageNotificationLabel = '',	// 里程保养
		str_bizCode = $('#hidBizCode').val(),	// 当前的业务
		obj_alarmAndDelay = $('.j_alarm, .j_delay'),
		b_trackStatus = $('#trackHeader').is(':visible');	// 轨迹是否打开着
	
	if ( obj_node.hasClass('j_corp') ) {		// 集团右键菜单
		renameLabel = '重命名集团';
		createLabel = '新建分组';
		deleteLabel = '删除集团';
	} else if (obj_node.hasClass('j_group')) {	// 组右键菜单
		renameLabel = '重命名组';
		deleteLabel = '删除分组';
		singleCreateLabel = '添加单个定位器';
		batchImportDeleteLabel = '批量导入/删除';
		batchDeleteLabel = '批量删除定位器';
		batchDefendLabel = '批量设防/撤防';
		batchRegionLabel = '批量绑定围栏';
		batchTrackLabel = '批量开启追踪';
		batchCancleTrackLabel = '批量取消追踪';
		moveToLabelForGroup = '批量移动至';
	} else {						// 定位器右键菜单
		wakeupLabel = '重新激活';
		terminalLabel = '参数设置';
		singleDeleteLabel = '删除定位器';
		realtimeLabel = '实时定位';
		trackLabel = '轨迹查询';
		eventLabel = '告警查询';
		moveToLabel = '移动定位器';
		singleDefendLabel = '设防/撤防';
		accStatusLabel = '远程控制';
		staticsLabel = '里程统计';
		bindLineLabel = '绑定/解绑线路';
		bindRegionLabel = '绑定围栏';
		mileageNotificationLabel = '保养提醒';
	}
	// 定位器的移动至菜单项
	
	for ( var i in arr_submenuGroups ) {
		var obj_group = arr_submenuGroups[i],
			str_groupName = obj_group.groupName,
			str_groupId = obj_group.groupId;
		
		if ( str_currentGroupName != str_groupName ) {
			submenuItems['moveToGroup' + str_groupId ] = fn_createSubMenu(obj_group);
		}
		if ( str_currentGroupIdForBatchMove != str_groupId ) {
			submenuItemsForGroup['moveToGroup' + str_groupId ] = fn_createSubMenuForGroup(obj_group);
		}
	}
	// 右键菜单执行的操作
	items = {
		"create" : {		// 新增分组
			"label" : createLabel,
			"action" : function (obj) {
				var obj_this = $(obj).eq(0);
				
				if ( obj_this.hasClass('j_corp') ) {
					this.create();
				} else {
					return false;
				}	
			}
		},
		"singleCreate": {		// 单个定位器添加
			"label": singleCreateLabel,
			"action": function(obj) {
				var obj_this = $(obj).eq(0);
				
				fn_initCreateTerminal('', obj_this.children('a').eq(0).attr('groupId'));
				return false;
			}
		},
		"realtime": {
			"label" : realtimeLabel,
			"action" : function(obj) {	// 实时定位初始化				
				dlf.fn_currentQuery();
			}
		},
		"track": {
			"label" : trackLabel,
			"action" : function(obj) {	// 轨迹查询初始化
				if ( b_trackStatus ) {
					return;
				}
				// dlf.fn_clearOpenTrackData();	// 初始化开启追踪
				obj_alarmAndDelay.hide();	
				dlf.fn_initTrack();
			}
		},
		"event": {
			"label" : eventLabel,
			"action" : function(obj) {	// 告警查询初始化
				// 查询单个终端告警
				dlf.fn_eachCheckedNode('.j_leafNode');
				// 将之前的checked状态填充 
				var n_treeNodeCheckLen = arr_treeNodeChecked.length;
				
				if ( n_treeNodeCheckLen > 0 ) {
					for ( var i = 0; i < n_treeNodeCheckLen; i++ ) {
						$('#corpTree').jstree('uncheck_node', arr_treeNodeChecked[i]);
					}
					arr_treeNodeChecked = [];
				}
				$('#corpTree').jstree('check_node', $(obj).eq(0));
				$("#showMusic").html('');
				dlf.fn_initRecordSearch('eventSearch');
			}
		},
		"bindLine": {
			"label" : bindLineLabel,
			"action" : function(obj) {	// 绑定线路	
				if ( b_trackStatus ) {	// 如果轨迹打开 要重启lastinfo
					dlf.fn_closeTrackWindow(true);	// 关闭轨迹查询,不操作lastinfo
				}
				$("#showMusic").html('');
				dlf.fn_routeLineBindEvent();
			}
		},
		/*
		"region": {
			"label" : '电子围栏',
			"action" : function(obj) {	// 终端右键菜单 电子围栏 kjj add  2013-07-10
				obj_alarmAndDelay.hide();
				dlf.fn_initRegion();
			}
		},*/
		"wakeUp": {	// 重新激活终端
			"label" : wakeupLabel,
			"action" : function (obj) {
				dlf.fn_wakeUpTerminal($(obj).children('a').eq(0).attr('title'));
				return false;
			}
		},
		"bindRegion": {
			"label" : bindRegionLabel,
			"action" : function(obj) {	// todo 
				// dlf.fn_clearOpenTrackData();	// 初始化开启追踪
				obj_alarmAndDelay.hide();
				dlf.fn_initBindRegion();
			}
		},
		"batchRegion" : {
			"label" : batchRegionLabel,
			"action": function (obj) { // 批量设置电子围栏
				// dlf.fn_clearOpenTrackData();	// 初始化开启追踪
				obj_alarmAndDelay.hide();
				dlf.fn_initBatchRegions(obj);
			}
		},
		"terminalSetting": {	// 参数设置
			"label" : terminalLabel,
			"action" : function (obj) {
				dlf.fn_initCorpTerminal($(obj).children('a').eq(0).attr('tid'));
				return false;
			}
		},
		'mileageNotification': {
			"label" : mileageNotificationLabel,
			"action" : function (obj) {
				dlf.fn_initMileageNotification($(obj).children('a').eq(0).attr('tid'));
				return false;
			}			
		},
		"accStatus": {	// 单个定位器设置远程控制
			"label" : accStatusLabel,
			"action" : function (obj) {
				dlf.fn_initAccStatus(obj.children('a').attr('alias'));
			}
		},
		"defend": {	// 单个定位器设防撤防
			"label" : singleDefendLabel,
			"action" : function (obj) {
				dlf.fn_defendQuery(obj.children('a').attr('alias'));
			}
		},
		"batchImportDelete": {	// 批量导入定位器操作菜单
			"label" : batchImportDeleteLabel,
			"submenu": {
				'batchImport': {
					"label" : "批量导入定位器",
					"action" : function (obj) {
						// todo 批量导入定位器操作
						var obj_batch = obj.children('a'),
							n_gid = obj_batch.attr('groupid'),
							str_gname = obj_batch.attr('title');
							
						fn_initBatchImport(n_gid, str_gname);
						return false;
					}
				},
				'batchDelete': {
					"label" : "批量删除定位器",
					"action" : function (obj) {
						fn_batchOperateValidate(obj, '删除');
					}
				}
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
		"batchTrack" : {
			"label" : "批量追踪",
			"submenu": {
				'batchTrack0': {
					"label" : "开启",
					"action" : function (obj) {
						fn_batchOpenTrack(obj, 'open');
					}
				},
				'batchTrack1': {
					"label" : "关闭",
					"action" : function (obj) {
						fn_batchOpenTrack(obj, 'close');
					}
				}
			}
		},
		"moveTerminalForGroup": {
			"label" : moveToLabelForGroup,
			"submenu": submenuItemsForGroup
		},
		/*		
		"batchTrack" : {
			"label" : "批量开启追踪",
			"action": function (obj) { // 批量追踪定位器
				
			}
		},
		"batchCancleTrack": {
			"label" : "批量取消追踪",
			"action": function (obj) { // 批量追踪定位器
				
			}		
		},*/
		"rename" : {
			"label" : renameLabel,
			"action" : function(obj) {
				var obj_node = $(obj).children('a'),
					str_class = obj_node.attr('class');
				
				this.rename(obj);
				// kjj add in 2013.10.10 重命名集团名称和分组名称时，名称>20不允许输入
				$('.jstree-rename-input').unbind('keydown').bind('keydown', function() {
					var obj_this = $(this),
						str_val = obj_this.val();
					
					if ( str_val.length > 20 ) {
						obj_this.val(str_val.substr(0, 20));
					}
				});
				$('.jstree-rename-input').val($(obj).children('a').attr('title'));
			}
		},
		/*"moveTo": {
			"label" : moveToLabel,
			"submenu": submenuItems
		},*/
		"moveTerminal": {
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
				}
			}
		},
		"singleDelete" : {
			"label" : singleDeleteLabel,
			"action" : function (obj) {
				fn_removeTerminal(obj);
				return false;
			}
		},
		"statics": {
			"label": staticsLabel,
			"action" : function (obj) {
				dlf.fn_initRecordSearch('singleMileage');
			}
		}
	};
	// 终端右键菜单菜单
   if ( obj_node.hasClass('j_leafNode') ) {
		delete items.create;
		delete items.singleCreate;
		delete items.batchImportDelete;
		delete items.rename;
		delete items.batchDefend;
		delete items.batchRegion;
		delete items.remove;
		delete items.batchTrack;
		delete items.moveTerminalForGroup;
   }
   // 集团右键菜单删除菜单
   if ( obj_node.hasClass('j_corp')  ) {
		delete items.wakeUp;
		delete items.singleCreate;
		delete items.remove;
		delete items.batchImportDelete;
		// delete items.moveTo;	
		delete items.moveTerminal;
		delete items.event;
		delete items.terminalSetting;
		delete items.batchDefend;
		delete items.batchRegion;
		delete items.defend;
		delete items.accStatus;
		delete items.realtime;
		delete items.track;
		delete items.statics;
		delete items.singleDelete;
		delete items.bindLine;
		delete items.bindRegion;
		delete items.region;
		delete items.batchTrack;
		delete items.moveTerminalForGroup;
		delete items.mileageNotification;
   }
   if ( obj_node.hasClass('j_group') ) {
		delete items.wakeUp;
		delete items.create;
		//delete items.moveTo;
		delete items.moveTerminal;
		delete items.event;
		delete items.terminalSetting;
		delete items.defend;
		delete items.accStatus;
		delete items.realtime;
		delete items.track;
		delete items.statics;
		delete items.singleDelete;
		delete items.bindLine;
		delete items.bindRegion;
		delete items.region;
		delete items.mileageNotification;
   }
   if ( str_userType == USER_OPERATOR ) {	// 操作员屏蔽右键	
		delete items.create;
		delete items.singleCreate;
		delete items.batchImportDelete;
		delete items.remove;
		delete items.rename;
		
		delete items.bindLine;
		delete items.singleDelete;
		delete items.moveTerminal;	// 暂时隐藏操作员的移动至功能
		
		/*
		delete items.batchRegion;
		delete items.batchDefend;
		delete items.moveTo;
		delete items.event;	
		delete items.terminalSetting;
		delete items.defend;
		delete items.statics;
		delete items.bindRegion;
		delete items.bindRegion;*/
   }
   if ( str_bizCode != 'znbc' ) {	// 如果集团业务不是智能班车业务的话  没有绑定线路功能
		delete items.bindLine;
   }
   return items;
}

/**
* 批量操作的数据验证：批量删除、批量设防撤防 (判断是否选中的是定位器)
*/
function fn_batchOperateValidate(obj, str_msg) {
	var obj_currentGroupChildren = obj.children('ul').children('li:visible'),
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
		obj_currentGroupChildren.each(function() {
			var obj_checkedTerminal = $(this),
				obj_terminalALink = obj_checkedTerminal.children('a'),
				b_isChecked = obj_checkedTerminal.hasClass('jstree-checked'),
				str_tid = obj_terminalALink.attr('tid'),
				str_alias = obj_terminalALink.attr('alias'),	
				str_tmobile = obj_terminalALink.attr('title');	
				str_loginSt = obj_terminalALink.attr('clogin'),
				obj_tempCarsData = $('.j_carList').data('carsData');
			
			if ( b_isChecked ) {
				arr_tids.push(str_tid);
				arr_dataes.push({'alias': dlf.fn_encode(str_alias), 'tmobile': str_tmobile, 'tid': str_tid, 'mennual_status': obj_tempCarsData[str_tid].mannual_status});	// #todo obj_carsData[str_tid].mannual_status
			}
			obj_params['tids'] = arr_tids;
			obj_params['characters'] = arr_dataes;
			obj_params['gname'] = str_gname;
		});
		str_msg == '删除' ? fn_batchRemoveTerminals(obj_params) : dlf.fn_initBatchDefend(str_msg, obj_params);
	}
}

/**
* 批量开启定位器
* obj: 操作的组对象
* str_operation: open:开启追踪  close: 取消追踪
*/
function fn_batchOpenTrack(obj, str_operation) {
	var obj_currentGroupChildren = obj.children('ul').children('li:visible'),
		str_gname = obj.children('a').text();	// 组名
	
	//  批量删除选中定位器操作
	if ( obj_currentGroupChildren.length <= 0 ) {	// 没有定位器，不能批量删除
		dlf.fn_jNotifyMessage('该组下没有定位器。', 'message', false, 3000); // 执行操作失败，提示错误消息
		return false;
	} else if ( obj.hasClass('jstree-unchecked') ) {	// 要删除定位器的组没有被选中
		dlf.fn_jNotifyMessage('没有选中要操作的定位器。', 'message', false, 3000); // 执行操作失败，提示错误消息
		return false;
	} else {
		var arr_tids = [],
			arr_dataes = [],
			obj_params = {};
		// 当前组下选中的tid
		obj_currentGroupChildren.each(function() {
			var obj_checkedTerminal = $(this),
				obj_terminalALink = obj_checkedTerminal.children('a'),
				b_isChecked = obj_checkedTerminal.hasClass('jstree-checked'),
				str_tid = obj_terminalALink.attr('tid'),
				obj_currentMarker = obj_selfmarkers[str_tid],
				str_alias = obj_terminalALink.attr('alias'),	// tnum
				str_tmobile = obj_terminalALink.attr('title'),	// tmobile
				str_actionTrack = dlf.fn_getActionTrackStatus(str_tid);
			
			if ( b_isChecked ) {
				if ( str_operation == 'open' && str_actionTrack != 'yes' && obj_currentMarker ) {	// 选中终端没有开启追踪
					arr_tids.push(str_tid);
				} else if ( str_operation == 'close' && str_actionTrack != 'no' && obj_currentMarker) {	// 选中终端 取消追踪
					arr_tids.push(str_tid);
				}
				arr_dataes.push({'alias': dlf.fn_encode(str_alias), 'tmobile': str_tmobile, 'tid': str_tid, 'track': str_actionTrack});
			}
		});
		if ( arr_tids.length <= 0 ) {
			dlf.fn_jNotifyMessage('您选中的定位器都'+ ( str_operation == 'open' ? '已' : '未' ) +'开启追踪。', 'message', false, 3000); // 执行操作失败，提示错误消息
			return false;
		}
		obj_params['tids'] = arr_tids;
		obj_params['characters'] = arr_dataes;
		obj_params['gname'] = str_gname;
		dlf.fn_initOpenTrack(str_operation, obj_params);
	}
}

/**
* 批量开启追踪数据回显
*/
window.dlf.fn_initOpenTrack  = function(str_operation, obj_params) {
	dlf.fn_dialogPosition('batchTrack');	// 设置dialog的位置
	
	var arr_dataes = obj_params.characters;
		obj_table = $('.batchTrackTable tbody'),
		obj_head = $('.batchTrackTable thead th');
	
	obj_table.html('');	// 清空表格数据
	for ( var i = 0; i < arr_dataes.length; i++ ) {
		var obj = arr_dataes[i],
			str_html = '',
			str_trackStatus = obj.track,
			str_track = '';
		
		str_html = '<tr><td>'+ obj.alias +'</td><td>'+ obj.tmobile +'</td>';
		if ( str_trackStatus == 'yes' ) {
			str_track = '已开启';
		} else {
			str_track = '未开启';
		}
		str_html += '<td>'+ str_track + '</td>';
		str_html += '</tr>';
		obj_table.append(str_html);	// 填充要删除的数据
	}
	obj_head.html(obj_params.gname);	// 表头显示组名
	
	var obj_defend = {},
		str_track = str_operation == 'open' ? '开启追踪' : '取消追踪';
	
	$('.j_batchTrack').val('批量' + str_track).unbind('click').bind('click', function() {
		dlf.setTrack(obj_params.tids);
	});
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
* 生成二级菜单项
* obj_group: 二级菜单项要显示的内容对象
*/
function fn_createSubMenuForGroup(obj_group) {
	var str_groupName = obj_group.groupName,
		str_groupId = obj_group.groupId;
		
	return {
		"label": str_groupName, 
		"action": function(obj) {
			//获取当前组下所有选中的终端
			var arr_nodeTerminsals = obj.children('ul').children('li'),
				arr_moveIds = [];
			
			for ( var i = 0; i< arr_nodeTerminsals.length; i++ ) { 
				var obj_tempNodeTerminal = $(arr_nodeTerminsals[i]),
					str_tempNodeClass = obj_tempNodeTerminal.attr('class'),
					str_tempNodeTid = obj_tempNodeTerminal.attr('id').substr(9);
				
				if ( obj_tempNodeTerminal.hasClass('jstree-checked') ) {
					arr_moveIds.push(str_tempNodeTid);
				}
			}

			if ( arr_moveIds.length > 0 ) {    // 只有终端才可以移动到组 
				fn_moveGroup(arr_moveIds, str_groupId, '');
			} else {
				dlf.fn_jNotifyMessage('请勾选要移动的终端', 'message', false, 3000); 
			}
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
			//'initially_select': str_checkedNodeId	// 设置默认选中的节点
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
        var arr_currentNode = data.rslt.o, 
            obj_target = data.rslt.np, 
            str_groupId = $(obj_target).children('a').attr('groupid'), 
            arr_tids = [];
                                                        
        for ( var i =0; i < arr_currentNode.length; i++){ 
            var obj_currentA = $(arr_currentNode[i]).children('a').eq(0), 
                str_tid = obj_currentA.attr('tid'); 
            if ( str_tid ) {    // 只有终端才可以移动到组
                arr_tids.push(str_tid); 
            } 
        } 
        if ( arr_tids.length > 0 ) {    // 只有终端才可以移动到组 
            fn_moveGroup(arr_tids, str_groupId, data.rlbk); 
        }

	}).bind('create.jstree', function(e, data) {
		var obj_rslt = data.rslt,
			obj_rollBack = data.rlbk,
			str_newName = obj_rslt.name,
			str_cid = $(obj_rslt.parent).children('a').attr('corpid') || $('.j_body').attr('cid');
		
		fn_createGroup(str_cid, str_newName, obj_rollBack, obj_rslt.obj);
	}).bind('rename.jstree', function(e, data) {	// 重命名
		var	obj_rslt = data.rslt,
			obj_currentNode = $(obj_rslt.obj[0]),
			obj_current = obj_currentNode.children('a').eq(0),
			str_newName = obj_rslt.new_name,
			obj_rlbk = data.rlbk,
			b_flag = obj_currentNode.hasClass('j_leafNode');

		if ( str_newName == data.rslt.old_name && !b_flag ){	// 如果新名称和旧名称相同 不操作
			return;
		}
		if ( obj_currentNode.hasClass('j_group') ) {	// 重命名组	
			fn_renameGroup(obj_current.attr('groupid'), str_newName, obj_rlbk);
		} else if ( obj_currentNode.hasClass('j_corp') ) {	// 重命名集团
			var str_cid = obj_current.attr('corpid') || $('.j_body').attr('cid');
			
			fn_renameCorp(str_cid, str_newName, obj_rlbk)
		}
	}).bind('loaded.jstree', function(e, data) {	// 树节点加载完成事件
		//data.inst.open_all(-1);	// 默认展开所有的节点
		dlf.fn_setCorpIconDiffBrowser();
		// 更新定位器总数
		fn_updateTerminalCount();
		// 循环所有定位器 找到当前定位器并更新车辆信息
		var n_num = 0,
			n_pointNum = 0,
			arr_locations = [],
			obj_tempCarsData = $('.j_carList').data('carsData');	
			
		for ( var index in obj_tempCarsData ) {
			n_num ++;
			if ( n_num > 0 ) {
				break;
			}
		}
		if ( n_num > 0 ) {
			/* tohs 为什么要更新别名			
			for(var param in obj_tempCarsData) {	// 加载完树后，更新alias
				var str_alias = dlf.fn_decode(obj_tempCarsData[param].alias);
				
				$('#leaf_'+param).attr('alias', str_alias);
			}*/
			for ( var x in arr_treeNodeChecked ) {
				var str_checkedNode = arr_treeNodeChecked[x],
					n_index = str_checkedNode.indexOf('#leafNode_'),
					str_tid = '';
				
				if ( n_index != -1 ) {
					str_tid = $.trim(str_checkedNode.substr(str_checkedNode.indexOf('_') + 1));
					
					var	obj_car = obj_tempCarsData[str_tid];
					
					/**
					* KJJ add in 2014.05.12
					* 判断是否有缓存数据
					* 如果是新增终端，tid==tmobile，所以需要根据tmobile获取对应tid以及对应缓存数据
					*/ 
					if ( !dlf.fn_isEmptyObj( obj_car )) {
						var obj_tempAddTerminal = $('#corpTree a[title='+ str_tid +']');
						
						if ( obj_tempAddTerminal.length <= 0 ) {
							return;
						} else {
							obj_car = obj_tempCarsData[obj_tempAddTerminal.attr('tid')];
						}
					}
					var obj_trace = obj_car.trace_info,	// 甩尾数据
						obj_track = obj_car.track_info,	// 开启追踪点数据
						n_enClon = obj_car.clongitude,
						n_enClat = obj_car.clatitude,
						n_lon = obj_car.longitude,
						n_lat = obj_car.latitude,
						n_clon = n_enClon/NUMLNGLAT,	
						n_clat = n_enClat/NUMLNGLAT;
					
					if ( n_lon != 0 && n_lat != 0 ) {
						if ( n_clon != 0 && n_clat != 0 ) {
							n_pointNum ++;
							//arr_locations.push({'clongitude': n_enClon, 'clatitude': n_enClat});
							
							arr_locations.push(dlf.fn_createMapPoint(n_enClon, n_enClat));
							obj_car.trace_info = obj_trace;
							obj_car.track_info = obj_track;
							dlf.fn_updateInfoData(obj_car); // 工具箱动态数据
							if ( dlf.fn_isEmptyObj(obj_trace) ) {	// 生成甩尾数据
								obj_trace.tid = str_tid;
							}
						} else {
							dlf.fn_translateToBMapPoint(n_lon, n_lat, 'actiontrack', obj_car, true);	// 前台偏转 kjj 2013-09-27
						}
					}
				}
			}
			if ( str_currentTid != undefined && str_currentTid != '' ) {
				if ( b_createTerminal ) {	// 如果是新建终端 发起switchCar
					var obj_newTerminal = $('#leaf_' + str_currentTid);
					
					dlf.fn_switchCar(str_currentTid, obj_newTerminal);
					//data.inst.open_all(0); // -1 opens all nodes in the container
				} else {
					for(var param in obj_tempCarsData) {
						var obj_carInfo = obj_tempCarsData[param], 
							str_tid = param;
						
						if ( str_currentTid == str_tid || str_checkedNodeId.substr(5, str_checkedNodeId.length) == str_tid ) {	// 更新当前车辆信息
							dlf.fn_updateTerminalInfo(obj_carInfo);
							break;
						}
					}
				}
			} else {	// 第一次发起switchCar启动lastinfo
				$('.j_group .j_leafNode').each(function() {
					var obj_terminalNode = $(this).children('.j_terminal'),
						str_tid = obj_terminalNode.attr('tid'),
						obj_car = obj_tempCarsData[str_tid],
						n_enClon = obj_car.clongitude,
						n_enClat = obj_car.clatitude,
						n_clon = n_enClon/NUMLNGLAT,	
						n_clat = n_enClat/NUMLNGLAT;
					
					if ( n_clon != 0 && n_clat != 0 ) {
						n_pointNum ++;
						//arr_locations.push({'clongitude': n_enClon, 'clatitude': n_enClat});
						arr_locations.push(dlf.fn_createMapPoint(n_enClon, n_enClat));
					} 
				});
				var obj_current = $('#' + data.inst.data.ui.to_select);
				
				if ( arr_locations.length > 0 ) {
					//dlf.fn_caculateBox(arr_locations);
					dlf.fn_setOptionsByType('viewport', arr_locations);
				}
				
				dlf.fn_switchCar(str_currentTid, obj_current);
			}
			fn_updateAllTerminalLogin();
			$('.groupNode').css('color', '#000');
		} else {	// 无终端 启动lastinfo
			dlf.fn_updateLastInfo();
			dlf.fn_initCarInfo();
		}
		// 如果无终端或终端都无位置  地图设置为全国地图
		if ( n_pointNum <= 0 ) {
			mapObj.setZoom(5);
		}
		// 将之前的checked状态填充 
		var n_treeNodeCheckLen = arr_treeNodeChecked.length;
		
		if ( n_treeNodeCheckLen > 0 ) {
			setTimeout(function() {
				for ( var i = 0; i < n_treeNodeCheckLen; i++ ) {
					$('#corpTree').jstree('check_node', arr_treeNodeChecked[i]);
				}
				arr_treeNodeChecked = [];
			}, 100);
		}
		
		//更新各分组下的终端在线/离线数
		fn_updateTerminalOnlineNum();
	}).bind('contextmenu.jstree', function(event, data) {	// 右键除当前定位器外其余都不被选中
		var obj_current = fn_nodeCurrentNode(event.target),
			obj_currentCarParent = $('.j_terminal[tid='+ str_currentTid +']').parent();
		
		if ( obj_current.b_terminalClass ) {	// 如果选中的是定位器
			var str_tid = obj_current.attr('tid');
			
			$('#corpTree').jstree('check_node', '#leafNode_' + str_tid);
			/*if ( str_currentTid == str_tid ) {	// 如果是同辆车则不switchcar
				var obj_currentMarker = obj_selfmarkers[str_tid];				
				
				if ( obj_currentMarker ) {	// 2013-07-29 add 切换当前车 只打开吹出框
					var obj_position = obj_currentMarker.getPosition(),
						obj_infowindow = obj_currentMarker.selfInfoWindow;
					
					mapObj.setCenter(obj_position);
					if ( dlf.fn_isBMap() ) {
						obj_currentMarker.openInfoWindow(obj_infowindow);
					} else {
						obj_selfmarkers[str_tid].selfInfoWindow.open(mapObj, obj_position);	// 显示吹出框
					}
				}
				return;
			}*/
			dlf.fn_switchCar(str_tid, obj_current); // 登录成功,
		} else {
			obj_current.removeClass(JSTREECLICKED);
		}
	}).bind('click.jstree', function(event, data) {	// 选中节点事件
		var obj_current = fn_nodeCurrentNode(event.target),
			str_clcikTerminalCls = obj_current.parent().hasClass('jstree-checked');		
		
		if ( obj_current.b_terminalClass ) {	// 如果选中的是定位器
			var str_tid = obj_current.attr('tid');
			
			$('#corpTree').jstree('check_node', '#leafNode_' + str_tid);
			
			str_currentTid = str_tid;
			if ( str_clcikTerminalCls ) { // 如果已经选中,不进行check_node事件
				dlf.fn_switchCar(str_tid, obj_current); 
			}
		} else {	// 集团或组	如果选中集团或组的话没有被选中的样式、上一次选中的定位器还被选中			
			$('.j_terminal[tid='+ str_currentTid +']').addClass(JSTREECLICKED);
			$('.groupCss').removeClass('groupCss');
			obj_current.removeClass(JSTREECLICKED).addClass('groupCss');
			return false;
		}
		//清除告警图标
		dlf.fn_clearAlarmMarker();
	}).bind('dblclick.jstree', function(event, data) {
		var obj_target = $(event.target),
			b_class = obj_target.hasClass('j_terminal'),
			str_tid = obj_target.attr('tid');

		if ( b_class ) {	// 双击定位器
			dlf.fn_initCorpTerminal(str_tid);
		} else {
			return false;
		}
	}).bind('check_node.jstree', function(event, data) {
		var obj_currentLi = $(data.rslt.obj[0]),
			str_class = obj_currentLi.attr('class'),
			n_terminalClass = str_class.indexOf('j_leafNode'),
			n_groupClass = str_class.indexOf('j_group'),
			n_corpClass = str_class.indexOf('j_corp'),
			b_trackStatus = $('#trackHeader').is(':visible'),
			obj_tempCarsData = $('.j_carList').data('carsData'),
			str_nodes = '';
		
		b_uncheckedAll = false;
		b_checkedAll = false;
		if ( n_terminalClass != -1 ) {	// 选中单个终端
			var obj_current = obj_currentLi.children('.j_terminal')
				str_tid = obj_current.attr('tid');
			
			str_currentTid = str_tid;
			dlf.fn_switchCar(str_tid, obj_current, 'check_node'); // 登录成功
			b_checkedAll = true;			
			//如果当前分组下可见的终端全部被选中
			var obj_currentGroup = obj_currentLi.parent().parent(),
				obj_groupVisibleTerminal = obj_currentGroup.children('ul').children('li:visible'),
				str_currentGroupId = obj_currentGroup.attr('id'),
				b_groupAllCheck = true;
			
			obj_groupVisibleTerminal.each(function(e) {
				if ( $(this).hasClass('jstree-unchecked') ) {
					b_groupAllCheck = false;
					return;
				}
			});
			// 设置组为'选中状态
			if ( b_groupAllCheck ) {
				$('#corpTree').jstree('check_node', '#'+str_currentGroupId);
			}
			
		} else if ( n_groupClass != -1 || n_corpClass != -1 ) {	// 选中整个分组
			// 获取该分组下所有终端
			dlf.fn_lockScreen();
			$('#loadingMsg').html('正在加载定位器...').show();
			
			if ( n_groupClass != -1 ) {	// 选中整个分组
				str_nodes = '#'+data.rslt.obj[0].id;
			} else if ( n_corpClass != -1 ) {	// 选中整个集团
				str_nodes = '.j_corp .j_group';
			}
			arr_checkedNode.push($(str_nodes).attr('id'));
			setTimeout(function() {
				var n_checkedLength = $(str_nodes+' .jstree-checked').length,
					n_num = 0,
					n_count = 0;
				
				/**
				* KJJ add in 2014.05.07
				* 每隔1s添加一个终端
				*/
				//n_addMarkerInterval = setInterval(function() {
					var obj_terminal = $($(str_nodes+' .jstree-checked')[n_count]),
						obj_current = obj_terminal.children('.j_terminal');
					
					if ( obj_current.length > 0 ) {
						var str_tid = obj_current.attr('tid'),
							str_loginSt = obj_current.attr('clogin'),
							obj_corpInfoStat = $('#terminalInfo .currentTNum').children(),
							str_currentCorpInfoStat = obj_corpInfoStat.attr('id'),
							obj_tempSelfmarker = obj_selfmarkers[str_tid];
						
						if ( str_currentCorpInfoStat == 'onlineCount' && str_loginSt != '1' ) {
							return;
						} else if ( str_currentCorpInfoStat == 'offlineCount' && str_loginSt != '0' ) {
							return;
						}
						if ( $.inArray($(str_nodes).attr('id'), arr_checkedNode) < 0 ) {	// 如果已经取消选中，则停止循环
							clearInterval(n_addMarkerInterval);
							return;							
						} else {
							if ( b_trackStatus ) {
								clearInterval(n_addMarkerInterval);
								return;	
							}
							dlf.fn_updateInfoData(obj_tempCarsData[str_tid]);
							n_num ++;
							
							if ( n_num == n_checkedLength ) {	// 全部执行完毕
								b_checkedAll = true;
								$('.j_body').data('intervalkey', false);
								clearInterval(n_addMarkerInterval);
								return;
							}
						}
						n_count ++;
					} else {
						clearInterval(n_addMarkerInterval);
					}
				//}, 50);
				$('#loadingMsg').html('').hide();
				dlf.fn_unLockScreen();
			}, 400);			
		}
	}).bind('uncheck_node.jstree', function(event, data) {
		fn_uncheckedNode(data.rslt.obj[0]);
	});
}

var arr_checkedNode = [];

function fn_uncheckedNode(obj) {
	var obj_currentLi = $(obj),
		str_id = obj_currentLi.attr('id'),
		str_class = obj_currentLi.attr('class'),
		n_terminalClass = str_class.indexOf('j_leafNode'),
		n_groupClass = str_class.indexOf('j_group'),
		n_corpClass = str_class.indexOf('j_corp');
	
	b_uncheckedAll = true;	// 设置反选为true
	arr_checkedNode.splice($.inArray(str_id,arr_checkedNode),1);	// 清除选中元素
	clearInterval(n_addMarkerInterval);	// 反选时，先清空全选计时器，避免继续添加终端
	// 延迟0.5s 清空地图
	setTimeout(function() {
		$('.j_body').data('intervalkey', false);
		if ( n_terminalClass != -1 ) {	// 取消单个终端
			var obj_current = obj_currentLi.children('.j_terminal'),
				str_tid = obj_current.attr('tid'),
				obj_marker = obj_selfmarkers[str_tid],
				obj_polyline = obj_polylines[str_tid];
			
			if ( dlf.fn_isEmptyObj(obj_marker) ) {				
				dlf.fn_clearMapComponent(obj_marker);
				delete obj_selfmarkers[str_tid];
				obj_actionTrack[str_tid].status = 'no';
			}
			if ( dlf.fn_isEmptyObj(obj_polyline) ) {
				dlf.fn_clearMapComponent(obj_polyline);
			}
			obj_current.removeClass('j_currentCar jstree-clicked');
			//如果当前分组下可见的终端全部被选中
			var obj_currentGroup = obj_currentLi.parent().parent(),
				obj_groupVisibleTerminal = obj_currentGroup.children('ul').children('li:visible'),
				str_currentGroupId = obj_currentGroup.attr('id'),
				b_groupAllCheck = true;
			
			obj_groupVisibleTerminal.each(function(e) {
				if ( $(this).hasClass('jstree-checked') ) {
					b_groupAllCheck = false;
					return;
				}
			});
			// 设置组为不选中状态
			if ( b_groupAllCheck ) {
				$('#corpTree').jstree('uncheck_node', '#'+str_currentGroupId);
			}
			
			
		} else if ( n_groupClass != -1 )  { //取消选中整个分组
			var arr_nodeTerminsals = obj_currentLi.children('ul').children('li').children('.j_terminal');
				
			for ( var i = 0; i< arr_nodeTerminsals.length; i++ ) { 
				var obj_tempNodeTerminal = $(arr_nodeTerminsals[i]),
					str_tempNodeTid = obj_tempNodeTerminal.attr('tid'),
					obj_tempNodeMarker = obj_selfmarkers[str_tempNodeTid];
				
				obj_tempNodeTerminal.removeClass('j_currentCar jstree-clicked');
				if ( dlf.fn_isEmptyObj(obj_tempNodeMarker) ) {
					dlf.fn_clearMapComponent(obj_tempNodeMarker);
					delete obj_selfmarkers[str_tempNodeTid];
					obj_actionTrack[str_tempNodeTid].status = 'no';
				}
			}
		} else if ( n_corpClass != -1 ) {	// 取消选中整个集团
			dlf.fn_clearMapComponent();
			obj_selfmarkers = {};
			for ( var param in obj_actionTrack ) {
				obj_actionTrack[param] = {'status': 'no', 'interval': '', 'color': '', 'track': 0};
			}
			$('.j_carList .j_currentCar').removeClass('j_currentCar jstree-clicked');
			// 关闭所有开启追踪
		}
		//清除告警图标
		dlf.fn_clearAlarmMarker();
	}, 500);	
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
	$('#carCount').html( n_onlineCnt + n_offlineCnt + '(全部)').unbind('click').click(function(e) {
		$('#terminalInfo td').removeClass('currentTNum');
		$(this).parent().addClass('currentTNum');
		fn_displayTerminalNode('all');
		fn_resetTreeChecked();
	});
	$('#onlineCount').html(n_onlineCnt + '(在线)').unbind('click').click(function(e) {
		$('#terminalInfo td').removeClass('currentTNum');
		$(this).parent().addClass('currentTNum');
		fn_displayTerminalNode('online');
		fn_resetTreeChecked();
	});
	$('#offlineCount').html(n_offlineCnt + '(离线)').unbind('click').click(function(e) {
		$('#terminalInfo td').removeClass('currentTNum');
		$(this).parent().addClass('currentTNum');
		fn_displayTerminalNode('offline');
		fn_resetTreeChecked();
	});
}

/*
* 重置树的选中状态
*/
function fn_resetTreeChecked() {
	$('#corpTree').jstree('uncheck_node','.j_corp');
}
/*
* 根据操作显示相应的终端
*/
function fn_displayTerminalNode(str_operator) {
	$('.j_terminal').each(function(e) {
		var obj_terminalNode = $(this).parent();
			str_currLoginSt = $(this).attr('clogin');
		
		if ( str_operator == 'all' ) { // 显示全部
			obj_terminalNode.show();
		} else if ( str_operator == 'online' ) { // 显示在线
			if ( str_currLoginSt == 0 ) {
				obj_terminalNode.hide();
				
			} else {
				obj_terminalNode.show();
			}
		} else { //显示离线
			if ( str_currLoginSt == 1 ) {
				obj_terminalNode.hide();
			} else {
				obj_terminalNode.show();
			}
		}
	});
}

/**
* 集团用户 lastinfo
* b_isOpenInfowindow
*/
window.dlf.fn_corpGetCarData = function(b_isCloseTrackInfowindow) {
	var obj_current = $('.j_leafNode a[class*='+ JSTREECLICKED +']'),
		str_checkedNodeId = obj_current.attr('id'),	// 上一次选中车辆的id
		str_tempTid = '',
		b_flg = false,
		obj_param = {'lastinfo_time': -1},
		str_lastinfoTime = $('.j_body').data('lastinfo_time'),
		arr_tracklist = [],
		obj_carsData = {},
		obj_tempCarsData = $('.j_carList').data('carsData');

	str_checkedNodeId = str_checkedNodeId == undefined ? 'leaf_' + str_currentTid : str_checkedNodeId;
	str_tempTid = str_checkedNodeId.substr(5, str_checkedNodeId.length);
	//str_currentTid = obj_current.attr('tid');	// load.jstree时更新选中的车
	
	if ( dlf.fn_isEmptyObj(obj_tempCarsData) ) {
		$('.j_terminal').each(function() {
			var str_tid = $(this).attr('tid'),
				str_actionTrack = dlf.fn_getActionTrackStatus(str_tid);
				
			if ( str_actionTrack == 'yes' ) {
				arr_tracklist.push({'track_tid': str_tid, 'track_time': obj_tempCarsData[str_tid].timestamp});
			}
		});
	}
	if ( str_lastinfoTime ) {
		obj_param.lastinfo_time = str_lastinfoTime;
	}
	if ( arr_tracklist.length > 0 ) {
		obj_param.track_lst = arr_tracklist;
	}
	
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
	$.post_(CORP_LASTINFO_URL, JSON.stringify(obj_param), function (data) {	// 向后台发起lastinfo请求
		$('.j_body').data('intervalkey', false);
		
		if ( data.status == 0 ) {
			var str_resDataType = data.res_type,
				b_isDifferentData = true;
			
			$('.j_body').data('lastinfo_time', data.res.lastinfo_time);	// 存储post返回的上次更新时间  返给后台
			$('.j_alarm').show();
			
			/**
			* KJJ add 2014.05.28
			* 判断缓存数据的点是否在移动，如果没有则修改marker的icon图标
			*/
			for ( var tid in obj_selfmarkers ) {
				var obj_tempCarInfo = obj_tempCarsData[tid];
				
				if ( obj_tempCarInfo ) {
					var n_speed = obj_tempCarInfo.speed,
						n_timestamp = obj_tempCarInfo.timestamp,
						b_flag = false,
						obj_marker = obj_selfmarkers[tid],
						obj_markerIcon = obj_marker.getIcon(),
						str_markerIconUrl = obj_markerIcon.imageUrl,
						n_nowtime = new Date().getTime()/1000,
						myIcon = new BMap.Icon(BASEIMGURL + 'default.png', new BMap.Size(34, 34)),
						obj_imageOffset = new BMap.Size(0, 0);
					
					if ( str_markerIconUrl.search('_trace') != -1 ) {
						if ( n_nowtime - n_timestamp > 300 || n_speed < 5 ) {
							myIcon.setImageUrl(dlf.fn_setMarkerIconType(27, obj_tempCarInfo.icon_type, obj_tempCarInfo.login, false));
							myIcon.setImageOffset(obj_imageOffset);
							obj_marker.setIcon(myIcon);
						}
					}
				}
			}
			
			if ( str_resDataType ==  0 ) { //本次数据未发生变化
				return;
			} else if ( str_resDataType == 1 ) { //1：本次数据部分终发生变化（只提供发生变化的那份数据）
				var obj_corp = data.res;
				
				n_onlineCnt = obj_corp.online,		// online count
				n_offlineCnt = obj_corp.offline;	// offline count
				
				fn_updateTerminalCount();
				fn_updateTreeNode(data.res, b_isCloseTrackInfowindow);
				return;
			} else { // 2或者3 当用户有改变时,2,全部更新,3,前台自己判断是否要进行树更新				
				var obj_corp = data.res,
					arr_groups = obj_corp.groups,	// all groups 
					n_groupLength = arr_groups.length,	// group length
					str_corpName = obj_corp.name,	// corp name
					str_tempCorpName = str_corpName,
					str_corpId = obj_corp.cid,		// corp id
					str_html = '<ul>',
					arr_groupIds = [], // 组ID组
					arr_tids = [], 	// 组下的tid组
					str_tempFirstTid = '',	// 默认第一个tid
					str_groupFirstId = '',	// 默认第一个groupid
					b_isHasTerminal = true,	// 是否有终端
					obj_newData = {},
					obj_tempSelfMarker = {},	// 临时存储最新的marker数据
					b_isFirst = $('#corpTree').data('ftree');
				
				//存储所有集团,以便进行计算组下的在/离线数据
				$('.j_body').data('groups', arr_groups);
				
				// $('.j_alarmTable').removeData('num');
				$('.j_body').attr('cid', str_corpId);	//  存储集团id防止树节点更新时 操作组 丢失cid	
				n_onlineCnt = obj_corp.online,		// online count
				n_offlineCnt = obj_corp.offline;	// offline count
				
				if ( str_corpId && str_corpName ) {
					str_tempCorpName = str_corpName.length > 10 ? str_corpName.substr(0,10)+ '...' : str_corpName;
					str_html += '<li class="j_corp jstree-open" id="treeNode_'+ str_corpId +'"><a title="'+ str_corpName +'" corpid="'+ str_corpId +'" class="corpNode" href="#">'+ str_tempCorpName +'</a>';
				}
				fn_updateTerminalCount();	// lastinfo 每次更新在线个数 2013-07-29 kjj add
				//2状态 ,显示所有终端
				$('#terminalInfo td').removeClass('currentTNum');
				$('#carCount').parent().addClass('currentTNum');
				fn_displayTerminalNode('all');
				
				arr_autoCompleteData = [];
				arr_submenuGroups = [];
				if ( n_groupLength > 0 ) {
					str_html += '<ul>';
					str_groupFirstId = 'group_' + arr_groups[0].gid;
					
					// #todo obj_carsData = {};
					$('.j_carList').data('carsData', {});
					for ( var i = 0; i < n_groupLength; i++ ) {	// 添加组
						var obj_group = arr_groups[i],
							str_groupName = obj_group.name,
							n_groupNameLng = str_groupName.length,
							str_tempGroupName = n_groupNameLng>10 ? str_groupName.substr(0,10)+ '...' : str_groupName,
							str_groupId = obj_group.gid,
							obj_trackers = obj_group.trackers,
							arr_tempTids = [], //tid组
							n_trackersNum = 0,
							str_groupOpenClass = 'jstree-open';
							//arr_tids = [];
						
						arr_submenuGroups.push({'groupId': str_groupId, 'groupName': str_groupName});
						// 终端个数大于等于50
						if ( b_isFirst ) {
							//计算终端个数
							for ( var param in obj_trackers ) {
								n_trackersNum++;
							}
							if ( n_trackersNum >= 50 ) {
								str_groupOpenClass = 'jstree-close';
							}
							
							$('#corpTree').data('ftree', false);
						}
						str_html += '<li class="j_group '+ str_groupOpenClass +'" id="groupNode_'+ str_groupId +'"><a href="#" class="groupNode" groupId="'+ str_groupId +'" title="'+ str_groupName +'" id="group_'+ str_groupId +'">'+ str_tempGroupName +'</a><label class="groupCount_'+ str_groupId +'"></label>';
						
						if ( dlf.fn_isEmptyObj(obj_trackers) ) {	// 如果有终端返回
							str_html += '<ul>';
							var str_tempData = '';
							
							if ( str_tempFirstTid == '' ) {
								for( var param in obj_trackers ) {
									if ( param ) {
										str_tempData = param;
										break;
									}
								}
								str_tempFirstTid = 'leaf_' + param;	// 第一个分组的第一个定位器 id							
							}
							// 首次登录根据在线状态排序
							for ( var paramGroup in arr_groups ) {
								var obj_cGroup = arr_groups[paramGroup],
									obj_cNodeItems = obj_cGroup.trackers,
									arr_markers1 = [],
									obj_cTrackers = {};
								
								// 将对象转换成数组
								for ( var param0 in obj_cNodeItems ) {
									var obj_newItems = obj_cNodeItems[param0];
									
									obj_newItems['tid'] = param0;
									
									arr_markers1.push(obj_newItems);
								}
								
								//对转换完成的数组进行排序 在线在前
								arr_markers1.sort(function(a, b) {		
									var str_cLogin0 = parseInt(a.basic_info.login),
										str_cLogin1 = parseInt(b.basic_info.login);
									
									if ( str_cLogin0 < str_cLogin1 )  return 1;
									return -1;
								});
								//将排序后的数据转换成相应对象
								for ( var paramMarker in arr_markers1 ) {
									var obj_newItems = arr_markers1[paramMarker],
										str_newTid = obj_newItems.tid;
									
									obj_cTrackers[str_newTid] = obj_newItems;
								}
								arr_groups[paramGroup].trackers = obj_cTrackers;
							}
							// 将排序后数据重新赋值
							obj_trackers = arr_groups[i].trackers;
							// 根据排序后数据生成树节点
							for ( var param in obj_trackers ) {	// 添加组下面的定位器
								var obj_infoes = obj_trackers[param],
									obj_car = obj_infoes.basic_info,	// 终端基本信息
									obj_trace = obj_infoes.trace_info,	// 甩尾数据
									obj_track = obj_infoes.track_info,	//  开启追踪后的点数据
									arr_alarm = obj_infoes.alarm_info,	// 告警提示列表
									str_tid = param,
									str_oldAlias = obj_car.alias,
									str_dealAlias = dlf.fn_dealAlias(str_oldAlias),	// 处理中文后的别名
									str_alias = dlf.fn_encode(str_dealAlias),	// 编码后的别名			
									n_degree = obj_car.degree,	// icon_type
									n_iconType = obj_car.icon_type,	// icon_type
									str_mobile = obj_car.mobile,	// 车主手机号
									str_login = obj_car.login,
									n_enClon = obj_car.clongitude,
									n_enClat = obj_car.clatitude,
									n_lon = obj_car.longitude,
									n_lat = obj_car.latitude,
									obj_currentSelfMarker = obj_selfmarkers[str_tid];
									// n_mannual_status = obj_car.set_mannual_status,	// 退出时默认设防状态 kjj add in 2013.10.09
																	
								obj_car.trace_info = obj_trace;
								obj_car.track_info = obj_track;
								obj_car.tid = str_tid;
								
								// 1. 判断之前数据是否合法 
								// 2. 新数据是否合法: yes:更新  no: 不更新
								if ( dlf.fn_isEmptyObj(obj_tempCarsData) ) {
									if ( dlf.fn_isEmptyObj(obj_tempCarsData[str_tid]) ) {
										var obj_myCar = obj_tempCarsData[str_tid];
										
										if ( n_lon != 0 && n_lat != 0 && n_enClon != 0 && n_enClat != 0 ) {	// 新数据可用
											obj_carsData[str_tid] = obj_car;
										} else {
											obj_carsData[str_tid] = obj_myCar;
										}
									} else {
										obj_carsData[str_tid] = obj_car;
									}
								} else {
									obj_carsData[str_tid] = obj_car;
								}
								if ( obj_car.acc_message != ''  ) {
									dlf.fn_accCallback(obj_car.acc_message, str_tid);
								}
								// obj_carsData[str_tid] =  obj_car;
								arr_tempTids.push(str_tid); //tid组string 串
								if ( str_login == LOGINOUT ) {
									str_html += '<li class="jstree-leaf j_leafNode" id="leafNode_'+ str_tid +'"><a actiontrack="no" clogin="'+ obj_car.login+'" fob_status="" tid="'+ str_tid +'" keys_num="'+ obj_car.keys_num +'" title="'+ str_mobile +'" degree="'+ n_degree +'" icon_type='+ n_iconType +' class="terminalNode j_terminal jstree-draggable" href="#" id="leaf_'+ str_tid +'" alias="'+ str_alias +'">'+ str_alias +'</a></li>';
								} else {
									str_html += '<li class="jstree-leaf j_leafNode" id="leafNode_'+ str_tid +'"><a actiontrack="no" clogin="'+ obj_car.login+'" fob_status="" tid="'+ str_tid +'" keys_num="'+ obj_car.keys_num +'" title="'+ str_mobile +'" degree="'+ n_degree +'" icon_type='+ n_iconType +'  class="terminalNode j_terminal jstree-draggable" href="#" id="leaf_'+ str_tid +'" alias="'+ str_alias +'">'+ str_alias +'</a></li>';	
								}
								if ( str_tempTid != '' && str_tempTid == str_tid ) {
									b_flg = true;
								}
								/** 
								* 自动完成数据填充:根据旅客姓名,手机号和车牌号进行搜索
								*/
							    var str_tempLabel = str_mobile +' '+ obj_car.owner_mobile +' '+ str_oldAlias;
								//var str_tempLabel = str_mobile;
								//if ( str_alias != str_mobile ) {
								//	str_tempLabel = str_oldAlias +' '+ str_mobile +' '+ obj_car.owner_mobile;
								//}
								arr_autoCompleteData.push({label: str_tempLabel, value: str_tid});
								// 存储最新的marker信息
								if ( obj_currentSelfMarker ) {
									obj_tempSelfMarker[str_tid] = obj_currentSelfMarker;
									obj_selfmarkers[str_tid] = undefined;
								}
								dlf.fn_checkTrackDatas(str_tid);	// 清除开启追踪后的轨迹线数据
								// 显示告警提示列表
								for ( var ia = 0; ia <arr_alarm.length; ia++ ) {	// 添加组下面的定位器
									arr_alarm[ia].owner_mobile = obj_car.owner_mobile;
								}
								fn_updateAlarmList(arr_alarm);
								b_isHasTerminal = true;
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
					// 清除被删除的marker
					dlf.fn_createTerminalListClearLayer(obj_selfmarkers);
				}
				obj_selfmarkers = obj_tempSelfMarker;
				if ( !b_isHasTerminal ) {
					obj_carsData = {};
					$('.j_carList').data('carsData', {});
					// 显示告警提示列表
					dlf.fn_closeAlarmPanel();
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
				
				if ( str_resDataType ==  3 ) { // 如果数据类型变化是 3 ,前台自已判断一次是否要重新加载树
					b_isDifferentData = fn_lastinfoCompare(obj_newData);
				}
				if ( b_isDifferentData ) {	// lastinfo 与当前树节点对比 是否需要重新加载树节点
					dlf.fn_loadJsTree(str_tempNodeId, str_html);
					dlf.fn_initAutoComplete();
					$('#txtautoComplete').val('请输入定位器名称或号码').addClass('gray');	
				} else {
					// 更新组名和集团名还有 在线离线状态
					fn_updateTreeNode(obj_corp, b_isCloseTrackInfowindow);
				}
				dlf.fn_corpLastinfoSwitch(b_isCloseTrackInfowindow);
			}
		}
	}, 
	function (XMLHttpRequest, textStatus, errorThrown) {
		$('.j_body').data('intervalkey', false);
		dlf.fn_serverError(XMLHttpRequest, 'lastinfo');
	});
}

/**
*集团数据更新后是否要切换车辆信息
*/
window.dlf.fn_corpLastinfoSwitch = function(b_isCloseTrackInfowindow) {
	if ( b_isCloseTrackInfowindow ) {
		var obj_carItem = $('.j_carList .j_currentCar'),
			str_tid = obj_carItem.attr('tid');
			
		dlf.fn_switchCar(str_tid, obj_carItem); // 车辆列表切换
	}
}

/**
* 播放背景音乐
* todo 控制暂停
*/
function playMusic() {
	var sound="/static/images/bg.mp3",
		str_playClass = $('#playMusic').attr('class');
	
	if ( str_playClass.search('playMusic') != -1 ) {
		$("#showMusic").html('<audio id="playMusicAudio" autoplay><source src="'+sound+'" type="audio/mpeg"></audio>');
	}
}

/**
* kjj 2013-05-21 
* 如果终端有告警，显示告警数据、初始化li的click、mouseover、mouseout事件
* arr_alarm: 告警数据
*/
var obj_trackPoint = {};

function fn_updateAlarmList(arr_alarm) {
	var n_alarmLength = arr_alarm.length,
		obj_table = $('.j_alarmTable'),
		arr_temp = obj_table.data('markers'),
		arr_markers = arr_temp == undefined ? [] : arr_temp,
		obj_alarmCon = $('.j_alarm'),
		str_html = '',
		obj_markers = {},
		obj_arrowCon = $('.j_alarmPanelCon'),
		n_windowWidth = $('body').width(),
		n_alarmIconLeft = n_windowWidth - 418,
		obj_cacheAlertOption = $('#hidumobile').data('alertoption'),
		n_playMusicNum = 0,
		b_panel = $('.j_alarmPanel').is(':hidden');
	
	// 首次提示用户无告警数据
	if ( !$('.j_alarmTable').data('markers') && n_alarmLength <= 0 ) {
		obj_table.html('<li class="j_noDataAlarmPanel noDataAlarm">暂无告警信息</li>');
		return;
	} else {
		$('.j_noDataAlarmPanel').remove();
	}
	if ( n_alarmLength > 0 ) {
		//str_html+= '<li class="closeAlarm"></li>';
		
		for ( var x = 0; x < n_alarmLength; x++ ) {
			var obj_alarm = arr_alarm[x],
				str_oldAlias = obj_alarm.alias,
				str_alias = dlf.fn_encode(dlf.fn_dealAlias(str_oldAlias)),
				str_date = dlf.fn_changeNumToDateString(obj_alarm.timestamp),
				n_categroy = obj_alarm.category,
				obj_li = $('.j_alarmTable li');
			
			if ( obj_cacheAlertOption[n_categroy] == 1 ) {	
				str_html= '<li><label class="colorBlue" title="'+ str_oldAlias +'">'+ str_alias +'</label> 在 '+ str_date +' 发生了 <label class="colorRed">'+ dlf.fn_eventText(n_categroy) +' </label>告警</li>';
				
				if ( obj_li.length > 0 ) {
					obj_li.first().before(str_html);
				} else {
					obj_table.append(str_html);
				}
				$('.j_alarmPanelCon').css('top', $('.j_alarmTable').height()/2+218);
				arr_markers.unshift(obj_alarm);	// 存储所有的告警数据
				n_playMusicNum++;
			}
		}
		obj_table.data('markers', arr_markers);
		
		var n_tempLength = obj_li.length;
		
		if ( n_tempLength > 50 ) {	//当告警超过50个时， 不再累加
			for ( var x = 0; x <= n_tempLength-50; x++ ) {
				$('.j_alarmTable li').last().remove();
				delete arr_markers[arr_markers.length-1];
			}
		}
		if ( n_playMusicNum > 0 ) {
			playMusic();
			
			//如果列表是关闭的,则显示告警切换图标
			if ( b_panel ) {
				$('.j_alarmPanelCon').addClass('alarmWitchIcon');
			}
		} else {
			if ( $('.j_alarmTable li').length == 0 ) {
				obj_table.html('<li class="j_noDataAlarmPanel noDataAlarm">暂无告警信息</li>');
				return;
			}
		}
		// obj_alarmCon.show();
		/*
		$('.j_alarmPanel').show();
		$('.j_alarmArrowClick').css('backgroundPosition', '-20px -29px');
		obj_arrowCon.css({'left': $('.j_alarmPanel').offset().left - 18});
		*/
		//进行图标闪烁
	}
	/** 
	* 初始化奇偶行
	*/
	$('.j_alarmTable li').unbind('mouseover mouseout click').mouseover(function() {
		$(this).css({'background-color': '#FFFACD', 'cursor': 'pointer'});
	}).mouseout(function() {
		$(this).css('background-color', '');
	}).click(function() {
		var obj_this = $(this),
			obj_alarmTable = $('.j_alarmTable'),
			n_num = obj_alarmTable.data('num'),
			arr_markerList = obj_alarmTable.data('markers'),
			n_index = $(this).index(),
			obj_alarm = arr_markerList[n_index],
			n_category = obj_alarm.category,
			n_lng = obj_alarm.clongitude
			n_lat = obj_alarm.clatitude,
			str_tempTid = obj_alarm.tid,
			b_tempTidIndex = $('.j_alarm').data(str_tempTid+n_index);
			obj_centerPointer = dlf.fn_createMapPoint(n_lng, n_lat),
			obj_marker = obj_this.data('marker'),
			obj_regionShape = null;
		
		//如果已经添加过报警点,刚进行清除操作
		if ( b_tempTidIndex ) {
			dlf.fn_clearAlarmMarker();
		} else {
			// 清除地图上告警的图层
			dlf.fn_clearAlarmMarker();
			obj_this.addClass('clickedBg').siblings('li').removeClass('clickedBg');	// 添加背景色
			
			if ( n_lng != 0 && n_lat != 0 ) {	// 如果有经纬度则添加marker
				// obj_alarmTable.data('num', n_index);
				obj_marker = dlf.fn_addMarker(obj_alarm, 'alarmInfo', $('.j_currentCar').attr('tid'), n_index); // 添加标记
				obj_alarmTable.data('alarmMarker', obj_marker);	// 存储当前的marker 以便下次先删除再添加
				$('.j_alarm').data(str_tempTid+n_index, true);
				dlf.fn_setOptionsByType('center', obj_centerPointer);
				obj_this.data('marker', obj_marker);
				
				if ( dlf.fn_isBMap() ) {
					obj_marker.setTop(true);
				} else {
					obj_marker.setzIndex(10);
				}
			} else {
				dlf.fn_jNotifyMessage('该告警没有位置信息。', 'message', false, 3000);
				return;
			}
			dlf.fn_drawRegion(n_category, obj_alarm.region_id, obj_centerPointer, 1);	// 画围栏
			/*
			if ( n_category == 7 || n_category == 8 ) {	// 如果是进出围栏告警 画围栏
				var obj_circleData = {},
					n_regionLon = obj_alarm.bounds[1],
					n_regionLat = obj_alarm.bounds[0],
					obj_centerPoint = dlf.fn_createMapPoint(n_regionLon, n_regionLat);
				
				obj_circleData.radius = obj_alarm.region_radius;
				obj_circleData.longitude = n_regionLon;
				obj_circleData.latitude = n_regionLat;
				dlf.fn_setOptionsByType('viewport', [obj_centerPoint, obj_centerPointer]);
				obj_circle = dlf.fn_displayCircle(obj_circleData);	// 调用地图显示圆形
				obj_alarmTable.data('region', obj_circle);
			}*/
			var obj_position = obj_marker.getPosition();
			
			if ( dlf.fn_isBMap() ) {
				//obj_marker.selfInfoWindow.open(mapObj, obj_position);
				//obj_marker.openInfoWindow(new BMap.InfoWindow(dlf.fn_tipContents(obj_alarm, 'alarmInfo')));
				dlf.fn_createMapInfoWindow(obj_alarm, 'alarmInfo', n_index);
				obj_marker.openInfoWindow(obj_mapInfoWindow); // 显示吹出框	
			} else {
				// todo gaode.???
				//obj_marker.openInfoWindow(obj_marker.selfInfoWindow);
			}
			mapObj.setCenter(obj_position);
		}
	});
	
}

/**
* kjj 2013-05-24 
* 关闭告警列表 
*/
window.dlf.fn_closeAlarmPanel = function() {
	var obj_alarmPanel = $('.j_alarm'),
		obj_alarmTable = $('.j_alarmTable');

	// 清除告警提示的所有marker和region
	dlf.fn_clearAlarmMarker();
	$('.j_alarmTable').removeData('markers');
	obj_alarmTable.html('');
	obj_alarmPanel.hide();		
}

/**
* kjj 2013-05-22 
* 告警提示marker清除
* n_num: 要清除marker在li上的位置
*/
window.dlf.fn_clearAlarmMarker = function() {
	var obj_alarmTable = $('.j_alarmTable'),
		obj_alarmMarker = obj_alarmTable.data('alarmMarker'),
		obj_alarmRegion = obj_alarmTable.data('region');
	
	if ( obj_alarmMarker ) {
		dlf.fn_clearMapComponent(obj_alarmMarker);
		
		if ( !dlf.fn_isBMap() ) {
			mapObj.clearInfoWindow();
		}
		obj_alarmTable.removeData('alarmMarker');
	}
	if ( obj_alarmRegion ) {
		dlf.fn_clearMapComponent(obj_alarmRegion);
		obj_alarmTable.removeData('region');
	}
	$('.j_alarm').removeData();
}

/**
* 对node节点做遍历查找选中的节点
*/
window.dlf.fn_eachCheckedNode = function(str_eachNode) {
	$(str_eachNode).each(function(leafEvent) { 
		var str_tempLeafClass = $(this).attr('class'),
			str_tempLeafId = '#' + $(this).attr('id');
		
		if ( str_tempLeafClass.search('jstree-checked') != -1) {
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
		str_val = '请输入定位器名称';
	}
	// autocomplete	自动完成 初始化
	obj_compelete.autocomplete({
		source: arr_autoCompleteData,
		select: function(event, ui) {
			var obj_item = ui.item,
				str_tid = obj_item.value,
				obj_itemLi = $('.j_carList a[tid='+ str_tid +']'),
				str_crntTid = $('.j_leafNode a[class*='+ JSTREECLICKED +']').attr('tid');
			
			$('#txtautoComplete').val(ui.item.label);
			if ( str_crntTid == str_tid ) {
				//return false;
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
function fn_updateTreeNode(obj_corp, b_isCloseTrackInfowindow) {
	var arr_groups = obj_corp.groups,	// all groups 
		n_groupLength = arr_groups.length,	// group length
		str_corpName = obj_corp.name,	// corp name
		str_tempCorpName = str_corpName.length > 10 ? str_corpName.substr(0,10)+ '...' : str_corpName,
		str_corpId = obj_corp.cid,		// corp id
		obj_carsData = $('.j_carList').data('carsData');	// 存储所有定位器信息
	
	$('.j_corp a[corpId='+ str_corpId +']').html('<ins class="jstree-checkbox">&nbsp;</ins><ins class="jstree-icon">&nbsp;</ins>' + str_tempCorpName).attr('title', str_corpName);	// 更新集团名 <img src="/static/images/corpImages/corp.png">
	for ( var gIndex in arr_groups ) {
		var obj_group = arr_groups[gIndex],
			str_groupName = obj_group.name,
			n_groupNameLng = str_groupName.length,
			str_tempGroupName = dlf.fn_dealAlias(str_groupName), // n_groupNameLng>10 ? str_groupName.substr(0,10)+ '...' : str_groupName,
			obj_trackers = obj_group.trackers;	// 所有终端 arr_cars

		$('#group_'+ obj_group.gid).html('<ins class="jstree-checkbox">&nbsp;</ins><ins class="jstree-icon">&nbsp;</ins>' + str_tempGroupName).attr('title', str_groupName);	// 更新组名
		
		if ( dlf.fn_isEmptyObj(obj_trackers) ) {
			for ( var param in obj_trackers ) {
				var obj_infoes = obj_trackers[param],
					arr_alarm = obj_infoes.alarm_info,	// 终端基本信息
					obj_car = obj_infoes.basic_info,	// 终端基本信息
					obj_trace = obj_infoes.trace_info,	// 甩尾点数据
					obj_track = obj_infoes.track_info,	// 开启追踪点数据
					str_tid = param,
					n_login = obj_car.login,
					str_tmobile = obj_car.mobile,
					str_alias = obj_car.alias,
					n_iconType = obj_car.icon_type,	
					str_tempAlias = dlf.fn_encode(dlf.fn_dealAlias(str_alias)),
					str_decodeAlias = dlf.fn_decode(str_alias) || str_tmobile,
					obj_leaf = $('#leaf_' + str_tid),
					n_checked = $('#leafNode_' + str_tid).attr('class').indexOf('jstree-checked'),
					str_imgUrl = '',
					n_lon = obj_car.longitude,
					n_lat = obj_car.latitude,
					n_clon = obj_car.clongitude/NUMLNGLAT,	
					n_clat = obj_car.clatitude/NUMLNGLAT;
				
				if ( obj_car.acc_message != '' ) {
					dlf.fn_accCallback(obj_car.acc_message, str_tid);
				}
				obj_car.tid = str_tid;
				obj_carsData[str_tid] = obj_car;
				if ( n_login == LOGINOUT ) {
					str_imgUrl = 'offline.png';
				} else {
					str_imgUrl = 'online.png';
				}
				obj_leaf.html('<ins class="jstree-checkbox">&nbsp;</ins><ins class="jstree-icon">&nbsp;</ins>' + str_tempAlias).attr('title', str_tmobile).attr('clogin', n_login).attr('alias', str_decodeAlias).attr('icon_type', n_iconType);	
				
				if ( str_currentTid == str_tid  ) {
					if ( n_clon != 0 && n_clat != 0 ) {
						dlf.fn_updateTerminalInfo(obj_car);
					}					
				}
				if ( n_checked != -1 ) {	// 被选中终端
					if ( n_lon != 0 && n_lat != 0 ) {
						if ( b_isCloseTrackInfowindow ) {	// 如果是轨迹或告警切lastinfo都更新
							if ( n_clon != 0 && n_clat != 0 ) {
								obj_car.trace_info = obj_trace;
								obj_car.track_info = obj_track;
								dlf.fn_updateInfoData(obj_car); // 工具箱动态数据
								if ( dlf.fn_isEmptyObj(obj_trace) ) {	// 生成甩尾数据
									obj_trace.tid = str_tid;
								}
							} else {
								dlf.fn_translateToBMapPoint(n_lon, n_lat, 'actiontrack', obj_car, true);	// 前台偏转 kjj 2013-09-27
							}
						} else {
							//if ( str_currentTid == str_tid ) { // 只更新当前终端
								if ( n_clon != 0 && n_clat != 0 ) {
									obj_car.trace_info = obj_trace;
									obj_car.track_info = obj_track;
									dlf.fn_updateInfoData(obj_car); // 工具箱动态数据
									if ( dlf.fn_isEmptyObj(obj_trace) ) {	// 生成甩尾数据
										obj_trace.tid = str_tid;
									}
								} else {
									dlf.fn_translateToBMapPoint(n_lon, n_lat, 'actiontrack', obj_car, true);	// 前台偏转 kjj 2013-09-27
								}
							//}
						}				
					}
				}
				for ( var ia = 0; ia <arr_alarm.length; ia++ ) {	// 添加组下面的定位器
					arr_alarm[ia].owner_mobile = obj_car.owner_mobile;
				}
				fn_updateAlarmList(arr_alarm);
			}
		}
	}
	
	//更新autocomplete数据
	arr_autoCompleteData = [];
	
	for ( var autoParam in obj_carsData ) {
		var obj_tempAutoData = obj_carsData[autoParam],
			str_mobile = obj_tempAutoData.mobile,
			str_alias = obj_tempAutoData.alias,
			str_ownerMobile = obj_tempAutoData.owner_mobile,
			str_tempLabel = str_mobile +' '+ str_ownerMobile +' '+ str_alias;
		
		arr_autoCompleteData.push({label: str_tempLabel, value: autoParam});
	}
	dlf.fn_initAutoComplete();
	
	$('.j_carList').data('carsData', obj_carsData);	// 存储所有定位器信息
	fn_updateAllTerminalLogin();
	dlf.fn_setCorpIconDiffBrowser();
	
	//更新各分组下的终端在线/离线数
	var arr_oldGroups = $('.j_body').data('groups'),
		n_groupLength = arr_oldGroups.length;
	
	for ( var gIndex in arr_groups ) {
		var obj_group = arr_groups[gIndex],
			str_groupId = obj_group.gid,
			arr_trackers = obj_group.trackers;
		
		for ( var i = 0; i < n_groupLength; i++ ) {
			var obj_oldGroup = arr_oldGroups[i],
				str_oldGroupId = obj_oldGroup.gid,
				arr_oldTrackers = obj_oldGroup.trackers;
			
			if ( str_groupId == str_oldGroupId ) {
				for ( var param in arr_trackers ) { 
					var obj_car = arr_trackers[param];
					
					arr_oldTrackers[param] = obj_car;
				}
				break;
			}
		}			
	}
	fn_updateTerminalOnlineNum();
}

/**
* 更新各分组下的终端在/离线数目
*/
function fn_updateTerminalOnlineNum() {
	var arr_groups = $('.j_body').data('groups'),
		n_groupLength = arr_groups.length;
	
	for ( var i = 0; i < n_groupLength; i++ ) {
		var obj_group = arr_groups[i],
			str_groupId = obj_group.gid,
			obj_trackers = obj_group.trackers,
			n_maxGroupNum = 0,
			n_onlineGroupNum = 0;
		
		for ( var param in obj_trackers ) {
			var obj_car = obj_trackers[param],
				str_login = obj_car.basic_info.login;
			
			if ( str_login == 1 ) {
				n_onlineGroupNum++;
			}
			
			n_maxGroupNum++;
		}
		$('.groupCount_'+str_groupId).html('('+n_onlineGroupNum+'/'+n_maxGroupNum+')');
	}	
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

/**
* 设置定位器的图标
* n_iconType: 图标类型
* n_login:  在线状态
*/
function fn_setIconType(n_iconType, n_login) {
	var str_tempImgUrl = '';
	
	if ( n_iconType == 0 ) {	// 车
		str_tempImgUrl = 'icon_car';
	} else if ( n_iconType == 1  ) {//摩托车
		str_tempImgUrl = 'icon_moto';
	} else if ( n_iconType == 2 ) {	// 人
		str_tempImgUrl = 'icon_person';
	} else if ( n_iconType == 3 ) {
		str_tempImgUrl = 'icon_default';
	} else if ( n_iconType == 4 ) {// 警车
		str_tempImgUrl = 'icon_police';
	} else if ( n_iconType == 5 ) {// 警摩托车
		str_tempImgUrl = 'icon_policeMoto';
	}
	return str_tempImgUrl + n_login + '.png';
}

/**
* obj_this: 要更新的定位器对象
* 更新定位器在线离线图标
*/
window.dlf.fn_updateTerminalLogin = function(obj_this) {
	var	str_login = obj_this.attr('clogin'),
		n_iconType = obj_this.attr('icon_type'),	// icon_type
		str_imgUrl = '',
		str_color = '',
		obj_ins = obj_this.children('ins[class=jstree-icon]');	// todo

	if ( str_login == LOGINOUT ) {
		// str_imgUrl = 'offline.png';
		str_color = 'gray';
	} else {
		// str_imgUrl = 'online.png';
		str_color = '#24d317';
	}
	str_imgUrl = fn_setIconType(n_iconType, str_login);	// 设置图标url
	obj_this.css('color', str_color);
	obj_ins.css('background', 'url("/static/images/corpImages/terminalIcons/'+ str_imgUrl +'") no-repeat');
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
* str_tid: 集团用户右键参数设置中修改定位器名称
*/
window.dlf.fn_updateCorpCnum = function(cnum) {
	var obj_current = $('.j_terminal[tid='+str_currentTid+']'),
		str_cnum = cnum['corp_cnum'] == undefined ? cnum : cnum['corp_cnum'],
		str_tmobile = obj_current.attr('title'),
		str_tempAlias = str_cnum,
		str_dealAlias = '',
		str_tid = str_currentTid,
		obj_selfMarker = obj_selfmarkers[str_tid],
		b_mapType = dlf.fn_isBMap();
	
	if ( str_cnum == '' ) {
		str_tempAlias = str_tmobile;
	}
	str_dealAlias = dlf.fn_dealAlias(str_tempAlias);
	str_tempAlias = dlf.fn_encode(str_dealAlias);
	var str_decodeAlias = dlf.fn_decode(str_tempAlias);
	
	obj_current.html('<ins class="jstree-checkbox">&nbsp;</ins><ins class="jstree-icon">&nbsp;</ins>' + str_tempAlias).attr('alias', str_decodeAlias);
	dlf.fn_updateTerminalLogin(obj_current);
	for ( var index in arr_autoCompleteData ) {
		var obj_terminal = arr_autoCompleteData[index],
			str_newLabel = '',
			str_tempTid = obj_terminal.value,	// tid
			str_label = obj_terminal.label;	// alias 或 tmobile
		// 当前终端的、alias不是tmobile
		if ( str_tempTid == str_tid ) {
			str_newLabel = str_tmobile +' '+ $('.j_carList').data('carsData')[str_tempTid].owner_mobile +' '+ str_tempAlias;
			
			obj_terminal.label = str_newLabel;
			dlf.fn_initAutoComplete();
			// todo 修改marker上的定位器名称和label的定位器名称
		}
	}
	if ( obj_selfMarker ) {	// 修改 marker label 别名
		/*var	str_content = obj_selfMarker.selfInfoWindow.getContent(),
			n_beginNum = str_content.indexOf('定位器：')+4,
			n_endNum = str_content.indexOf('</h4>'),
			str_oldname = str_content.substring(n_beginNum, n_endNum),
			str_content = str_content.replace(str_oldname, str_tempAlias);
		*/
		if ( b_mapType ) {	// 百度地图修改label
			obj_selfMarker.getLabel().setContent(str_tempAlias);
		}
		//obj_selfmarkers[str_tid].selfInfoWindow.setContent(str_content);
		var obj_carDatas = $('.j_carList').data('carsData'),
			obj_tempCarData = obj_carDatas[str_tid];
			
		//obj_marker.openInfoWindow(new BMap.InfoWindow(dlf.fn_tipContents(obj_tempCarData, 'actiontrack')));
		if ( obj_selfMarker && obj_selfMarker.infoWindow ) {
			dlf.fn_createMapInfoWindow(obj_tempCarData, 'actiontrack');
			obj_selfMarker.openInfoWindow(obj_mapInfoWindow); // 显示吹出框
		}
		$('#markerWindowtitle h4[tid='+ str_tid +']').html('定位器：' + str_tempAlias);
		dlf.fn_updateOpenTrackStatusColor(str_tid);
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
					dlf.fn_corpGetCarData();	// 重新加载树 2013.09.04
					$('#corpTree').jstree('refresh',-1);
				} else {
					dlf.fn_jNotifyMessage(data.message, 'message', false, 3000);
					$.jstree.rollback(obj_rollBack);
				}
			}, 
			function (XMLHttpRequest, textStatus, errorThrown) {
				dlf.fn_serverError(XMLHttpRequest);
			});
		}
	}
}

/**
* 判断组名是否重复
*/
function fn_checkGroupName(str_name, node, str_gid) {
	var b_flg = false,
		n_length = str_name.length;
	
	if ( n_length > 0 ) {
		// 验证集团名称合法性
		if ( n_length > 20 ) {
			$.jstree.rollback(node);
			dlf.fn_jNotifyMessage('分组名称最大长度是20个汉字或字符！', 'message', false, 3000);
			b_flg = true;
		}
		if ( !/^[\u4e00-\u9fa5A-Za-z0-9]+$/.test(str_name) ) {
			$.jstree.rollback(node);
			dlf.fn_jNotifyMessage('分组名称只能由数字、英文、中文组成！', 'message', false, 3000); // 查询状态不正确,错误提示
			b_flg = true;
		}
	} else {
		$.jstree.rollback(node);
		dlf.fn_jNotifyMessage('分组名称不能为空！', 'message', false, 3000);
		b_flg = true;
	}
	
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
				dlf.fn_corpGetCarData();	// 重新加载树2013.09.04
				$('#corpTree').jstree('refresh',-1);
			} else {
				dlf.fn_jNotifyMessage(data.message, 'message', false, 3000); // 查询状态不正确,错误提示
				$.jstree.rollback(node);
				return false;
			}
		}, 
		function (XMLHttpRequest, textStatus, errorThrown) {
			dlf.fn_serverError(XMLHttpRequest);
		});
	}
}

/**
* 删除组
*/
function fn_removeGroup(node) {
	var str_param = node.children('a').attr('groupid'),
		str_groupTitle = node.children('a').attr('title');
	
	$('#vakata-contextmenu').hide();	// 右键菜单隐藏
	if ( confirm('确定要删除'+ str_groupTitle +'吗？') ) {
		$.delete_(GROUPS_URL + '?ids=' + str_param, '', function (data) {
			if ( data.status == 0 ) {
				$("#corpTree").jstree('remove');
				dlf.fn_corpGetCarData();	// 重新加载树2013.09.04
				$('#corpTree').jstree('refresh',-1);
			} else {
				dlf.fn_jNotifyMessage(data.message, 'message', false, 3000); // 查询状态不正确,错误提示
				return false;
			}
		}, 
		function (XMLHttpRequest, textStatus, errorThrown) {
			dlf.fn_serverError(XMLHttpRequest);
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
				dlf.fn_corpGetCarData(true);	// 重新加载树2013.09.04
			} else {
				dlf.fn_jNotifyMessage(data.message, 'message', false, 3000); // 执行操作失败，提示错误消息
				$.jstree.rollback(obj_rlbk);
			}
		}, 
		function (XMLHttpRequest, textStatus, errorThrown) {
			dlf.fn_serverError(XMLHttpRequest);
		});
	}
}

/**
* 重命名集团名称 
*/
function fn_renameCorp(cid, str_name, node) {
	var obj_param = {'name': str_name, 'cid': cid},
		n_length = str_name.length;
	
	// 验证集团名称合法性
	if ( n_length > 0 ) {
		if ( n_length > 20 ) {
			$.jstree.rollback(node);
			dlf.fn_jNotifyMessage('集团名称最多可输入20个汉字或字符！', 'message', false, 3000); // 查询状态不正确,错误提示
			return;
		}
		if ( !/^[\u4e00-\u9fa5A-Za-z0-9]+$/.test(str_name) ) {
			$.jstree.rollback(node);
			dlf.fn_jNotifyMessage('集团名称只能由中文、英文、数字组成！', 'message', false, 3000); // 查询状态不正确,错误提示
			return;
		}
	} else {
		$.jstree.rollback(node);
		dlf.fn_jNotifyMessage('集团名称不能为空！', 'message', false, 3000); // 查询状态不正确,错误提示
		return;
	}
	
	$.put_(CORP_URL, JSON.stringify(obj_param), function (data) {
		if ( data.status != 0 ) {
			dlf.fn_jNotifyMessage(data.message, 'message', false, 3000); // 查询状态不正确,错误提示
			$.jstree.rollback(node);
		} else {
			var str_tempCName = str_name.length > 10 ? str_name.substr(0,10)+ '...' : str_name;
			$('.corpNode').html('<ins class="jstree-checkbox">&nbsp;</ins><ins class="jstree-icon">&nbsp;</ins>' + str_tempCName).attr('title', str_name).children().eq(1).css('background', 'url("/static/images/corpImages/corp.png") 0px no-repeat');;
		}
	}, 
	function (XMLHttpRequest, textStatus, errorThrown) {
		dlf.fn_serverError(XMLHttpRequest);
	});
}

/**
* 添加单个定位器
*/
function fn_initCreateTerminal(obj_node, str_groupId) {
	$('.cTerminalList input[type=text]').val();
	$('#c_icon_type0').attr('checked', true);
	dlf.fn_dialogPosition('cTerminal'); // 新增定位器dialog显示
	dlf.fn_lockScreen(); // 添加页面遮罩
	dlf.fn_onInputBlur();	// input的鼠标样式
	/**
	* 初始化报警查询选择时间
	*/
	$('#hidGroupId').val(str_groupId);	// 保存groupId
	$('.j_corpData').val('');
	$('#hidTMobile').val('');
	$('#c_corp_push_status1, #c_login_permit0, #c_icon_type0, #c_biz_code_st1').attr('checked', 'checked');
	$('#c_corp_vibl').val(1);
}

/**
* 保存单个定位器
*/
window.dlf.fn_cTerminalSave = function() {
	var str_tmobile = $('#c_tmobile').val(),
		str_umobile = $('#c_umobile').val(),
		str_cnum = $('#c_cnum').val(),
		n_pushStatus = $('#cTerminalForm input[name="corp_cStatus"]input:checked').val(),
		n_loginPermit = $('#cTerminalForm input[name="clogin_permit"]input:checked').val(),
		n_corpVibl = $('#c_corp_vibl').val(),
		n_iconType = $('#cTerminalForm input[name="c_icon_type"]input:checked').val(), 
		n_bizType = $('#cTerminalForm input[name="c_corpBizcode"]input:checked').val(), 
		n_groupId = parseInt($('#hidGroupId').val()),
		obj_corpData = {};
		
	obj_corpData['tmobile'] = str_tmobile;
	obj_corpData['group_id'] = n_groupId;
	obj_corpData['umobile'] = str_umobile;
	obj_corpData['cnum'] = str_cnum;
	obj_corpData['icon_type'] = n_iconType;
	obj_corpData['biz_type'] = n_bizType;
	
	obj_corpData['push_status'] = n_pushStatus;
	obj_corpData['login_permit'] = n_loginPermit;
	obj_corpData['vibl'] = n_corpVibl;
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
		str_param = obj_target.attr('tid'),
		obj_clearDataWp = $('#clearDataWrapper'), 
		obj_ck = $('#clearDataCk');
		
	$('#vakata-contextmenu').hide();	// 右键菜单隐藏
	
	obj_clearDataWp.css({'left': '40%'}).show();
	obj_ck.removeAttr('checked');
	$('#clearDataMsgCon').html('确定要删除该定位器吗？');
	dlf.fn_lockScreen(); // 添加页面遮罩
	
	
	$('#clearDataSure').unbind('click').click(function(e) {
		obj_clearDataWp.hide();
		var n_clearFlag = obj_ck.attr('checked') ? 1 : 0,
			str_delTerminalUrl = TERMINALCORP_URL+'?tid='+ str_param +'&flag='+ n_clearFlag;
			
		dlf.fn_jNotifyMessage('定位器正在删除中' + WAITIMG, 'message', true);
		$.delete_(str_delTerminalUrl, '', function (data) {
			if ( data.status == 0 ) {
				if ( str_login == LOGINOUT ) {
					n_offlineCnt -= 1;
				} else {
					n_onlineCnt  -=1;
				}
				fn_updateTerminalCount();				
				$("#corpTree").jstree('remove');				
				// 删除地图marker
				obj_actionTrack[str_param].status = 'no';
				if ( obj_selfmarkers[str_param] ) {
					mapObj.removeOverlay(obj_selfmarkers[str_param]);
					delete obj_selfmarkers[str_param];
					delete [str_param];	// #todo obj_carsData
					dlf.fn_checkTrackDatas(str_param, true, $('.j_carList').data('carsData'));	// 删除开启追踪的轨迹线
				}
				var obj_current = $('.' + JSTREECLICKED),
					b_class = obj_current.hasClass('groupNode'),
					str_tid = obj_current.attr('tid') || $('.j_terminal').eq(0).attr('tid');
				
				if ( str_tid != undefined ) {
					obj_current = $('.j_terminal').eq(0);
					$('.' + JSTREECLICKED).removeClass(JSTREECLICKED);
					obj_current.addClass(JSTREECLICKED);
					dlf.fn_switchCar(str_tid, obj_current);
				} else {
					dlf.fn_initCarInfo();
				}
				dlf.fn_closeJNotifyMsg('#jNotifyMessage');  // 关闭消息提示
			} else {
				dlf.fn_jNotifyMessage(data.message, 'message', false, 3000); // 查询状态不正确,错误提示
			}
			dlf.fn_unLockScreen(); // 去除页面遮罩
		}, 
		function (XMLHttpRequest, textStatus, errorThrown) {
			dlf.fn_serverError(XMLHttpRequest);
		});
	});
	$('#clearDataCancel').unbind('click').click(function(e) {
		obj_clearDataWp.hide();
		dlf.fn_unLockScreen(); // 去除页面遮罩
	});
}

/**
* 批量删除数据回显
*/
function fn_initBatchDeleteData(obj_params) {
	var obj_param = {'tids': obj_params.tids, 'flag': 0},
		obj_clearDataWp = $('#clearDataWrapper'), 
		obj_maskLayer = $('#maskLayer'), 
		obj_ck = $('#clearDataCk');
	
	dlf.fn_echoData('batchDeleteTable', obj_params, '删除');
	$('.j_batchDeleteHead').html(obj_params.gname);	// 表头显示组名
		
	$('.j_batchDelete').unbind('click').bind('click', function() {
		dlf.fn_lockScreen(); // 添加页面遮罩
		obj_clearDataWp.css({'left': '40%'}).show();
		obj_ck.removeAttr('checked');
		$('#clearDataMsgCon').html('确定要删除以上定位器吗？');
		obj_maskLayer.css('z-index', 1002);
		
		$('#clearDataSure').unbind('click').click(function(e) {
			obj_clearDataWp.hide();
			obj_param.flag = obj_ck.attr('checked') ? 1 : 0;
			
			dlf.fn_jNotifyMessage('定位器正在删除中' + WAITIMG, 'message', true);
			
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
					
					$('.j_batchDelete').attr('disabled', true);	// 批量删除按钮变成灰色并且不可用
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
						dlf.fn_initCarInfo();
					}
					dlf.fn_closeJNotifyMsg('#jNotifyMessage');  // 关闭消息提示
				} else {
					dlf.fn_jNotifyMessage(data.message, 'message', false, 3000); // 查询状态不正确,错误提示
				} 
				dlf.fn_unLockScreen(); // 添加页面遮罩
				obj_maskLayer.css('z-index', 1000);
			}, 
			function (XMLHttpRequest, textStatus, errorThrown) {
				dlf.fn_serverError(XMLHttpRequest);
			});
		});
		$('#clearDataCancel').unbind('click').click(function(e) {
			obj_clearDataWp.hide();
			dlf.fn_unLockScreen(); // 去除页面遮罩
			obj_maskLayer.css('z-index', 1000);
		});
	});
	
}

/**
* 批量删除定位器
*/
function fn_batchRemoveTerminals(obj_params) {
	$('#vakata-contextmenu').hide();	// 右键菜单隐藏
	dlf.fn_dialogPosition('batchDelete');	// 设置dialog的位置
	// 数据回显
	$('.j_batchDelete').attr('disabled', false);	// 批量删除按钮变成绿色并且可用
	fn_initBatchDeleteData(obj_params);
}

/**
* 验证定位器手机号
*/
window.dlf.fn_checkTMobile = function(str_tmobile) {
	$.get_(CHECKMOBILE_URL + '/' + str_tmobile, '', function(data){
		if ( data.status != 0 ) {
			$('#hidTMobile').val('1');
			dlf.fn_jNotifyMessage(data.message, 'message', false, 5000);
			return;
		} else {
			$('#hidTMobile').val('');
		}
	}, 
	function (XMLHttpRequest, textStatus, errorThrown) {
		dlf.fn_serverError(XMLHttpRequest);
	});
}

/**
* 操作员手机号已存在。
*/
window.dlf.fn_checkOperatorMobile = function(str_tmobile) {
	$.get_(CHECKOPERATORMOBILE_URL + '/' + str_tmobile, '', function(data){
		if ( data.status != 0 ) {
			var str_msg = data.message;
			
			dlf.fn_jNotifyMessage(str_msg, 'message', false, 4000);
			$('#hidOperatorMobile').val(str_msg);
			return;
		} else {
			$('#hidOperatorMobile').val('');
		}
	}, 
	function (XMLHttpRequest, textStatus, errorThrown) {
		dlf.fn_serverError(XMLHttpRequest);
	});
}
/**
* 验证乘客手机号
*/
window.dlf.fn_checkPassengerMobile = function(str_tmobile) {
	$.get_(CHECKPASSENGERMOBILE_URL + '/' + str_tmobile, '', function(data){
		if ( data.status != 0 ) {
			dlf.fn_jNotifyMessage('乘客手机号已存在。', 'message', false, 5000);
			$('#hidPassengerMobile').val('1');
			return;
		} else {
			$('#hidPassengerMobile').val('');
		}
	}, 
	function (XMLHttpRequest, textStatus, errorThrown) {
		dlf.fn_serverError(XMLHttpRequest);
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
	}, 
	function (XMLHttpRequest, textStatus, errorThrown) {
		dlf.fn_serverError(XMLHttpRequest);
	});
}

/**
* 批量导入文件
*/
function fn_initBatchImport(gid, gname) {
	$('.fileInfoTable').html('');
	var obj_upfile = window.frames['fileUploadIframe'].document.getElementById('fileUploadTable'),
		obj_msg = window.frames['fileUploadIframe'].document.getElementById('jNotifyMessage');
		
	$(obj_upfile).remove().html('');
	$(obj_msg).html('');
	dlf.fn_dialogPosition('fileUpload');	// 设置dialog的位置
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

/**
* 重新激活终端
* str_tid: 激活终端tid
* kjj add in 2013-11.05
*/
window.dlf.fn_wakeUpTerminal = function(str_tmobile) {
	var obj_param = {'tmobile': str_tmobile};
	
	$.post_(CORP_REREGISTER_URL, JSON.stringify(obj_param), function(data){
		if ( data.status != 0 ) {
			dlf.fn_jNotifyMessage('激活指令已下发失败。', 'message', false, 4000);
			return;
		} else {
			dlf.fn_jNotifyMessage('激活指令下发成功。', 'message', false, 4000);
		}
	}, 
	function (XMLHttpRequest, textStatus, errorThrown) {
		dlf.fn_serverError(XMLHttpRequest);
	});
}
})();
