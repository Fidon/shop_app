var CSRF_TOKEN = document.querySelector('meta[name="csrf-token"]').getAttribute('content');

// Dropdown menu
function dropMenu(event) {
    event.preventDefault();
    const $el = $(event.currentTarget);
    const $parent = $el.parent();
    const $icon2 = $el.find(':nth-child(2)');
    const $icon3 = $el.find(':nth-child(3)');
    
    if ($icon2.css('display') === 'none') {
        $icon3.hide();
        $icon2.fadeIn('fast');
    } else {
        $icon2.hide();
        $icon3.fadeIn('fast');
    }

    const $menu = $parent.find('.submenu');
    $menu.slideToggle('fast');
}
$(document).on('click', '#navbar .link .header', dropMenu);
$(document).on('click', '#menucanvas .link .header', dropMenu);


function signout(event) {
    event.preventDefault();
    $.ajax({
        type: 'POST',
        url: '/logout/',
        data: {},
        dataType: 'json',
        contentType: false,
        processData: false,
        headers: { 'X-CSRFToken': CSRF_TOKEN },
        success: function(response) {
          if (response.message === '200') {
            window.location.href = "/";
          }
        },
        error: function(xhr, status, error) {
          console.log(error);
        }
    });
}
$(document).on('click', '#log_out_btn', signout);


$("#container header .divbars span").click(function (event) { 
    event.preventDefault();
    const $canvaHtml = $('#navbar_canvas .offcanvas-body');

    if ($canvaHtml.html().trim().length === 0) {
        $canvaHtml.html($("#navbar").html());
    }
    
    $('#navbar_canvas').offcanvas('show');
});
