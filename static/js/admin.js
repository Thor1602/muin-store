$(document).ready(function () {
    $.fn.digits = function () {
        return this.each(function () {
            $(this).text($(this).text().replace(/(\d)(?=(\d\d\d)+(?!\d))/g, "$1,"));
        })
    }
    $(".number-format").digits();
    var count = 1;
    $("#ingredientProductAdd").click(function () {
        var ingredient = $('#ingredientid').val();
        var weight = $('#input_weight_in_gram').val();
        if (weight !== '' && ingredient !== '') {
            var html = '<input type="text" class="form-control" name="ingredientid_' + count + '" value="' + ingredient + '"><input type="text" class="form-control" name="weight_in_gram_' + count + '" value="' + weight + '" required>'
            $('#ingredientsList').append(html);
            count = count + 1;
        }
        $('#ingredientid').val('');
        $('#input_weight_in_gram').val('');

    });
    var count_1 = 1;
    $("#packagingProductAdd").click(function () {
        var packaging = $('#packagingid').val();
        if (packaging !== '') {
            var html = '<input type="text" class="form-control" name="packagingid_' + count_1 + '" value="' + packaging + '" required>'
            $("#packagingList").append(html);
            count_1 = count_1 + 1;
        }
        $('#packagingid').val('');
    });

});
