$(document).ready(function () {
    var modalMembershipCheck = new bootstrap.Modal(document.getElementById('modalCheckMembershipPoints'), {
        keyboard: false
    });

    $("#contact_form").validate({
        rules: {
            name: {
                required: true
            },
            email: {
                required: true,
                email: true
            },
            phone: {
                required: true
            },
            subject: {
                required: true
            },
            message: {
                required: true
            }
        },
        messages: {
            name: {
                required: "Please enter your name"},
            phone: {
                required: "Please enter your phone"},
            email: {
                required: "Please enter a valid email address"},
            subject: {
                required: "Please enter a subject"},
            message: {
                required: "Please enter a message"}
        },
        errorPlacement: function ($error, $element) {
            $element.appendTo($element.after($error));
        }
    })

    $('#contact_submit_button').click(function (e) {
        if (!$("#contact_form").valid()) {
            return false;
        } else {
            $(document).ajaxStart(function () {
                $('.loading').fadeIn(100);
            });
            $(document).ajaxStop(function () {
                $('.loading').delay(300).fadeOut(100);
            });
            $.ajax({
                url: '/',
                type: 'POST',
                data: $('#contact_form').serialize(),
                datatype: 'json'
            })
                .done(function (data) {
                    $("#name").val('');
                    $("#email").val('');
                    $("#address").val('');
                    $("#phone").val('');
                    $("#subject").val('');
                    $("#message").val('');
                    $('.sent-message').fadeIn(2000).delay(2000).fadeOut(500);
                })
                .fail(function (jqXHR, textStatus, errorThrown) {
                    $('.error-message').fadeIn(2000).delay(2000).fadeOut(500);
                });
        }
    });

    $('.check-membership-points').click(function (e) {
        $('html, body').animate({
        scrollTop: $("#hero").offset().top
    }, 2000);
    });
});

