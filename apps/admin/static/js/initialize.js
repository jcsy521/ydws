$(document).ready(function () {
	$.ajaxSetup({cache: false});
    $("button, input:submit, input:reset, .button").button();
	$("#accordion").accordion({autoHeight: false,navigation: true});
	
    $('#begDelegation').click(function () {
        $('.hideLeft').show();
    });
		
	/*
		*index  loginhistory dataTable style
	*/
	$('#loginhistory').dataTable({
		"aaSorting": [[0, "desc" ]],
		"bScrollCollapse": true,
		"bJQueryUI": true,
		"bProcessing": true,
		"sPaginationType": "full_numbers",
		"oLanguage": {
			"sUrl":"/static/js/dataTables.zh_CN.txt"
		}
	});
	
    $('#loginhistory tr').hover(
		function(){
			$(this).children().css({
				'background-color' : '#87CEFF'
			});
		},function(){
			$(this).children().removeAttr('style');
		}
	);

	$('.hideLeft').toggle(function () {
		$('#left').hide();
		$('#right').css({'width':'99%'});
		$('.hideLeft').hide();
        $('.hideRight').show();
	}, function () {
		$('#left').show();
		$('#right').css({'width':'82%'});
        $('.hideLeft').show();
        $('.hideRight').hide();
	});
    $('#adminUser').click(function () {
        $('#toggle').toggle('fast');
    });
	
	// set left and right width 
	var n_width = $(window).width() - 20;
	$('#logo').width(n_width-15);
	$('#content').width(n_width);
	$('#right').width(n_width - 170);

	$(window).resize(function() {
		var n_width = $(window).width() - 20;
		$('#logo').width(n_width-15);
		$('#content').width(n_width);
		$('#right').width(n_width - 170);
	});
});
/*
	*点击左侧菜单获得URL传递给 iframe的src
*/
function fn_CreateIframeSrc(url) {
	if ( url == '/user/search' ) {
		var element = document.getElementById('cacheDatas');
		$(element).children().remove();
	}
	$('#contantIframe').attr('src',url);
}
