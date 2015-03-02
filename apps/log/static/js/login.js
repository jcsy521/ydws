$(function() {
    $('tr.input input').focus(function() {
        $(this).parent().parent().addClass('highlight');
    });
    $('tr.input input').blur(function() {
        $(this).parent().parent().removeClass('highlight');
    });
});

window.onload = function() {
    var $imgElem = $('#captchaimg');
    $imgElem.click(function() {
        fn_getCaptcha($(this));
    });
    fn_getCaptcha($imgElem);
    // 获取后台验证码
    function fn_getCaptcha($obj) {
        $obj.attr('src', '/captcha?nocache=' + Math.random()).load(function() {
            $('#captchahash').val($.cookie('captchahash'));
        });
    }
}