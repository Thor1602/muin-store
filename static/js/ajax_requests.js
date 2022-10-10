$(document).ready(function () {
    $("#contact_form").validate({
        errorPlacement: function ($error, $element) {
            $element.appendTo($element.after($error));
        },
        // Specify validation rules
        rules: {

            name: {
                required: true
            },
            email: {
                message: true
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
            name: "Please enter your name",
            phone: "Please enter your phone",
            email: "Please enter a valid email address",
            subject: "Please enter a subject",
            message: "Please enter a message"
        },
    })

    $('#contact_submit_button').click(function () {
        if (!$("#contact_form").valid()) { // Not Valid
            return false;
        } else {
            $(document).ajaxStart(function () {
                $('.loading').fadeIn(100);
            });
            $(document).ajaxStop(function () {
                $('.loading').delay(300).fadeOut(100);
                $(document).unbind("ajaxStart")

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
                    $('.sent-message').fadeIn(2000).delay(8000).fadeOut(500);

                })
                .fail(function (jqXHR, textStatus, errorThrown) {
                    $('.error-message').fadeIn(2000).delay(5000).fadeOut(500);
                });
        }
    })


    $("#get_verification_form").validate({
        // Specify validation rules
        rules: {
            first_name: {
                required: true,
            },
            last_name: {
                required: true
            },
            phone_number: {
                required: true,
            }
        },
        messages: {
            first_name: {
                required: "Please enter your name",
            },
            last_name: {
                required: "Please enter your name"
            },
            phone_number: {
                required: "Please enter your phone",
            }
        },
        errorPlacement: function ($error, $element) {
            $element.appendTo($element.after($error));
        }
    })

    $('#get_verification').click(function (e) {
        if (!$("#get_verification_form").valid()) {
            return false;
        } else {
            $(document).ajaxStart(function () {
                $('.spinner-get-verification').addClass('spinner-border spinner-border-sm');
                $("#first_name").attr("disabled", "disabled");
                $("#last_name").attr("disabled", "disabled");
                $("#phone_number").attr("disabled", "disabled");
            });
            $(document).ajaxStop(function () {
                $('.spinner-get-verification').removeClass('spinner-border spinner-border-sm');
                $(document).unbind("ajaxStart");
                $("#check_verification").removeAttr("disabled", "disabled");
            });
            $.ajax({
                url: '/register_membership',
                type: 'POST',
                data: $('#get_verification_form').serialize() + "&get_verification=",
                datatype: 'json'
            })
                .done(function (data) {
                    $('.sent-message-add-membership').text(data.message).fadeIn(2000).delay(8000).fadeOut(500);
                })
                .fail(function (jqXHR, textStatus, errorThrown) {
                    $('.error-message-add-membership').text(errorThrown.message).fadeIn(2000).delay(5000).fadeOut(500);
                });

        }
    });


    $('#check_verification').click(function () {
        if ($("#verification_code").val().length !== 6) {
            $('.error-message-add-membership').text("The verification code has 6 numbers.").fadeIn(2000).delay(5000).fadeOut(500);
        } else {
            $(document).ajaxStart(function () {
                $('.loading-add-membership').fadeIn(100);
            });
            $(document).ajaxStop(function () {
                $('.loading-add-membership').delay(300).fadeOut(100);
                $(document).unbind("ajaxStart")
            });
            $.ajax({
                url: '/register_membership',
                type: 'POST',
                data: $('#verification_code').serialize() + "&check_verification=",
                datatype: 'json',
            })
                .done(function (data) {
                    $('.sent-message-add-membership').text(data.message).fadeIn(2000).delay(8000).fadeOut(500);
                    window.location.href = "/";
                })
                .fail(function (jqXHR, textStatus, errorThrown) {
                    $('.error-message-add-membership').text(errorThrown.message).fadeIn(2000).delay(5000).fadeOut(500);
                });
        }
    })

});

