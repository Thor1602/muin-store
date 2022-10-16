$(document).ready(function () {
    var myModal = new bootstrap.Modal(document.getElementById('modalRegistrationComplete'), {
        keyboard: false,
        backdrop: 'static'
    });
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
                required: "Please enter your name"
            },
            last_name: {
                required: "Please enter your name"
            },
            phone_number: {
                required: "Please enter your phone"
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
                    if (data.code === "SUCCESS") {
                        $('.sent-message-add-membership').text(data.message).fadeIn(2000).delay(2000).fadeOut(500);
                    } else {
                        $('.error-message-add-membership').text(data.message).fadeIn(2000).delay(2000).fadeOut(500);
                    }
                })
                .fail(function (jqXHR, textStatus, errorThrown) {
                    $('.error-message-add-membership').fadeIn(2000).delay(2000).fadeOut(500);
                });

        }
    });


    $('#check_verification').click(function () {
        if ($("#verification_code").val().length !== 6) {
            $('.error-message-add-membership').text("The verification code has 6 numbers.").fadeIn(2000).delay(2000).fadeOut(500);
        } else {
            $(document).ajaxStart(function () {
                $("#check_verification").attr("disabled", "disabled");
                $('.loading-add-membership').fadeIn(100);
            });
            $(document).ajaxStop(function () {
                $('.loading-add-membership').fadeOut(100);
                $(document).unbind("ajaxStart")
            });
            $.ajax({
                url: '/register_membership',
                type: 'POST',
                data: $('#verification_code').serialize() + "&check_verification=",
                datatype: 'json',
            })
                .done(function (data) {
                    if (data.code === "SUCCESS") {
                        myModal.show();
                    } else {
                        $('.error-message-add-membership').text(data.message).fadeIn(2000).delay(2000).fadeOut(500);
                    }
                })
                .fail(function (jqXHR, textStatus, errorThrown) {
                    $('.error-message-add-membership').fadeIn(2000).delay(2000).fadeOut(500);
                });

        }
    });
    $('.go_to_homepage').click(function () {
        myModal.hide()
        $("#check_verification").removeAttr("disabled", "disabled");
        window.location.href = "/";
    });


});

