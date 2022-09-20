$(document).ready(function () {
    test_kakao
    $('#test_kakao').click(function () {
        Kakao.API.request({
            url: '/v1/api/talk/profile',
            success: function (response) {
                alert(response);
            },
            fail: function (error) {
                alert(error);
            }
        });
    })

    $('#contact_submit_button').click(function () {
        $("#contact_form").validate({
            errorPlacement: function ($error, $element) {
                $error.appendTo($element.closest("span"));
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

        $(document).ajaxStart(function () {
            $('.loading').fadeIn(100);
        });
        $(document).ajaxStop(function () {
            $('.loading').delay(300).fadeOut(100);
        });
        $.ajax({
            url: '/contact_submission',
            type: 'POST',
            data: $('#contact_form').serialize(),
            datatype: 'json'
        })
            .done(function (data) {
                $('.sent-message').fadeIn(2000);
                $('.sent-message').delay(8000).fadeOut(500);

            })
            .fail(function (jqXHR, textStatus, errorThrown) {
                $('.error-message').fadeIn(2000);
                $('.error-message').delay(5000).fadeOut(500);
            });
    })

});

