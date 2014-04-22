$(function() {
	if ( window.location.host == 'ajt.zhydgps.com' ) { 
		document.title='安捷通后台管理系统';
		$('#login').children('h1').eq(0).html('安捷通后台系统');
	} 
	/*
		*login img
	*/
    $("#captchaimg").click(function(){
        $(this).attr('src', '/captcha?nocache=' + Math.random());
        //todo: 
        setTimeout(function(){
		  // get the captchahash from the cookie
          var captchahash = $.cookie("captchahash")
          $("#captchahash").val(captchahash);
        }, 1000);
    });

    $("#captchaimg").click();

    $('tr.input input').focus(function() {
        $(this).parent().parent().addClass('highlight');
    });

    $('tr.input input').blur(function(){
        $(this).parent().parent().removeClass('highlight');
    });
	
	$('.cbtns,#login').corner('8px');
	$("button, input:submit, input:reset, .button").button();

    /**
        * 当session失效时，login页面会填入到iframe中
        * 这时判断是否找到captchaimg，如果找到说明本页面就是login页面
        * 所以整个父窗口显示登录页面
    */
    var id = parent.document.getElementById('loginIf');
    if (($('#captchaimg').length > 0) && ($(id).val() == $('#captchaimg')[0].id)) {
        alert('本次登陆已经超时，系统将重新进入登陆页面。');
        parent.window.location.replace('/');
    }
});
