$(document).ready(function () {
    // Financial plan HTML
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

    // Cost Calculation HTML
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

    $("#addImage").click(function () {
        $("#image-registration").clone().appendTo("#image-list");
    });

    $.fn.digits = function () {
        return this.each(function () {
            $(this).text($(this).text().replace(/(\d)(?=(\d\d\d)+(?!\d))/g, "$1,"));
        })
    }

    function changeTable() {
        var totalBreakeven = 0;
        var turnoverTotal = 0;
        var turnoverAfterVat = 0;
        var totalNetProfitAfterVariableCosts = 0;
        var totalVariableCosts = 0;
        var totalVAT = 0;
        $('#break-even-table tbody tr').each(function () {
            var $tblrow = $(this);
            var price = $tblrow.find('.turnover-total').text();
            var varcost = $tblrow.find('.variable-costs').text();
            var breakevenProduct = $tblrow.find('.breakeven-per-product').text();
            var turnoverAfterVAT = $tblrow.find('.turnover-after-vat').text();
            var qty = $tblrow.find('.unit-product').val();
            if (!isNaN(qty) && !isNaN(price) && !isNaN(varcost) && !isNaN(breakevenProduct) && !isNaN(turnoverAfterVAT)) {
                var subTotal = parseInt(qty) * parseInt(price);
                var afterTax = parseInt(turnoverAfterVAT) * parseInt(qty);
                var netProfitAfterVariableCosts = parseInt(breakevenProduct) * parseInt(qty);
                var subTotalVariableCosts = parseInt(varcost) * parseInt(qty);
                var subTotalVAT = (parseInt(price) - parseInt(turnoverAfterVAT)) * parseInt(qty);
                $tblrow.find('.subtotal-vat').text(subTotalVAT).digits();
                $tblrow.find('.subtotal-variable-costs').text(subTotalVariableCosts).digits();
                $tblrow.find('.turnover-per-product').text(subTotal).digits();
                $tblrow.find('.turnover-per-product-after-vat').text(afterTax).digits();
                $tblrow.find('.turnover-per-product-after-varcost').text(netProfitAfterVariableCosts).digits();

                totalVAT += subTotalVAT;
                turnoverTotal += subTotal;
                turnoverAfterVat += afterTax;
                totalNetProfitAfterVariableCosts += netProfitAfterVariableCosts;
                totalVariableCosts += subTotalVariableCosts;
            }
        });
        var totalFixedCost = $("#fixedCostTotal").text();
        alert(parseInt(totalFixedCost));
        $('.total-turnover-after-vat').text(parseInt(turnoverAfterVat)).digits();
        $('.total-variable-costs').text(parseInt(totalVariableCosts)).digits();
        $('#total-turnover').text(parseInt(turnoverTotal)).digits();
        $('#total-vat').text(parseInt(totalVAT)).digits();
        var netProfit = turnoverAfterVat - (totalVariableCosts + totalFixedCost);
        $('#net-profit').text(netProfit).digits();
        var netProfitAfterCTax;
        if (netProfit > 0) {
            netProfitAfterCTax = netProfit - (netProfit * 0.11);

        } else {
            netProfitAfterCTax = netProfit;
        }
        $('#net-profit-after-tax').text(parseInt(netProfitAfterCTax)).digits();

    }


    $('.sales-table tbody tr').each(function () {
        var $tblrow = $(this);
        var incomes = $tblrow.find('.income-per-sale').text();
        var vats = $tblrow.find('.vat-per-sale').text();
        var var_costs = $tblrow.find('.variable-cost-per-sale').text();
        if (!isNaN(var_costs) && !isNaN(vats) && !isNaN(incomes)) {
            var total = parseInt(incomes) - (parseInt(var_costs) + parseInt(vats));
            $tblrow.find('.breakeven-per-sale').text(parseInt(total)).digits();
        }
    });

    $('.unit-product').change(function () {
        changeTable();
    });

    $('#period-toggle-sales-btn').click(function () {
        var $btnContent = $("#period-toggle-sales-btn").text();
        if ($btnContent === 'DAY') {
            $("#period-toggle-sales-btn").html('MONTH');
            $('.sale-toggle-table .row .col').each(function () {
                var $input_val = $(this);
                var input_val_1 = Math.ceil(($input_val.find('.period-toggle-sales').val()) * 25);
                $input_val.find('.period-toggle-sales').val(input_val_1).digits();
            });
        } else {
            $("#period-toggle-sales-btn").html('DAY');
            $('.sale-toggle-table .row .col').each(function () {
                var $input_val = $(this);
                var input_val_1 = Math.ceil(($input_val.find('.period-toggle-sales').val()) / 25);
                $input_val.find('.period-toggle-sales').val(input_val_1).digits();
            });
        }
    });
    $('#period-toggle-sales-simplified-btn').click(function () {
        var $btnContent = $('#period-toggle-sales-simplified-btn').text();
        if ($btnContent === 'DAY') {
            $("#period-toggle-sales-simplified-btn").html('MONTH');
            $('.sale-toggle-table-simplified .row .col').each(function () {
                var $input_val = $(this);
                var input_val_1 = Math.ceil(($input_val.find('.period-toggle-sales-simplified').val()) * 25);
                $input_val.find('.period-toggle-sales-simplified').val(input_val_1).digits();
            });
        } else {
            $("#period-toggle-sales-simplified-btn").html('DAY');
            $('.sale-toggle-table-simplified .row .col').each(function () {
                var $input_val = $(this);
                var input_val_1 = Math.ceil(($input_val.find('.period-toggle-sales-simplified').val()) / 25);
                $input_val.find('.period-toggle-sales-simplified').val(input_val_1).digits();
            });
        }
    });
    var breakevenpermonth = $("#break-even-per-month").text().replace(/[^\d.]/g, '');
    if (parseInt(breakevenpermonth) > 0) {
        $('#break-even-per-month').html(parseInt(breakevenpermonth) - (parseInt(breakevenpermonth) * 0.11)).css({
            'color': 'green',
            'font-weight': 'bold'
        }).digits();
    } else {
        $('#break-even-per-month').css({'color': 'red', 'font-weight': 'bold'});
    }
    $("input").click(function () {
        $(this).select();
    });
    changeTable();

});
