$(function () {
    var CSRF_TOKEN = document.querySelector('meta[name="csrf-token"]').getAttribute('content');

    // Login
    $("#login_auth_form").submit(function (e) {
        e.preventDefault();

        $.ajax({
            type: 'POST',
            url: $(this).attr('action'),
            data: new FormData($(this)[0]),
            dataType: 'json',
            contentType: false,
            processData: false,
            headers: {
                'X-CSRFToken': CSRF_TOKEN
            },
            beforeSend: function() {
                $("#auth_submit_button").html("<i class='fas fa-spinner fa-pulse'></i>").attr('type', 'button');
            },
            success: function(response) {
                if(response.success) {
                    window.location.href = response.url;
                } else {
                    $("#auth_submit_button").html("Login").attr('type', 'submit');
                    var fdback = `<div class="alert alert-danger alert-dismissible fade show px-2 m-0 d-block w-100"><i class='fas fa-exclamation-circle'></i> ${response.sms} <button type="button" class="btn-close d-inline-block" data-bs-dismiss="alert"></button></div>`;
                    $("#login_auth_form .formsms").html(fdback).show();
                }
            },
            error: function(xhr, status, error) {
                console.log(error);
                $("#auth_submit_button").html("Login").attr('type', 'submit');
                var fdback = `<div class="alert alert-danger alert-dismissible fade show px-2 m-0 d-block w-100"><i class='fas fa-exclamation-circle'></i> Internal error. <button type="button" class="btn-close d-inline-block" data-bs-dismiss="alert"></button></div>`;
                $("#login_auth_form .formsms").html(fdback).show();
            }
        });
    });
})