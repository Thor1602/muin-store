
$(document).ready(function () {
    var modalMembershipCheck = new bootstrap.Modal(document.getElementById('modalCheckMembershipPoints'), {
        keyboard: false
    });
    $('.check-membership-points').click(function (e) {
        $('html, body').animate({
        scrollTop: $("#hero").offset().top
    }, 2000);
        modalMembershipCheck.show();
    });

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

// MAIN JS FILE

function sendLinkCustom() {
    Kakao.init('89b7805630fad951b149909a300389f8')
    Kakao.Link.sendDefault({
        objectType: 'feed',
        content: {
            title: 'It is me',
            description: 'Odin grew to regard Týr as a threat to his power, correctly suspecting him of plotting with the giants. As a result, Odin had Týr imprisoned and spread rumors that he had died. As a result, everyone in the Nine Realms believed Týr to be gone fore',
        }
    })
}

try {
    function sendLinkDefault() {
        Kakao.init('89b7805630fad951b149909a300389f8')
        Kakao.Link.sendDefault({
            objectType: 'feed',
            content: {
                title: 'Sumin saranhe',
                description: 'Kim Sumin Saranhe',
                imageUrl:
                    'https://guardian.ng/wp-content/uploads/2016/09/Love-Yoursself-974x548.jpg',
                link: {
                    mobileWebUrl: 'https://developers.kakao.com',
                    webUrl: 'https://developers.kakao.com',
                },
            },
            social: {
                likeCount: 20,
                commentCount: 10,
                sharedCount: 20,
            },
            buttons: [
                {
                    title: '웹으로 보기',
                    link: {
                        mobileWebUrl: 'https://developers.kakao.com',
                        webUrl: 'https://developers.kakao.com',
                    },
                },
                {
                    title: '앱으로 보기',
                    link: {
                        mobileWebUrl: 'https://developers.kakao.com',
                        webUrl: 'https://developers.kakao.com',
                    },
                },
            ],
        })
    }

    window.kakaoDemoCallback && window.kakaoDemoCallback()
} catch (e) {
    window.kakaoDemoException && window.kakaoDemoException(e)
}


document.addEventListener('DOMContentLoaded', () => {
    "use strict";

    /**
     * Preloader
     */
    const preloader = document.querySelector('#preloader');
    if (preloader) {
        window.addEventListener('load', () => {
            preloader.remove();
        });
    }

    /**
     * Sticky Header on Scroll
     */
    const selectHeader = document.querySelector('#header');
    if (selectHeader) {
        let headerOffset = selectHeader.offsetTop;
        let nextElement = selectHeader.nextElementSibling;

        const headerFixed = () => {
            if ((headerOffset - window.scrollY) <= 0) {
                selectHeader.classList.add('sticked');
                if (nextElement) nextElement.classList.add('sticked-header-offset');
            } else {
                selectHeader.classList.remove('sticked');
                if (nextElement) nextElement.classList.remove('sticked-header-offset');
            }
        }
        window.addEventListener('load', headerFixed);
        document.addEventListener('scroll', headerFixed);
    }

    /**
     * Navbar links active state on scroll
     */
    let navbarlinks = document.querySelectorAll('#navbar a');

    function navbarlinksActive() {
        navbarlinks.forEach(navbarlink => {

            if (!navbarlink.hash) return;

            let section = document.querySelector(navbarlink.hash);
            if (!section) return;

            let position = window.scrollY + 200;

            if (position >= section.offsetTop && position <= (section.offsetTop + section.offsetHeight)) {
                navbarlink.classList.add('active');
            } else {
                navbarlink.classList.remove('active');
            }
        })
    }

    window.addEventListener('load', navbarlinksActive);
    document.addEventListener('scroll', navbarlinksActive);

    /**
     * Mobile nav toggle
     */
    const mobileNavShow = document.querySelector('.mobile-nav-show');
    const mobileNavHide = document.querySelector('.mobile-nav-hide');

    document.querySelectorAll('.mobile-nav-toggle').forEach(el => {
        el.addEventListener('click', function (event) {
            event.preventDefault();
            mobileNavToogle();
        })
    });

    function mobileNavToogle() {
        document.querySelector('body').classList.toggle('mobile-nav-active');
        mobileNavShow.classList.toggle('d-none');
        mobileNavHide.classList.toggle('d-none');
    }

    /**
     * Hide mobile nav on same-page/hash links
     */
    document.querySelectorAll('#navbar a').forEach(navbarlink => {

        if (!navbarlink.hash) return;

        let section = document.querySelector(navbarlink.hash);
        if (!section) return;

        navbarlink.addEventListener('click', () => {
            if (document.querySelector('.mobile-nav-active')) {
                mobileNavToogle();
            }
        });

    });

    /**
     * Toggle mobile nav dropdowns
     */
    const navDropdowns = document.querySelectorAll('.navbar .dropdown > a');

    navDropdowns.forEach(el => {
        el.addEventListener('click', function (event) {
            if (document.querySelector('.mobile-nav-active')) {
                event.preventDefault();
                this.classList.toggle('active');
                this.nextElementSibling.classList.toggle('dropdown-active');

                let dropDownIndicator = this.querySelector('.dropdown-indicator');
                dropDownIndicator.classList.toggle('bi-chevron-up');
                dropDownIndicator.classList.toggle('bi-chevron-down');
            }
        })
    });

    /**
     * Initiate glightbox
     */
    const glightbox = GLightbox({
        selector: '.glightbox'
    });

    /**
     * Scroll top button
     */
    const scrollTop = document.querySelector('.scroll-top');
    if (scrollTop) {
        const togglescrollTop = function () {
            window.scrollY > 100 ? scrollTop.classList.add('active') : scrollTop.classList.remove('active');
        }
        window.addEventListener('load', togglescrollTop);
        document.addEventListener('scroll', togglescrollTop);
        scrollTop.addEventListener('click', window.scrollTo({
            top: 0,
            behavior: 'smooth'
        }));
    }

    /**
     * Initiate Pure Counter
     */
    new PureCounter();

    /**
     * Clients Slider
     */
    new Swiper('.clients-slider', {
        speed: 400,
        loop: true,
        autoplay: {
            delay: 5000,
            disableOnInteraction: false
        },
        slidesPerView: 'auto',
        pagination: {
            el: '.swiper-pagination',
            type: 'bullets',
            clickable: true
        },
        breakpoints: {
            320: {
                slidesPerView: 2,
                spaceBetween: 40
            },
            480: {
                slidesPerView: 3,
                spaceBetween: 60
            },
            640: {
                slidesPerView: 4,
                spaceBetween: 80
            },
            992: {
                slidesPerView: 6,
                spaceBetween: 120
            }
        }
    });

    /**
     * Init swiper slider with 1 slide at once in desktop view
     */
    new Swiper('.slides-1', {
        speed: 600,
        loop: true,
        autoplay: {
            delay: 5000,
            disableOnInteraction: false
        },
        slidesPerView: 'auto',
        pagination: {
            el: '.swiper-pagination',
            type: 'bullets',
            clickable: true
        },
        navigation: {
            nextEl: '.swiper-button-next',
            prevEl: '.swiper-button-prev',
        }
    });

    /**
     * Init swiper slider with 3 slides at once in desktop view
     */
    new Swiper('.slides-3', {
        speed: 600,
        loop: true,
        autoplay: {
            delay: 5000,
            disableOnInteraction: false
        },
        slidesPerView: 'auto',
        pagination: {
            el: '.swiper-pagination',
            type: 'bullets',
            clickable: true
        },
        navigation: {
            nextEl: '.swiper-button-next',
            prevEl: '.swiper-button-prev',
        },
        breakpoints: {
            320: {
                slidesPerView: 1,
                spaceBetween: 40
            },

            1200: {
                slidesPerView: 3,
            }
        }
    });

    /**
     * Porfolio isotope and filter
     */
    let portfolionIsotope = document.querySelector('.portfolio-isotope');

    if (portfolionIsotope) {

        let portfolioFilter = portfolionIsotope.getAttribute('data-portfolio-filter') ? portfolionIsotope.getAttribute('data-portfolio-filter') : '*';
        let portfolioLayout = portfolionIsotope.getAttribute('data-portfolio-layout') ? portfolionIsotope.getAttribute('data-portfolio-layout') : 'masonry';
        let portfolioSort = portfolionIsotope.getAttribute('data-portfolio-sort') ? portfolionIsotope.getAttribute('data-portfolio-sort') : 'original-order';

        window.addEventListener('load', () => {
            let portfolioIsotope = new Isotope(document.querySelector('.portfolio-container'), {
                itemSelector: '.portfolio-item',
                layoutMode: portfolioLayout,
                filter: portfolioFilter,
                sortBy: portfolioSort
            });
            let menuFilters = document.querySelectorAll('.portfolio-isotope .portfolio-flters li');
            menuFilters.forEach(function (el) {
                el.addEventListener('click', function () {
                    document.querySelector('.portfolio-isotope .portfolio-flters .filter-active').classList.remove('filter-active');
                    this.classList.add('filter-active');
                    portfolioIsotope.arrange({
                        filter: this.getAttribute('data-filter')
                    });
                    if (typeof aos_init === 'function') {
                        aos_init();
                    }
                }, false);
            });

        });

    }

    /**
     * Animation on scroll function and init
     */
    function aos_init() {
        AOS.init({
            duration: 1000,
            easing: 'ease-in-out',
            once: true,
            mirror: false
        });
    }

    window.addEventListener('load', () => {
        aos_init();
    });

});


